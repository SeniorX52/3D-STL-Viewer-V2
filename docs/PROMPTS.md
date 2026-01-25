# Orthosis STL Mirror & Engrave Tool - Development Prompts

## PROJECT METADATA
```yaml
project_name: "Orthosis STL Mirror & Engrave Tool"
base_project: "3D-STL-Viewer-V2 (Insole Adapter)"
target_platform: Windows Desktop
language: Python 3.10+
gui_framework: PySide6
3d_engine: VTK
mesh_library: trimesh
csg_library: MeshLib (meshlib.mrmeshpy)
```

---

## SECTION 1: BASE PROJECT ANALYSIS

### 1.1 Current Project Structure
```
3D-STL-Viewer-V2/
├── main.py                    # 1823 lines - Main application & GUI
├── src/
│   ├── __init__.py
│   ├── mesh_viewer.py         # 735 lines - VTK-based 3D viewer
│   └── stl_processor.py       # 2524 lines - STL/mesh operations
├── models/
│   ├── foot/                  # Sample foot STL files
│   └── insole/                # Sample insole templates
├── logo/                      # Logo files (to be used in new project)
├── requirements.txt           # Dependencies
├── build.bat                  # Build script
├── build.spec                 # PyInstaller spec
└── installer.iss              # Inno Setup installer
```

### 1.2 Current Feature Mapping

| Current Feature | Location | Lines | Status in New Project |
|----------------|----------|-------|----------------------|
| Load STL files | main.py + stl_processor.py | ~100 | **KEEP** (simplify for single mesh) |
| VTK 3D Viewer | mesh_viewer.py | 735 | **KEEP** (full reuse) |
| Reference Points (5-point picking) | main.py + mesh_viewer.py | ~300 | **REMOVE** |
| Foot dimension calculation | stl_processor.py | ~50 | **REMOVE** |
| Auto-scale insole | stl_processor.py | ~150 | **REMOVE** |
| Manual scale sliders | main.py | ~100 | **REMOVE** |
| Mirror X/Y axis | stl_processor.py | ~80 | **KEEP** (modify for auto L/R) |
| Position/Rotation sliders | main.py | ~150 | **REMOVE** |
| Align insole to foot | stl_processor.py | ~100 | **REMOVE** |
| Text label engraving | stl_processor.py | ~800 | **KEEP** (core feature) |
| Pick label position | main.py + mesh_viewer.py | ~150 | **MODIFY** (auto + manual adjust) |
| Boolean difference (MeshLib) | stl_processor.py | ~100 | **KEEP** (critical) |
| Surface wrapping for text | stl_processor.py | ~200 | **KEEP** (may simplify) |
| Font rendering (matplotlib) | stl_processor.py | ~400 | **KEEP** |
| Multi-line text | stl_processor.py | ~50 | **KEEP** |
| Export STL | stl_processor.py | ~50 | **KEEP** (modify for dual export) |
| Auto filename generation | stl_processor.py | ~30 | **KEEP** (modify format) |
| View controls (solid/wireframe) | mesh_viewer.py | ~100 | **KEEP** |
| Opacity/Color controls | mesh_viewer.py + main.py | ~80 | **SIMPLIFY** |
| Menu bar | main.py | ~100 | **SIMPLIFY** |
| Settings persistence | main.py | ~30 | **KEEP** |

### 1.3 Code Reuse Summary

```
FULL REUSE (~60%):
├── src/mesh_viewer.py          # 100% reuse - just remove foot mesh handling
├── VTK rendering pipeline      # 100% reuse
├── Text mesh creation          # 100% reuse
├── Boolean CSG operations      # 100% reuse
├── STL loading/saving          # 95% reuse
└── Font rendering              # 100% reuse

PARTIAL REUSE (~25%):
├── main.py UI structure        # 50% reuse - simplify significantly
├── Mirror operations           # 80% reuse - add auto side detection
├── Label placement             # 70% reuse - add auto-placement
└── Export functions            # 60% reuse - modify for L/R export

REMOVE (~15%):
├── Foot mesh handling          # 0% - not needed
├── Reference points            # 0% - not needed
├── Scaling features            # 0% - not needed
├── Alignment features          # 0% - not needed
└── Position/rotation sliders   # 0% - not needed
```

---

## SECTION 2: NEW PROJECT REQUIREMENTS BREAKDOWN

### 2.1 Functional Requirements

