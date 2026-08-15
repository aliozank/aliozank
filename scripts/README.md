# Profile art generator

The repository treats the profile as a tiny generated site. All six panels
are standalone SVG files with their own backgrounds, typography and CSS
animation, so GitHub only has to render ordinary images.

## Rebuild locally

```bash
python scripts/generate_profile.py --offline
```

Remove `--offline` to refresh public GitHub statistics before rendering. The
script uses only the Python standard library. Copy, links and identity fields
live in `profile.config.json`.

## Automatic refresh

`.github/workflows/update-profile-art.yml` runs daily and on relevant pushes.
It reads the public contribution calendar and user API, regenerates the SVGs,
and commits only when the output changed. The workflow needs the default
`GITHUB_TOKEN` with `contents: write`; no personal token or third-party service
is required.

## Design constraints

- Canvas width: 1000 px for every panel.
- No `foreignObject`, JavaScript, remote fonts or external image hosts.
- Animation is CSS/SVG only and stops when reduced motion is preferred.
- Panels remain legible if animation or network access is unavailable.
