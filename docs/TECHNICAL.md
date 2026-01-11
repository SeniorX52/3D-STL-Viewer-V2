# 3D Insole Adapter - Technical Documentation

**Author:** Mostafa Abdelaziz

## Overview

The 3D Insole Adapter is a Python-based desktop application built with PySide6 (Qt) for the GUI and VTK for 3D rendering. It processes STL files for orthotic insole customization.

---

## Table of Contents

1. [Architecture](#architecture)
2. [Project Structure](#project-structure)
3. [Dependencies](#dependencies)
4. [Core Modules](#core-modules)
5. [Key Algorithms](#key-algorithms)
6. [Building the Application](#building-the-application)
7. [API Reference](#api-reference)
8. [Extending the Application](#extending-the-application)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           main.py (MainWindow)                          │
│                         Application Entry Point                         │
│                      Qt Widgets, Event Handling                         │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
           ┌──────────────────────┴──────────────────────┐
           │                                             │
           ▼                                             ▼
┌─────────────────────────┐                 ┌─────────────────────────────┐
│   src/stl_processor.py  │                 │   src/mesh_viewer.py        │
│                         │                 │                             │
│  • STL Loading/Saving   │                 │  • VTK 3D Rendering         │
│  • Mesh Transformations │                 │  • Point Picking            │
│  • Boolean Operations   │                 │  • Camera Control           │
│  • Text Label Creation  │                 │  • Mesh Display             │
│  • Surface Wrapping     │                 │                             │
└─────────────────────────┘                 └─────────────────────────────┘
           │                                             │
           ▼                                             ▼
┌─────────────────────────┐                 ┌─────────────────────────────┐
│    External Libraries   │                 │      VTK Pipeline           │
│                         │                 │                             │
│  • trimesh (mesh ops)   │                 │  • vtkRenderer              │
│  • numpy (math)         │                 │  • vtkPolyDataMapper        │
│  • shapely (2D geom)    │                 │  • vtkActor                 │
│  • matplotlib (fonts)   │                 │  • vtkCellPicker            │
│  • MeshLib (booleans)   │                 │  • QVTKRenderWindowInteractor│
└─────────────────────────┘                 └─────────────────────────────┘
```

---

## Project Structure

```
3D-STL-Viewer/
├── main.py                    # Application entry point, MainWindow class
├── requirements.txt           # Python dependencies
├── build.spec                 # PyInstaller configuration
├── build.bat                  # Windows build script
├── installer.iss              # Inno Setup installer script
│
├── src/
│   ├── __init__.py
│   ├── stl_processor.py       # Core STL processing logic
│   └── mesh_viewer.py         # VTK-based 3D viewer widget
│
├── docs/
│   ├── USER_GUIDE.md          # Non-technical user documentation
│   ├── TECHNICAL.md           # This file
│   └── LABEL_METHOD.md        # Text labeling implementation details
│
└── models/                    # Sample STL files
    ├── foot/
    └── insole/
```

---

## Dependencies

### Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| PySide6 | ≥6.5.0 | Qt GUI framework |
| VTK | ≥9.2.0 | 3D visualization and rendering |
| trimesh | ≥4.0.0 | STL loading, mesh operations |
| numpy | ≥1.24.0 | Numerical computing |
| scipy | ≥1.11.0 | Scientific algorithms |
| shapely | ≥2.0.0 | 2D geometry operations |
| matplotlib | ≥3.5.0 | Font rendering for text labels |

### Optional Dependencies (for enhanced features)

| Package | Purpose |
|---------|---------|
| MeshLib (meshlib) | Robust boolean operations |
| manifold3d | Alternative boolean engine |
| mapbox-earcut | Polygon triangulation |

### Build Dependencies

| Package | Purpose |
|---------|---------|
| PyInstaller | Create standalone executable |
| Inno Setup | Create Windows installer (optional) |

---

## Core Modules

### main.py - MainWindow

The main application window containing all GUI elements and event handlers.

**Key Classes:**
- `MainWindow`: Main application window (QMainWindow subclass)
- `NoWheelSlider`: Custom QSlider that ignores wheel events

**Key Responsibilities:**
- Initialize GUI layout and controls
- Connect signals to slots
- Coordinate between processor and viewer
- Handle file I/O dialogs
- Manage application state

### src/stl_processor.py - STLProcessor

Core mesh processing engine handling all STL operations.

**Key Methods:**

```python
class STLProcessor:
    # File Operations
    def load_foot(self, filepath: str) -> trimesh.Trimesh
    def load_insole(self, filepath: str) -> trimesh.Trimesh
    def save_stl(self, filepath: str) -> str
    
    # Transformations
    def scale_insole(self, scale_x, scale_y, scale_z)
    def mirror_insole(self, axis: str)
    def transform_insole(self, translation, rotation)
    
    # Alignment
    def align_insole_to_foot() -> Tuple[np.ndarray, float]
    def auto_scale_to_foot() -> Tuple[float, float, float]
    
    # Labeling
    def add_text_label(self, text, position, depth, font_size, 
                       engrave, custom_position, custom_normal,
                       offset_x, offset_y, rotation, wrap_to_surface)
    
    # Internal Methods
    def _wrap_text_to_surface(...)      # Curved surface text wrapping
    def _create_text_mesh(...)          # Text to 3D mesh conversion
    def _meshlib_boolean_difference(...)# Boolean subtraction
```

### src/mesh_viewer.py - SimpleMeshViewer (VTKMeshViewer)

VTK-based 3D visualization widget with Qt integration.

**Key Features:**
- GPU-accelerated rendering via OpenGL
- Trackball camera interaction
- Point picking on mesh surfaces
- Multiple render modes (solid, wireframe, points)
- Reference point visualization

**Key Methods:**

```python
class VTKMeshViewer(QWidget):
    # Signals
    point_picked = Signal(object)           # Emits [x,y,z] for reference points
    label_point_picked = Signal(object, object)  # Emits (point, normal) for labels
    
    # Mesh Display
    def set_foot_mesh(self, mesh)
    def set_insole_mesh(self, mesh)
    
    # Picking
    def set_picking_mode(self, enabled: bool)
    def set_label_picking_mode(self, enabled: bool)
    
    # View Control
    def reset_view()
    def set_view(self, view: str)  # 'top', 'front', 'side', 'iso'
    def set_render_mode(self, mode: str)
```

---

## Key Algorithms

### 1. Surface-Conforming Text Wrapping

Located in `STLProcessor._wrap_text_to_surface()`

**Purpose:** Wrap flat text mesh around curved surfaces (e.g., insole sides)

**Algorithm:**
1. Compute local coordinate frame at picked point:
   - `normal`: Surface normal (points outward)
   - `text_right`: Tangent direction (text flows along this)
   - `text_up`: Vertical direction (character height)

2. Sample surface along text width:
   ```python
   for i in range(30):  # 30 sample points
       t = (i / 29) - 0.5  # -0.5 to 0.5
       ray_origin = center + text_right * (t * text_width) + normal * 100
       hit_point, hit_normal = ray_cast(ray_origin, -normal)
       samples.append((hit_point, hit_normal))
   ```

3. Deform text vertices:
   ```python
   for vertex in text_mesh.vertices:
       t = normalize_x(vertex.x)  # 0 to 1 along text width
       surf_pos, surf_normal = interpolate_samples(t)
       
       height_offset = vertex.y  # Character height
       depth_offset = map_depth(vertex.z, engrave)
       
       new_pos = surf_pos + text_up * height_offset + surf_normal * depth_offset
   ```

### 2. Text Mesh Generation

Located in `STLProcessor._create_text_mesh_matplotlib_fast()`

**Pipeline:**
```
Text String → matplotlib TextPath → Bezier Curves → Polygons → Extrusion → 3D Mesh
```

**Steps:**
1. Use matplotlib's `TextPath` to get font outlines
2. Sample Bezier curves (12 points for quadratic, 16 for cubic)
3. Convert to Shapely polygons
4. Clean with `buffer(0)` to fix self-intersections
5. Extrude using `trimesh.creation.extrude_polygon()`
6. Optionally subdivide mesh for smoother edges

### 3. Boolean Operations for Engraving

**Priority order:**
1. **MeshLib** - Most robust, handles complex geometry
2. **Manifold** - Fast, good for simple cases
3. **Blender** - Fallback option
4. **Visual engrave** - Concatenate with inverted normals (last resort)

```python
def engrave_text(insole_mesh, text_mesh):
    # Try MeshLib first
    if meshlib_boolean_difference(text_mesh):
        return success
    
    # Fallback to trimesh engines
    for engine in ['manifold', 'blender']:
        result = insole_mesh.difference(text_mesh, engine=engine)
        if result is not None:
            return result
    
    # Visual fallback
    text_mesh.invert()
    return concatenate([insole_mesh, text_mesh])
```

### 4. Reference Point Alignment

**Algorithm for `align_insole_to_foot()`:**

1. Calculate foot axis from heel to midpoint of metatarsals
2. Find insole principal axis using PCA or bounding box
3. Compute rotation to align axes
4. Translate insole centroid to foot centroid
5. Adjust Z position to place insole on top of foot

---

## Building the Application

### Development Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

### Building Standalone Executable

```bash
# Using build script (recommended)
build.bat

# Or manually
pyinstaller build.spec --clean
```

The executable is created in `dist/InsoleAdapter.exe`

### Creating Windows Installer

Using Inno Setup:

```bash
# Compile the installer script
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

This creates `InsoleAdapter_Setup.exe` in the `installer_output/` folder.

---

## API Reference

### STLProcessor

#### Constructor
```python
STLProcessor()
```

#### Properties
| Property | Type | Description |
|----------|------|-------------|
| `foot_mesh` | trimesh.Trimesh | Loaded foot mesh |
| `insole_mesh` | trimesh.Trimesh | Current insole mesh |
| `original_insole_mesh` | trimesh.Trimesh | Original insole (for reset) |
| `reference_points` | List[np.ndarray] | Three reference points |

#### Methods

**load_foot(filepath: str) -> trimesh.Trimesh**
Load a foot STL file.

**load_insole(filepath: str) -> trimesh.Trimesh**
Load an insole STL file.

**add_text_label(...) -> trimesh.Trimesh**
Add text label to insole surface.

Parameters:
- `text`: Label text
- `position`: 'heel', 'center', 'front', or 'custom'
- `depth`: Engraving/embossing depth (mm)
- `font_size`: Character height (mm)
- `engrave`: True for cut-in, False for raised
- `custom_position`: np.ndarray [x,y,z] for custom placement
- `custom_normal`: Surface normal at custom position
- `offset_x`, `offset_y`: Position offsets (mm)
- `rotation`: Rotation angle (degrees)
- `wrap_to_surface`: Enable curved surface wrapping
- `mirror_horizontal`: Flip text left-right (for backwards text)
- `mirror_vertical`: Flip text up-down (for upside-down text)

### VTKMeshViewer

#### Signals

| Signal | Parameters | Description |
|--------|------------|-------------|
| `point_picked` | np.ndarray | Emitted when reference point picked |
| `label_point_picked` | (np.ndarray, np.ndarray) | Emitted with (position, normal) for label |

#### Methods

**set_foot_mesh(mesh: trimesh.Trimesh)**
Display foot mesh in viewer.

**set_insole_mesh(mesh: trimesh.Trimesh)**
Display insole mesh in viewer.

**set_picking_mode(enabled: bool)**
Enable/disable reference point picking.

**set_label_picking_mode(enabled: bool)**
Enable/disable label position picking.

---

## Extending the Application

### Adding New Mesh Operations

1. Add method to `STLProcessor`:
```python
def my_operation(self, param1, param2):
    if self.insole_mesh is None:
        raise ValueError("No insole loaded")
    
    # Perform operation
    self.insole_mesh = modified_mesh
    return self.insole_mesh
```

2. Add UI control in `MainWindow._create_control_panel()`:
```python
self.my_button = QPushButton("My Operation")
self.my_button.clicked.connect(self._my_operation)
layout.addWidget(self.my_button)
```

3. Add handler method:
```python
def _my_operation(self):
    try:
        self.processor.my_operation(param1, param2)
        self.viewer.set_insole_mesh(self.processor.insole_mesh)
        self.status_bar.showMessage("Operation complete")
    except Exception as e:
        QMessageBox.critical(self, "Error", str(e))
```

### Adding New Render Modes

In `VTKMeshViewer`:

```python
def set_custom_render_mode(self):
    if self.insole_actor:
        prop = self.insole_actor.GetProperty()
        prop.SetRepresentationToSurface()
        prop.SetColor(1.0, 0.5, 0.0)  # Orange
        prop.SetOpacity(0.8)
    self.render()
```

---

## Performance Considerations

### Memory Management
- Large STL files can consume significant memory
- Use `trimesh.load()` with `process=False` for faster loading
- Clear unused meshes when loading new files

### Rendering Optimization
- VTK uses GPU acceleration automatically
- Reduce mesh complexity for smoother interaction
- Use `SetNumberOfContours()` sparingly

### Boolean Operation Performance
- MeshLib is fastest for complex operations
- Simpler meshes = faster booleans
- Consider mesh decimation for very complex text

---

## Troubleshooting (Developer)

### Common Build Issues

**"ModuleNotFoundError" in built executable:**
- Add missing module to `hiddenimports` in build.spec
- Run `pyinstaller --collect-all <module>` to find dependencies

**"DLL not found" errors:**
- Ensure all runtime DLLs are included
- Check `binaries` section in build.spec
- VTK DLLs may need explicit inclusion

**Boolean operations failing:**
- Ensure meshes are watertight (`mesh.is_watertight`)
- Use `mesh.fill_holes()` before operations
- Try different boolean engines

### Debugging

Enable console output in build.spec:
```python
exe = EXE(
    ...
    console=True,  # Set to True for debugging
)
```

---

*Last updated: January 2026*