```yaml
FR-001:
  name: "Import Orthosis STL"
  description: "Load a single orthosis STL file (without logo/text)"
  priority: P0-Critical
  source_code: stl_processor.load_insole_stl()
  modifications:
    - Rename to load_orthosis_stl()
    - Remove foot-specific logic
    - Keep centering behavior

FR-002:
  name: "Logo Selection"
  description: "User selects from 2 predefined logo versions"
  priority: P0-Critical
  source_code: NEW
  implementation:
    - Store 2 logo STL files in /logos/ directory
    - ComboBox for logo selection
    - Preview thumbnail if possible

FR-003:
  name: "Mirror Generation"
  description: "Generate both L and R versions from single import"
  priority: P0-Critical
  source_code: stl_processor.mirror_insole()
  modifications:
    - Create both L and R automatically
    - Store both versions in memory
    - User can preview each

FR-004:
  name: "Patient Name Input"
  description: "Text input for patient name"
  priority: P0-Critical
  source_code: main.py name_input (exists)
  modifications: None - direct reuse

FR-005:
  name: "Manufacturing Date Input"
  description: "Date input with auto-today option"
  priority: P0-Critical
  source_code: main.py date_input (exists)
  modifications:
    - Add "Use Today" button
    - Format: YYYY-MM-DD

FR-006:
  name: "Automatic Placement"
  description: "Logo and text placed at predefined position"
  priority: P0-Critical
  source_code: stl_processor.add_text_label() (position='heel')
  modifications:
    - Define standard position algorithm
    - Use surface detection for Z positioning

FR-007:
  name: "Safety Margin Detection"
  description: "Detect if placement violates 5mm margins"
  priority: P1-High
  source_code: NEW
  implementation:
    - Detect mesh edges (boundary vertices)
    - Detect holes (perforation areas)
    - Calculate distances from label bounds
    - Show warning if < 5mm

FR-008:
  name: "Manual Adjustment"
  description: "Allow position adjustment when margins violated"
  priority: P1-High
  source_code: main.py label offset sliders (exists)
  modifications:
    - Only enable when warning shown
    - Real-time preview

FR-009:
  name: "Engraving at 0.6mm Depth"
  description: "Negative engraving into orthosis surface"
  priority: P0-Critical
  source_code: stl_processor.add_text_label(engrave=True, depth=0.6)
  modifications:
    - Set default depth to 0.6mm
    - Remove depth adjustment UI

FR-010:
  name: "Dual Export"
  description: "Export both L and R as separate STL files"
  priority: P0-Critical
  source_code: stl_processor.save_stl()
  modifications:
    - Export two files in one action
    - Naming: PatientName_Date_L.stl and PatientName_Date_R.stl
```

### 2.2 Non-Functional Requirements

```yaml
NFR-001:
  name: "Fast Workflow"
  description: "Minimal clicks from import to export"
  target: "< 30 seconds typical workflow"
  
NFR-002:
  name: "Reliable Boolean Operations"
  description: "Engraving must not fail or corrupt mesh"
  implementation: "Use MeshLib as primary, trimesh blender as fallback"

NFR-003:
  name: "Windows Compatibility"
  description: "Standalone .exe for Windows 10/11"
  implementation: "PyInstaller bundle"
```

---

## SECTION 3: ARCHITECTURE

### 3.1 New File Structure

```
Orthosis-Engrave-Tool/
├── main.py                    # Simplified main application (~800 lines)
├── src/
│   ├── __init__.py
│   ├── mesh_viewer.py         # Reused from base (minor modifications)
│   ├── orthosis_processor.py  # Renamed/modified stl_processor.py
│   └── placement_validator.py # NEW - margin/hole detection
├── logos/
│   ├── logo_v1.stl            # Logo version 1 (3D mesh)
│   ├── logo_v2.stl            # Logo version 2 (3D mesh)
│   ├── logo_v1.png            # Preview thumbnail
│   └── logo_v2.png            # Preview thumbnail
├── config/
│   └── defaults.json          # Default placement parameters
├── requirements.txt
├── build.bat
├── build.spec
└── installer.iss
```

### 3.2 Class Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      MainWindow                              │
│─────────────────────────────────────────────────────────────│
│ - processor: OrthosisProcessor                               │
│ - viewer: SimpleMeshViewer                                   │
│ - validator: PlacementValidator                              │
│ - left_mesh: trimesh.Trimesh                                 │
│ - right_mesh: trimesh.Trimesh                                │
│─────────────────────────────────────────────────────────────│
│ + load_orthosis()                                            │
│ + select_logo(version: int)                                  │
│ + generate_both_sides()                                      │
│ + apply_engraving()                                          │
│ + validate_placement() -> ValidationResult                   │
│ + adjust_placement(offset_x, offset_y)                       │
│ + export_both()                                              │
│ + preview_left()                                             │
│ + preview_right()                                            │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   OrthosisProcessor                          │
│─────────────────────────────────────────────────────────────│
│ - orthosis_mesh: trimesh.Trimesh                             │
│ - original_mesh: trimesh.Trimesh                             │
│ - logo_mesh: trimesh.Trimesh                                 │
│ - left_version: trimesh.Trimesh                              │
│ - right_version: trimesh.Trimesh                             │
│─────────────────────────────────────────────────────────────│
│ + load_orthosis(filepath: str)                               │
│ + load_logo(filepath: str)                                   │
│ + mirror_to_left_right() -> (left, right)                    │
│ + add_logo_and_text(mesh, text, date, logo_mesh)            │
│ + calculate_standard_position(mesh) -> (pos, normal)         │
│ + save_stl(mesh, filepath)                                   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  PlacementValidator                          │
│─────────────────────────────────────────────────────────────│
│ + detect_boundary_edges(mesh) -> List[Edge]                  │
│ + detect_holes(mesh) -> List[HoleRegion]                     │
│ + calculate_min_distance_to_boundary(position, mesh) -> float│
│ + calculate_min_distance_to_holes(position, mesh) -> float   │
│ + validate_placement(position, label_bounds, mesh) -> Result │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   SimpleMeshViewer                           │
│─────────────────────────────────────────────────────────────│
│ (Reused from base project - VTK rendering)                   │
│ - Removed: foot_mesh, reference_points, foot picking         │
│ - Kept: orthosis display, label picking, view controls       │
└─────────────────────────────────────────────────────────────┘
```

---

## SECTION 4: IMPLEMENTATION PROMPTS

### PROMPT 4.1: Project Setup
```
Create a new Python project "Orthosis-Engrave-Tool" based on the structure of 3D-STL-Viewer-V2.

