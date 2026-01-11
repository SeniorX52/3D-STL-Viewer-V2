"""
VTK-Based 3D Mesh Viewer
========================
High-performance 3D viewer using VTK (Visualization Toolkit).
Features:
- GPU-accelerated rendering (uses OpenGL)
- Proper solid/wireframe/points rendering
- Smooth trackball rotation
- Point picking for reference points
- Works with or without dedicated GPU

VTK automatically uses the best available graphics hardware.
"""

import numpy as np
from typing import Optional, List
import vtk
from vtk.util.numpy_support import numpy_to_vtk

from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PySide6.QtCore import Signal, Qt

# VTK-Qt integration
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


class VTKMeshViewer(QWidget):
    """
    VTK-based 3D mesh viewer with Qt integration.
    Provides GPU-accelerated rendering of STL meshes.
    """
    
    # Signal emitted when a point is picked on the mesh
    point_picked = Signal(object)  # Emits numpy array [x, y, z]
    label_point_picked = Signal(object, object)  # Emits (point, normal) for label placement
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Store mesh data
        self.foot_mesh = None
        self.insole_mesh = None
        
        # VTK actors for meshes
        self.foot_actor: Optional[vtk.vtkActor] = None
        self.insole_actor: Optional[vtk.vtkActor] = None
        
        # Reference points
        self.reference_points: List[np.ndarray] = []
        self.reference_labels = ['Heel', '1st Meta', '5th Meta']
        self.point_actors: List[vtk.vtkActor] = []
        self.label_actors: List[vtk.vtkActor2D] = []
        
        # Picking mode
        self.picking_enabled = False
        self.label_picking_enabled = False  # For label placement picking
        
        # Label placement marker
        self.label_marker_actor: Optional[vtk.vtkActor] = None
        
        # Render mode: 'solid', 'wireframe', 'points'
        self._render_mode = 'solid'
        
        # Setup VTK
        self._setup_vtk()
        
        # Setup widget
        self.setMinimumSize(400, 400)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    
    def _setup_vtk(self):
        """Initialize VTK rendering pipeline."""
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create VTK widget
        self.vtk_widget = QVTKRenderWindowInteractor(self)
        layout.addWidget(self.vtk_widget)
        
        # Create renderer
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.15, 0.17, 0.20)  # Dark background
        self.renderer.SetBackground2(0.25, 0.28, 0.32)  # Gradient
        self.renderer.GradientBackgroundOn()
        
        # Get render window and add renderer
        self.render_window = self.vtk_widget.GetRenderWindow()
        self.render_window.AddRenderer(self.renderer)
        
        # Enable anti-aliasing if available
        self.render_window.SetMultiSamples(4)
        
        # Setup interactor
        self.interactor = self.render_window.GetInteractor()
        
        # Use trackball camera style for intuitive rotation
        style = vtk.vtkInteractorStyleTrackballCamera()
        self.interactor.SetInteractorStyle(style)
        
        # Setup picker for point selection
        self.picker = vtk.vtkCellPicker()
        self.picker.SetTolerance(0.005)
        
        # Add pick observer for point selection
        self.interactor.AddObserver('LeftButtonPressEvent', self._on_left_click)
        
        # Add coordinate axes
        self._add_axes_widget()
        
        # Add lighting
        self._setup_lighting()
        
        # Initialize the interactor
        self.vtk_widget.Initialize()
        self.vtk_widget.Start()
    
    def _setup_lighting(self):
        """Setup lighting for better visualization."""
        # Remove default lights
        self.renderer.RemoveAllLights()
        
        # Enable two-sided lighting - critical for proper rendering after boolean operations
        # This ensures both sides of faces are lit correctly regardless of normal direction
        self.renderer.SetTwoSidedLighting(True)
        
        # Key light (main light from front-top-right)
        key_light = vtk.vtkLight()
        key_light.SetLightTypeToSceneLight()
        key_light.SetPosition(1, 1, 1)
        key_light.SetFocalPoint(0, 0, 0)
        key_light.SetColor(1.0, 1.0, 1.0)
        key_light.SetIntensity(0.8)
        self.renderer.AddLight(key_light)
        
        # Fill light (softer light from left)
        fill_light = vtk.vtkLight()
        fill_light.SetLightTypeToSceneLight()
        fill_light.SetPosition(-1, 0.5, 0.5)
        fill_light.SetFocalPoint(0, 0, 0)
        fill_light.SetColor(0.9, 0.9, 1.0)
        fill_light.SetIntensity(0.4)
        self.renderer.AddLight(fill_light)
        
        # Back light (rim light)
        back_light = vtk.vtkLight()
        back_light.SetLightTypeToSceneLight()
        back_light.SetPosition(0, -1, -0.5)
        back_light.SetFocalPoint(0, 0, 0)
        back_light.SetColor(1.0, 0.95, 0.9)
        back_light.SetIntensity(0.3)
        self.renderer.AddLight(back_light)
    
    def _add_axes_widget(self):
        """Add coordinate axes indicator."""
        axes = vtk.vtkAxesActor()
        axes.SetTotalLength(20, 20, 20)
        axes.SetShaftTypeToCylinder()
        axes.SetCylinderRadius(0.02)
        
        # Configure labels
        axes.GetXAxisCaptionActor2D().GetTextActor().SetTextScaleModeToNone()
        axes.GetYAxisCaptionActor2D().GetTextActor().SetTextScaleModeToNone()
        axes.GetZAxisCaptionActor2D().GetTextActor().SetTextScaleModeToNone()
        
        # Create orientation marker widget
        self.axes_widget = vtk.vtkOrientationMarkerWidget()
        self.axes_widget.SetOrientationMarker(axes)
        self.axes_widget.SetInteractor(self.interactor)
        self.axes_widget.SetViewport(0, 0, 0.15, 0.15)
        self.axes_widget.EnabledOn()
        self.axes_widget.InteractiveOff()
    
    def _on_left_click(self, obj, event):
        """Handle left mouse click for point picking."""
        # Handle label picking mode (for insole)
        if self.label_picking_enabled and self.insole_mesh is not None:
            click_pos = self.interactor.GetEventPosition()
            self.picker.Pick(click_pos[0], click_pos[1], 0, self.renderer)
            
            picked_actor = self.picker.GetActor()
            if picked_actor == self.insole_actor:
                pick_pos = self.picker.GetPickPosition()
                point = np.array(pick_pos)
                
                # Get cell ID and compute normal
                cell_id = self.picker.GetCellId()
                if cell_id >= 0:
                    normal = self._get_cell_normal(self.insole_actor, cell_id)
                else:
                    normal = np.array([0, 0, 1])  # Default up
                
                # Add marker at picked point
                self._add_label_marker(point, normal)
                
                # Emit signal with point and normal
                self.label_point_picked.emit(point, normal)
                
                # Disable picking mode
                self.set_label_picking_mode(False)
            return
        
        if not self.picking_enabled:
            return
        
        if self.foot_mesh is None:
            return
        
        # Get click position
        click_pos = self.interactor.GetEventPosition()
        
        # Perform pick
        self.picker.Pick(click_pos[0], click_pos[1], 0, self.renderer)
        
        # Check if we picked the foot mesh
        picked_actor = self.picker.GetActor()
        if picked_actor == self.foot_actor:
            # Get picked position
            pick_pos = self.picker.GetPickPosition()
            point = np.array(pick_pos)
            
            # Add reference point
            self.add_reference_point(point)
            self.point_picked.emit(point)
            
            # Disable picking after 3 points
            if len(self.reference_points) >= 3:
                self.set_picking_mode(False)
    

    
    def _trimesh_to_vtk(self, mesh) -> vtk.vtkPolyData:
        """Convert trimesh mesh to VTK polydata."""
        # Create VTK points
        points = vtk.vtkPoints()
        vtk_points = numpy_to_vtk(mesh.vertices.astype(np.float64), deep=True)
        points.SetData(vtk_points)
        
        # Create VTK cells (triangles)
        cells = vtk.vtkCellArray()
        for face in mesh.faces:
            cells.InsertNextCell(3)
            cells.InsertCellPoint(face[0])
            cells.InsertCellPoint(face[1])
            cells.InsertCellPoint(face[2])
        
        # Create polydata
        polydata = vtk.vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetPolys(cells)
        
        # Compute normals for proper shading
        # Use ConsistencyOn to ensure normals face the same direction
        normals = vtk.vtkPolyDataNormals()
        normals.SetInputData(polydata)
        normals.ComputePointNormalsOn()
        normals.ComputeCellNormalsOn()
        normals.SplittingOff()
        normals.ConsistencyOn()  # Ensure consistent normal orientation
        normals.AutoOrientNormalsOn()  # Auto-orient normals outward
        normals.Update()
        
        return normals.GetOutput()
    
    def _create_actor(self, polydata: vtk.vtkPolyData, color: tuple, opacity: float = 1.0) -> vtk.vtkActor:
        """Create a VTK actor from polydata."""
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(polydata)
        
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        
        # Set material properties
        prop = actor.GetProperty()
        prop.SetColor(*color)
        prop.SetOpacity(opacity)
        prop.SetAmbient(0.1)
        prop.SetDiffuse(0.7)
        prop.SetSpecular(0.3)
        prop.SetSpecularPower(20)
        
        # Enable two-sided lighting - this ensures faces render correctly
        # regardless of normal direction (important after boolean operations)
        prop.SetBackfaceCulling(False)
        prop.SetFrontfaceCulling(False)
        
        # Apply current render mode
        self._apply_render_mode_to_actor(actor)
        
        return actor
    
    def _apply_render_mode_to_actor(self, actor: vtk.vtkActor):
        """Apply current render mode to an actor."""
        prop = actor.GetProperty()
        
        if self._render_mode == 'wireframe':
            prop.SetRepresentationToWireframe()
            prop.SetLineWidth(1.0)
            prop.EdgeVisibilityOff()
        elif self._render_mode == 'points':
            prop.SetRepresentationToPoints()
            prop.SetPointSize(3.0)
            prop.EdgeVisibilityOff()
        elif self._render_mode == 'solid_edges':
            prop.SetRepresentationToSurface()
            prop.EdgeVisibilityOn()
            prop.SetEdgeColor(0.1, 0.1, 0.1)
            prop.SetLineWidth(1.0)
        else:  # solid
            prop.SetRepresentationToSurface()
            prop.EdgeVisibilityOff()
    
    def set_foot_mesh(self, mesh):
        """Set the foot mesh to display."""
        self.foot_mesh = mesh
        
        # Remove old actor
        if self.foot_actor is not None:
            self.renderer.RemoveActor(self.foot_actor)
        
        if mesh is not None:
            # Convert to VTK and create actor
            polydata = self._trimesh_to_vtk(mesh)
            self.foot_actor = self._create_actor(
                polydata, 
                color=(0.85, 0.75, 0.65),  # Skin-like color
                opacity=1.0
            )
            self.renderer.AddActor(self.foot_actor)
        
        self.reset_camera()
        self.render()
    
    def set_insole_mesh(self, mesh):
        """Set the insole mesh to display."""
        self.insole_mesh = mesh
        
        # Remove old actor
        if self.insole_actor is not None:
            self.renderer.RemoveActor(self.insole_actor)
        
        if mesh is not None:
            # Convert to VTK and create actor
            polydata = self._trimesh_to_vtk(mesh)
            self.insole_actor = self._create_actor(
                polydata,
                color=(0.4, 0.6, 0.85),  # Blue color
                opacity=1.0
            )
            self.renderer.AddActor(self.insole_actor)
        
        self.render()
    
    def set_picking_mode(self, enabled: bool):
        """Enable or disable point picking mode."""
        self.picking_enabled = enabled
        
        if enabled:
            self.setCursor(Qt.CursorShape.CrossCursor)
            # Reduce foot opacity for better point visibility during picking
            if self.foot_actor:
                self.foot_actor.GetProperty().SetOpacity(0.7)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            if self.foot_actor:
                self.foot_actor.GetProperty().SetOpacity(1.0)
        
        self.render()
    
    def set_label_picking_mode(self, enabled: bool):
        """Enable or disable label placement picking mode."""
        self.label_picking_enabled = enabled
        
        if enabled:
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        
        self.render()
    
    def _get_cell_normal(self, actor: vtk.vtkActor, cell_id: int) -> np.ndarray:
        """Get the normal vector of a specific cell (triangle face)."""
        try:
            mapper = actor.GetMapper()
            poly_data = mapper.GetInput()
            
            # Compute normals if not present
            normals_filter = vtk.vtkPolyDataNormals()
            normals_filter.SetInputData(poly_data)
            normals_filter.ComputeCellNormalsOn()
            normals_filter.Update()
            
            output = normals_filter.GetOutput()
            cell_normals = output.GetCellData().GetNormals()
            
            if cell_normals and cell_id < cell_normals.GetNumberOfTuples():
                normal = np.array(cell_normals.GetTuple3(cell_id))
                return normal / np.linalg.norm(normal)
        except Exception as e:
            print(f"Could not get cell normal: {e}")
        
        return np.array([0, 0, 1])  # Default up
    
    def _add_label_marker(self, point: np.ndarray, normal: np.ndarray):
        """Add a marker showing where the label will be placed."""
        # Remove existing marker
        self.remove_label_marker()
        
        # Create sphere for point marker
        sphere = vtk.vtkSphereSource()
        sphere.SetCenter(*point)
        sphere.SetRadius(2.0)
        sphere.SetPhiResolution(16)
        sphere.SetThetaResolution(16)
        sphere.Update()
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(sphere.GetOutputPort())
        
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0.2, 1.0, 0.2)  # Green
        
        self.label_marker_actor = actor
        self.renderer.AddActor(actor)
        self.render()
    
    def remove_label_marker(self):
        """Remove the label placement marker."""
        if self.label_marker_actor is not None:
            self.renderer.RemoveActor(self.label_marker_actor)
            self.label_marker_actor = None
            self.render()
    
    def add_reference_point(self, point: np.ndarray):
        """Add a reference point marker."""
        if len(self.reference_points) >= 3:
            return
        
        self.reference_points.append(np.array(point))
        
        # Create sphere for point marker
        sphere = vtk.vtkSphereSource()
        sphere.SetCenter(*point)
        sphere.SetRadius(3.0)  # Adjust size as needed
        sphere.SetPhiResolution(16)
        sphere.SetThetaResolution(16)
        sphere.Update()
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(sphere.GetOutputPort())
        
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(1.0, 0.2, 0.2)  # Red
        
        self.point_actors.append(actor)
        self.renderer.AddActor(actor)
        
        # Create text label
        idx = len(self.reference_points) - 1
        label_text = self.reference_labels[idx] if idx < len(self.reference_labels) else f"P{idx+1}"
        
        text_actor = vtk.vtkBillboardTextActor3D()
        text_actor.SetInput(label_text)
        text_actor.SetPosition(point[0] + 5, point[1] + 5, point[2] + 5)
        text_actor.GetTextProperty().SetFontSize(14)
        text_actor.GetTextProperty().SetColor(1.0, 1.0, 1.0)
        text_actor.GetTextProperty().SetBold(True)
        text_actor.GetTextProperty().SetShadow(True)
        
        self.label_actors.append(text_actor)
        self.renderer.AddActor(text_actor)
        
        self.render()
    
    def clear_reference_points(self):
        """Clear all reference points."""
        for actor in self.point_actors:
            self.renderer.RemoveActor(actor)
        for actor in self.label_actors:
            self.renderer.RemoveActor(actor)
        
        self.point_actors.clear()
        self.label_actors.clear()
        self.reference_points.clear()
        
        self.render()
    
    def get_reference_points(self) -> List[np.ndarray]:
        """Get the current reference points."""
        return self.reference_points.copy()
    
    def set_render_mode(self, mode: str):
        """Set render mode: 'solid', 'solid_edges', 'wireframe', or 'points'."""
        if mode not in ('solid', 'solid_edges', 'wireframe', 'points'):
            return
        
        self._render_mode = mode
        
        # Apply to all mesh actors
        for actor in [self.foot_actor, self.insole_actor]:
            if actor is not None:
                self._apply_render_mode_to_actor(actor)
        
        self.render()
    
    def get_render_mode(self) -> str:
        """Get current render mode."""
        return self._render_mode
    
    def set_foot_opacity(self, opacity: float):
        """Set foot mesh opacity (0.0 to 1.0)."""
        if self.foot_actor is not None:
            self.foot_actor.GetProperty().SetOpacity(opacity)
            self.render()
    
    def set_insole_opacity(self, opacity: float):
        """Set insole mesh opacity (0.0 to 1.0)."""
        if self.insole_actor is not None:
            self.insole_actor.GetProperty().SetOpacity(opacity)
            self.render()
    
    def set_foot_color(self, r: float, g: float, b: float):
        """Set foot mesh color (RGB values 0.0 to 1.0)."""
        if self.foot_actor is not None:
            self.foot_actor.GetProperty().SetColor(r, g, b)
            self.render()
    
    def set_insole_color(self, r: float, g: float, b: float):
        """Set insole mesh color (RGB values 0.0 to 1.0)."""
        if self.insole_actor is not None:
            self.insole_actor.GetProperty().SetColor(r, g, b)
            self.render()
    
    def reset_view(self):
        """Reset the camera to show all objects."""
        self.reset_camera()
        self.render()
    
    def reset_camera(self):
        """Reset camera to fit all visible objects."""
        self.renderer.ResetCamera()
        # Zoom out a bit for better view
        self.renderer.GetActiveCamera().Zoom(0.9)
    
    def set_view(self, view: str):
        """Set predefined camera view."""
        camera = self.renderer.GetActiveCamera()
        
        # Get focal point (center of scene)
        self.renderer.ResetCamera()
        focal = camera.GetFocalPoint()
        distance = camera.GetDistance()
        
        if view == 'top':
            camera.SetPosition(focal[0], focal[1], focal[2] + distance)
            camera.SetViewUp(0, 1, 0)
        elif view == 'front':
            camera.SetPosition(focal[0], focal[1] - distance, focal[2])
            camera.SetViewUp(0, 0, 1)
        elif view == 'side':
            camera.SetPosition(focal[0] + distance, focal[1], focal[2])
            camera.SetViewUp(0, 0, 1)
        elif view == 'iso':
            camera.SetPosition(
                focal[0] + distance * 0.6,
                focal[1] - distance * 0.6,
                focal[2] + distance * 0.5
            )
            camera.SetViewUp(0, 0, 1)
        
        self.renderer.ResetCameraClippingRange()
        self.render()
    
    def render(self):
        """Refresh the render window."""
        self.render_window.Render()
    
    def closeEvent(self, event):
        """Clean up VTK resources on close."""
        self.vtk_widget.Finalize()
        super().closeEvent(event)


# Alias for backward compatibility
SimpleMeshViewer = VTKMeshViewer
