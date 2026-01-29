"""
Dual VTK-Based 3D Mesh Viewer
=============================
Displays LEFT and RIGHT orthosis meshes side-by-side in split viewports.
Features:
- GPU-accelerated rendering (uses OpenGL)
- Dual viewport display (50/50 split)
- Synchronized camera controls
- Point picking on RIGHT viewport only
- Marker mirroring to LEFT viewport

Based on the original VTKMeshViewer with dual-viewport modifications.
"""

import numpy as np
from typing import Optional, List
import vtk
from vtk.util.numpy_support import numpy_to_vtk

from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PySide6.QtCore import Signal, Qt

# VTK-Qt integration
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


class DualMeshViewer(QWidget):
    """
    VTK-based dual viewport 3D mesh viewer with Qt integration.
    Displays LEFT (mirrored) and RIGHT (original) orthosis side-by-side.
    """
    
    # Signals for point picking on RIGHT viewport
    logo_point_picked = Signal(object, object)  # Emits (point, normal) for logo placement
    text_point_picked = Signal(object, object)  # Emits (point, normal) for text placement
    combined_point_picked = Signal(object, object)  # Emits (point, normal) for combined logo+text placement
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Store mesh data
        self.left_mesh = None  # Mirrored mesh
        self.right_mesh = None  # Original mesh
        
        # VTK actors for meshes
        self.left_actor: Optional[vtk.vtkActor] = None
        self.right_actor: Optional[vtk.vtkActor] = None
        
        # Marker actors (logo and text position markers)
        self.right_logo_marker: Optional[vtk.vtkActor] = None
        self.right_text_marker: Optional[vtk.vtkActor] = None
        self.left_logo_marker: Optional[vtk.vtkActor] = None
        self.left_text_marker: Optional[vtk.vtkActor] = None
        
        # Picking mode
        self.logo_picking_enabled = False
        self.text_picking_enabled = False
        self.combined_picking_enabled = False
        
        # Render mode: 'solid', 'wireframe', 'points'
        self._render_mode = 'solid'
        
        # Render settings storage for when actors are recreated
        self._render_settings = {}
        
        # Setup VTK
        self._setup_vtk()
        
        # Setup widget
        self.setMinimumSize(800, 400)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    
    def _setup_vtk(self):
        """Initialize VTK rendering pipeline with dual viewports."""
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create VTK widget
        self.vtk_widget = QVTKRenderWindowInteractor(self)
        layout.addWidget(self.vtk_widget)
        
        # Get render window
        self.render_window = self.vtk_widget.GetRenderWindow()
        
        # Standard anti-aliasing - clean and simple like most STL viewers
        self.render_window.SetMultiSamples(4)
        
        # Create LEFT viewport renderer (0 to 0.5 horizontally)
        self.left_renderer = vtk.vtkRenderer()
        self.left_renderer.SetViewport(0.0, 0.0, 0.5, 1.0)
        self.left_renderer.SetBackground(0.12, 0.15, 0.18)
        self.left_renderer.SetBackground2(0.20, 0.23, 0.28)
        self.left_renderer.GradientBackgroundOn()
        self.render_window.AddRenderer(self.left_renderer)
        
        # Create RIGHT viewport renderer (0.5 to 1.0 horizontally)
        self.right_renderer = vtk.vtkRenderer()
        self.right_renderer.SetViewport(0.5, 0.0, 1.0, 1.0)
        self.right_renderer.SetBackground(0.15, 0.17, 0.20)
        self.right_renderer.SetBackground2(0.25, 0.28, 0.32)
        self.right_renderer.GradientBackgroundOn()
        self.render_window.AddRenderer(self.right_renderer)
        
        # Use INDEPENDENT CAMERAS for left and right viewports
        self.left_camera = vtk.vtkCamera()
        self.right_camera = vtk.vtkCamera()
        self.left_renderer.SetActiveCamera(self.left_camera)
        self.right_renderer.SetActiveCamera(self.right_camera)
        
        # Add viewport labels
        self._add_viewport_labels()
        
        # Setup interactor
        self.interactor = self.render_window.GetInteractor()
        
        # Use trackball camera style for intuitive rotation
        style = vtk.vtkInteractorStyleTrackballCamera()
        self.interactor.SetInteractorStyle(style)
        
        # Setup picker for point selection (RIGHT viewport only)
        self.picker = vtk.vtkCellPicker()
        self.picker.SetTolerance(0.005)
        
        # Add pick observer for point selection
        self.interactor.AddObserver('LeftButtonPressEvent', self._on_left_click)
        
        # Add axes widgets to both viewports
        self._add_axes_widget(self.left_renderer, viewport=(0.0, 0.0, 0.08, 0.15))
        self._add_axes_widget(self.right_renderer, viewport=(0.5, 0.0, 0.58, 0.15))
        
        # Add lighting to both renderers
        self._setup_lighting(self.left_renderer)
        self._setup_lighting(self.right_renderer)
        
        # Initialize the interactor
        self.vtk_widget.Initialize()
        self.vtk_widget.Start()
    
    def _add_viewport_labels(self):
        """Add 'LEFT' and 'RIGHT' labels to viewports."""
        # LEFT label
        left_label = vtk.vtkTextActor()
        left_label.SetInput("LEFT (L)")
        left_label.GetTextProperty().SetFontSize(24)
        left_label.GetTextProperty().SetColor(0.7, 0.7, 0.7)
        left_label.GetTextProperty().SetBold(True)
        left_label.GetTextProperty().SetShadow(True)
        left_label.SetPosition(10, 10)
        self.left_renderer.AddActor2D(left_label)
        self.left_label_actor = left_label
        
        # RIGHT label
        right_label = vtk.vtkTextActor()
        right_label.SetInput("RIGHT (R) - Pick Here")
        right_label.GetTextProperty().SetFontSize(24)
        right_label.GetTextProperty().SetColor(0.7, 0.7, 0.7)
        right_label.GetTextProperty().SetBold(True)
        right_label.GetTextProperty().SetShadow(True)
        right_label.SetPosition(10, 10)
        self.right_renderer.AddActor2D(right_label)
        self.right_label_actor = right_label
    
    def _setup_lighting(self, renderer: vtk.vtkRenderer):
        """Setup lighting for a renderer with fixed world-space lights."""
        # Remove default lights
        renderer.RemoveAllLights()
        
        # Enable two-sided lighting
        renderer.SetTwoSidedLighting(True)
        
        # Use LightKit for consistent, camera-independent lighting
        light_kit = vtk.vtkLightKit()
        light_kit.SetKeyLightIntensity(0.8)
        light_kit.SetKeyLightWarmth(0.6)
        light_kit.SetFillLightWarmth(0.4)
        light_kit.SetBackLightWarmth(0.5)
        light_kit.AddLightsToRenderer(renderer)
    
    def _add_axes_widget(self, renderer: vtk.vtkRenderer, viewport: tuple):
        """Add coordinate axes indicator to a renderer."""
        axes = vtk.vtkAxesActor()
        axes.SetTotalLength(20, 20, 20)
        axes.SetShaftTypeToCylinder()
        axes.SetCylinderRadius(0.02)
        
        axes.GetXAxisCaptionActor2D().GetTextActor().SetTextScaleModeToNone()
        axes.GetYAxisCaptionActor2D().GetTextActor().SetTextScaleModeToNone()
        axes.GetZAxisCaptionActor2D().GetTextActor().SetTextScaleModeToNone()
        
        widget = vtk.vtkOrientationMarkerWidget()
        widget.SetOrientationMarker(axes)
        widget.SetInteractor(self.interactor)
        widget.SetCurrentRenderer(renderer)
        widget.SetViewport(*viewport)
        widget.EnabledOn()
        widget.InteractiveOff()
        
        # Store reference
        if not hasattr(self, 'axes_widgets'):
            self.axes_widgets = []
        self.axes_widgets.append(widget)
    
    def _on_left_click(self, obj, event):
        """Handle left mouse click for point picking on RIGHT viewport."""
        if not (self.logo_picking_enabled or self.text_picking_enabled or self.combined_picking_enabled):
            return
        
        if self.right_mesh is None:
            return
        
        # Get click position
        click_pos = self.interactor.GetEventPosition()
        
        # Check if click is in RIGHT viewport (x > window_width/2)
        window_size = self.render_window.GetSize()
        if click_pos[0] < window_size[0] / 2:
            return  # Click was in LEFT viewport, ignore
        
        # Perform pick in RIGHT renderer
        self.picker.Pick(click_pos[0], click_pos[1], 0, self.right_renderer)
        
        # Check if we picked the right mesh
        picked_actor = self.picker.GetActor()
        if picked_actor == self.right_actor:
            pick_pos = self.picker.GetPickPosition()
            point = np.array(pick_pos)
            
            # Get cell normal
            cell_id = self.picker.GetCellId()
            if cell_id >= 0:
                normal = self._get_cell_normal(self.right_actor, cell_id)
            else:
                normal = np.array([0, 0, 1])
            
            if self.logo_picking_enabled:
                self._add_logo_marker(point, normal)
                self.logo_point_picked.emit(point, normal)
                self.set_logo_picking_mode(False)
                
            elif self.text_picking_enabled:
                self._add_text_marker(point, normal)
                self.text_point_picked.emit(point, normal)
                self.set_text_picking_mode(False)
            
            elif self.combined_picking_enabled:
                self._add_logo_marker(point, normal)  # Use green marker for combined
                self.combined_point_picked.emit(point, normal)
                self.set_combined_picking_mode(False)
    
    def _get_cell_normal(self, actor: vtk.vtkActor, cell_id: int) -> np.ndarray:
        """Get the normal vector of a specific cell."""
        try:
            mapper = actor.GetMapper()
            poly_data = mapper.GetInput()
            
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
        
        return np.array([0, 0, 1])
    
    def _mirror_point(self, point: np.ndarray, axis: str = 'y') -> np.ndarray:
        """Mirror a point about the specified axis (Y-axis mirror only)."""
        mirrored = point.copy()
        if axis.lower() == 'y':
            mirrored[1] = -mirrored[1]
        
        return mirrored
    
    def _add_logo_marker(self, point: np.ndarray, normal: np.ndarray):
        """Add markers showing logo placement on both viewports."""
        # Remove existing logo markers
        self._remove_logo_markers()
        
        # RIGHT viewport marker (green cube for logo)
        self.right_logo_marker = self._create_marker(point, color=(0.2, 0.9, 0.2), shape='cube')
        self.right_renderer.AddActor(self.right_logo_marker)
        
        # LEFT viewport marker (mirrored position)
        mirrored_point = self._mirror_point(point)
        self.left_logo_marker = self._create_marker(mirrored_point, color=(0.2, 0.9, 0.2), shape='cube')
        self.left_renderer.AddActor(self.left_logo_marker)
        
        self.render()
    
    def _add_text_marker(self, point: np.ndarray, normal: np.ndarray):
        """Add markers showing text placement on both viewports."""
        # Remove existing text markers
        self._remove_text_markers()
        
        # RIGHT viewport marker (yellow sphere for text)
        self.right_text_marker = self._create_marker(point, color=(0.9, 0.9, 0.2), shape='sphere')
        self.right_renderer.AddActor(self.right_text_marker)
        
        # LEFT viewport marker (mirrored position)
        mirrored_point = self._mirror_point(point)
        self.left_text_marker = self._create_marker(mirrored_point, color=(0.9, 0.9, 0.2), shape='sphere')
        self.left_renderer.AddActor(self.left_text_marker)
        
        self.render()
    
    def _create_marker(self, point: np.ndarray, color: tuple, shape: str = 'sphere') -> vtk.vtkActor:
        """Create a visual marker at the given point."""
        if shape == 'cube':
            source = vtk.vtkCubeSource()
            source.SetCenter(*point)
            source.SetXLength(4.0)
            source.SetYLength(4.0)
            source.SetZLength(4.0)
        else:  # sphere
            source = vtk.vtkSphereSource()
            source.SetCenter(*point)
            source.SetRadius(2.5)
            source.SetPhiResolution(16)
            source.SetThetaResolution(16)
        
        source.Update()
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(source.GetOutputPort())
        
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*color)
        
        return actor
    
    def _remove_logo_markers(self):
        """Remove logo markers from both viewports."""
        if self.right_logo_marker:
            self.right_renderer.RemoveActor(self.right_logo_marker)
            self.right_logo_marker = None
        if self.left_logo_marker:
            self.left_renderer.RemoveActor(self.left_logo_marker)
            self.left_logo_marker = None
    
    def _remove_text_markers(self):
        """Remove text markers from both viewports."""
        if self.right_text_marker:
            self.right_renderer.RemoveActor(self.right_text_marker)
            self.right_text_marker = None
        if self.left_text_marker:
            self.left_renderer.RemoveActor(self.left_text_marker)
            self.left_text_marker = None
    
    def _trimesh_to_vtk(self, mesh) -> vtk.vtkPolyData:
        """Convert trimesh mesh to VTK polydata with proper normals."""
        points = vtk.vtkPoints()
        vtk_points = numpy_to_vtk(mesh.vertices.astype(np.float64), deep=True)
        points.SetData(vtk_points)
        
        cells = vtk.vtkCellArray()
        for face in mesh.faces:
            cells.InsertNextCell(3)
            cells.InsertCellPoint(face[0])
            cells.InsertCellPoint(face[1])
            cells.InsertCellPoint(face[2])
        
        polydata = vtk.vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetPolys(cells)
        
        # Simple normals computation - matches most STL viewers
        normals = vtk.vtkPolyDataNormals()
        normals.SetInputData(polydata)
        normals.ComputePointNormalsOn()
        normals.ComputeCellNormalsOn()
        normals.SplittingOff()  # Keep original mesh topology
        normals.ConsistencyOn()
        normals.AutoOrientNormalsOn()
        normals.Update()
        
        return normals.GetOutput()
    
    def _create_actor(self, polydata: vtk.vtkPolyData, color: tuple, opacity: float = 1.0) -> vtk.vtkActor:
        """Create a VTK actor from polydata."""
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(polydata)
        mapper.ScalarVisibilityOff()
        
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        
        prop = actor.GetProperty()
        prop.SetColor(*color)
        prop.SetOpacity(opacity)
        prop.SetAmbient(0.1)
        prop.SetDiffuse(0.9)
        prop.SetSpecular(0.3)
        prop.SetSpecularPower(20)
        prop.SetBackfaceCulling(False)
        prop.SetFrontfaceCulling(False)
        prop.SetInterpolationToPhong()
        
        self._apply_render_mode_to_actor(actor)
        
        # Apply stored render settings if available
        if hasattr(self, '_render_settings') and self._render_settings:
            self._apply_stored_settings_to_actor(actor, color)
        
        return actor
    
    def set_render_settings(self, settings: dict):
        """Store render settings and apply to current actors."""
        self._render_settings = settings
        self.apply_render_settings(settings)
    
    def apply_render_settings(self, settings: dict):
        """Apply render settings to all actors."""
        if not settings:
            return
        
        render = settings.get('render', settings)  # Handle both full dict and render-only dict
        
        # Apply to actors
        for actor, color_key in [(self.right_actor, 'right_color'), (self.left_actor, 'left_color')]:
            if actor:
                self._apply_stored_settings_to_actor(actor, render.get(color_key, (0.4, 0.6, 0.85)), render)
        
        # Apply background settings
        bg = render.get('bg_color', (0.15, 0.17, 0.20))
        bg2 = render.get('bg_color2', (0.25, 0.28, 0.32))
        if render.get('gradient_bg', True):
            self.right_renderer.GradientBackgroundOn()
            self.left_renderer.GradientBackgroundOn()
            self.right_renderer.SetBackground(*bg)
            self.right_renderer.SetBackground2(*bg2)
            self.left_renderer.SetBackground(bg[0] * 0.8, bg[1] * 0.88, bg[2] * 0.9)
            self.left_renderer.SetBackground2(bg2[0] * 0.8, bg2[1] * 0.88, bg2[2] * 0.9)
        else:
            self.right_renderer.GradientBackgroundOff()
            self.left_renderer.GradientBackgroundOff()
            self.right_renderer.SetBackground(*bg)
            self.left_renderer.SetBackground(bg[0] * 0.8, bg[1] * 0.88, bg[2] * 0.9)
        
        # Apply depth peeling
        if render.get('depth_peeling', False):
            self.right_renderer.SetUseDepthPeeling(1)
            self.right_renderer.SetMaximumNumberOfPeels(4)
            self.left_renderer.SetUseDepthPeeling(1)
            self.left_renderer.SetMaximumNumberOfPeels(4)
        else:
            self.right_renderer.SetUseDepthPeeling(0)
            self.left_renderer.SetUseDepthPeeling(0)
        
        # Apply MSAA
        msaa = render.get('msaa', 4)
        self.render_window.SetMultiSamples(msaa)
        
        self.render()
    
    def _apply_stored_settings_to_actor(self, actor, color, render=None):
        """Apply stored settings to a single actor."""
        if render is None:
            render = getattr(self, '_render_settings', {}).get('render', {})
        
        prop = actor.GetProperty()
        prop.SetColor(*color)
        
        # Lighting
        prop.SetAmbient(render.get('ambient', 0.1))
        prop.SetDiffuse(render.get('diffuse', 0.9))
        prop.SetSpecular(render.get('specular', 0.3))
        prop.SetSpecularPower(render.get('specular_power', 20))
        
        # Opacity
        prop.SetOpacity(render.get('opacity', 1.0))
        
        # Backface culling
        prop.SetBackfaceCulling(render.get('backface_culling', False))
        
        # Edge visibility
        if render.get('edge_visibility', False):
            prop.EdgeVisibilityOn()
            prop.SetEdgeColor(*render.get('edge_color', (0.1, 0.1, 0.1)))
            prop.SetLineWidth(render.get('edge_width', 1.0))
        else:
            prop.EdgeVisibilityOff()
        
        # Point size
        prop.SetPointSize(render.get('point_size', 3.0))
        
        # Shading mode
        shading = render.get('shading', 0)
        if shading == 0:
            prop.SetInterpolationToPhong()
        elif shading == 1:
            prop.SetInterpolationToGouraud()
        else:
            prop.SetInterpolationToFlat()
    
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
    
    def set_left_mesh(self, mesh, auto_reset=True):
        """Set the LEFT (mirrored) mesh."""
        self.left_mesh = mesh
        
        if self.left_actor is not None:
            self.left_renderer.RemoveActor(self.left_actor)
        
        if mesh is not None:
            polydata = self._trimesh_to_vtk(mesh)
            # Use stored color from settings if available
            render = self._render_settings.get('render', {})
            left_color = render.get('left_color', (0.4, 0.6, 0.85))
            self.left_actor = self._create_actor(
                polydata,
                color=left_color,
                opacity=1.0
            )
            self.left_renderer.AddActor(self.left_actor)
        
        if auto_reset:
            self.reset_camera()
            self.render()
    
    def set_right_mesh(self, mesh, auto_reset=True):
        """Set the RIGHT (original) mesh."""
        self.right_mesh = mesh
        
        if self.right_actor is not None:
            self.right_renderer.RemoveActor(self.right_actor)
        
        if mesh is not None:
            polydata = self._trimesh_to_vtk(mesh)
            # Use stored color from settings if available
            render = self._render_settings.get('render', {})
            right_color = render.get('right_color', (0.4, 0.6, 0.85))
            self.right_actor = self._create_actor(
                polydata,
                color=right_color,
                opacity=1.0
            )
            self.right_renderer.AddActor(self.right_actor)
        
        if auto_reset:
            self.reset_camera()
            self.render()
    
    def set_both_meshes(self, left_mesh, right_mesh, auto_reset: bool = True):
        """Set both LEFT and RIGHT meshes at once."""
        # Set meshes without auto-reset
        self.set_left_mesh(left_mesh, auto_reset=False)
        self.set_right_mesh(right_mesh, auto_reset=False)
        # Reset camera once after both meshes are set (unless disabled)
        if auto_reset:
            self.reset_camera()
        self.render()
    
    def set_logo_picking_mode(self, enabled: bool):
        """Enable or disable logo placement picking mode."""
        self.logo_picking_enabled = enabled
        self.text_picking_enabled = False
        self.combined_picking_enabled = False
        
        if enabled:
            self.setCursor(Qt.CursorShape.CrossCursor)
            self.right_label_actor.SetInput("RIGHT (R) - Click to place LOGO")
            self.right_label_actor.GetTextProperty().SetColor(0.2, 0.9, 0.2)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.right_label_actor.SetInput("RIGHT (R) - Pick Here")
            self.right_label_actor.GetTextProperty().SetColor(0.7, 0.7, 0.7)
        
        self.render()
    
    def set_text_picking_mode(self, enabled: bool):
        """Enable or disable text placement picking mode."""
        self.text_picking_enabled = enabled
        self.logo_picking_enabled = False
        self.combined_picking_enabled = False
        
        if enabled:
            self.setCursor(Qt.CursorShape.CrossCursor)
            self.right_label_actor.SetInput("RIGHT (R) - Click to place TEXT")
            self.right_label_actor.GetTextProperty().SetColor(0.9, 0.9, 0.2)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.right_label_actor.SetInput("RIGHT (R) - Pick Here")
            self.right_label_actor.GetTextProperty().SetColor(0.7, 0.7, 0.7)
        
        self.render()
    
    def set_combined_picking_mode(self, enabled: bool):
        """Enable or disable combined logo+text placement picking mode."""
        self.combined_picking_enabled = enabled
        self.logo_picking_enabled = False
        self.text_picking_enabled = False
        
        if enabled:
            self.setCursor(Qt.CursorShape.CrossCursor)
            self.right_label_actor.SetInput("RIGHT (R) - Click to place LOGO + TEXT")
            self.right_label_actor.GetTextProperty().SetColor(0.2, 0.9, 0.5)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.right_label_actor.SetInput("RIGHT (R) - Pick Here")
            self.right_label_actor.GetTextProperty().SetColor(0.7, 0.7, 0.7)
        
        self.render()
    
    def clear_all_markers(self):
        """Clear all placement markers."""
        self._remove_logo_markers()
        self._remove_text_markers()
        self.render()
    
    def set_render_mode(self, mode: str):
        """Set render mode: 'solid', 'solid_edges', 'wireframe', or 'points'."""
        if mode not in ('solid', 'solid_edges', 'wireframe', 'points'):
            return
        
        self._render_mode = mode
        
        for actor in [self.left_actor, self.right_actor]:
            if actor is not None:
                self._apply_render_mode_to_actor(actor)
        
        self.render()
    
    def get_render_mode(self) -> str:
        """Get current render mode."""
        return self._render_mode
    
    def set_mesh_color(self, r: float, g: float, b: float):
        """Set mesh color for both viewports."""
        for actor in [self.left_actor, self.right_actor]:
            if actor is not None:
                actor.GetProperty().SetColor(r, g, b)
        self.render()
    
    def reset_view(self):
        """Reset the camera to show all objects."""
        self.reset_camera()
        self.render()
    
    def reset_camera(self):
        """Reset both cameras to isometric view fitting all visible objects."""
        # Reset each camera independently to fit content
        self.left_renderer.ResetCamera()
        self.right_renderer.ResetCamera()
        
        # Set isometric view for both cameras
        for renderer, camera in [(self.left_renderer, self.left_camera), 
                                  (self.right_renderer, self.right_camera)]:
            focal = camera.GetFocalPoint()
            distance = camera.GetDistance()
            
            # Isometric view position
            camera.SetPosition(
                focal[0] + distance * 0.6,
                focal[1] - distance * 0.6,
                focal[2] + distance * 0.5
            )
            camera.SetViewUp(0, 0, 1)
            
            # Zoom out slightly for better view
            camera.Zoom(0.9)
            
            renderer.ResetCameraClippingRange()
    
    def set_view(self, view: str):
        """Set predefined camera view for both viewports."""
        # Set view for both cameras independently
        for renderer, camera in [(self.left_renderer, self.left_camera), 
                                  (self.right_renderer, self.right_camera)]:
            renderer.ResetCamera()
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
            
            renderer.ResetCameraClippingRange()
        
        self.render()
    
    def render(self):
        """Refresh the render window."""
        self.render_window.Render()
    
    def closeEvent(self, event):
        """Clean up VTK resources on close."""
        self.vtk_widget.Finalize()
        super().closeEvent(event)