Copy these files with modifications:
1. main.py - Will be heavily modified (keep as template)
2. src/mesh_viewer.py - Copy and remove foot-related code
3. src/stl_processor.py - Copy and rename to orthosis_processor.py
4. requirements.txt - Copy as-is
5. build.bat, build.spec, installer.iss - Copy and update names

Create new directories:
- logos/ (empty, for logo STL files)
- config/ (for defaults.json)

The project should be immediately runnable after setup.
```

### PROMPT 4.2: Simplify mesh_viewer.py
```
Modify src/mesh_viewer.py to remove foot-related functionality:

REMOVE:
- self.foot_mesh and foot_actor
- self.reference_points and related picking (4 foot points)
- self.insole_surface_point (5th point)
- set_foot_mesh(), set_foot_opacity(), set_foot_color()
- Point labels for Heel, Toe, Left Side, Right Side
- All foot picking mode code

RENAME:
- set_insole_mesh() -> set_orthosis_mesh()
- insole_actor -> orthosis_actor
- insole_picking_enabled -> orthosis_picking_enabled

KEEP INTACT:
- VTK rendering pipeline
- Label picking mode (label_point_picked signal)
- set_render_mode(), reset_view(), set_view()
- set_orthosis_opacity(), set_orthosis_color()
- Label marker display

The viewer should only handle ONE mesh (the orthosis) plus label markers.
```

### PROMPT 4.3: Create orthosis_processor.py
```
Create src/orthosis_processor.py based on stl_processor.py:

CLASS OrthosisProcessor:

REMOVE these methods completely:
- load_foot_stl()
- set_reference_points()
- calculate_foot_dimensions()
- auto_scale_insole_to_cover_points()
- align_insole_to_foot()
- position_insole_below_foot()
- _link_insole_to_foot(), is_insole_linked(), unlink_insole()
- apply_foot_transform(), scale_foot()
- find_best_matching_insole()
- detect_foot_side()
- _get_stl_x_length_fast()

RENAME and MODIFY:
- load_insole_stl() -> load_orthosis_stl(filepath)
  * Remove foot-related comments
  * Keep centering behavior
  
- mirror_insole() -> mirror_orthosis(axis='y')
  * Keep the mirror matrix logic
  * Remove label re-application (will be done separately)
  
- scale_insole() -> REMOVE (not needed)

ADD new methods:
- load_logo_stl(filepath: str) -> trimesh.Trimesh
  * Load logo as 3D mesh
  * Store in self.logo_mesh
  
- create_left_right_versions() -> Tuple[trimesh.Trimesh, trimesh.Trimesh]
  * Create mirrored copy for left version
  * Return (left_mesh, right_mesh)
  
- calculate_standard_position(mesh: trimesh.Trimesh) -> Tuple[np.ndarray, np.ndarray]
  * Determine the standard label position on the orthosis
  * Return (position, surface_normal)
  * Algorithm: Find a flat area on the lateral surface
  
- add_logo_to_mesh(mesh, logo_mesh, position, normal) -> trimesh.Trimesh
  * Position and orient logo mesh
  * Perform boolean subtraction (engrave at 0.6mm)
  
- add_text_to_mesh(mesh, text, position, normal, offset_y) -> trimesh.Trimesh
  * Add patient name and date below logo
  * Use existing text creation methods
  * Offset from logo position

KEEP these methods intact:
- add_text_label() and all helper methods
- _create_text_mesh_matplotlib_fast()
- _create_multiline_text_mesh()
- _meshlib_boolean_difference()
- _wrap_text_to_surface()
- save_stl()
- generate_filename() - modify format to "Name_Date_L.stl"
- get_mesh_info()

KEEP these constants:
- LETTER_PATHS dictionary (for fallback font)
```

### PROMPT 4.4: Create placement_validator.py
```
Create src/placement_validator.py for safety margin validation:

from dataclasses import dataclass
from typing import List, Tuple
import numpy as np
import trimesh

@dataclass
class ValidationResult:
    is_valid: bool
    min_edge_distance: float      # mm to nearest outer/inner edge
    min_hole_distance: float      # mm to nearest hole/perforation
    warnings: List[str]
    suggested_adjustment: Tuple[float, float]  # (x_offset, y_offset) to fix

