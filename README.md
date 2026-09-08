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
```

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
