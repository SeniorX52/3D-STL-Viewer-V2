# 3D Insole Adapter

A professional Windows desktop application for adapting orthotic insoles to 3D foot scans. Create custom-fitted insoles with automatic scaling, text labels, and curved surface engraving.

![Platform](https://img.shields.io/badge/platform-Windows-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.10+-yellow)

**Author:** Mostafa Abdelaziz

---

## Quick Start (For Users)

### Installation

1. **Download** `InsoleAdapter_Setup.exe` from the [Releases](releases) page
2. **Run** the installer and follow the prompts
3. **Launch** from the Start Menu or Desktop shortcut

**That's it!** No Python, Blender, or other software required.

### Basic Workflow

1. **Load Files** - Import your foot scan and insole template (STL format)
2. **Place Points** - Mark 3 reference points on the foot
3. **Scale** - Auto-scale the insole to match foot dimensions
4. **Label** - Add patient name, side, and date
5. **Export** - Save the customized insole as STL

**Full User Guide:** [docs/USER_GUIDE.md](docs/USER_GUIDE.md)

---

## Features

### Core Functionality
- **STL File Support** - Load and save industry-standard STL files
- **Interactive 3D Viewer** - GPU-accelerated visualization with rotation, pan, zoom
- **Reference Point System** - Mark heel and metatarsals for accurate measurements
- **Automatic Scaling** - Scale insoles to match foot length and width
- **Manual Adjustments** - Fine-tune scale, position, and rotation

### Advanced Labeling
- **Surface-Conforming Text** - Labels wrap around curved surfaces (sides of insole)
- **Emboss or Engrave** - Raised or cut-in text
- **Custom Positioning** - Click anywhere on the insole to place labels
- **Adjustable Parameters** - Font size, depth, rotation, offset
- **Mirror Options** - Flip labels horizontally or vertically if needed

### Export Options
- **Auto-Generated Filenames** - `PatientName_L_2026-01-11_insole.stl`
- **Standard STL Format** - Compatible with all 3D printers and slicers

---

## Interface Overview

```
┌──────────────────────┬────────────────────────────────────────┐
│   CONTROL PANEL      │              3D VIEWER                 │
│                      │                                        │
│  ┌─ File Loading ──┐ │     ┌─────────────────────────┐       │
│  │ Load Foot       │ │     │                         │       │
│  │ Load Insole     │ │     │    [3D foot model]      │       │
│  └─────────────────┘ │     │    [3D insole model]    │       │
│                      │     │                         │       │
│  ┌─ Reference ─────┐ │     │    Rotate: Left-drag    │       │
│  │ Pick Points     │ │     │    Pan: Right-drag      │       │
│  └─────────────────┘ │     │    Zoom: Scroll         │       │
│                      │     └─────────────────────────┘       │
│  ┌─ Scaling ───────┐ │                                        │
│  │ Auto Scale      │ │     ┌───┐                              │
│  │ Manual X/Y/Z    │ │     │XYZ│ Axes indicator               │
│  └─────────────────┘ │     └───┘                              │
│                      │                                        │
│  ┌─ Text Label ────┐ │                                        │
│  │ Name: [______]  │ │                                        │
│  │ Side: [L/R]     │ │                                        │
│  │ Apply Label     │ │                                        │
│  └─────────────────┘ │                                        │
│                      │                                        │
│  ┌─ Export ────────┐ │                                        │
│  │ Export STL      │ │                                        │
│  └─────────────────┘ │                                        │
└──────────────────────┴────────────────────────────────────────┘
```

---

## For Developers

### Prerequisites

- Python 3.10 or later
- Windows 10/11 (for the desktop app)
- Git (optional)

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/your-repo/3d-insole-adapter.git
cd 3d-insole-adapter

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Project Structure

```
3D-STL-Viewer/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── build.spec             # PyInstaller configuration
├── build.bat              # Build script
├── installer.iss          # Inno Setup installer script
│
├── src/
│   ├── stl_processor.py   # Mesh processing engine
│   └── mesh_viewer.py     # VTK 3D viewer widget
│
├── docs/
│   ├── USER_GUIDE.md      # End-user documentation
│   ├── TECHNICAL.md       # Developer documentation
│   └── LABEL_METHOD.md    # Text label implementation
│
└── models/                # Sample STL files
    ├── foot/
    └── insole/
```

### Building the Executable

```bash
# Option 1: Use the build script (recommended)
build.bat

# Option 2: Manual PyInstaller
pip install pyinstaller
pyinstaller build.spec --clean
```

The executable is created at `dist/InsoleAdapter.exe`

### Creating the Windows Installer

1. Install [Inno Setup 6](https://jrsoftware.org/isdl.php)
2. Build the executable first using `build.bat`
3. Compile the installer:

```bash
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

The installer is created at `installer_output/InsoleAdapter_Setup_1.0.0.exe`

**Full Technical Docs:** [docs/TECHNICAL.md](docs/TECHNICAL.md)

---

## Dependencies

| Package | Purpose |
|---------|---------|
| PySide6 | Qt GUI framework |
| VTK | 3D visualization |
| trimesh | STL processing |
| numpy | Numerical computing |
| scipy | Scientific algorithms |
| shapely | 2D geometry |
| matplotlib | Font rendering |
| MeshLib | Boolean operations |

---

## Building a Distributable Package

### What End Users Get
The final installer includes everything needed:
- No Python installation required
- No Blender required  
- No development environment needed
- Single installer file
- Runs immediately after installation

### Build Steps

1. **Install build tools:**
   ```bash
   pip install pyinstaller
   ```

2. **Build executable:**
   ```bash
   pyinstaller build.spec --clean
   ```
   Or simply run `build.bat`

3. **Create installer (optional but recommended):**
   - Install [Inno Setup 6](https://jrsoftware.org/isdl.php)
   - Run: `"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss`

4. **Distribute:**
   - **Single EXE:** `dist/InsoleAdapter.exe` (portable, ~150-300MB)
   - **Installer:** `installer_output/InsoleAdapter_Setup_1.0.0.exe` (recommended for end users)

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| R | Reset view |
| T | Top view |
| F | Front view |
| I | Isometric view |
| P | Toggle settings panel |
| 1 | Wireframe mode |
| 2 | Solid mode |
| 3 | Points mode |
| Ctrl+O | Open foot STL |
| Ctrl+I | Open insole STL |
| Ctrl+E | Export insole |

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

## Acknowledgments

- [trimesh](https://trimsh.org/) - Mesh processing library
- [VTK](https://vtk.org/) - Visualization toolkit
- [PySide6](https://www.qt.io/) - Qt for Python
- [MeshLib](https://github.com/MeshInspector/MeshLib) - Boolean operations

---

## Support

- **User Guide:** [docs/USER_GUIDE.md](docs/USER_GUIDE.md)
- **Technical Docs:** [docs/TECHNICAL.md](docs/TECHNICAL.md)
- **Issues:** Create an issue on GitHub
