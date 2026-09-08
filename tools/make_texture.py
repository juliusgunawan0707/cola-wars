"""Tempel artwork label rata ke tata letak UV milik model kaleng GetLayers.

Kartu produk TIDAK dibuat di sini. Generator kaleng PIL sudah dibuang - Julius
yang me-render `assets/card_*.png` sendiri (fotorealistis, jauh lebih baik).

Model `deit_soda2.glb` memakai tekstur 2048x2048, tapi wrap kalengnya hanya
menempati pita kiri (u 0..0.586) dan artwork-nya DIPUTAR 90 derajat:

    sumbu V tekstur  = keliling kaleng
    sumbu U tekstur  = tinggi kaleng  (0 .. 0.586)

Bukti orientasi: rasio pita itu 1 : 0.586 = 1.71, sedangkan keliling/tinggi
kaleng 350 ml asli = (pi*66)/115 = 1.80. Orientasi yang satunya memberi 0.59,
jauh meleset.

Artwork sumber rasionya 2.155 (lebih lebar dari wrap kaleng asli), jadi ia
dipaskan pada KELILING dan disisakan pita warna merek di ujung tinggi —
persis seperti kaleng sungguhan yang polos di dekat bibir dan alas.

Pakai: python tools/make_texture.py
"""

from PIL import Image
import os

import make_condensation as cond

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIZE = 2048
BAND_U = 0.586          # lebar pita terpakai pada sumbu U
ROTATE = 90             # derajat CCW; dipastikan lewat tes kalibrasi UV di browser

# Artwork sumber memuat wordmark selebar ~65% gambar. Kalau gambar direntang ke
# 360 derajat penuh, wordmark membentang ~234 derajat dan tidak pernah terbaca
# utuh dari depan. WRAP_FILL mengecilkannya ke porsi keliling yang wajar.
# Bibir aluminium di tiap ujung tinggi kaleng. Nilainya kecil DENGAN SENGAJA:
# wilayah tekstur x > BAND_PX (tutup & alas bawaan model) sudah menyumbang
# silver sendiri, jadi nilai di sini bertumpuk dengan itu. 0,062 menghasilkan
# ~12% silver di layar - badan kalengnya ikut kelihatan silver.
RIM_FRAC = 0.024         # porsi tinggi kaleng yang jadi bibir aluminium
RIM_BLEND = 0.5          # porsi bibir yang dipakai untuk peralihan ke warna merek

ROLL = 0.19             # ~68 derajat; diukur dari posisi tanda R pada render

# WRAP_FILL harus PER MEREK, bukan satu nilai bersama: proporsi isi kedua artwork
# beda jauh. Wordmark Coca-Cola membentang ~65% lebar gambarnya, sedangkan globe
# Pepsi cuma ~23%. Dengan nilai yang sama, merek Pepsi tampil jauh lebih kecil di
# kaleng dan komposisinya jadi timpang.
JOBS = [
    ("labels/coke.png",  "assets/can_coke.jpg",  0.56),
    ("labels/pepsi.png", "assets/can_pepsi.jpg", 0.86),
]


