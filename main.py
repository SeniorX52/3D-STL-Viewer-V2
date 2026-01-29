"""
Orthosis Customizer - Main Application
======================================
A Windows desktop application for customizing orthosis STL files with:
- Automatic left/right mirroring
- Logo engraving
- Patient name and date text engraving
- Dual STL export (Left and Right versions)

Author: Mostafa Abdelaziz
License: MIT
"""

import sys
import os
from datetime import datetime
from typing import Optional


def get_application_path() -> str:
    """Get the application base directory."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))


# PySide6 imports for GUI
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QPushButton, QLabel, QLineEdit, QComboBox,
    QFileDialog, QMessageBox, QStatusBar, QSplitter,
    QFrame, QGridLayout, QSlider, QScrollArea, QDialog,
    QTabWidget, QSpinBox, QDoubleSpinBox, QCheckBox, QColorDialog,
    QDialogButtonBox, QFormLayout
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QAction, QPixmap, QColor

# Import our custom modules
from src.orthosis_processor import OrthosisProcessor
from src.dual_mesh_viewer import DualMeshViewer

import numpy as np


class NoWheelSlider(QSlider):
    """QSlider that ignores mouse wheel events to prevent accidental changes."""
    def wheelEvent(self, event):
        event.ignore()


class SettingsDialog(QDialog):
    """Comprehensive settings dialog for the application."""
    
    def __init__(self, parent=None, settings: QSettings = None):
        super().__init__(parent)
        self.settings = settings or QSettings('OrthosisCustomizer', 'OrthosisApp')
        self.setWindowTitle("Settings")
        self.setMinimumSize(600, 500)
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        """Setup the settings dialog UI."""
        layout = QVBoxLayout(self)
        
        # Tab widget for different setting categories
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self._create_rendering_tab()
        self._create_engraving_tab()
        self._create_logo_tab()
        self._create_export_tab()
        self._create_display_tab()
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.RestoreDefaults
        )
        button_box.accepted.connect(self._save_and_accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self._restore_defaults)
        layout.addWidget(button_box)
    
    def _create_rendering_tab(self):
        """Create rendering settings tab."""
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setSpacing(10)
        
        # === Rendering Engine Section ===
        engine_header = QLabel("<b>Rendering Engine</b>")
        layout.addRow(engine_header)
        
        # Rendering backend
        self.render_backend_combo = QComboBox()
        self.render_backend_combo.addItems(['OpenGL (Default)', 'OpenGL2 (Modern)', 'OSPRay (Ray Tracing)'])
        self.render_backend_combo.setToolTip("OpenGL2 is recommended for best quality. OSPRay requires additional installation.")
        layout.addRow("Render Backend:", self.render_backend_combo)
        
        # Anti-aliasing
        self.msaa_combo = QComboBox()
        self.msaa_combo.addItems(['Off (0)', '2x MSAA', '4x MSAA', '8x MSAA', '16x MSAA'])
        layout.addRow("Anti-Aliasing:", self.msaa_combo)
        
        # FXAA (Fast approximate anti-aliasing)
        self.fxaa_check = QCheckBox("Enable FXAA (Fast Approximate AA)")
        self.fxaa_check.setChecked(False)
        self.fxaa_check.setToolTip("Additional screen-space anti-aliasing")
        layout.addRow("", self.fxaa_check)
        
        # SSAO (Screen Space Ambient Occlusion)
        self.ssao_check = QCheckBox("Enable SSAO (Ambient Occlusion)")
        self.ssao_check.setChecked(False)
        self.ssao_check.setToolTip("Adds realistic shadows in corners and crevices")
        layout.addRow("", self.ssao_check)
        
        # Depth peeling for transparency
        self.depth_peeling_check = QCheckBox("Enable Depth Peeling")
        self.depth_peeling_check.setChecked(False)
        self.depth_peeling_check.setToolTip("Better handling of overlapping transparent surfaces")
        layout.addRow("", self.depth_peeling_check)
        
        # === Colors Section ===
        color_header = QLabel("<b>Colors</b>")
        layout.addRow(color_header)
        
        # Mesh color (Right side)
        self.right_color_btn = QPushButton()
        self.right_color_btn.setFixedSize(100, 25)
        self.right_color_btn.clicked.connect(lambda: self._pick_color('right'))
        self._right_color = QColor(102, 153, 217)  # Default blue
        layout.addRow("Right Mesh Color:", self.right_color_btn)
        
        # Mesh color (Left side)
        self.left_color_btn = QPushButton()
        self.left_color_btn.setFixedSize(100, 25)
        self.left_color_btn.clicked.connect(lambda: self._pick_color('left'))
        self._left_color = QColor(102, 153, 217)  # Default blue
        layout.addRow("Left Mesh Color:", self.left_color_btn)
        
        # Background color
        self.bg_color_btn = QPushButton()
        self.bg_color_btn.setFixedSize(100, 25)
        self.bg_color_btn.clicked.connect(lambda: self._pick_color('background'))
        self._bg_color = QColor(38, 43, 51)
        layout.addRow("Background Color:", self.bg_color_btn)
        
        # Background color 2 (for gradient)
        self.bg_color2_btn = QPushButton()
        self.bg_color2_btn.setFixedSize(100, 25)
        self.bg_color2_btn.clicked.connect(lambda: self._pick_color('background2'))
        self._bg_color2 = QColor(64, 71, 82)
        layout.addRow("Background Gradient:", self.bg_color2_btn)
        
        # Gradient background
        self.gradient_bg_check = QCheckBox("Use Gradient Background")
        self.gradient_bg_check.setChecked(True)
        layout.addRow("", self.gradient_bg_check)
        
        # Edge color (for solid_edges mode)
        self.edge_color_btn = QPushButton()
        self.edge_color_btn.setFixedSize(100, 25)
        self.edge_color_btn.clicked.connect(lambda: self._pick_color('edge'))
        self._edge_color = QColor(25, 25, 25)
        layout.addRow("Edge Color:", self.edge_color_btn)
        
        # === Lighting Section ===
        lighting_header = QLabel("<b>Lighting</b>")
        layout.addRow(lighting_header)
        
        # Ambient lighting
        self.ambient_spin = QDoubleSpinBox()
        self.ambient_spin.setRange(0.0, 1.0)
        self.ambient_spin.setSingleStep(0.05)
        self.ambient_spin.setValue(0.1)
        layout.addRow("Ambient Light:", self.ambient_spin)
        
        # Diffuse lighting
        self.diffuse_spin = QDoubleSpinBox()
        self.diffuse_spin.setRange(0.0, 1.0)
        self.diffuse_spin.setSingleStep(0.05)
        self.diffuse_spin.setValue(0.9)
        layout.addRow("Diffuse Light:", self.diffuse_spin)
        
        # Specular lighting
        self.specular_spin = QDoubleSpinBox()
        self.specular_spin.setRange(0.0, 1.0)
        self.specular_spin.setSingleStep(0.05)
        self.specular_spin.setValue(0.3)
        layout.addRow("Specular Light:", self.specular_spin)
        
        # Specular power
        self.specular_power_spin = QSpinBox()
        self.specular_power_spin.setRange(1, 100)
        self.specular_power_spin.setValue(20)
        layout.addRow("Specular Power:", self.specular_power_spin)
        
        # Light intensity
        self.light_intensity_spin = QDoubleSpinBox()
        self.light_intensity_spin.setRange(0.1, 3.0)
        self.light_intensity_spin.setSingleStep(0.1)
        self.light_intensity_spin.setValue(1.0)
        layout.addRow("Light Intensity:", self.light_intensity_spin)
        
        # Two-sided lighting
        self.two_sided_lighting_check = QCheckBox("Two-Sided Lighting")
        self.two_sided_lighting_check.setChecked(True)
        self.two_sided_lighting_check.setToolTip("Light both sides of surfaces")
        layout.addRow("", self.two_sided_lighting_check)
        
        # === Material Section ===
        material_header = QLabel("<b>Material</b>")
        layout.addRow(material_header)
        
        # Shading mode
        self.shading_combo = QComboBox()
        self.shading_combo.addItems(['Phong (Smooth)', 'Gouraud', 'Flat'])
        layout.addRow("Shading Mode:", self.shading_combo)
        
        # Metallic look
        self.metallic_spin = QDoubleSpinBox()
        self.metallic_spin.setRange(0.0, 1.0)
        self.metallic_spin.setSingleStep(0.1)
        self.metallic_spin.setValue(0.0)
        self.metallic_spin.setToolTip("0 = plastic/matte, 1 = metallic")
        layout.addRow("Metallic:", self.metallic_spin)
        
        # Roughness
        self.roughness_spin = QDoubleSpinBox()
        self.roughness_spin.setRange(0.0, 1.0)
        self.roughness_spin.setSingleStep(0.1)
        self.roughness_spin.setValue(0.4)
        self.roughness_spin.setToolTip("0 = shiny/smooth, 1 = rough/matte")
        layout.addRow("Roughness:", self.roughness_spin)
        
        # Opacity
        self.opacity_spin = QDoubleSpinBox()
        self.opacity_spin.setRange(0.1, 1.0)
        self.opacity_spin.setSingleStep(0.1)
        self.opacity_spin.setValue(1.0)
        layout.addRow("Opacity:", self.opacity_spin)
        
        # Backface culling
        self.backface_culling_check = QCheckBox("Enable Backface Culling")
        self.backface_culling_check.setChecked(False)
        self.backface_culling_check.setToolTip("Hide back-facing triangles (faster rendering)")
        layout.addRow("", self.backface_culling_check)
        
        # Edge visibility
        self.edge_visibility_check = QCheckBox("Show Mesh Edges")
        self.edge_visibility_check.setChecked(False)
        layout.addRow("", self.edge_visibility_check)
        
        # Edge width
        self.edge_width_spin = QDoubleSpinBox()
        self.edge_width_spin.setRange(0.5, 5.0)
        self.edge_width_spin.setSingleStep(0.5)
        self.edge_width_spin.setValue(1.0)
        layout.addRow("Edge Width:", self.edge_width_spin)
        
        # Point size (for point cloud mode)
        self.point_size_spin = QDoubleSpinBox()
        self.point_size_spin.setRange(1.0, 10.0)
        self.point_size_spin.setSingleStep(0.5)
        self.point_size_spin.setValue(3.0)
        layout.addRow("Point Size:", self.point_size_spin)
        
        # === Performance Section ===
        perf_header = QLabel("<b>Performance</b>")
        layout.addRow(perf_header)
        
        # LOD (Level of Detail)
        self.lod_check = QCheckBox("Enable Level of Detail (LOD)")
        self.lod_check.setChecked(False)
        self.lod_check.setToolTip("Reduce mesh detail when zoomed out for better performance")
        layout.addRow("", self.lod_check)
        
        # Frustum culling
        self.frustum_culling_check = QCheckBox("Enable Frustum Culling")
        self.frustum_culling_check.setChecked(True)
        self.frustum_culling_check.setToolTip("Don't render objects outside the view")
        layout.addRow("", self.frustum_culling_check)
        
        # Immediate mode
        self.immediate_mode_check = QCheckBox("Use Immediate Mode Rendering")
        self.immediate_mode_check.setChecked(False)
        self.immediate_mode_check.setToolTip("Legacy rendering mode (slower but more compatible)")
        layout.addRow("", self.immediate_mode_check)
        
        self.tab_widget.addTab(tab, "Rendering")
    
    def _create_engraving_tab(self):
        """Create engraving settings tab."""
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setSpacing(10)
        
        # Default engraving depth
        self.engrave_depth_spin = QDoubleSpinBox()
        self.engrave_depth_spin.setRange(0.1, 3.0)
        self.engrave_depth_spin.setSingleStep(0.1)
        self.engrave_depth_spin.setValue(0.6)
        self.engrave_depth_spin.setSuffix(" mm")
        layout.addRow("Default Engraving Depth:", self.engrave_depth_spin)
        
        # Max outward extension (for boolean)
        self.max_outward_spin = QDoubleSpinBox()
        self.max_outward_spin.setRange(5.0, 50.0)
        self.max_outward_spin.setSingleStep(1.0)
        self.max_outward_spin.setValue(20.0)
        self.max_outward_spin.setSuffix(" mm")
        self.max_outward_spin.setToolTip("Extension distance for cutting through curved surfaces")
        layout.addRow("Boolean Extension:", self.max_outward_spin)
        
        # Surface samples for wrapping
        self.surface_samples_spin = QSpinBox()
        self.surface_samples_spin.setRange(10, 100)
        self.surface_samples_spin.setValue(30)
        self.surface_samples_spin.setToolTip("Number of samples for surface curvature detection")
        layout.addRow("Surface Samples:", self.surface_samples_spin)
        
        # Apply to mirrored side
        self.mirror_engraving_check = QCheckBox("Apply engraving to mirrored (left) side")
        self.mirror_engraving_check.setChecked(True)
        layout.addRow("", self.mirror_engraving_check)
        
        # Mirror logo orientation
        self.mirror_logo_check = QCheckBox("Mirror logo image on left side")
        self.mirror_logo_check.setChecked(False)
        self.mirror_logo_check.setToolTip("If checked, logo will be flipped horizontally on left side")
        layout.addRow("", self.mirror_logo_check)
        
        # --- Slider Defaults Section ---
        layout.addRow(QLabel("<b>Slider Defaults</b>"))
        
        # Default logo scale
        self.default_logo_scale_spin = QSpinBox()
        self.default_logo_scale_spin.setRange(50, 200)
        self.default_logo_scale_spin.setValue(100)
        self.default_logo_scale_spin.setSuffix(" %")
        self.default_logo_scale_spin.setToolTip("Default logo scale percentage")
        layout.addRow("Logo Scale:", self.default_logo_scale_spin)
        
        # Default text size
        self.default_text_size_spin = QDoubleSpinBox()
        self.default_text_size_spin.setRange(2.0, 10.0)
        self.default_text_size_spin.setSingleStep(0.1)
        self.default_text_size_spin.setValue(4.0)
        self.default_text_size_spin.setSuffix(" mm")
        self.default_text_size_spin.setToolTip("Default text font size")
        layout.addRow("Font Size:", self.default_text_size_spin)
        
        # Default text spacing
        self.default_text_spacing_spin = QDoubleSpinBox()
        self.default_text_spacing_spin.setRange(0.0, 10.0)
        self.default_text_spacing_spin.setSingleStep(0.5)
        self.default_text_spacing_spin.setValue(6.0)
        self.default_text_spacing_spin.setSuffix(" mm")
        self.default_text_spacing_spin.setToolTip("Default spacing between logo and text")
        layout.addRow("Text Spacing:", self.default_text_spacing_spin)
        
        # Default offset X
        self.default_offset_x_spin = QSpinBox()
        self.default_offset_x_spin.setRange(-50, 50)
        self.default_offset_x_spin.setValue(0)
        self.default_offset_x_spin.setSuffix(" mm")
        self.default_offset_x_spin.setToolTip("Default horizontal offset")
        layout.addRow("Offset X:", self.default_offset_x_spin)
        
        # Default offset Y
        self.default_offset_y_spin = QSpinBox()
        self.default_offset_y_spin.setRange(-50, 50)
        self.default_offset_y_spin.setValue(0)
        self.default_offset_y_spin.setSuffix(" mm")
        self.default_offset_y_spin.setToolTip("Default vertical offset")
        layout.addRow("Offset Y:", self.default_offset_y_spin)
        
        # Default rotation
        self.default_rotation_spin = QSpinBox()
        self.default_rotation_spin.setRange(-180, 180)
        self.default_rotation_spin.setValue(0)
        self.default_rotation_spin.setSuffix(" °")
        self.default_rotation_spin.setToolTip("Default rotation angle")
        layout.addRow("Rotation:", self.default_rotation_spin)
        
        # Default engrave depth
        self.default_engrave_depth_spin = QDoubleSpinBox()
        self.default_engrave_depth_spin.setRange(0.3, 2.0)
        self.default_engrave_depth_spin.setSingleStep(0.1)
        self.default_engrave_depth_spin.setValue(0.6)
        self.default_engrave_depth_spin.setSuffix(" mm")
        self.default_engrave_depth_spin.setToolTip("Default engraving depth for both logo and text")
        layout.addRow("Engrave Depth:", self.default_engrave_depth_spin)
        
        self.tab_widget.addTab(tab, "Engraving")
    
    def _create_logo_tab(self):
        """Create logo settings tab."""
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setSpacing(10)
        
        # Logo size
        self.logo_size_spin = QDoubleSpinBox()
        self.logo_size_spin.setRange(5.0, 100.0)
        self.logo_size_spin.setSingleStep(1.0)
        self.logo_size_spin.setValue(25.0)
        self.logo_size_spin.setSuffix(" mm")
        layout.addRow("Default Logo Size:", self.logo_size_spin)
        
        # Logo simplification
        self.logo_simplify_spin = QDoubleSpinBox()
        self.logo_simplify_spin.setRange(0.1, 5.0)
        self.logo_simplify_spin.setSingleStep(0.1)
        self.logo_simplify_spin.setValue(0.5)
        self.logo_simplify_spin.setSuffix(" px")
        self.logo_simplify_spin.setToolTip("Contour simplification tolerance (lower = more detail)")
        layout.addRow("Contour Simplification:", self.logo_simplify_spin)
        
        # Minimum polygon area
        self.min_area_spin = QDoubleSpinBox()
        self.min_area_spin.setRange(0.01, 5.0)
        self.min_area_spin.setSingleStep(0.05)
        self.min_area_spin.setValue(0.1)
        self.min_area_spin.setSuffix(" mm²")
        self.min_area_spin.setToolTip("Minimum area for logo polygons (filters noise)")
        layout.addRow("Minimum Polygon Area:", self.min_area_spin)
        
        # Image threshold
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(1, 254)
        self.threshold_spin.setValue(128)
        self.threshold_spin.setToolTip("Threshold for converting image to black/white (higher = more black)")
        layout.addRow("Image Threshold:", self.threshold_spin)
        
        self.tab_widget.addTab(tab, "Logo")
    
    def _create_export_tab(self):
        """Create export settings tab."""
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setSpacing(10)
        
        # Export format
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(['STL Binary', 'STL ASCII', 'OBJ', 'PLY'])
        layout.addRow("Export Format:", self.export_format_combo)
        
        # File naming
        self.filename_pattern = QLineEdit()
        self.filename_pattern.setText("{name}_{side}")
        self.filename_pattern.setToolTip("Pattern: {name}=filename, {side}=LEFT/RIGHT, {date}=date")
        layout.addRow("Filename Pattern:", self.filename_pattern)
        
        # Auto-add date
        self.add_date_check = QCheckBox("Add date to filename")
        self.add_date_check.setChecked(False)
        layout.addRow("", self.add_date_check)
        
        # Open folder after export
        self.open_folder_check = QCheckBox("Open folder after export")
        self.open_folder_check.setChecked(True)
        layout.addRow("", self.open_folder_check)
        
        self.tab_widget.addTab(tab, "Export")
    
    def _create_display_tab(self):
        """Create display settings tab."""
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setSpacing(10)
        
        # Show LEFT/RIGHT labels
        self.show_labels_check = QCheckBox("Show LEFT/RIGHT labels on viewports")
        self.show_labels_check.setChecked(True)
        layout.addRow("", self.show_labels_check)
        
        # Show coordinate axes
        self.show_axes_check = QCheckBox("Show coordinate axes")
        self.show_axes_check.setChecked(False)
        layout.addRow("", self.show_axes_check)
        
        # Auto-reset camera on load
        self.auto_reset_camera_check = QCheckBox("Auto-reset camera when loading model")
        self.auto_reset_camera_check.setChecked(True)
        layout.addRow("", self.auto_reset_camera_check)
        
        # Sync cameras
        self.sync_cameras_check = QCheckBox("Synchronize left/right camera movements")
        self.sync_cameras_check.setChecked(False)
        layout.addRow("", self.sync_cameras_check)
        
        # Default view
        self.default_view_combo = QComboBox()
        self.default_view_combo.addItems(['Isometric', 'Front', 'Top', 'Right', 'Left'])
        layout.addRow("Default View:", self.default_view_combo)
        
        # Marker size
        self.marker_size_spin = QDoubleSpinBox()
        self.marker_size_spin.setRange(1.0, 20.0)
        self.marker_size_spin.setSingleStep(0.5)
        self.marker_size_spin.setValue(5.0)
        self.marker_size_spin.setSuffix(" mm")
        layout.addRow("Position Marker Size:", self.marker_size_spin)
        
        self.tab_widget.addTab(tab, "Display")
    
    def _pick_color(self, color_type: str):
        """Open color picker dialog."""
        color_map = {
            'right': ('_right_color', 'right_color_btn'),
            'left': ('_left_color', 'left_color_btn'),
            'background': ('_bg_color', 'bg_color_btn'),
            'background2': ('_bg_color2', 'bg_color2_btn'),
            'edge': ('_edge_color', 'edge_color_btn'),
        }
        
        if color_type not in color_map:
            return
        
        attr_name, btn_name = color_map[color_type]
        current = getattr(self, attr_name, QColor(128, 128, 128))
        
        color = QColorDialog.getColor(current, self, f"Select {color_type.title()} Color")
        if color.isValid():
            setattr(self, attr_name, color)
            getattr(self, btn_name).setStyleSheet(f"background-color: {color.name()};")
    
    def _load_settings(self):
        """Load settings from QSettings."""
        # Rendering Engine
        self.render_backend_combo.setCurrentIndex(self.settings.value('render/backend', 0, type=int))
        self.msaa_combo.setCurrentIndex(self.settings.value('render/msaa', 2, type=int))
        self.fxaa_check.setChecked(self.settings.value('render/fxaa', False, type=bool))
        self.ssao_check.setChecked(self.settings.value('render/ssao', False, type=bool))
        self.depth_peeling_check.setChecked(self.settings.value('render/depth_peeling', False, type=bool))
        
        # Colors
        self._right_color = QColor(self.settings.value('render/right_color', '#6699D9'))
        self._left_color = QColor(self.settings.value('render/left_color', '#6699D9'))
        self._bg_color = QColor(self.settings.value('render/bg_color', '#262B33'))
        self._bg_color2 = QColor(self.settings.value('render/bg_color2', '#404752'))
        self._edge_color = QColor(self.settings.value('render/edge_color', '#191919'))
        self.right_color_btn.setStyleSheet(f"background-color: {self._right_color.name()};")
        self.left_color_btn.setStyleSheet(f"background-color: {self._left_color.name()};")
        self.bg_color_btn.setStyleSheet(f"background-color: {self._bg_color.name()};")
        self.bg_color2_btn.setStyleSheet(f"background-color: {self._bg_color2.name()};")
        self.edge_color_btn.setStyleSheet(f"background-color: {self._edge_color.name()};")
        self.gradient_bg_check.setChecked(self.settings.value('render/gradient_bg', True, type=bool))
        
        # Lighting
        self.ambient_spin.setValue(self.settings.value('render/ambient', 0.1, type=float))
        self.diffuse_spin.setValue(self.settings.value('render/diffuse', 0.9, type=float))
        self.specular_spin.setValue(self.settings.value('render/specular', 0.3, type=float))
        self.specular_power_spin.setValue(self.settings.value('render/specular_power', 20, type=int))
        self.light_intensity_spin.setValue(self.settings.value('render/light_intensity', 1.0, type=float))
        self.two_sided_lighting_check.setChecked(self.settings.value('render/two_sided', True, type=bool))
        
        # Material
        self.shading_combo.setCurrentIndex(self.settings.value('render/shading', 2, type=int))
        self.metallic_spin.setValue(self.settings.value('render/metallic', 0.0, type=float))
        self.roughness_spin.setValue(self.settings.value('render/roughness', 0.4, type=float))
        self.opacity_spin.setValue(self.settings.value('render/opacity', 1.0, type=float))
        self.backface_culling_check.setChecked(self.settings.value('render/backface_culling', False, type=bool))
        self.edge_visibility_check.setChecked(self.settings.value('render/edge_visibility', False, type=bool))
        self.edge_width_spin.setValue(self.settings.value('render/edge_width', 1.0, type=float))
        self.point_size_spin.setValue(self.settings.value('render/point_size', 3.0, type=float))
        
        # Performance
        self.lod_check.setChecked(self.settings.value('render/lod', False, type=bool))
        self.frustum_culling_check.setChecked(self.settings.value('render/frustum_culling', True, type=bool))
        self.immediate_mode_check.setChecked(self.settings.value('render/immediate_mode', False, type=bool))
        
        # Engraving
        self.engrave_depth_spin.setValue(self.settings.value('engrave/depth', 0.6, type=float))
        self.max_outward_spin.setValue(self.settings.value('engrave/max_outward', 20.0, type=float))
        self.surface_samples_spin.setValue(self.settings.value('engrave/surface_samples', 30, type=int))
        self.mirror_engraving_check.setChecked(self.settings.value('engrave/mirror_engraving', True, type=bool))
        self.mirror_logo_check.setChecked(self.settings.value('engrave/mirror_logo', False, type=bool))
        
        # Slider Defaults
        self.default_logo_scale_spin.setValue(self.settings.value('engrave/default_logo_scale', 100, type=int))
        self.default_text_size_spin.setValue(self.settings.value('engrave/default_text_size', 4.0, type=float))
        self.default_text_spacing_spin.setValue(self.settings.value('engrave/default_text_spacing', 6.0, type=float))
        self.default_offset_x_spin.setValue(self.settings.value('engrave/default_offset_x', 0, type=int))
        self.default_offset_y_spin.setValue(self.settings.value('engrave/default_offset_y', 0, type=int))
        self.default_rotation_spin.setValue(self.settings.value('engrave/default_rotation', 0, type=int))
        self.default_engrave_depth_spin.setValue(self.settings.value('engrave/default_engrave_depth', 0.6, type=float))
        
        # Logo
        self.logo_size_spin.setValue(self.settings.value('logo/size', 25.0, type=float))
        self.logo_simplify_spin.setValue(self.settings.value('logo/simplify', 0.5, type=float))
        self.min_area_spin.setValue(self.settings.value('logo/min_area', 0.1, type=float))
        self.threshold_spin.setValue(self.settings.value('logo/threshold', 128, type=int))
        
        # Export
        self.export_format_combo.setCurrentIndex(self.settings.value('export/format', 0, type=int))
        self.filename_pattern.setText(self.settings.value('export/pattern', '{name}_{side}'))
        self.add_date_check.setChecked(self.settings.value('export/add_date', False, type=bool))
        self.open_folder_check.setChecked(self.settings.value('export/open_folder', True, type=bool))
        
        # Display
        self.show_labels_check.setChecked(self.settings.value('display/show_labels', True, type=bool))
        self.show_axes_check.setChecked(self.settings.value('display/show_axes', False, type=bool))
        self.auto_reset_camera_check.setChecked(self.settings.value('display/auto_reset_camera', True, type=bool))
        self.sync_cameras_check.setChecked(self.settings.value('display/sync_cameras', False, type=bool))
        self.default_view_combo.setCurrentIndex(self.settings.value('display/default_view', 0, type=int))
        self.marker_size_spin.setValue(self.settings.value('display/marker_size', 5.0, type=float))
    
    def _save_settings(self):
        """Save settings to QSettings."""
        # Rendering Engine
        self.settings.setValue('render/backend', self.render_backend_combo.currentIndex())
        self.settings.setValue('render/msaa', self.msaa_combo.currentIndex())
        self.settings.setValue('render/fxaa', self.fxaa_check.isChecked())
        self.settings.setValue('render/ssao', self.ssao_check.isChecked())
        self.settings.setValue('render/depth_peeling', self.depth_peeling_check.isChecked())
        
        # Colors
        self.settings.setValue('render/right_color', self._right_color.name())
        self.settings.setValue('render/left_color', self._left_color.name())
        self.settings.setValue('render/bg_color', self._bg_color.name())
        self.settings.setValue('render/bg_color2', self._bg_color2.name())
        self.settings.setValue('render/edge_color', self._edge_color.name())
        self.settings.setValue('render/gradient_bg', self.gradient_bg_check.isChecked())
        
        # Lighting
        self.settings.setValue('render/ambient', self.ambient_spin.value())
        self.settings.setValue('render/diffuse', self.diffuse_spin.value())
        self.settings.setValue('render/specular', self.specular_spin.value())
        self.settings.setValue('render/specular_power', self.specular_power_spin.value())
        self.settings.setValue('render/light_intensity', self.light_intensity_spin.value())
        self.settings.setValue('render/two_sided', self.two_sided_lighting_check.isChecked())
        
        # Material
        self.settings.setValue('render/shading', self.shading_combo.currentIndex())
        self.settings.setValue('render/metallic', self.metallic_spin.value())
        self.settings.setValue('render/roughness', self.roughness_spin.value())
        self.settings.setValue('render/opacity', self.opacity_spin.value())
        self.settings.setValue('render/backface_culling', self.backface_culling_check.isChecked())
        self.settings.setValue('render/edge_visibility', self.edge_visibility_check.isChecked())
        self.settings.setValue('render/edge_width', self.edge_width_spin.value())
        self.settings.setValue('render/point_size', self.point_size_spin.value())
        
        # Performance
        self.settings.setValue('render/lod', self.lod_check.isChecked())
        self.settings.setValue('render/frustum_culling', self.frustum_culling_check.isChecked())
        self.settings.setValue('render/immediate_mode', self.immediate_mode_check.isChecked())
        
        # Engraving
        self.settings.setValue('engrave/depth', self.engrave_depth_spin.value())
        self.settings.setValue('engrave/max_outward', self.max_outward_spin.value())
        self.settings.setValue('engrave/surface_samples', self.surface_samples_spin.value())
        self.settings.setValue('engrave/mirror_engraving', self.mirror_engraving_check.isChecked())
        self.settings.setValue('engrave/mirror_logo', self.mirror_logo_check.isChecked())
        
        # Slider Defaults
        self.settings.setValue('engrave/default_logo_scale', self.default_logo_scale_spin.value())
        self.settings.setValue('engrave/default_text_size', self.default_text_size_spin.value())
        self.settings.setValue('engrave/default_text_spacing', self.default_text_spacing_spin.value())
        self.settings.setValue('engrave/default_offset_x', self.default_offset_x_spin.value())
        self.settings.setValue('engrave/default_offset_y', self.default_offset_y_spin.value())
        self.settings.setValue('engrave/default_rotation', self.default_rotation_spin.value())
        self.settings.setValue('engrave/default_engrave_depth', self.default_engrave_depth_spin.value())
        
        # Logo
        self.settings.setValue('logo/size', self.logo_size_spin.value())
        self.settings.setValue('logo/simplify', self.logo_simplify_spin.value())
        self.settings.setValue('logo/min_area', self.min_area_spin.value())
        self.settings.setValue('logo/threshold', self.threshold_spin.value())
        
        # Export
        self.settings.setValue('export/format', self.export_format_combo.currentIndex())
        self.settings.setValue('export/pattern', self.filename_pattern.text())
        self.settings.setValue('export/add_date', self.add_date_check.isChecked())
        self.settings.setValue('export/open_folder', self.open_folder_check.isChecked())
        
        # Display
        self.settings.setValue('display/show_labels', self.show_labels_check.isChecked())
        self.settings.setValue('display/show_axes', self.show_axes_check.isChecked())
        self.settings.setValue('display/auto_reset_camera', self.auto_reset_camera_check.isChecked())
        self.settings.setValue('display/sync_cameras', self.sync_cameras_check.isChecked())
        self.settings.setValue('display/default_view', self.default_view_combo.currentIndex())
        self.settings.setValue('display/marker_size', self.marker_size_spin.value())
    
    def _save_and_accept(self):
        """Save settings and close dialog."""
        self._save_settings()
        self.accept()
    
    def _restore_defaults(self):
        """Restore all settings to defaults."""
        # Rendering
        # Rendering Engine
        self.render_backend_combo.setCurrentIndex(0)
        self.msaa_combo.setCurrentIndex(2)
        self.fxaa_check.setChecked(False)
        self.ssao_check.setChecked(False)
        self.depth_peeling_check.setChecked(False)
        
        # Colors
        self._right_color = QColor('#6699D9')
        self._left_color = QColor('#6699D9')
        self._bg_color = QColor('#262B33')
        self._bg_color2 = QColor('#404752')
        self._edge_color = QColor('#191919')
        self.right_color_btn.setStyleSheet(f"background-color: {self._right_color.name()};")
        self.left_color_btn.setStyleSheet(f"background-color: {self._left_color.name()};")
        self.bg_color_btn.setStyleSheet(f"background-color: {self._bg_color.name()};")
        self.bg_color2_btn.setStyleSheet(f"background-color: {self._bg_color2.name()};")
        self.edge_color_btn.setStyleSheet(f"background-color: {self._edge_color.name()};")
        self.gradient_bg_check.setChecked(True)
        
        # Lighting
        self.ambient_spin.setValue(0.1)
        self.diffuse_spin.setValue(0.9)
        self.specular_spin.setValue(0.3)
        self.specular_power_spin.setValue(20)
        self.light_intensity_spin.setValue(1.0)
        self.two_sided_lighting_check.setChecked(True)
        
        # Material
        self.shading_combo.setCurrentIndex(2)
        self.metallic_spin.setValue(0.0)
        self.roughness_spin.setValue(0.4)
        self.opacity_spin.setValue(1.0)
        self.backface_culling_check.setChecked(False)
        self.edge_visibility_check.setChecked(False)
        self.edge_width_spin.setValue(1.0)
        self.point_size_spin.setValue(3.0)
        
        # Performance
        self.lod_check.setChecked(False)
        self.frustum_culling_check.setChecked(True)
        self.immediate_mode_check.setChecked(False)
        
        # Engraving
        self.engrave_depth_spin.setValue(0.6)
        self.max_outward_spin.setValue(20.0)
        self.surface_samples_spin.setValue(30)
        self.mirror_engraving_check.setChecked(True)
        self.mirror_logo_check.setChecked(False)
        
        # Slider Defaults
        self.default_logo_scale_spin.setValue(100)
        self.default_text_size_spin.setValue(4.0)
        self.default_text_spacing_spin.setValue(6.0)
        self.default_offset_x_spin.setValue(0)
        self.default_offset_y_spin.setValue(0)
        self.default_rotation_spin.setValue(0)
        self.default_engrave_depth_spin.setValue(0.6)
        
        # Logo
        self.logo_size_spin.setValue(25.0)
        self.logo_simplify_spin.setValue(0.5)
        self.min_area_spin.setValue(0.1)
        self.threshold_spin.setValue(128)
        
        # Export
        self.export_format_combo.setCurrentIndex(0)
        self.filename_pattern.setText('{name}_{side}')
        self.add_date_check.setChecked(False)
        self.open_folder_check.setChecked(True)
        
        # Display
        self.show_labels_check.setChecked(True)
        self.show_axes_check.setChecked(False)
        self.auto_reset_camera_check.setChecked(True)
        self.sync_cameras_check.setChecked(False)
        self.default_view_combo.setCurrentIndex(0)
        self.marker_size_spin.setValue(5.0)
    
    def get_settings_dict(self) -> dict:
        """Return current settings as a dictionary."""
        return {
            'render': {
                'backend': self.render_backend_combo.currentIndex(),
                'msaa': [0, 2, 4, 8, 16][self.msaa_combo.currentIndex()],
                'fxaa': self.fxaa_check.isChecked(),
                'ssao': self.ssao_check.isChecked(),
                'depth_peeling': self.depth_peeling_check.isChecked(),
                'right_color': (self._right_color.redF(), self._right_color.greenF(), self._right_color.blueF()),
                'left_color': (self._left_color.redF(), self._left_color.greenF(), self._left_color.blueF()),
                'bg_color': (self._bg_color.redF(), self._bg_color.greenF(), self._bg_color.blueF()),
                'bg_color2': (self._bg_color2.redF(), self._bg_color2.greenF(), self._bg_color2.blueF()),
                'edge_color': (self._edge_color.redF(), self._edge_color.greenF(), self._edge_color.blueF()),
                'gradient_bg': self.gradient_bg_check.isChecked(),
                'ambient': self.ambient_spin.value(),
                'diffuse': self.diffuse_spin.value(),
                'specular': self.specular_spin.value(),
                'specular_power': self.specular_power_spin.value(),
                'light_intensity': self.light_intensity_spin.value(),
                'two_sided': self.two_sided_lighting_check.isChecked(),
                'shading': self.shading_combo.currentIndex(),
                'metallic': self.metallic_spin.value(),
                'roughness': self.roughness_spin.value(),
                'opacity': self.opacity_spin.value(),
                'backface_culling': self.backface_culling_check.isChecked(),
                'edge_visibility': self.edge_visibility_check.isChecked(),
                'edge_width': self.edge_width_spin.value(),
                'point_size': self.point_size_spin.value(),
                'lod': self.lod_check.isChecked(),
                'frustum_culling': self.frustum_culling_check.isChecked(),
                'immediate_mode': self.immediate_mode_check.isChecked(),
            },
            'engrave': {
                'depth': self.engrave_depth_spin.value(),
                'max_outward': self.max_outward_spin.value(),
                'surface_samples': self.surface_samples_spin.value(),
                'mirror_engraving': self.mirror_engraving_check.isChecked(),
                'mirror_logo': self.mirror_logo_check.isChecked(),
            },
            'logo': {
                'size': self.logo_size_spin.value(),
                'simplify': self.logo_simplify_spin.value(),
                'min_area': self.min_area_spin.value(),
                'threshold': self.threshold_spin.value(),
            },
            'export': {
                'format': self.export_format_combo.currentIndex(),
                'pattern': self.filename_pattern.text(),
                'add_date': self.add_date_check.isChecked(),
                'open_folder': self.open_folder_check.isChecked(),
            },
            'display': {
                'show_labels': self.show_labels_check.isChecked(),
                'show_axes': self.show_axes_check.isChecked(),
                'auto_reset_camera': self.auto_reset_camera_check.isChecked(),
                'sync_cameras': self.sync_cameras_check.isChecked(),
                'default_view': self.default_view_combo.currentIndex(),
                'marker_size': self.marker_size_spin.value(),
            }
        }


class MainWindow(QMainWindow):
    """Main application window for the Orthosis Customizer."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize processor
        self.processor = OrthosisProcessor()
        
        # Settings
        self.settings = QSettings('OrthosisCustomizer', 'OrthosisApp')
        
        # Default to models folder in app directory if no last directory saved
        default_models_dir = os.path.join(get_application_path(), 'models')
        if not os.path.exists(default_models_dir):
            default_models_dir = get_application_path()
        
        saved_dir = self.settings.value('last_directory', '')
        if saved_dir and os.path.exists(saved_dir):
            self.last_directory = saved_dir
        else:
            self.last_directory = default_models_dir
        
        # Current file path
        self.orthosis_file_path: Optional[str] = None
        
        # Engraving placement state (unified)
        self._engrave_position: Optional[np.ndarray] = None
        self._engrave_normal: Optional[np.ndarray] = None
        
        # Track if engraving has been applied
        self._engraving_applied = False
        
        # Legacy state variables (for compatibility)
        self._logo_position: Optional[np.ndarray] = None
        self._logo_normal: Optional[np.ndarray] = None
        self._text_position: Optional[np.ndarray] = None
        self._text_normal: Optional[np.ndarray] = None
        self._logo_applied = False
        self._text_applied = False
        
        # App settings dict
        self._app_settings = {}
        
        # Setup UI
        self._setup_window()
        self._create_menu_bar()
        self._create_central_widget()
        self._create_status_bar()
        
        # Load logos
        self._load_logos()
        
        # Connect signals
        self._connect_signals()
        
        # Initial state
        self._update_ui_state()
        
        # Load and apply saved settings
        self._load_app_settings()
    
    def _setup_window(self):
        """Configure main window properties."""
        self.setWindowTitle("Orthosis Customizer - STL Processing Tool")
        self.setMinimumSize(1200, 800)
        
        geometry = self.settings.value('geometry')
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(1400, 900)
    
    def _create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        open_action = QAction('&Open Orthosis STL...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self._open_orthosis_stl)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        export_action = QAction('&Export Both STL Files...', self)
        export_action.setShortcut('Ctrl+E')
        export_action.triggered.connect(self._export_both)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Alt+F4')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu('&View')
        
        reset_view_action = QAction('&Reset View', self)
        reset_view_action.setShortcut('R')
        reset_view_action.triggered.connect(lambda: self.viewer.reset_view())
        view_menu.addAction(reset_view_action)
        
        view_menu.addSeparator()
        
        top_view_action = QAction('&Top View', self)
        top_view_action.setShortcut('T')
        top_view_action.triggered.connect(lambda: self.viewer.set_view('top'))
        view_menu.addAction(top_view_action)
        
        front_view_action = QAction('&Front View', self)
        front_view_action.setShortcut('F')
        front_view_action.triggered.connect(lambda: self.viewer.set_view('front'))
        view_menu.addAction(front_view_action)
        
        iso_view_action = QAction('&Isometric View', self)
        iso_view_action.setShortcut('I')
        iso_view_action.triggered.connect(lambda: self.viewer.set_view('iso'))
        view_menu.addAction(iso_view_action)
        
        view_menu.addSeparator()
        
        # Render mode submenu
        render_menu = view_menu.addMenu('Render &Mode')
        
        self.solid_action = QAction('&Solid', self)
        self.solid_action.setShortcut('1')
        self.solid_action.setCheckable(True)
        self.solid_action.setChecked(True)
        self.solid_action.triggered.connect(lambda: self._set_render_mode('solid'))
        render_menu.addAction(self.solid_action)
        
        self.wireframe_action = QAction('&Wireframe', self)
        self.wireframe_action.setShortcut('2')
        self.wireframe_action.setCheckable(True)
        self.wireframe_action.triggered.connect(lambda: self._set_render_mode('wireframe'))
        render_menu.addAction(self.wireframe_action)
        
        # Settings menu (between View and Help)
        settings_menu = menubar.addMenu('&Settings')
        
        open_settings_action = QAction('&Preferences...', self)
        open_settings_action.setShortcut('Ctrl+,')
        open_settings_action.triggered.connect(self._open_settings)
        settings_menu.addAction(open_settings_action)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        about_action = QAction('&About', self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_central_widget(self):
        """Create the main content area."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left side - Controls (scrollable)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumWidth(420)
        
        control_panel = self._create_control_panel()
        scroll_area.setWidget(control_panel)
        splitter.addWidget(scroll_area)
        
        # Right side - 3D Viewer (dual viewport)
        self.viewer = DualMeshViewer()
        splitter.addWidget(self.viewer)
        
        # Set splitter sizes (20% controls, 80% viewer)
        splitter.setSizes([300, 1100])
    
    def _create_control_panel(self) -> QWidget:
        """Create the right control panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)
        
        # === Step 1: Load Orthosis ===
        load_group = QGroupBox("1. Load Orthosis")
        load_layout = QVBoxLayout(load_group)
        
        self.load_btn = QPushButton("Open Orthosis STL...")
        self.load_btn.setMinimumHeight(35)
        self.load_btn.setStyleSheet("font-weight: bold;")
        self.load_btn.clicked.connect(self._open_orthosis_stl)
        load_layout.addWidget(self.load_btn)
        
        self.file_label = QLabel("No file loaded")
        self.file_label.setWordWrap(True)
        load_layout.addWidget(self.file_label)
        
        layout.addWidget(load_group)
        
        # === Step 2: Engraving (Logo + Text) ===
        engrave_group = QGroupBox("2. Engraving")
        engrave_layout = QGridLayout(engrave_group)
        
        # --- Logo Section ---
        logo_header = QLabel("<b>Logo</b>")
        engrave_layout.addWidget(logo_header, 0, 0, 1, 2)
        
        # Logo preview
        self.logo_preview = QLabel()
        self.logo_preview.setFixedHeight(80)
        self.logo_preview.setAlignment(Qt.AlignCenter)
        self.logo_preview.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 4px;")
        self.logo_preview.setText("No logo selected")
        engrave_layout.addWidget(self.logo_preview, 1, 0, 1, 2)
        
        # Logo selection
        engrave_layout.addWidget(QLabel("Select Logo:"), 2, 0)
        logo_btn_layout = QHBoxLayout()
        self.logo_v1_btn = QPushButton("Logo V1")
        self.logo_v1_btn.setCheckable(True)
        self.logo_v1_btn.setChecked(True)
        self.logo_v1_btn.setStyleSheet("font-weight: bold;")
        self.logo_v1_btn.clicked.connect(lambda: self._select_logo(1))
        logo_btn_layout.addWidget(self.logo_v1_btn)
        
        self.logo_v2_btn = QPushButton("Logo V2")
        self.logo_v2_btn.setCheckable(True)
        self.logo_v2_btn.setStyleSheet("font-weight: bold;")
        self.logo_v2_btn.clicked.connect(lambda: self._select_logo(2))
        logo_btn_layout.addWidget(self.logo_v2_btn)
        engrave_layout.addLayout(logo_btn_layout, 2, 1)
        
        # Logo Scale slider
        self.logo_scale_label = QLabel("Logo Scale: 100%")
        engrave_layout.addWidget(self.logo_scale_label, 3, 0)
        self.logo_scale_slider = NoWheelSlider(Qt.Orientation.Horizontal)
        self.logo_scale_slider.setRange(50, 200)  # 50% to 200%
        self.logo_scale_slider.setValue(100)
        self.logo_scale_slider.valueChanged.connect(self._on_engrave_slider_changed)
        engrave_layout.addWidget(self.logo_scale_slider, 3, 1)
        
        # --- Separator ---
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.HLine)
        separator1.setStyleSheet("color: #555;")
        engrave_layout.addWidget(separator1, 4, 0, 1, 2)
        
        # --- Text Section ---
        text_header = QLabel("<b>Text (Optional)</b>")
        engrave_layout.addWidget(text_header, 5, 0, 1, 2)
        
        engrave_layout.addWidget(QLabel("Patient Name:"), 6, 0)
        self.patient_name_edit = QLineEdit()
        self.patient_name_edit.setPlaceholderText("Enter patient name")
        engrave_layout.addWidget(self.patient_name_edit, 6, 1)
        
        engrave_layout.addWidget(QLabel("Date:"), 7, 0)
        self.date_edit = QLineEdit()
        self.date_edit.setText(datetime.now().strftime("%Y-%m-%d"))
        engrave_layout.addWidget(self.date_edit, 7, 1)
        
        # Font Size slider
        self.text_size_label = QLabel("Font Size: 4.0mm")
        engrave_layout.addWidget(self.text_size_label, 8, 0)
        self.text_size_slider = NoWheelSlider(Qt.Orientation.Horizontal)
        self.text_size_slider.setRange(20, 100)  # 2.0 to 10.0 mm
        self.text_size_slider.setValue(40)  # 4.0mm default
        self.text_size_slider.valueChanged.connect(self._on_engrave_slider_changed)
        engrave_layout.addWidget(self.text_size_slider, 8, 1)
        
        # Spacing between logo and text
        self.text_spacing_label = QLabel("Text Spacing: 6.0mm")
        engrave_layout.addWidget(self.text_spacing_label, 9, 0)
        self.text_spacing_slider = NoWheelSlider(Qt.Orientation.Horizontal)
        self.text_spacing_slider.setRange(0, 100)  # 0 to 10mm (value / 10)
        self.text_spacing_slider.setValue(60)  # 6.0mm default
        self.text_spacing_slider.valueChanged.connect(self._on_engrave_slider_changed)
        engrave_layout.addWidget(self.text_spacing_slider, 9, 1)
        
        # --- Separator ---
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setStyleSheet("color: #555;")
        engrave_layout.addWidget(separator2, 10, 0, 1, 2)
        
        # --- Position & Transform Section ---
        position_header = QLabel("<b>Position & Transform</b>")
        engrave_layout.addWidget(position_header, 11, 0, 1, 2)
        
        # Pick position button
        self.pick_engrave_btn = QPushButton("Pick Engraving Position")
        self.pick_engrave_btn.setMinimumHeight(30)
        self.pick_engrave_btn.setStyleSheet("font-weight: bold;")
        self.pick_engrave_btn.clicked.connect(self._start_engrave_picking)
        engrave_layout.addWidget(self.pick_engrave_btn, 12, 0, 1, 2)
        
        self.engrave_pos_info = QLabel("Position: Not set")
        self.engrave_pos_info.setStyleSheet("color: gray;")
        engrave_layout.addWidget(self.engrave_pos_info, 13, 0, 1, 2)
        
        # Offset X slider
        self.offset_x_label = QLabel("Offset X: 0")
        engrave_layout.addWidget(self.offset_x_label, 14, 0)
        self.engrave_offset_x_slider = NoWheelSlider(Qt.Orientation.Horizontal)
        self.engrave_offset_x_slider.setRange(-50, 50)
        self.engrave_offset_x_slider.setValue(0)
        self.engrave_offset_x_slider.valueChanged.connect(self._on_engrave_slider_changed)
        engrave_layout.addWidget(self.engrave_offset_x_slider, 14, 1)
        
        # Offset Y slider
        self.offset_y_label = QLabel("Offset Y: 0")
        engrave_layout.addWidget(self.offset_y_label, 15, 0)
        self.engrave_offset_y_slider = NoWheelSlider(Qt.Orientation.Horizontal)
        self.engrave_offset_y_slider.setRange(-50, 50)
        self.engrave_offset_y_slider.setValue(0)
        self.engrave_offset_y_slider.valueChanged.connect(self._on_engrave_slider_changed)
        engrave_layout.addWidget(self.engrave_offset_y_slider, 15, 1)
        
        # Rotation slider (affects both logo and text)
        self.rotation_label = QLabel("Rotation: 0°")
        engrave_layout.addWidget(self.rotation_label, 16, 0)
        self.engrave_rotation_slider = NoWheelSlider(Qt.Orientation.Horizontal)
        self.engrave_rotation_slider.setRange(-180, 180)
        self.engrave_rotation_slider.setValue(0)
        self.engrave_rotation_slider.valueChanged.connect(self._on_engrave_slider_changed)
        engrave_layout.addWidget(self.engrave_rotation_slider, 16, 1)
        
        # Engrave Depth slider (common for logo and text)
        self.engrave_depth_label = QLabel("Engrave Depth: 0.6mm")
        engrave_layout.addWidget(self.engrave_depth_label, 17, 0)
        self.engrave_depth_slider = NoWheelSlider(Qt.Orientation.Horizontal)
        self.engrave_depth_slider.setRange(3, 20)  # 0.3mm to 2.0mm
        self.engrave_depth_slider.setValue(6)  # 0.6mm default
        self.engrave_depth_slider.valueChanged.connect(self._on_engrave_slider_changed)
        engrave_layout.addWidget(self.engrave_depth_slider, 17, 1)
        
        # Engrave button
        self.engrave_btn = QPushButton("Engrave")
        self.engrave_btn.setMinimumHeight(40)
        self.engrave_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; font-size: 14px;")
        self.engrave_btn.clicked.connect(self._apply_engraving)
        engrave_layout.addWidget(self.engrave_btn, 18, 0, 1, 2)
        
        # Reset button
        self.reset_engrave_btn = QPushButton("Reset Engraving")
        self.reset_engrave_btn.setStyleSheet("font-weight: bold;")
        self.reset_engrave_btn.clicked.connect(self._reset_engraving)
        engrave_layout.addWidget(self.reset_engrave_btn, 19, 0, 1, 2)
        
        self.engrave_status = QLabel("")
        engrave_layout.addWidget(self.engrave_status, 20, 0, 1, 2)
        
        layout.addWidget(engrave_group)
        
        # === Step 3: Export ===
        export_group = QGroupBox("3. Export STL Files")
        export_layout = QVBoxLayout(export_group)
        
        # Export both button
        self.export_btn = QPushButton("Export Both L and R")
        self.export_btn.setMinimumHeight(40)
        self.export_btn.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
        self.export_btn.clicked.connect(self._export_both)
        export_layout.addWidget(self.export_btn)
        
        # Separate export buttons
        separate_layout = QHBoxLayout()
        self.export_left_btn = QPushButton("Export Left Only")
        self.export_left_btn.clicked.connect(lambda: self._export_single('L'))
        separate_layout.addWidget(self.export_left_btn)
        
        self.export_right_btn = QPushButton("Export Right Only")
        self.export_right_btn.clicked.connect(lambda: self._export_single('R'))
        separate_layout.addWidget(self.export_right_btn)
        export_layout.addLayout(separate_layout)
        
        self.export_status = QLabel("")
        self.export_status.setWordWrap(True)
        export_layout.addWidget(self.export_status)
        
        layout.addWidget(export_group)
        
        # Stretch
        layout.addStretch()
        
        # Reset button
        self.reset_btn = QPushButton("Reset All")
        self.reset_btn.setStyleSheet("font-weight: bold;")
        self.reset_btn.clicked.connect(self._reset_all)
        layout.addWidget(self.reset_btn)
        
        return panel
    
    def _create_status_bar(self):
        """Create the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Load an orthosis STL file to begin")
    
    def _load_logos(self):
        """Load logo files from logos directory."""
        app_path = get_application_path()
        logos_dir = os.path.join(app_path, "logos")
        
        if os.path.exists(logos_dir):
            self.processor.load_logos(logos_dir)
            if self.processor.logo_v1 is not None or self.processor.logo_v2 is not None:
                self.status_bar.showMessage("Logos loaded from: " + logos_dir)
                # Set initial logo preview
                self._update_logo_preview(1)
            else:
                self.status_bar.showMessage("Warning: No logo files found in logos/ folder. Add logo_v1.png or logo_v2.png")
        else:
            self.status_bar.showMessage("Warning: logos/ directory not found")
    
    def _connect_signals(self):
        """Connect Qt signals to slots."""
        self.viewer.logo_point_picked.connect(self._on_engrave_picked)
        self.viewer.text_point_picked.connect(self._on_engrave_picked)
        
        # Initialize slider values from saved defaults
        self._load_slider_defaults()
    
    def _load_slider_defaults(self):
        """Load slider default values from settings."""
        # Get default values from settings
        logo_scale = self.settings.value('engrave/default_logo_scale', 100, type=int)
        text_size = int(self.settings.value('engrave/default_text_size', 4.0, type=float) * 10)
        text_spacing = int(self.settings.value('engrave/default_text_spacing', 6.0, type=float) * 10)
        offset_x = self.settings.value('engrave/default_offset_x', 0, type=int)
        offset_y = self.settings.value('engrave/default_offset_y', 0, type=int)
        rotation = self.settings.value('engrave/default_rotation', 0, type=int)
        engrave_depth = int(self.settings.value('engrave/default_engrave_depth', 0.6, type=float) * 10)
        
        # Apply to sliders
        self.logo_scale_slider.setValue(logo_scale)
        self.text_size_slider.setValue(text_size)
        self.text_spacing_slider.setValue(text_spacing)
        self.engrave_offset_x_slider.setValue(offset_x)
        self.engrave_offset_y_slider.setValue(offset_y)
        self.engrave_rotation_slider.setValue(rotation)
        self.engrave_depth_slider.setValue(engrave_depth)
        
        # Update labels
        self._on_engrave_slider_changed()
    
    def _update_ui_state(self):
        """Update UI enabled/disabled states."""
        has_mesh = self.processor.orthosis_mesh is not None
        has_engrave_pos = self._engrave_position is not None
        
        # Enable controls based on state
        self.logo_v1_btn.setEnabled(has_mesh)
        self.logo_v2_btn.setEnabled(has_mesh)
        self.pick_engrave_btn.setEnabled(has_mesh)
        self.patient_name_edit.setEnabled(has_mesh)
        self.date_edit.setEnabled(has_mesh)
        
        # Engraving sliders
        self.logo_scale_slider.setEnabled(has_engrave_pos)
        self.text_size_slider.setEnabled(has_engrave_pos)
        self.text_spacing_slider.setEnabled(has_engrave_pos)
        self.engrave_offset_x_slider.setEnabled(has_engrave_pos)
        self.engrave_offset_y_slider.setEnabled(has_engrave_pos)
        self.engrave_rotation_slider.setEnabled(has_engrave_pos)
        self.engrave_depth_slider.setEnabled(has_engrave_pos)
        
        # Engrave button
        self.engrave_btn.setEnabled(has_engrave_pos and has_mesh)
        self.reset_engrave_btn.setEnabled(self._engraving_applied)
        
        # Export requires engraving applied
        can_export = has_mesh and self._engraving_applied
        self.export_btn.setEnabled(can_export)
        self.export_left_btn.setEnabled(can_export)
        self.export_right_btn.setEnabled(can_export)
    
    # === Slider handlers ===
    
    def _on_engrave_slider_changed(self):
        """Update slider value labels."""
        scale = self.logo_scale_slider.value()
        font_size = self.text_size_slider.value() / 10.0
        spacing = self.text_spacing_slider.value() / 10.0
        ox = self.engrave_offset_x_slider.value()
        oy = self.engrave_offset_y_slider.value()
        rot = self.engrave_rotation_slider.value()
        depth = self.engrave_depth_slider.value() / 10.0
        
        # Update individual labels
        self.logo_scale_label.setText(f"Logo Scale: {scale}%")
        self.text_size_label.setText(f"Font Size: {font_size:.1f}mm")
        self.text_spacing_label.setText(f"Text Spacing: {spacing:.1f}mm")
        self.offset_x_label.setText(f"Offset X: {ox}")
        self.offset_y_label.setText(f"Offset Y: {oy}")
        self.rotation_label.setText(f"Rotation: {rot}°")
        self.engrave_depth_label.setText(f"Engrave Depth: {depth:.1f}mm")
    
    # === File Operations ===
    
    def _open_orthosis_stl(self):
        """Open file dialog to load orthosis STL."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Orthosis STL",
            self.last_directory,
            "STL Files (*.stl);;All Files (*.*)"
        )
        
        if file_path:
            try:
                self.processor.load_orthosis_stl(file_path)
                
                self.orthosis_file_path = file_path
                self.last_directory = os.path.dirname(file_path)
                self.settings.setValue('last_directory', self.last_directory)
                
                # Create mirrored version
                left_mesh, right_mesh = self.processor.mirror_for_dual_display()
                
                # Display in viewer
                self.viewer.set_both_meshes(left_mesh, right_mesh)
                
                # Update UI
                self.file_label.setText(os.path.basename(file_path))
                self._reset_positions()
                self._update_ui_state()
                
                self.status_bar.showMessage(f"Loaded: {os.path.basename(file_path)}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load STL:\n{str(e)}")
    
    def _export_both(self):
        """Export both L and R STL files with proper save dialog."""
        if not (self._logo_applied or self._text_applied):
            QMessageBox.warning(self, "Warning", "Please apply logo or text first.")
            return
        
        patient_name = self.patient_name_edit.text().strip()
        if not patient_name:
            patient_name = "Orthosis"
        
        date_str = self.date_edit.text().strip().replace('/', '-').replace('\\', '-').replace(':', '-')
        
        # Create default filename
        default_filename = f"{patient_name}_{date_str}"
        
        # Use getSaveFileName for clearer save action
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save STL Files (Base Name)",
            os.path.join(self.last_directory, default_filename),
            "STL Files (*.stl);;All Files (*.*)"
        )
        
        if file_path:
            try:
                # Remove extension if present
                base_path = file_path
                if base_path.lower().endswith('.stl'):
                    base_path = base_path[:-4]
                
                output_dir = os.path.dirname(base_path)
                base_name = os.path.basename(base_path)
                
                # Export both files
                left_path = f"{base_path}_L.stl"
                right_path = f"{base_path}_R.stl"
                
                self.processor.orthosis_mirrored.export(left_path, file_type='stl')
                self.processor.orthosis_original.export(right_path, file_type='stl')
                
                # Update last directory
                self.last_directory = output_dir
                self.settings.setValue('last_directory', self.last_directory)
                
                self.export_status.setText(f"Saved:\n{os.path.basename(left_path)}\n{os.path.basename(right_path)}")
                self.status_bar.showMessage(f"Successfully exported to {output_dir}")
                
                QMessageBox.information(
                    self, 
                    "Export Complete",
                    f"Files saved:\n\n{os.path.basename(left_path)}\n{os.path.basename(right_path)}\n\nLocation: {output_dir}"
                )
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed:\n{str(e)}")
    
    def _export_single(self, side: str):
        """Export a single L or R STL file."""
        if not (self._logo_applied or self._text_applied):
            QMessageBox.warning(self, "Warning", "Please apply logo or text first.")
            return
        
        patient_name = self.patient_name_edit.text().strip()
        if not patient_name:
            patient_name = "Orthosis"
        
        date_str = self.date_edit.text().strip().replace('/', '-').replace('\\', '-').replace(':', '-')
        
        # Create default filename
        default_filename = f"{patient_name}_{date_str}_{side}.stl"
        
        # Use getSaveFileName for clear save action
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Save {side} STL File",
            os.path.join(self.last_directory, default_filename),
            "STL Files (*.stl);;All Files (*.*)"
        )
        
        if file_path:
            try:
                # Ensure .stl extension
                if not file_path.lower().endswith('.stl'):
                    file_path += '.stl'
                
                # Export the appropriate mesh
                if side == 'L':
                    self.processor.orthosis_mirrored.export(file_path, file_type='stl')
                else:
                    self.processor.orthosis_original.export(file_path, file_type='stl')
                
                # Update last directory
                self.last_directory = os.path.dirname(file_path)
                self.settings.setValue('last_directory', self.last_directory)
                
                self.export_status.setText(f"Saved: {os.path.basename(file_path)}")
                self.status_bar.showMessage(f"Successfully exported: {file_path}")
                
                QMessageBox.information(
                    self, 
                    "Export Complete",
                    f"File saved:\n{os.path.basename(file_path)}\n\nLocation: {os.path.dirname(file_path)}"
                )
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed:\n{str(e)}")
    
    # === Logo Operations ===
    
    def _select_logo(self, version: int):
        """Select logo version 1 or 2."""
        self.processor.select_logo(version)
        self.logo_v1_btn.setChecked(version == 1)
        self.logo_v2_btn.setChecked(version == 2)
        self.status_bar.showMessage(f"Selected Logo V{version}")
        
        # Update logo preview
        self._update_logo_preview(version)
    
    def _update_logo_preview(self, version: int):
        """Update the logo preview image."""
        app_path = get_application_path()
        logos_dir = os.path.join(app_path, "logos")
        
        # Search for logo file with various naming patterns and extensions
        patterns = [
            f"logo_v{version}",
            f"Logo_v{version}",
            f"logo_V{version}",
            f"Logo_V{version}",
        ]
        extensions = ['.png', '.jpg', '.jpeg']
        
        logo_path = None
        for pattern in patterns:
            for ext in extensions:
                test_path = os.path.join(logos_dir, pattern + ext)
                if os.path.exists(test_path):
                    logo_path = test_path
                    break
            if logo_path:
                break
        
        if logo_path and os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            # Scale to fit preview while maintaining aspect ratio
            scaled = pixmap.scaled(
                self.logo_preview.width() - 10,
                self.logo_preview.height() - 10,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.logo_preview.setPixmap(scaled)
        else:
            self.logo_preview.setText(f"Logo V{version} not found")
    
    def _start_engrave_picking(self):
        """Enable engraving position picking mode."""
        self.viewer.set_logo_picking_mode(True)
        self.status_bar.showMessage("Click on the RIGHT orthosis to place the engraving (logo + text)")
    
    def _on_engrave_picked(self, point: np.ndarray, normal: np.ndarray):
        """Handle engraving position picked."""
        self._engrave_position = point.copy()
        self._engrave_normal = normal.copy()
        
        # For legacy compatibility
        self._logo_position = point.copy()
        self._logo_normal = normal.copy()
        
        self.engrave_pos_info.setText(f"Position: ({point[0]:.1f}, {point[1]:.1f}, {point[2]:.1f})")
        self.engrave_pos_info.setStyleSheet("color: green;")
        self.status_bar.showMessage("Position set. Adjust settings and click Engrave.")
        
        self._update_ui_state()
    
    def _apply_engraving(self):
        """Apply combined logo and text engraving to the mesh."""
        if self._engrave_position is None:
            QMessageBox.warning(self, "Warning", "Please pick an engraving position first.")
            return
        
        if self.processor.logo_mesh is None:
            QMessageBox.warning(self, "Warning", "No logo loaded. Please add logo_v1.png or logo_v2.png to the logos/ folder.")
            return
        
        try:
            self.status_bar.showMessage("Applying engraving... please wait")
            QApplication.processEvents()
            
            # Get slider values
            offset_x = self.engrave_offset_x_slider.value()
            offset_y = self.engrave_offset_y_slider.value()
            rotation = self.engrave_rotation_slider.value()
            logo_scale = self.logo_scale_slider.value() / 100.0
            engrave_depth = self.engrave_depth_slider.value() / 10.0  # Common depth for logo and text
            text_font_size = self.text_size_slider.value() / 10.0
            text_spacing = self.text_spacing_slider.value() / 10.0
            
            # Build text (only if patient name is provided)
            patient_name = self.patient_name_edit.text().strip()
            text = None
            if patient_name:
                date_str = self.date_edit.text().strip()
                text = f"{patient_name}\n{date_str}"
            
            # Apply combined engraving
            self.processor.apply_engraving(
                position=self._engrave_position,
                normal=self._engrave_normal,
                offset_x=offset_x,
                offset_y=offset_y,
                rotation=rotation,
                logo_scale=logo_scale,
                logo_depth=engrave_depth,
                text=text,
                text_font_size=text_font_size,
                text_depth=engrave_depth,  # Same depth for both
                text_spacing=text_spacing
            )
            
            # Update viewer (don't reset camera)
            self.viewer.set_both_meshes(self.processor.orthosis_mirrored, self.processor.orthosis_original, auto_reset=False)
            
            # Clear the markers since engraving is now applied
            self.viewer.clear_all_markers()
            
            self._engraving_applied = True
            self._logo_applied = True
            if text:
                self._text_applied = True
            
            status_msg = "Logo" + (" and text" if text else "") + " engraved"
            self.engrave_status.setText(status_msg)
            self.engrave_status.setStyleSheet("color: green;")
            self.status_bar.showMessage(status_msg + " successfully!")
            
            self._update_ui_state()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Engraving failed:\n{str(e)}")
            self.status_bar.showMessage("Engraving failed")
    
    def _reset_engraving(self):
        """Reset to remove all engravings and restore original mesh."""
        if self.processor._pristine_mesh is None:
            return
        
        try:
            # Restore to pristine state (removes all engravings)
            self.processor._restore_to_pristine()
            
            # Update viewer
            self.viewer.set_both_meshes(
                self.processor.orthosis_mirrored, 
                self.processor.orthosis_original, 
                auto_reset=False
            )
            
            # Clear markers
            self.viewer.clear_all_markers()
            
            # Reset state
            self._engraving_applied = False
            self._engrave_position = None
            self._engrave_normal = None
            self._logo_applied = False
            self._text_applied = False
            self._logo_position = None
            self._logo_normal = None
            self._text_position = None
            self._text_normal = None
            
            # Reset UI
            self.engrave_pos_info.setText("Position: Not set")
            self.engrave_pos_info.setStyleSheet("color: gray;")
            self.engrave_status.setText("")
            
            # Reset sliders to defaults
            self.logo_scale_slider.setValue(100)
            self.text_size_slider.setValue(40)
            self.text_spacing_slider.setValue(60)  # 6mm default
            self.engrave_offset_x_slider.setValue(0)
            self.engrave_offset_y_slider.setValue(0)
            self.engrave_rotation_slider.setValue(0)
            self.engrave_depth_slider.setValue(6)  # 0.6mm default
            
            self.status_bar.showMessage("Engraving reset - original mesh restored")
            self._update_ui_state()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Reset failed:\n{str(e)}")
    
    # === Reset ===
    
    def _reset_positions(self):
        """Reset engraving positions."""
        self._engrave_position = None
        self._engrave_normal = None
        self._engraving_applied = False
        self._logo_position = None
        self._logo_normal = None
        self._text_position = None
        self._text_normal = None
        self._logo_applied = False
        self._text_applied = False
        
        self.engrave_pos_info.setText("Position: Not set")
        self.engrave_pos_info.setStyleSheet("color: gray;")
        self.engrave_status.setText("")
        self.export_status.setText("")
        
        # Reset sliders to defaults
        self.logo_scale_slider.setValue(100)
        self.text_size_slider.setValue(40)
        self.text_spacing_slider.setValue(60)  # 6mm default
        self.engrave_offset_x_slider.setValue(0)
        self.engrave_offset_y_slider.setValue(0)
        self.engrave_rotation_slider.setValue(0)
        self.engrave_depth_slider.setValue(6)  # 0.6mm default
        
        self.viewer.clear_all_markers()
    
    def _reset_all(self):
        """Reset entire workflow."""
        reply = QMessageBox.question(
            self,
            "Reset All",
            "This will clear all loaded data and reset the workflow. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.processor = OrthosisProcessor()
            self._load_logos()
            
            self.orthosis_file_path = None
            self.file_label.setText("No file loaded")
            
            self._reset_positions()
            self.patient_name_edit.clear()
            self.date_edit.setText(datetime.now().strftime("%Y-%m-%d"))
            
            self.viewer.set_both_meshes(None, None)
            
            self._update_ui_state()
            self.status_bar.showMessage("Reset complete - Load an orthosis STL to begin")
    
    # === View Operations ===
    
    def _set_render_mode(self, mode: str):
        """Set the render mode."""
        self.viewer.set_render_mode(mode)
        self.solid_action.setChecked(mode == 'solid')
        self.wireframe_action.setChecked(mode == 'wireframe')
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Orthosis Customizer",
            "<h3>Orthosis Customizer</h3>"
            "<p>Version 1.0</p>"
            "<p>A tool for customizing orthosis STL files with logo and text engraving.</p>"
        )
    
    def _open_settings(self):
        """Open the settings dialog."""
        dialog = SettingsDialog(self, self.settings)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Apply settings to viewer and processor
            self._apply_settings(dialog.get_settings_dict())
            self.status_bar.showMessage("Settings saved", 3000)
    
    def _apply_settings(self, settings_dict: dict):
        """Apply settings from the settings dialog."""
        # Store settings for later use
        self._app_settings = settings_dict
        
        # Apply render settings via the viewer's method (which stores them for mesh updates)
        self.viewer.set_render_settings(settings_dict)
        
        # Apply engraving settings
        engrave = settings_dict.get('engrave', {})
        self.processor.ENGRAVE_DEPTH = engrave.get('depth', 0.6)
    
    def _load_app_settings(self):
        """Load and apply settings on startup."""
        dialog = SettingsDialog(self, self.settings)
        self._app_settings = dialog.get_settings_dict()
        self._apply_settings(self._app_settings)
    
    def closeEvent(self, event):
        """Handle window close event."""
        self.settings.setValue('geometry', self.saveGeometry())
        event.accept()


def main():
    """Application entry point."""
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("Orthosis Customizer")
    app.setOrganizationName("OrthosisCustomizer")
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
