# Cola Wars

An interactive 3D product hero: a photoreal soda can you can spin with your
cursor, switching between two brands with one click — background, copy,
typography and motif all change with it.

**Live:** https://juliusgunawan0707.github.io/cola-wars/

> Concept / design exercise. Not affiliated with The Coca-Cola Company or PepsiCo.
> Brand marks are used here as the subject of a personal, non-commercial study.

## What it does

- A real 3D can rendered with Google `<model-viewer>`, tilting toward the cursor
- Condensation baked into both the base colour **and** a matching normal map, so
  droplets actually catch the light instead of reading as smudges
- Click a flavour: the can spins 720° behind a motion blur and swaps its texture
  at the peak, floating props implode and explode outward, and the page below
  changes its entire design language — Coca-Cola's script and dynamic ribbon
  versus Pepsi's 2023 electric-blue, uppercase and pulse motif
- A story section with historically accurate detail for each brand
- Dark (default) and light themes, English (default) and Bahasa Indonesia — both
  remembered per browser. The brand worlds stay red and blue in either theme; light
  only moves the neutrals.

## History, sourced

Coca-Cola was first poured at Jacobs' Pharmacy, Atlanta, on 8 May 1886 — five
cents a glass, about nine glasses a day that first year. Pepsi began in 1893 as
"Brad's Drink" at Caleb Bradham's New Bern pharmacy and took the name Pepsi-Cola
on 28 August 1898.

## Running it

Static — no build step. Serve the folder over HTTP (the page loads assets by
relative path, so opening `index.html` from disk will not work):

```bash
python -m http.server 8125
```

## Regenerating the can textures

`labels/*.png` are flat wrap artwork. `tools/make_texture.py` maps them onto the
model's UV layout and bakes the condensation:

```bash
python tools/make_texture.py
python tools/make_web_assets.py   # the smaller files the page actually loads
```

`make_web_assets.py` turns the masters (JPG/PNG) into WebP: the labels stay 2048 px
(588 KB -> 131 KB), the normal map is **lossless** on purpose — lossy WebP
subsamples chroma, and a normal map's R/G channels are its direction.

## Loading order

The can is on screen as soon as the *active* brand is textured: the GLB, the
Coca-Cola label, the MR map and the normal map are preloaded; Pepsi's label and
props load after the can appears. A transparent render of the can
(`assets/can_poster_coke.webp`) sits in the model's own box from the first paint
and crossfades to the live model. model-viewer (4.3.1) and the Draco decoder are
served from `assets/`, and the Google Fonts stylesheet no longer blocks the
parser — a slow route to Google used to hold the whole page blank.

If the camera, the model or the Coca-Cola label changes, re-capture the poster:
render the page at 1824x1140, call `modelViewer.toBlob({idealAspect:false})`
once the can is revealed, scale to 1152x720 and crop the transparent sides
symmetrically.

Two things about that model are worth knowing before editing it. Its texture is
2048×2048 but the can's wrap only occupies the left 58.6%, rotated 90° — the
texture's vertical axis is the can's circumference, the horizontal axis is its
height. And the brand text is baked into the *metallicRoughness* map as well as
the base colour, so replacing the base colour alone leaves the old wordmark
ghosting through as a difference in gloss.

## Credits

Layout and motion choreography adapted from the free "Soda" layer at
[getlayers.ai](https://getlayers.ai). All geometry handling, textures, props,
copy and the story section are original work.