def build(src_path, out_path, wrap_fill):
    art = Image.open(os.path.join(HERE, src_path)).convert("RGB")

    # warna merek diambil dari tepi kiri (sengaja dibuat polos saat generate)
    fill = art.getpixel((4, art.height // 2))

    band_px = int(round(SIZE * BAND_U))

    # skala seragam supaya proporsi logo terjaga
    new_w = int(round(SIZE * wrap_fill))
    new_h = int(round(art.height * new_w / art.width))
    art = art.resize((new_w, new_h), Image.LANCZOS)

    if new_h > band_px:                      # terlalu tinggi -> pangkas tengah
        top = (new_h - band_px) // 2
        art = art.crop((0, top, new_w, top + band_px))
        new_h = band_px

    # kanvas seukuran pita, artwork di tengah, sisanya warna merek
    band = Image.new("RGB", (SIZE, band_px), fill)
    band.paste(art, ((SIZE - new_w) // 2, (band_px - new_h) // 2))

    # putar mengelilingi kaleng: sumbu keliling itu siklik, jadi geser melingkar
    shift = int(round(SIZE * ROLL)) % SIZE
    if shift:
        rolled = Image.new("RGB", (SIZE, band_px), fill)
        rolled.paste(band.crop((SIZE - shift, 0, SIZE, band_px)), (0, 0))
        rolled.paste(band.crop((0, 0, SIZE - shift, band_px)), (shift, 0))
        band = rolled

    band = band.rotate(ROTATE, expand=True)  # -> (band_px, SIZE)

    # Wilayah di luar pita (x >= BAND_PX) memetakan TUTUP dan ALAS kaleng, dan
    # pada tekstur asli isinya abu aluminium (228,228,228) - bukan warna merek.
    # Mengisi seluruh kanvas dengan warna merek membuat tutup & alas ikut merah
    # atau biru. Maka: mulai dari tekstur asli, lalu timpa pita-nya saja.
    tex = Image.open(os.path.join(HERE, "assets/_glb_img1.webp")).convert("RGB")
    if tex.size != (SIZE, SIZE):
        tex = tex.resize((SIZE, SIZE), Image.LANCZOS)
    tex.paste(band, (0, 0))

    # Sumbu X tekstur = tinggi kaleng, jadi kolom di kedua ujungnya adalah bibir
    # atas dan alas. Pada kaleng sungguhan label tidak sampai ke ujung; di situ
    # aluminiumnya telanjang. Tanpa ini kaleng terlihat dicelup warna merek.
    band_px = int(round(SIZE * BAND_U))
    rim = int(band_px * RIM_FRAC)
    blend = max(1, int(rim * RIM_BLEND))
    alu = (214, 216, 219)
    px = tex.load()

    def paint_rim(x_from, x_to, step):
        """Cat bibir lalu luruh ke warna merek - tepi keras terbaca sebagai
        garis stiker, bukan aluminium yang tersambung ke badan."""
        for i, x in enumerate(range(x_from, x_to, step)):
            t = 0.0 if i < rim - blend else (i - (rim - blend)) / blend
            for y in range(SIZE):
                r0, g0, b0 = px[x, y]
                px[x, y] = (int(alu[0] * (1 - t) + r0 * t),
                            int(alu[1] * (1 - t) + g0 * t),
                            int(alu[2] * (1 - t) + b0 * t))

    paint_rim(0, rim, 1)                          # ujung atas
    paint_rim(band_px - 1, band_px - 1 - rim, -1)  # ujung bawah
    # Embun ditempel SETELAH paste supaya koordinatnya identik dengan normal
    # map — kalau bergeser, kilau muncul di tempat yang tidak ada butirannya.
    cond.apply_to_base(tex, DROPS)
    tex.save(os.path.join(HERE, out_path), quality=94, subsampling=0)

    print("%-22s -> %-22s pita=%dpx artwork=%dpx sisa=%dpx isi=%s"
          % (src_path, out_path, band_px, new_h, band_px - new_h, fill))


def build_mr():
    """Ratakan peta metallicRoughness.

    Teks "ORIGINAL DO BRASIL" dan tabel nutrisi Guarana ikut dipanggang ke peta
    ini, bukan cuma ke base color — tanpa diratakan, teks itu tetap membayang
    sebagai variasi kilap berapa pun label yang dipasang.
    """
    src = os.path.join(HERE, "assets/_glb_img2.webp")
    mr = Image.open(src).convert("RGB")
    band_px = int(round(SIZE * BAND_U))

    # Peta asli memberi metalness 1.0 pada pita label. Itu benar untuk aluminium
    # telanjang, tapi SALAH untuk permukaan bercetak: putih metalik dirender abu
    # dan merah metalik jadi kusam - persis wordmark pudar yang terlihat di layar.
    # Cat pada kaleng itu dielektrik dengan sedikit kilau logam di bawahnya.
    # G = roughness, B = metalness.
    flat = (255, 92, 34)          # roughness 0.36, metalness 0.13
    mr.paste(Image.new("RGB", (band_px, SIZE), flat), (0, 0))
    mr.save(os.path.join(HERE, "assets/can_mr.png"))
    print("%-22s -> %-22s pita diratakan ke %s" % ("glb metallicRoughness", "assets/can_mr.png", flat))


DROPS = cond.droplets()


if __name__ == "__main__":
    print("butiran embun: %d" % len(DROPS))
    cond.build_normal(DROPS)
    cond.build_env()
    build_mr()
    for src, out, wrap in JOBS:
        build(src, out, wrap)
