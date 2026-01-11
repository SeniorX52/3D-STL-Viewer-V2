"""
Standalone 3D Label Test Environment
Test engraving and embossing on a simple box to tune settings.
"""

import sys
import numpy as np
import trimesh
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QCheckBox, QSlider, QGroupBox,
    QFormLayout, QComboBox, QSpinBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt

# Add src to path
sys.path.insert(0, 'src')
from mesh_viewer import VTKMeshViewer as MeshViewer


class LabelTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Label Test Environment")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create base mesh (simple box)
        self.base_mesh = None
        self.text_mesh = None
        self.result_mesh = None
        
        self._setup_ui()
        self._create_base_mesh()
    
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        
        # Left panel - controls
        controls = QWidget()
        controls.setFixedWidth(350)
        ctrl_layout = QVBoxLayout(controls)
        
        # Base mesh settings
        base_group = QGroupBox("Base Mesh")
        base_layout = QFormLayout(base_group)
        
        self.mesh_type = QComboBox()
        self.mesh_type.addItems(["Box", "Cylinder", "Sphere"])
        self.mesh_type.currentIndexChanged.connect(self._create_base_mesh)
        base_layout.addRow("Type:", self.mesh_type)
        
        self.mesh_size = QDoubleSpinBox()
        self.mesh_size.setRange(10, 200)
        self.mesh_size.setValue(50)
        self.mesh_size.valueChanged.connect(self._create_base_mesh)
        base_layout.addRow("Size (mm):", self.mesh_size)
        
        self.mesh_thickness = QDoubleSpinBox()
        self.mesh_thickness.setRange(1, 50)
        self.mesh_thickness.setValue(10)
        self.mesh_thickness.setSingleStep(1)
        self.mesh_thickness.valueChanged.connect(self._create_base_mesh)
        base_layout.addRow("Thickness:", self.mesh_thickness)
        
        ctrl_layout.addWidget(base_group)
        
        # Text settings
        text_group = QGroupBox("Text Settings")
        text_layout = QFormLayout(text_group)
        
        self.text_input = QLineEdit("TEST")
        text_layout.addRow("Text:", self.text_input)
        
        self.font_size = QDoubleSpinBox()
        self.font_size.setRange(1, 20)
        self.font_size.setValue(5)
        self.font_size.setSingleStep(0.5)
        text_layout.addRow("Font Size:", self.font_size)
        
        self.depth = QDoubleSpinBox()
        self.depth.setRange(0.1, 5)
        self.depth.setValue(0.6)
        self.depth.setSingleStep(0.1)
        text_layout.addRow("Depth (mm):", self.depth)
        
        self.engrave_check = QCheckBox("Engrave (subtract)")
        self.engrave_check.setChecked(True)
        text_layout.addRow("", self.engrave_check)
        
        ctrl_layout.addWidget(text_group)
        
        # Position settings
        pos_group = QGroupBox("Position")
        pos_layout = QFormLayout(pos_group)
        
        self.offset_x = QDoubleSpinBox()
        self.offset_x.setRange(-50, 50)
        self.offset_x.setValue(0)
        pos_layout.addRow("Offset X:", self.offset_x)
        
        self.offset_y = QDoubleSpinBox()
        self.offset_y.setRange(-50, 50)
        self.offset_y.setValue(0)
        pos_layout.addRow("Offset Y:", self.offset_y)
        
        self.rotation = QSpinBox()
        self.rotation.setRange(-180, 180)
        self.rotation.setValue(0)
        pos_layout.addRow("Rotation:", self.rotation)
        
        ctrl_layout.addWidget(pos_group)
        
        # Boolean engine
        engine_group = QGroupBox("Boolean Engine")
        engine_layout = QFormLayout(engine_group)
        
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(["MeshLib", "Manifold", "Visual (fallback)"])
        engine_layout.addRow("Engine:", self.engine_combo)
        
        ctrl_layout.addWidget(engine_group)
        
        # Rendering options
        render_group = QGroupBox("Rendering")
        render_layout = QFormLayout(render_group)
        
        self.wireframe_check = QCheckBox("Show Wireframe")
        self.wireframe_check.stateChanged.connect(self._toggle_wireframe)
        render_layout.addRow("", self.wireframe_check)
        
        self.show_edges_check = QCheckBox("Show Edges")
        self.show_edges_check.stateChanged.connect(self._toggle_edges)
        render_layout.addRow("", self.show_edges_check)
        
        ctrl_layout.addWidget(render_group)
        
        # Buttons
        btn_layout = QVBoxLayout()
        
        self.preview_text_btn = QPushButton("1. Preview Text Mesh")
        self.preview_text_btn.clicked.connect(self._preview_text)
        btn_layout.addWidget(self.preview_text_btn)
        
        self.apply_btn = QPushButton("2. Apply Boolean")
        self.apply_btn.clicked.connect(self._apply_boolean)
        self.apply_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        btn_layout.addWidget(self.apply_btn)
        
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self._create_base_mesh)
        btn_layout.addWidget(self.reset_btn)
        
        self.export_btn = QPushButton("Export Result STL")
        self.export_btn.clicked.connect(self._export_result)
        btn_layout.addWidget(self.export_btn)
        
        self.top_view_btn = QPushButton("Top View (Z)")
        self.top_view_btn.clicked.connect(self._set_top_view)
        btn_layout.addWidget(self.top_view_btn)
        
        ctrl_layout.addLayout(btn_layout)
        
        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("padding: 10px; background: #f0f0f0; border-radius: 5px;")
        ctrl_layout.addWidget(self.status_label)
        
        ctrl_layout.addStretch()
        layout.addWidget(controls)
        
        # Right panel - 3D viewer
        self.viewer = MeshViewer()
        layout.addWidget(self.viewer, stretch=1)
    
    def _create_base_mesh(self):
        """Create a simple base mesh for testing."""
        size = self.mesh_size.value()
        thickness = self.mesh_thickness.value()
        mesh_type = self.mesh_type.currentText()
        
        if mesh_type == "Box":
            self.base_mesh = trimesh.creation.box(extents=[size, size * 1.5, thickness])
        elif mesh_type == "Cylinder":
            self.base_mesh = trimesh.creation.cylinder(radius=size/2, height=thickness, sections=64)
        else:  # Sphere
            self.base_mesh = trimesh.creation.icosphere(radius=size/2, subdivisions=3)
        
        # Move so top surface is at z=0
        self.base_mesh.vertices[:, 2] -= self.base_mesh.bounds[1][2]
        
        self.result_mesh = self.base_mesh.copy()
        self.viewer.set_insole_mesh(self.base_mesh)
        self._update_status(f"Created {mesh_type}: {len(self.base_mesh.vertices)} verts, {len(self.base_mesh.faces)} faces\n"
                           f"Thickness: {thickness}mm, Watertight: {self.base_mesh.is_watertight}")
    
    def _create_text_mesh(self):
        """Create 3D text mesh with proper hole handling for letters like O, 0, A, B, etc."""
        from matplotlib.textpath import TextPath
        from matplotlib.font_manager import FontProperties
        from shapely.geometry import Polygon, MultiPolygon
        from shapely.ops import unary_union
        
        text = self.text_input.text().strip()
        if not text:
            return None
        
        font_size = self.font_size.value()
        depth = self.depth.value()
        
        font_props = FontProperties(family='sans-serif', weight='bold')
        text_path = TextPath((0, 0), text, size=font_size, prop=font_props)
        
        MOVETO, LINETO, CURVE3, CURVE4, CLOSEPOLY = 1, 2, 3, 4, 79
        
        # Collect all contours (outer boundaries AND holes)
        contours = []
        current_contour = []
        vertices = text_path.vertices
        codes = text_path.codes
        
        t_samples_quad = np.linspace(0, 1, 12)[1:]
        t_samples_cubic = np.linspace(0, 1, 16)[1:]
        
        i = 0
        while i < len(codes):
            code = codes[i]
            
            if code == MOVETO:
                if len(current_contour) >= 3:
                    contours.append(current_contour)
                current_contour = [tuple(vertices[i])]
                i += 1
            elif code == LINETO:
                current_contour.append(tuple(vertices[i]))
                i += 1
            elif code == CURVE3:
                if len(current_contour) > 0:
                    p0 = current_contour[-1]
                    p1 = tuple(vertices[i])
                    p2 = tuple(vertices[i + 1])
                    for t in t_samples_quad:
                        x = (1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0]
                        y = (1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1]
                        current_contour.append((x, y))
                i += 2
            elif code == CURVE4:
                if len(current_contour) > 0:
                    p0 = current_contour[-1]
                    p1 = tuple(vertices[i])
                    p2 = tuple(vertices[i + 1])
                    p3 = tuple(vertices[i + 2])
                    for t in t_samples_cubic:
                        x = (1-t)**3 * p0[0] + 3*(1-t)**2*t * p1[0] + 3*(1-t)*t**2 * p2[0] + t**3 * p3[0]
                        y = (1-t)**3 * p0[1] + 3*(1-t)**2*t * p1[1] + 3*(1-t)*t**2 * p2[1] + t**3 * p3[1]
                        current_contour.append((x, y))
                i += 3
            elif code == CLOSEPOLY:
                if len(current_contour) >= 3:
                    contours.append(current_contour)
                current_contour = []
                i += 1
            else:
                i += 1
        
        if len(current_contour) >= 3:
            contours.append(current_contour)
        
        if not contours:
            return None
        
        # Convert contours to polygons
        raw_polygons = []
        for contour in contours:
            try:
                poly = Polygon(contour)
                if poly.is_valid and poly.area > 0.001:
                    raw_polygons.append(poly.buffer(0))  # Clean up
            except:
                continue
        
        if not raw_polygons:
            return None
        
        # CRITICAL: Properly handle holes by checking containment
        # Sort polygons by area (largest first = outer boundaries)
        raw_polygons.sort(key=lambda p: p.area, reverse=True)
        
        # Build polygons with holes
        final_polygons = []
        used = set()
        
        for i, outer in enumerate(raw_polygons):
            if i in used:
                continue
            
            # Find all polygons that are INSIDE this one (potential holes)
            holes = []
            for j, inner in enumerate(raw_polygons):
                if j <= i or j in used:
                    continue
                # Check if inner is completely inside outer
                if outer.contains(inner):
                    holes.append(inner)
                    used.add(j)
            
            # Create polygon with holes
            if holes:
                # Subtract holes from outer polygon
                result = outer
                for hole in holes:
                    try:
                        result = result.difference(hole)
                    except:
                        pass
                if not result.is_empty:
                    final_polygons.append(result)
            else:
                final_polygons.append(outer)
            
            used.add(i)
        
        if not final_polygons:
            return None
        
        # Extrude each polygon (now with proper holes)
        meshes = []
        for poly in final_polygons:
            try:
                if isinstance(poly, MultiPolygon):
                    for p in poly.geoms:
                        if p.is_valid and p.area > 0.01:
                            m = trimesh.creation.extrude_polygon(p, height=depth)
                            if m:
                                meshes.append(m)
                elif poly.is_valid and poly.area > 0.01:
                    m = trimesh.creation.extrude_polygon(poly, height=depth)
                    if m:
                        meshes.append(m)
            except Exception as e:
                print(f"Extrusion failed for polygon: {e}")
                continue
        
        if meshes:
            combined = trimesh.util.concatenate(meshes)
            # Center
            bounds = combined.bounds
            center = (bounds[0] + bounds[1]) / 2
            combined.vertices -= center
            return combined
        
        return None
    
    def _preview_text(self):
        """Preview just the text mesh."""
        self.text_mesh = self._create_text_mesh()
        if self.text_mesh is None:
            self._update_status("Failed to create text mesh")
            return
        
        # Position text on top of base mesh
        text = self.text_mesh.copy()
        
        # Apply rotation
        if self.rotation.value() != 0:
            rot = trimesh.transformations.rotation_matrix(
                np.radians(self.rotation.value()), [0, 0, 1]
            )
            text.apply_transform(rot)
        
        # Position at top surface
        text.vertices[:, 0] += self.offset_x.value()
        text.vertices[:, 1] += self.offset_y.value()
        
        depth = self.depth.value()
        if self.engrave_check.isChecked():
            # For engrave: text extends from ABOVE surface DOWN INTO the mesh
            text_height = text.bounds[1][2] - text.bounds[0][2]
            text.vertices[:, 2] -= text.bounds[0][2]  # Bottom at z=0
            text.vertices[:, 2] -= depth  # Bottom now at -depth
            text.vertices[:, 2] += 0.1  # Shift up slightly so top is just above surface
        else:
            # For emboss: bottom at z=0
            text.vertices[:, 2] -= text.bounds[0][2]
        
        # Show both meshes
        combined = trimesh.util.concatenate([self.base_mesh, text])
        self.viewer.set_insole_mesh(combined)
        
        self._update_status(f"Text mesh: {len(self.text_mesh.vertices)} verts, {len(self.text_mesh.faces)} faces\n"
                           f"Text Z range: {text.bounds[0][2]:.2f} to {text.bounds[1][2]:.2f}\n"
                           f"Watertight: {self.text_mesh.is_watertight}, Volume: {self.text_mesh.is_volume}")
    
    def _apply_boolean(self):
        """Apply boolean operation."""
        self.text_mesh = self._create_text_mesh()
        if self.text_mesh is None:
            self._update_status("Failed to create text mesh")
            return
        
        text = self.text_mesh.copy()
        
        # Apply rotation
        if self.rotation.value() != 0:
            rot = trimesh.transformations.rotation_matrix(
                np.radians(self.rotation.value()), [0, 0, 1]
            )
            text.apply_transform(rot)
        
        # Position
        text.vertices[:, 0] += self.offset_x.value()
        text.vertices[:, 1] += self.offset_y.value()
        
        depth = self.depth.value()
        if self.engrave_check.isChecked():
            # For engrave: text must fully INTERSECT the base mesh
            # Position so text extends from slightly ABOVE surface DOWN INTO the mesh
            text_height = text.bounds[1][2] - text.bounds[0][2]
            text.vertices[:, 2] -= text.bounds[0][2]  # Bottom at z=0
            text.vertices[:, 2] -= depth  # Bottom now at -depth
            text.vertices[:, 2] += 0.1  # Shift up slightly so top is just above surface
            
            self._update_status(f"Text positioned for engrave:\nZ from {text.bounds[0][2]:.2f} to {text.bounds[1][2]:.2f}\nBase top at Z=0, bottom at Z=-{self.mesh_thickness.value()}")
        else:
            text.vertices[:, 2] -= text.bounds[0][2]
        
        engine = self.engine_combo.currentText()
        
        if not self.engrave_check.isChecked():
            # Emboss - just concatenate
            self.result_mesh = trimesh.util.concatenate([self.base_mesh, text])
            self._update_status(f"Emboss applied (concatenation)")
        elif engine == "MeshLib":
            success = self._meshlib_boolean(self.base_mesh, text)
            if not success:
                self._update_status("MeshLib failed - try another engine")
                return
        elif engine == "Manifold":
            try:
                result = self.base_mesh.difference(text, engine='manifold')
                if result and len(result.vertices) > 0:
                    self.result_mesh = result
                    self._update_status(f"Manifold success: {len(result.vertices)} verts")
                else:
                    self._update_status("Manifold returned empty result")
                    return
            except Exception as e:
                self._update_status(f"Manifold failed: {e}")
                return
        else:  # Visual fallback
            text.invert()
            self.result_mesh = trimesh.util.concatenate([self.base_mesh, text])
            self._update_status("Visual engrave (inverted normals)")
        
        self.viewer.set_insole_mesh(self.result_mesh)
    
    def _meshlib_boolean(self, base, text):
        """Use MeshLib for boolean difference."""
        try:
            import meshlib.mrmeshpy as mr
            import tempfile
            import os
            
            with tempfile.TemporaryDirectory() as tmpdir:
                base_path = os.path.join(tmpdir, "base.stl")
                text_path = os.path.join(tmpdir, "text.stl")
                result_path = os.path.join(tmpdir, "result.stl")
                
                base.export(base_path)
                text.export(text_path)
                
                base_mr = mr.loadMesh(base_path)
                text_mr = mr.loadMesh(text_path)
                
                self._update_status(f"MeshLib: base={base_mr.topology.numValidFaces()} faces, "
                                   f"text={text_mr.topology.numValidFaces()} faces")
                
                result = mr.boolean(base_mr, text_mr, mr.BooleanOperation.DifferenceAB)
                
                if result.valid():
                    mr.saveMesh(result.mesh, result_path)
                    self.result_mesh = trimesh.load(result_path)
                    self._update_status(f"MeshLib success: {len(self.result_mesh.vertices)} verts, "
                                       f"{len(self.result_mesh.faces)} faces")
                    return True
                else:
                    error = getattr(result, 'errorString', 'Unknown')
                    self._update_status(f"MeshLib failed: {error}")
                    return False
                    
        except Exception as e:
            self._update_status(f"MeshLib error: {e}")
            return False
    
    def _export_result(self):
        """Export result mesh."""
        if self.result_mesh is None:
            self._update_status("No result to export")
            return
        
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, "Export STL", "label_test.stl", "STL Files (*.stl)")
        if path:
            self.result_mesh.export(path)
            self._update_status(f"Exported to {path}")
    
    def _update_status(self, msg):
        self.status_label.setText(msg)
        print(msg)
    
    def _toggle_wireframe(self, state):
        """Toggle wireframe rendering."""
        if hasattr(self.viewer, 'insole_actor') and self.viewer.insole_actor:
            if state:
                self.viewer.insole_actor.GetProperty().SetRepresentationToWireframe()
            else:
                self.viewer.insole_actor.GetProperty().SetRepresentationToSurface()
            self.viewer.render_window.Render()
    
    def _toggle_edges(self, state):
        """Toggle edge visibility."""
        if hasattr(self.viewer, 'insole_actor') and self.viewer.insole_actor:
            self.viewer.insole_actor.GetProperty().SetEdgeVisibility(state)
            self.viewer.render_window.Render()
    
    def _set_top_view(self):
        """Set camera to top-down view."""
        camera = self.viewer.renderer.GetActiveCamera()
        camera.SetPosition(0, 0, 100)
        camera.SetFocalPoint(0, 0, 0)
        camera.SetViewUp(0, 1, 0)
        self.viewer.renderer.ResetCamera()
        self.viewer.render_window.Render()


def main():
    app = QApplication(sys.argv)
    window = LabelTestWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
