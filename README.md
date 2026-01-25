# Orthosis Customizer

A professional Windows desktop application for customizing orthosis STL files with logo and text engraving. Automatically generates left and right versions with patient information.

![Platform](https://img.shields.io/badge/platform-Windows-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.11+-yellow)

**Author:** Mostafa Abdelaziz

---

## Quick Start (For Users)

### Installation

1. **Download** `OrthosisCustomizer_Setup.exe` from the [Releases](releases) page
2. **Run** the installer and follow the prompts
3. **Launch** from the Start Menu or Desktop shortcut

**That's it!** No Python or other software required.

### Basic Workflow

1. **Load Orthosis** - Import your orthosis STL file (File → Open or drag & drop)
2. **Select Logo** - Choose between Logo V1 or V2
3. **Pick Logo Position** - Click "Pick Logo Position" then click on the RIGHT orthosis
4. **Adjust Logo** - Use sliders for offset, rotation, scale, and depth
5. **Apply Logo** - Click "Apply Logo" to engrave
6. **Enter Patient Info** - Fill in patient name (date auto-fills)
7. **Pick Text Position** - Click "Pick Text Position" then click on the RIGHT orthosis
8. **Apply Text** - Click "Apply Text" to engrave patient info
9. **Export** - File → Export Both to save `PatientName_Date_L.stl` and `PatientName_Date_R.stl`

---

## Features

### Core Functionality
- **STL File Support** - Load and save industry-standard STL files
- **Dual Viewport Display** - View LEFT (mirrored) and RIGHT (original) versions side-by-side
- **Automatic Mirroring** - Load once, get both L and R versions automatically
- **GPU-Accelerated 3D Viewer** - Smooth rotation, pan, and zoom with VTK
- **Camera Synchronization** - Both viewports move together
- **Settings Persistence** - All settings are saved and restored between sessions

### Logo Engraving
- **PNG Logo Support** - Load logos from PNG images (dark regions become engravings)
- **Two Logo Versions** - Switch between logo_v1 and logo_v2
- **Point-and-Click Placement** - Click directly on the mesh surface
- **Adjustable Parameters**:
  - Offset X/Y (position fine-tuning)
  - Rotation (-180° to +180°)
  - Scale (10% to 300%)
  - Depth (0.1mm to 3.0mm)
- **Horizontal Orientation** - Logo always stays level/horizontal
- **Internal Features** - Properly handles holes in letters (a, e, R, etc.)

### Text Engraving
- **Patient Name** - Multi-line text support
- **Auto Date** - Defaults to current date (YYYY-MM-DD format)
- **Adjustable Parameters**:
  - Offset X/Y
  - Rotation
  - Font size
- **Clean Rendering** - Uses matplotlib fonts with proper curves

### Settings Menu (Settings → Preferences)
- **Rendering Tab**: MSAA, FXAA, SSAO, mesh colors, lighting, materials
- **Engraving Tab**: Default depth, surface samples
- **Logo Tab**: Default size, simplification tolerance
- **Export Tab**: File format, naming pattern
- **Display Tab**: Show/hide labels, axes, camera options

### View Modes
- **Solid** - Standard surface rendering
- **Wireframe** - See mesh structure
- **Points** - Point cloud view
- **Solid + Edges** - Surface with edge lines

### Export
- **Dual File Export** - Exports both L and R versions in one click
- **Automatic Naming** - `PatientName_Date_L.stl` and `PatientName_Date_R.stl`
- **Standard STL Format** - Compatible with all 3D printers and slicers

---

## Interface Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│  File   View   Settings   Help                                          │
├──────────────────────┬───────────────────────┬─────────────────────────┤
│   CONTROL PANEL      │   LEFT VIEWPORT       │   RIGHT VIEWPORT        │
│                      │   (Mirrored - L)      │   (Original - R)        │
│  ┌─ Load ──────────┐ │                       │                         │
│  │ Open Orthosis   │ │                       │   Click here to pick    │
│  │ Open Folder     │ │                       │   logo/text positions   │
│  └─────────────────┘ │                       │                         │
│                      │   [3D Mesh View]      │   [3D Mesh View]        │
│  ┌─ Logo ──────────┐ │                       │                         │
│  │ ○V1  ○V2        │ │   Cameras move        │   Cameras move          │
│  │ Pick Position   │ │   together            │   together              │
│  │ Offset X [===]  │ │                       │                         │
│  │ Offset Y [===]  │ │                       │                         │
│  │ Rotation [===]  │ │                       │                         │
│  │ Scale    [===]  │ │                       │                         │
│  │ Depth    [===]  │ │                       │                         │
│  │ [Apply Logo]    │ │                       │                         │
│  └─────────────────┘ │                       │                         │
│                      │                       │                         │
│  ┌─ Patient Info ──┐ │                       │                         │
│  │ Name: [______]  │ │                       │                         │
│  │ Date: [______]  │ │                       │                         │
│  │ Pick Position   │ │                       │                         │
│  │ Offset X [===]  │ │                       │                         │
│  │ Rotation [===]  │ │                       │                         │
│  │ Font Size[===]  │ │                       │                         │
│  │ [Apply Text]    │ │                       │                         │
│  └─────────────────┘ │                       │                         │
│                      │                       │                         │
│  [Reset All]         │                       │                         │
└──────────────────────┴───────────────────────┴─────────────────────────┘
```

---

## Technical Specifications

| Feature | Specification |
|---------|---------------|
| Engraving Depth | Adjustable (default 0.6mm) |
| Export Format | Binary STL |
| Logo Files | logos/logo_v1.png, logos/logo_v2.png |
| Mirror Axis | Y-axis |
| Boolean Engine | MeshLib |
| Rendering | VTK with OpenGL |

---

## For Developers

### Requirements

```
Python 3.11+
PySide6>=6.5.0
VTK>=9.2.0
trimesh>=4.0.0
numpy>=1.24.0
meshlib>=2.0.0
matplotlib>=3.7.0
shapely>=2.0.0
scipy>=1.10.0
opencv-python>=4.8.0
Pillow>=10.0.0
```

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/orthosis-customizer.git
cd orthosis-customizer

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

### Building Executable

```bash
# Build with PyInstaller
pyinstaller build.spec --clean

# Create installer (requires Inno Setup)
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

### Project Structure

```
orthosis-customizer/
├── main.py                    # Application entry point & UI
├── src/
│   ├── __init__.py
│   ├── orthosis_processor.py  # Mesh processing (load, mirror, engrave)
│   └── dual_mesh_viewer.py    # VTK dual-viewport viewer
├── logos/
│   ├── logo_v1.png            # First logo option
│   └── logo_v2.png            # Second logo option
├── docs/
│   ├── USER_GUIDE.md
│   ├── TECHNICAL.md
│   └── LABEL_METHOD.md
├── icon.ico                   # Application icon
├── icon.png                   # Application icon (PNG)
├── build.spec                 # PyInstaller configuration
├── build.bat                  # Build script
├── installer.iss              # Inno Setup installer script
├── requirements.txt           # Python dependencies
└── README.md
```

---

## License

MIT License - See LICENSE file for details.

---

## Changelog

### Version 2.0.0
- Complete UI redesign with separate logo and text controls
- Added comprehensive Settings dialog with 5 tabs
- PNG logo support (replaces STL logos)
- Adjustable engraving parameters (offset, rotation, scale, depth)
- Proper internal feature handling (holes in letters)
- Consistent engraving depth on curved surfaces
- Settings persistence between sessions
- Improved rendering quality options
- Fixed logo/text orientation issues

### Version 1.0.0
- Initial release
- Dual viewport display (LEFT | RIGHT)
- Automatic L/R mirroring
- Logo selection and placement
- Text engraving (patient name + date)
- 0.6mm fixed engraving depth
- Dual STL export

---

## Support

For issues or feature requests, please open a GitHub issue.
