# FOLLOW — archive page

Single self-contained `index.html` (one `<style>`, one `<script>` at the end of `<body>`,
no framework, no bundler). It follows the reference archive page exactly — splash,
2× intro film with Skip, Fibonacci photo sphere with the headline on the sphere origin,
drag to rotate, 16vh scroll dolly, flat grid, FLIP lightbox, full-screen menu, custom
cursor, all breakpoints — adapted to the FOLLOW brand (black + electric blue,
Space Grotesk + Inter, FOLLOW copy).

## Run locally

```bash
npx http-server -p 8080 .    # or: python3 -m http.server 8080
```

Open <http://localhost:8080>. Opening the file directly also works.

## What is provisional

| Item | Status |
|---|---|
| Intro film | The reference CloudFront film (the eye transition), played at 2×. |
| 21 sphere / grid visuals | **Provisional FOLLOW visuals**, drawn in the browser. Replace them by filling `thumb` (≈2500 px webp) and `full` (full-size still) on each entry of the `SHOTS` array at the top of the main script. Once a URL is set, it is decoded and downscaled per breakpoint exactly like the reference. |
| QR codes in the visuals | Decorative, not scannable. |
| Dashboard / map / concept visuals | Illustrations only, no real data. |
| Menu links | Same behaviour as the reference: "The Campaigns" opens the grid, the others close the menu. |
| Contact details | None shown (no verified email or phone yet). |

## Brand changes vs. the reference

- Wordmark and splash mark: `FOLLOW.` (blue full stop) instead of `Ethan Vale`.
- Headline: "Your Brand. Everywhere." (3 words, staggered reveal).
- Bio card → FOLLOW card (logo mark + short description), colophon → "Mobile advertising · Da Nang", splash tag → "Move. Be seen. Be remembered."
- Colours: `#05080F` background, `#F5FAFF` text, `#00BFFF` accents; fonts: Space Grotesk (in place of Playfair Display) + Inter.

Two technical adjustments, with no visual change to the layout:
`#headline` has `transform-style: preserve-3d`, and the zoom fades `.inner` rather than
`#headline`. Without them, Chromium cuts the title in half when a card crosses its plane.
The centering method is unchanged (negative half-width margin + `translateY(-50%)` on `.inner`).