class PlacementValidator:
    """Validates label placement against safety margins."""
    
    REQUIRED_EDGE_MARGIN = 5.0   # mm from inner/outer edge
    REQUIRED_HOLE_MARGIN = 5.0   # mm from perforations
    
    def detect_boundary_edges(self, mesh: trimesh.Trimesh) -> np.ndarray:
        """
        Find the outer boundary of the orthosis mesh.
        Returns array of edge vertex indices.
        
        Implementation:
        1. Use mesh.edges_unique to get all edges
        2. Use mesh.edges_unique_length for edge count per face
        3. Boundary edges appear in only ONE face (not shared)
        4. Return vertices on boundary edges
        """
        pass
    
    def detect_holes(self, mesh: trimesh.Trimesh) -> List[np.ndarray]:
        """
        Detect perforation holes in the mesh.
        Returns list of hole boundary polygons.
        
        Implementation:
        1. Find interior boundary loops (holes have closed boundaries)
        2. Use mesh face connectivity
        3. Small closed boundaries = perforation holes
        4. Filter by size to distinguish from mesh artifacts
        """
        pass
    
    def calculate_label_bounds(self, 
                               position: np.ndarray,
                               text: str,
                               logo_width: float,
                               font_size: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate the bounding box of the combined logo+text label.
        Returns (min_corner, max_corner) in 3D.
        """
        pass
    
    def validate_placement(self,
                          mesh: trimesh.Trimesh,
                          position: np.ndarray,
                          label_bounds: Tuple[np.ndarray, np.ndarray]
                          ) -> ValidationResult:
        """
        Main validation method.
        
        1. Get boundary edges
        2. Get hole boundaries
        3. Calculate distance from label bounds to each boundary
        4. Check if all distances >= 5mm
        5. If not, suggest adjustment direction
        """
        pass
    
    def suggest_adjustment(self,
                          current_position: np.ndarray,
                          boundary_edges: np.ndarray,
                          holes: List[np.ndarray],
                          label_bounds: Tuple[np.ndarray, np.ndarray]
                          ) -> Tuple[float, float]:
        """
        Calculate suggested (x, y) offset to satisfy margins.
        """
        pass
```

### PROMPT 4.5: Create Simplified main.py
```
Create main.py with simplified UI for orthosis workflow:

REMOVE ENTIRELY:
- File Loading Group: foot STL loading
- Reference Points Group: all picking, point status
- Scaling Group: auto scale, manual scale spinboxes
- Insole Position and Rotation Group: all sliders
- Foot opacity/color controls
- Foot-related menu items

UI LAYOUT (Control Panel - Left Side):
┌────────────────────────────────────────────┐
│ ═══ File Loading ═══                       │
│ [Select Orthosis STL...]     [filename]    │
│                                            │
│ ═══ Logo Selection ═══                     │
│ ○ Logo Version 1  [preview]                │
│ ○ Logo Version 2  [preview]                │
│                                            │
│ ═══ Patient Information ═══                │
│ Name: [________________________]           │
│ Date: [2026-01-24____]  [Today]            │
│                                            │
│ ═══ Placement ═══                          │
│ [!] Warning: Too close to edge (4.2mm)     │
│ Offset X: [---------|----] 0               │
│ Offset Y: [---------|----] 0               │
│ Status: ✓ Valid / ⚠ Adjust Required        │
│                                            │
│ ═══ Preview ═══                            │
│ [Preview Left (L)]  [Preview Right (R)]    │
│                                            │
│ ═══ Export ═══                             │
│ Output: PatientName_2026-01-24_L.stl       │
│         PatientName_2026-01-24_R.stl       │
│ [        EXPORT BOTH STL FILES        ]    │
│                                            │
│ ═══ View Settings ═══                      │
│ Render: [Solid ▼]  Opacity: [-------|] 80% │
└────────────────────────────────────────────┘

WORKFLOW:
1. User clicks "Select Orthosis STL" -> loads file
2. User selects logo version (radio buttons)
3. User enters patient name
4. Date auto-fills with today, can be changed
5. System auto-calculates placement, runs validation
6. If warning shown, offset sliders become enabled
7. User can preview L or R version
8. User clicks "Export Both" -> saves 2 files

SIGNALS TO IMPLEMENT:
- orthosis_loaded: Show mesh in viewer
- logo_selected: Update preview
- name_changed: Update filename preview
- date_changed: Update filename preview
- validate_placement: Run on any parameter change
- preview_left: Show left version in viewer
- preview_right: Show right version in viewer
- export: Save both files

MENU BAR:
- File: Open Orthosis, Export, Exit
- View: Reset View, Top/Front/Side/Iso, Render Mode
- Help: About, Instructions
```

### PROMPT 4.6: Logo Integration
```
Implement logo integration in OrthosisProcessor:

The logo is a 3D STL mesh that gets SUBTRACTED from the orthosis surface.
Logo files are stored in /logos/ directory.

LOGO LOADING:
def load_logo(self, logo_path: str) -> trimesh.Trimesh:
    """
    Load logo STL file.
    1. Load with trimesh
    2. Center at origin
    3. Store in self.logo_mesh
    4. Calculate logo dimensions for placement
    """
    self.logo_mesh = trimesh.load(logo_path, force='mesh')
    self.logo_mesh.vertices -= self.logo_mesh.centroid
    
    # Store dimensions
    bounds = self.logo_mesh.bounds
    self.logo_width = bounds[1][0] - bounds[0][0]
    self.logo_height = bounds[1][1] - bounds[0][1]
    self.logo_depth = bounds[1][2] - bounds[0][2]
    
    return self.logo_mesh

LOGO POSITIONING:
def position_logo_on_surface(self, 
                             orthosis_mesh: trimesh.Trimesh,
                             position: np.ndarray,
                             normal: np.ndarray,
                             engraving_depth: float = 0.6
                            ) -> trimesh.Trimesh:
    """
    Position logo at the given surface position.
    
    1. Copy logo mesh
    2. Orient to face along surface normal
    3. Scale depth to engraving_depth + safety margin
    4. Position at surface point
    5. Return positioned logo ready for boolean
    """
    logo = self.logo_mesh.copy()
    
    # Create rotation matrix to align Z-axis with surface normal
    # Default logo Z points out, we want it to point INTO surface
    # So align -Z with the surface outward normal
    ...
    
    # Position so logo extends INTO the surface by engraving_depth
    # and extends OUTSIDE by small margin for clean boolean cut
    ...
    
    return logo

COMBINED ENGRAVING:
def engrave_logo_and_text(self,
                          mesh: trimesh.Trimesh,
                          patient_name: str,
                          date: str,
                          side: str,  # 'L' or 'R'
                          position: np.ndarray,
                          normal: np.ndarray,
                          offset_x: float = 0,
                          offset_y: float = 0
                         ) -> trimesh.Trimesh:
    """
    Engrave both logo and text onto the orthosis.
    
    Layout:
    ┌─────────────────┐
    │     [LOGO]      │  <- Logo at position
    │  Patient Name   │  <- Text below logo
    │   L 2026-01-24  │  <- Side + Date below name
    └─────────────────┘
    
    Steps:
    1. Position logo at (position + offset)
    2. Boolean subtract logo from mesh
    3. Create text mesh for name
    4. Position text below logo
    5. Boolean subtract text
    6. Create text for side+date
    7. Position below name
    8. Boolean subtract
    9. Return final mesh
    
    All text is engraved at 0.6mm depth.
    """
    pass
```

### PROMPT 4.7: Automatic Placement Algorithm
```
Implement automatic standard placement in OrthosisProcessor:

def calculate_standard_position(self, 
                                mesh: trimesh.Trimesh
                               ) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate the standard placement position for logo+text.
    
    For an orthosis (lower leg brace):
    - The label should go on the LATERAL (outer) side
    - Position: Lower 1/3 of the orthosis height
    - Avoid: Too close to top/bottom edges, holes, cutouts
    
    Algorithm:
    1. Find mesh bounds and center
    2. Determine "lateral" side (usually larger X or Y extent)
    3. Cast rays from outside to find surface points
    4. Find relatively flat area (low curvature)
    5. Return position and surface normal
    
    Returns:
        position: np.ndarray [x, y, z] - center point for label
        normal: np.ndarray [nx, ny, nz] - surface normal (pointing out)
    """
    bounds = mesh.bounds
    center = mesh.centroid
    
    # Orthosis is typically taller in Z, wider in X/Y
    height = bounds[1][2] - bounds[0][2]
    
    # Target Z: lower third (30% from bottom)
    target_z = bounds[0][2] + height * 0.30
    
    # Find lateral (outer) side
    # Cast rays from multiple angles to find the outermost surface
    # at our target Z height
    
    # Sample angles around the orthosis
    angles = np.linspace(0, 2*np.pi, 36)
    best_point = None
    best_normal = None
    best_flatness = float('inf')
    
    for angle in angles:
        # Ray direction pointing inward
        direction = np.array([np.cos(angle), np.sin(angle), 0])
        
        # Ray origin far outside mesh
        origin = center.copy()
        origin[2] = target_z
        origin[:2] += direction * 500  # 500mm outside
        
        # Cast ray toward center
        locations, _, face_ids = mesh.ray.intersects_location(
            ray_origins=[origin],
            ray_directions=[-direction]
        )
        
        if len(locations) > 0:
            # Take first hit (outermost surface)
            hit_point = locations[0]
            hit_face = face_ids[0]
            hit_normal = mesh.face_normals[hit_face]
            
            # Calculate local curvature (flatness)
            # Lower curvature = flatter = better for engraving
            curvature = calculate_local_curvature(mesh, hit_face)
            
            if curvature < best_flatness:
                best_flatness = curvature
                best_point = hit_point
                best_normal = hit_normal
    
    if best_point is None:
        # Fallback: use bounding box side
        best_point = np.array([bounds[1][0], center[1], target_z])
        best_normal = np.array([1, 0, 0])
    
    # Ensure normal points outward
    if np.dot(best_normal, best_point - center) < 0:
        best_normal = -best_normal
    
    return best_point, best_normal
```

### PROMPT 4.8: Dual Export Feature
```
Implement dual L/R export in OrthosisProcessor:

def generate_both_versions(self,
                          patient_name: str,
                          date: str,
                          offset_x: float = 0,
                          offset_y: float = 0
                         ) -> Tuple[trimesh.Trimesh, trimesh.Trimesh]:
    """
    Generate both Left and Right versions with engraving.
    
    Process:
    1. Calculate standard position on original mesh
    2. Create RIGHT version (original or mirrored based on input)
    3. Engrave logo + "Name\nR Date" on right version
    4. Mirror mesh for LEFT version
    5. Calculate mirrored position
    6. Engrave logo + "Name\nL Date" on left version
    7. Return (left_mesh, right_mesh)
    
    Note: After mirroring, the label position must also be mirrored
    to maintain the same relative location on the orthosis.
    """
    # Store original for both versions
    original = self.orthosis_mesh.copy()
    
    # Calculate placement on original
    position, normal = self.calculate_standard_position(original)
    
    # Apply user offset
    adjusted_pos = position.copy()
    # Offset in local coordinate system (tangent to surface)
    tangent1 = np.cross(normal, [0, 0, 1])
    if np.linalg.norm(tangent1) < 0.01:
        tangent1 = np.cross(normal, [0, 1, 0])
    tangent1 = tangent1 / np.linalg.norm(tangent1)
    tangent2 = np.cross(normal, tangent1)
    
    adjusted_pos += tangent1 * offset_x + tangent2 * offset_y
    
    # --- RIGHT VERSION ---
    right_mesh = original.copy()
    right_mesh = self.engrave_logo_and_text(
        right_mesh,
        patient_name,
        date,
        side='R',
        position=adjusted_pos,
        normal=normal
    )
    
    # --- LEFT VERSION ---
    # Mirror the original mesh
    left_mesh = original.copy()
    left_mesh = self.mirror_orthosis(left_mesh, axis='y')
    
    # Mirror the position and normal
    mirrored_pos = adjusted_pos.copy()
    mirrored_pos[1] = -mirrored_pos[1]  # Mirror Y
    mirrored_normal = normal.copy()
    mirrored_normal[1] = -mirrored_normal[1]
    
    left_mesh = self.engrave_logo_and_text(
        left_mesh,
        patient_name,
        date,
        side='L',
        position=mirrored_pos,
        normal=mirrored_normal
    )
    
    return left_mesh, right_mesh


def export_both(self,
               left_mesh: trimesh.Trimesh,
               right_mesh: trimesh.Trimesh,
               patient_name: str,
               date: str,
               output_dir: str
              ) -> Tuple[str, str]:
    """
    Export both versions to STL files.
    
    Naming convention: PatientName_Date_L.stl and PatientName_Date_R.stl
    
    Returns:
        (left_filepath, right_filepath)
    """
    # Sanitize name for filename
    safe_name = "".join(c for c in patient_name if c.isalnum() or c in ' -_')
    safe_name = safe_name.strip().replace(' ', '_')
    
    # Format date
    safe_date = date.replace('/', '-').replace('\\', '-')
    
    # Generate filenames
    left_filename = f"{safe_name}_{safe_date}_L.stl"
    right_filename = f"{safe_name}_{safe_date}_R.stl"
    
    left_path = os.path.join(output_dir, left_filename)
    right_path = os.path.join(output_dir, right_filename)
    
    # Export
    left_mesh.export(left_path, file_type='stl')
    right_mesh.export(right_path, file_type='stl')
    
    return left_path, right_path
```

### PROMPT 4.9: Warning System UI
```
Implement the warning system in main.py:

class PlacementWarningWidget(QWidget):
    """Widget to display placement validation warnings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        # Warning icon and message
        self.warning_frame = QFrame()
        self.warning_frame.setStyleSheet("""
            QFrame {
                background-color: #FFF3CD;
                border: 1px solid #FFC107;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        warning_layout = QHBoxLayout(self.warning_frame)
        
        self.warning_icon = QLabel("⚠")
        self.warning_icon.setStyleSheet("font-size: 20px;")
        warning_layout.addWidget(self.warning_icon)
        
        self.warning_text = QLabel("")
        self.warning_text.setWordWrap(True)
        warning_layout.addWidget(self.warning_text, 1)
        
        layout.addWidget(self.warning_frame)
        
        # Success indicator (hidden by default)
        self.success_frame = QFrame()
        self.success_frame.setStyleSheet("""
            QFrame {
                background-color: #D4EDDA;
                border: 1px solid #28A745;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        success_layout = QHBoxLayout(self.success_frame)
        
        self.success_icon = QLabel("✓")
        self.success_icon.setStyleSheet("font-size: 20px; color: #28A745;")
        success_layout.addWidget(self.success_icon)
        
        self.success_text = QLabel("Placement valid - all margins OK")
        success_layout.addWidget(self.success_text, 1)
        
        layout.addWidget(self.success_frame)
        
        # Initially hide both
        self.warning_frame.hide()
        self.success_frame.hide()
    
    def show_warning(self, message: str):
        """Display a warning message."""
        self.warning_text.setText(message)
        self.warning_frame.show()
        self.success_frame.hide()
    
    def show_success(self):
        """Display success indicator."""
        self.warning_frame.hide()
        self.success_frame.show()
    
    def hide_all(self):
        """Hide all indicators."""
        self.warning_frame.hide()
        self.success_frame.hide()

# In MainWindow:
def _validate_and_update_ui(self):
    """Run validation and update UI accordingly."""
    if self.processor.orthosis_mesh is None:
        self.placement_warning.hide_all()
        return
    
    # Get current position with offsets
    position = self.processor.calculate_standard_position(
        self.processor.orthosis_mesh
    )
    
    offset_x = self.offset_x_slider.value()
    offset_y = self.offset_y_slider.value()
    
    # Run validation
    result = self.validator.validate_placement(
        self.processor.orthosis_mesh,
        position,
        self._calculate_label_bounds()
    )
    
    if result.is_valid:
        self.placement_warning.show_success()
        self.offset_x_slider.setEnabled(False)
        self.offset_y_slider.setEnabled(False)
    else:
        # Build warning message
        messages = []
        if result.min_edge_distance < 5.0:
            messages.append(
                f"Edge margin: {result.min_edge_distance:.1f}mm (need 5mm)"
            )
        if result.min_hole_distance < 5.0:
            messages.append(
                f"Hole margin: {result.min_hole_distance:.1f}mm (need 5mm)"
            )
        
        self.placement_warning.show_warning("\n".join(messages))
        
        # Enable adjustment sliders
        self.offset_x_slider.setEnabled(True)
        self.offset_y_slider.setEnabled(True)
        
        # Apply suggested adjustment if user hasn't manually adjusted
        if self._auto_adjust_enabled:
            self.offset_x_slider.setValue(int(result.suggested_adjustment[0]))
            self.offset_y_slider.setValue(int(result.suggested_adjustment[1]))
```

### PROMPT 4.10: Build and Package
```
Create build configuration for standalone Windows executable:

# build.spec (PyInstaller spec file)
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('logos/*.stl', 'logos'),
        ('logos/*.png', 'logos'),
        ('config/*.json', 'config'),
    ],
    hiddenimports=[
        'vtkmodules',
        'vtkmodules.all',
        'vtkmodules.qt.QVTKRenderWindowInteractor',
        'vtkmodules.util.numpy_support',
        'trimesh',
        'meshlib',
        'meshlib.mrmeshpy',
        'shapely',
        'shapely.geometry',
        'matplotlib',
        'matplotlib.font_manager',
        'matplotlib.textpath',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='OrthosisEngraveTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='logo/icon.ico',
)

# build.bat
@echo off
echo Building Orthosis Engrave Tool...
pip install pyinstaller
pyinstaller --clean build.spec
echo Build complete! Check dist/ folder.
pause

# installer.iss (Inno Setup)
[Setup]
AppName=Orthosis Engrave Tool
AppVersion=1.0.0
DefaultDirName={autopf}\OrthosisEngraveTool
DefaultGroupName=Orthosis Engrave Tool
OutputDir=installer_output
OutputBaseFilename=OrthosisEngraveTool_Setup
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Files]
Source: "dist\OrthosisEngraveTool.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "logos\*"; DestDir: "{app}\logos"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\Orthosis Engrave Tool"; Filename: "{app}\OrthosisEngraveTool.exe"
Name: "{autodesktop}\Orthosis Engrave Tool"; Filename: "{app}\OrthosisEngraveTool.exe"

[Run]
Filename: "{app}\OrthosisEngraveTool.exe"; Description: "Launch Orthosis Engrave Tool"; Flags: nowait postinstall skipifsilent
```

---

## SECTION 5: TESTING PROMPTS

### PROMPT 5.1: Unit Tests
```
Create tests/test_orthosis_processor.py:

import pytest
import numpy as np
import trimesh
from src.orthosis_processor import OrthosisProcessor

class TestOrthosisProcessor:
    
    @pytest.fixture
    def processor(self):
        return OrthosisProcessor()
    
    @pytest.fixture
    def sample_orthosis(self, tmp_path):
        """Create a simple cylinder mesh for testing."""
        mesh = trimesh.creation.cylinder(radius=50, height=200)
        path = tmp_path / "test_orthosis.stl"
        mesh.export(str(path))
        return str(path)
    
    def test_load_orthosis(self, processor, sample_orthosis):
        mesh = processor.load_orthosis_stl(sample_orthosis)
        assert mesh is not None
        assert len(mesh.vertices) > 0
    
    def test_mirror_orthosis(self, processor, sample_orthosis):
        processor.load_orthosis_stl(sample_orthosis)
        original = processor.orthosis_mesh.copy()
        
        left, right = processor.create_left_right_versions()
        
        # Check that meshes are different (mirrored)
        assert not np.allclose(left.vertices, right.vertices)
        
        # Check that volumes are equal
        assert abs(left.volume - right.volume) < 0.01
    
    def test_standard_position(self, processor, sample_orthosis):
        processor.load_orthosis_stl(sample_orthosis)
        
        position, normal = processor.calculate_standard_position(
            processor.orthosis_mesh
        )
        
        # Position should be on the mesh surface
        assert len(position) == 3
        assert len(normal) == 3
        
        # Normal should be unit vector
        assert abs(np.linalg.norm(normal) - 1.0) < 0.01
    
    def test_engrave_text(self, processor, sample_orthosis):
        processor.load_orthosis_stl(sample_orthosis)
        original_faces = len(processor.orthosis_mesh.faces)
        
        position, normal = processor.calculate_standard_position(
            processor.orthosis_mesh
        )
        
        result = processor.add_text_to_mesh(
            processor.orthosis_mesh,
            "TEST",
            position,
            normal,
            offset_y=0
        )
        
        # Mesh should be modified (different face count after boolean)
        assert result is not None
    
    def test_export_both(self, processor, sample_orthosis, tmp_path):
        processor.load_orthosis_stl(sample_orthosis)
        
        left, right = processor.generate_both_versions(
            "John Doe",
            "2026-01-24"
        )
        
        left_path, right_path = processor.export_both(
            left, right,
            "John Doe",
            "2026-01-24",
            str(tmp_path)
        )
        
        # Check files exist
        assert os.path.exists(left_path)
        assert os.path.exists(right_path)
        
        # Check naming
        assert "John_Doe" in left_path
        assert "_L.stl" in left_path
        assert "_R.stl" in right_path
```

### PROMPT 5.2: Integration Tests
```
Create tests/test_workflow.py:

import pytest
from PySide6.QtWidgets import QApplication
from main import MainWindow

class TestWorkflow:
    
    @pytest.fixture
    def app(self):
        return QApplication([])
    
    @pytest.fixture
    def window(self, app):
        return MainWindow()
    
    def test_complete_workflow(self, window, sample_orthosis, sample_logo, tmp_path):
        """Test the complete user workflow."""
        
        # 1. Load orthosis
        window._load_orthosis(sample_orthosis)
        assert window.processor.orthosis_mesh is not None
        
        # 2. Select logo
        window._select_logo(0)  # Logo version 1
        assert window.processor.logo_mesh is not None
        
        # 3. Enter patient info
        window.name_input.setText("Max Mustermann")
        window.date_input.setText("2026-01-24")
        
        # 4. Check validation runs
        window._validate_placement()
        
        # 5. Export
        window._export_both(str(tmp_path))
        
        # Verify output files
        expected_left = tmp_path / "Max_Mustermann_2026-01-24_L.stl"
        expected_right = tmp_path / "Max_Mustermann_2026-01-24_R.stl"
        
        assert expected_left.exists()
        assert expected_right.exists()
```

---

## SECTION 6: MIGRATION CHECKLIST

### Phase 1: Setup (Day 1)
- [ ] Create new project directory structure
- [ ] Copy base files from 3D-STL-Viewer-V2
- [ ] Rename project in all config files
- [ ] Verify project runs with copied code
- [ ] Create empty placeholder files for new modules

### Phase 2: Mesh Viewer (Day 1)
- [ ] Remove foot mesh handling from mesh_viewer.py
- [ ] Rename insole -> orthosis throughout
- [ ] Test basic mesh loading and display
- [ ] Verify label picking still works

### Phase 3: Orthosis Processor (Day 2-3)
- [ ] Create orthosis_processor.py from stl_processor.py
- [ ] Remove foot-related methods
- [ ] Add logo loading method
- [ ] Implement create_left_right_versions()
- [ ] Implement calculate_standard_position()
- [ ] Add engrave_logo_and_text()
- [ ] Add export_both() method
- [ ] Test each method individually

### Phase 4: Placement Validator (Day 3)
- [ ] Create placement_validator.py
- [ ] Implement boundary edge detection
- [ ] Implement hole detection
- [ ] Implement distance calculations
- [ ] Implement validate_placement()
- [ ] Test with various orthosis shapes

### Phase 5: UI Implementation (Day 4-5)
- [ ] Strip main.py to minimal UI
- [ ] Implement new control panel layout
- [ ] Add logo selection radio buttons
- [ ] Implement warning widget
- [ ] Connect all signals
- [ ] Implement preview L/R switching
- [ ] Implement export workflow
- [ ] Polish UI styling

### Phase 6: Testing & Polish (Day 6)
- [ ] Run all unit tests
- [ ] Test complete workflow
- [ ] Test edge cases (long names, special characters)
- [ ] Build standalone executable
- [ ] Test on clean Windows machine
- [ ] Create installer

---

## SECTION 7: DEPENDENCY MAP

```
main.py
├── PySide6 (GUI)
├── src/mesh_viewer.py
│   ├── VTK (rendering)
│   └── numpy
├── src/orthosis_processor.py
│   ├── trimesh (STL operations)
│   ├── numpy
│   ├── meshlib.mrmeshpy (boolean CSG)
│   ├── shapely (polygon operations)
│   └── matplotlib (text paths)
└── src/placement_validator.py
    ├── trimesh
    └── numpy

External files:
├── logos/logo_v1.stl
├── logos/logo_v2.stl
└── config/defaults.json
```

---

## SECTION 8: CONFIGURATION DEFAULTS

### config/defaults.json
```json
{
  "engraving": {
    "depth_mm": 0.6,
    "font_size_mm": 4.0,
    "logo_scale": 1.0
  },
  "placement": {
    "min_edge_margin_mm": 5.0,
    "min_hole_margin_mm": 5.0,
    "default_z_position_ratio": 0.30,
    "prefer_lateral_side": true
  },
  "text_layout": {
    "line_spacing": 1.4,
    "logo_text_gap_mm": 3.0
  },
  "export": {
    "filename_format": "{name}_{date}_{side}.stl",
    "date_format": "YYYY-MM-DD"
  },
  "viewer": {
    "default_render_mode": "solid",
    "default_opacity": 1.0,
    "orthosis_color": [0.4, 0.6, 0.85]
  }
}
```

---

## SECTION 9: ESTIMATED EFFORT

| Task | Hours | Complexity |
|------|-------|------------|
| Project setup & file organization | 2 | Low |
| Simplify mesh_viewer.py | 2 | Low |
| Create orthosis_processor.py | 8 | Medium |
| Create placement_validator.py | 6 | Medium |
| Redesign main.py UI | 8 | Medium |
| Logo integration | 4 | Medium |
| Auto-placement algorithm | 4 | High |
| Dual export feature | 2 | Low |
| Warning system UI | 3 | Low |
| Testing | 6 | Medium |
| Build & packaging | 2 | Low |
| Documentation | 2 | Low |
| **TOTAL** | **49 hours** | - |

---

## END OF PROMPTS FILE
