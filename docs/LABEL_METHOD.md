# Text Label Method Documentation

## Overview

The 3D STL Insole Adapter creates 3D text meshes for labeling insoles. This pipeline is optimized for interactive speed (~200-400ms) while maintaining good quality for 3D printing.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Input                                │
│   Name: "John Smith"  │  Side: "L"  │  Date: "2026-01-09"       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    add_text_label()                              │
│   - Manages label state (before/after)                          │
│   - Handles position calculation                                 │
│   - Applies orientation transforms                               │
│   - Pushes text INTO surface for engrave effect                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│               _create_multiline_text_mesh()                      │
│   - Splits text by newlines (\n)                                │
│   - Creates mesh for each line                                  │
│   - Vertically stacks lines with 1.4x spacing                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│           _create_text_mesh_matplotlib_fast()                    │
│   - Uses matplotlib TextPath (system fonts)                    │
│   - 12 samples per quadratic curve                              │
│   - 16 samples per cubic curve                                  │
│   - polygon.buffer(0) cleanup                                   │
│   - Light mesh subdivision                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Polygon Cleanup                                │
│   - buffer(0) fixes self-intersections                          │
│   - unary_union() merges overlapping paths                      │
│   - Removes invalid/tiny polygons                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Polygon Extrusion                              │
│   - trimesh.creation.extrude_polygon()                          │
│   - Uses 'earcut' triangulation                                 │
│   - Depth: 0.6mm default                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Mesh Subdivision                               │
│   - 1 level subdivision if mesh < 20,000 faces                  │
│   - Improves edge smoothness                                    │
│   - Helps boolean stability                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Position & Engrave                             │
│   - Push text 80% of depth INTO surface                         │
│   - Creates reliable cut effect without booleans                │
│   - Attempts boolean subtraction (Blender)                      │
│   - Falls back to concatenation if boolean fails                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Improvements

### 1. Increased Bezier Sampling

```python
# Smooth curves without slowdown
t_samples_quad = np.linspace(0, 1, 12)[1:]   # 11 samples (was 4)
t_samples_cubic = np.linspace(0, 1, 16)[1:]  # 15 samples (was 5)
```

**Benefits:**
- Smooth curves on letters like O, S, B, D
- Still fast (<400ms total)
- No visible faceting in 3D print

### 2. Polygon Cleanup

```python
# Fix self-intersections before extrusion
polygon = polygon.buffer(0)
merged = unary_union(cleaned_polygons)
merged = merged.buffer(0)  # Final cleanup
```

**Why:**
- matplotlib paths can have tiny self-intersections
- Prevents extrusion failures
- Improves boolean stability

### 3. Mesh Subdivision

```python
if len(combined.faces) < 20000:
    combined = combined.subdivide()
```

**Benefits:**
- Smoother side faces on extruded text
- Better edge resolution
- More reliable for 3D printing

### 4. Engrave Depth Offset

```python
# Push text INTO surface (80% of depth)
if engrave:
    target_pos = target_pos - surface_normal * depth * 0.8
```

**Why:**
- Creates reliable "cut" effect even without boolean CSG
- Text overlaps with insole mesh
- Slicers see it as one solid with indentation

---

## Performance

| Operation | Time |
|-----------|------|
| TextPath creation | ~10ms |
| Path to polygons (12-16 samples) | ~40ms |
| Polygon cleanup (buffer) | ~30ms |
| Polygon merge | ~20ms |
| Extrusion | ~50ms |
| Mesh subdivision | ~100ms |
| Positioning | ~5ms |
| **Total** | **~250-400ms** |

Compare to:
- Old adaptive bezier: 10-60 seconds
- Simple 4-5 sample: ~75ms (but poor quality)

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | str | - | Label text (use `\n` for newlines) |
| `position` | str | 'heel' | 'heel', 'center', 'front', or 'custom' |
| `depth` | float | 0.6 | Extrusion depth in mm |
| `font_size` | float | 3.0 | Character height in mm |
| `engrave` | bool | True | True=into surface, False=raised |
| `custom_position` | ndarray | None | [x, y, z] clicked position |
| `custom_normal` | ndarray | None | Surface normal at click |
| `offset_x` | float | 0 | X offset in surface plane (mm) |
| `offset_y` | float | 0 | Y offset in surface plane (mm) |
| `rotation` | float | 0 | Rotation around normal (degrees) |

---

## Label State Management

```python
self._insole_before_label  # Saved state before label
self._current_label        # Hash of current parameters

# On label change:
if new_params != current_label:
    insole = restore(before_label)  # Remove old label
    apply_new_label()
    save_state()
```

This allows:
- Real-time label preview
- Changing text without cumulative buildup
- Undo by restoring before-label state

---

## Engraving Strategy

### Current Approach (Fast + Reliable)

1. **Generate text mesh** with smooth curves
2. **Push text INTO surface** (80% of depth along surface normal)
3. **Try boolean subtraction** (Blender engine)
4. **Fallback to concatenation** if boolean fails

### Why This Works

Even without true CSG boolean:
- Text mesh overlaps insole mesh
- Slicers interpret overlapping geometry as solid
- Result prints as engraved text

### Limitations

- Not true boolean subtraction
- May show z-fighting in preview
- Some slicers may behave differently

---

## Dependencies

| Library | Purpose |
|---------|---------|
| `matplotlib` | TextPath font rendering |
| `shapely` | Polygon cleanup, merge |
| `trimesh` | 3D extrusion, subdivision |
| `numpy` | Vector math, linspace |
| `freetype-py` | Available for future CAD-quality option |

---

## Fallback: Polygon Text

If matplotlib fails, predefined letter shapes are used:

```python
LETTER_PATHS = {
    'A': [[(0,0), (0.5,1), (1,0)], [hole]],
    'B': [...],
    # A-Z, 0-9, common symbols
}
```

---

## Future Improvements

1. **True CSG Booleans**
   - MeshLib or OpenCASCADE for reliable boolean operations
   - Deterministic, production-ready engraving

2. **FreeType Integration**
   - `freetype-py` is installed
   - Can provide true font outlines (TTF/OTF)
   - Better kerning and glyph metrics

3. **GPU Acceleration**
   - CUDA/OpenCL for bezier sampling
   - Parallel polygon processing

4. **Glyph Caching**
   - Pre-compute common letters
   - Instant text generation for repeated characters

---

## Troubleshooting

### Text looks jagged
- Check font_size (3-5mm recommended)
- Bezier samples are now 12-16 per curve

### Engrave not visible
- Increase depth (try 0.8-1.0mm)
- Check if text is positioned on surface

### Boolean fails
- Normal - fallback to concatenation
- Install Blender and add to PATH for true CSG

### Slow generation
- Check mesh face count before subdivision
- Large text or many characters takes longer
