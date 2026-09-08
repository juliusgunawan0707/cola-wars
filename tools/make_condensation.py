"""Embun kaleng: butiran dipanggang ke base color DAN ke normal map.

Kenapa dua peta sekaligus. Butiran yang hanya digambar di base color terbaca
sebagai noda, bukan air — ia tidak punya relief sehingga tidak memantulkan apa
pun. Yang menjual kesan basah adalah SPEKULAR: tiap butir harus membelokkan
normal permukaan supaya menangkap cahaya lingkungan. Normal map bawaan GLB
kosong (datar biru-ungu), jadi ruang itu memang tersedia.

Kedua peta WAJIB memakai daftar butiran yang sama, kalau tidak kilau akan
muncul di tempat yang tidak ada butirannya. Karena itu posisi butiran
dibangkitkan sekali dengan seed tetap dan dipakai bersama.

Koreksi aspek: pada tekstur final sumbu X = tinggi kaleng, sumbu Y = keliling.
Satu piksel tidak mewakili jarak dunia yang sama di kedua sumbu (0,0020 vs
0,0025 satuan), jadi butiran digambar sebagai elips yang sedikit pipih agar
tampil bundar di permukaan kaleng.
"""

import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SIZE = 2048
BAND_PX = 1200          # lebar pita terpakai pada sumbu X (= 0.586 * 2048)
SEED = 20260906

# "embun halus merata": banyak butir kecil, sedikit butir sedang
N_FINE, R_FINE = 3200, (3, 9)
N_MID,  R_MID = 420, (10, 17)
N_BIG,  R_BIG = 70, (18, 26)

Y_SQUASH = 0.79         # koreksi aspek keliling vs tinggi
EDGE_PAD = 26           # jangan menempel di bibir/alas


def droplets():
    """Daftar butiran (x, y, r) — sama untuk base color dan normal map."""
    rng = random.Random(SEED)
    out = []
    for n, (lo, hi) in ((N_FINE, R_FINE), (N_MID, R_MID), (N_BIG, R_BIG)):
        for _ in range(n):
            r = rng.uniform(lo, hi)
            x = rng.uniform(EDGE_PAD + r, BAND_PX - EDGE_PAD - r)
            y = rng.uniform(0, SIZE)          # keliling itu siklik, boleh mepet
            out.append((x, y, r))
    return out


def _ellipse(d, x, y, r, fill):
    ry = r * Y_SQUASH
    d.ellipse([x - r, y - ry, x + r, y + ry], fill=fill)
    # keliling siklik: butiran di tepi harus muncul lagi di sisi seberang
    if y - ry < 0:
        d.ellipse([x - r, y - ry + SIZE, x + r, y + ry + SIZE], fill=fill)
    elif y + ry > SIZE:
        d.ellipse([x - r, y - ry - SIZE, x + r, y + ry - SIZE], fill=fill)


def apply_to_base(tex, drops):
    """Efek lensa halus pada base color: tepi sedikit gelap, inti sedikit terang."""
    shade = Image.new("L", (SIZE, SIZE), 128)
    d = ImageDraw.Draw(shade)
    for x, y, r in drops:
        _ellipse(d, x, y, r, 112)                    # bayangan tepi butir
    for x, y, r in drops:
        _ellipse(d, x - r * 0.16, y - r * 0.16, r * 0.62, 150)   # inti terang
    shade = shade.filter(ImageFilter.GaussianBlur(1.1))

    px, sh = tex.load(), shade.load()
    for yy in range(SIZE):
        for xx in range(BAND_PX):
            s = sh[xx, yy]
            if s == 128:
                continue
            k = s / 128.0
            r0, g0, b0 = px[xx, yy]
            px[xx, yy] = (min(255, int(r0 * k)), min(255, int(g0 * k)), min(255, int(b0 * k)))
    return tex


def build_normal(drops, out_path="assets/can_normal.png"):
    """Normal map: tiap butir jadi kubah kecil yang membelokkan pantulan."""
    nrm = Image.new("RGB", (SIZE, SIZE), (128, 128, 255))
    px = nrm.load()
    for x, y, r in drops:
        ry = max(1.0, r * Y_SQUASH)
        x0, x1 = int(x - r) - 1, int(x + r) + 2
        y0, y1 = int(y - ry) - 1, int(y + ry) + 2
        for yy in range(y0, y1):
            yw = yy % SIZE                      # keliling siklik
            for xx in range(x0, x1):
                if xx < 0 or xx >= BAND_PX:
                    continue
                dx = (xx - x) / r
                dy = (yy - y) / ry
                d2 = dx * dx + dy * dy
                if d2 >= 1.0:
                    continue
                # kubah: normal condong keluar makin ke tepi butir
                nz = math.sqrt(1.0 - d2)
                k = 0.55                        # kedalaman relief; >0.7 terlihat plastik
                nx, ny = dx * k, dy * k
                ln = math.sqrt(nx * nx + ny * ny + nz * nz)
                px[xx, yw] = (int((nx / ln) * 0.5 * 255 + 128),
                              int((ny / ln) * 0.5 * 255 + 128),
                              int((nz / ln) * 0.5 * 255 + 128))
    nrm.save(os.path.join(HERE, out_path))
    print("%-24s -> %s" % ("normal map embun", out_path))


def build_env(out_path="assets/env_cold.png", w=1024, h=512):
    """Environment map dingin.

    Ini yang membuat butiran terbaca sebagai AIR: tanpa tepi cahaya dingin,
    butir di badan merah tidak punya apa pun untuk dipantulkan. Key besar
    kebiruan di satu sisi, fill hangat lemah di sisi lain agar merah Coca-Cola
    tidak ikut membiru.
    """
    env = Image.new("RGB", (w, h))
    px = env.load()
    for y in range(h):
        v = y / (h - 1)
        # langit dingin di atas, lantai gelap di bawah
        top = (206, 226, 246)
        bot = (14, 16, 20)
        base = tuple(int(top[i] + (bot[i] - top[i]) * (v ** 0.85)) for i in range(3))
        for x in range(w):
            px[x, y] = base

    d = ImageDraw.Draw(env, "RGBA")
    # key dingin besar (kiri-atas) -> rim biru pada kaleng
    d.ellipse([w * 0.02, h * 0.02, w * 0.34, h * 0.52], fill=(226, 242, 255, 255))
    # fill hangat lemah (kanan) -> menjaga merah tetap merah
    d.ellipse([w * 0.62, h * 0.18, w * 0.92, h * 0.60], fill=(255, 232, 208, 150))
    # garis softbox tipis -> kilau memanjang di butiran
    d.rectangle([w * 0.40, h * 0.06, w * 0.52, h * 0.34], fill=(255, 255, 255, 210))

    env = env.filter(ImageFilter.GaussianBlur(w * 0.012))
    env.save(os.path.join(HERE, out_path))
    print("%-24s -> %s" % ("environment dingin", out_path))


if __name__ == "__main__":
    drops = droplets()
    print("butiran: %d" % len(drops))
    build_normal(drops)
    build_env()
