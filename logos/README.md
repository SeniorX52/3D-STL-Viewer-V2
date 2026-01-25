# Logo Files Directory

Place your logo image files here:

- **logo_v1.png** or **logo_v1.jpg** - First logo version
- **logo_v2.png** or **logo_v2.jpg** - Second logo version

## Supported Formats

- **PNG** - Recommended (supports transparency)
- **JPG/JPEG** - Supported (white background will be ignored)
- **STL** - Legacy support (pre-made 3D mesh)

## How It Works

The application automatically extracts the **dark/black regions** from your logo image:

1. Image is loaded and converted to grayscale
2. Dark pixels (< 50% brightness) are detected as the logo
3. Light/white pixels are treated as background (ignored)
4. Contours are extracted and converted to 3D mesh
5. Logo is engraved at 0.6mm depth

## Logo Guidelines

- Use **high contrast** images (dark logo on light background)
- Recommended size: 500x500 pixels or larger for good detail
- Simple shapes work best (avoid very thin lines)
- The black/dark parts will be engraved into the orthosis
- Logo will be scaled to approximately 15mm width

## Examples

✅ **Good**: Black logo on white background
✅ **Good**: Dark gray logo on light gray background  
✅ **Good**: PNG with transparent background and dark logo
❌ **Bad**: White logo on dark background (will invert)
❌ **Bad**: Very thin/complex lines (may not engrave well)
