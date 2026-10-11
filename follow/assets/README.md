# FOLLOW — asset folder

Nothing in here is required: every visual has a procedural placeholder.
Drop files at these exact paths, then set `CONFIG.media.probeLocalAssets = true`
in `index.html` (the intro film is always tried, even with the flag off).

| Path | Used for |
|---|---|
| `follow-intro.mp4` | Cinematic intro film (muted, plays inline) |
| `brand/follow-logo.svg` | Header wordmark |
| `media/hero-backdrop.webp` | Faint background behind the 3D sphere |
| `map/danang-ground-2048.png` | Ground texture of the 3D city (2048², x/z −90…+90, north up, transparent water) |
| `scooter/follow-scooter-*.webp` | Reserved for photo renders (not used yet) |
| `sphere/<key>.webp` | 21 sphere cards — keys in the `SPHERE` array (e.g. `01-branded-scooter`) |
| `campaigns/<key>.webp` | 6 concept campaigns — `hospitality`, `beach-club`, `restaurant`, `tourism`, `events`, `lifestyle` |
