"""
3D STL Insole Adapter - Main Application
=========================================
A Windows desktop application for adapting predefined insole STL files
to 3D foot STL models.

Features:
- Load foot and insole STL files
- Place 4 reference points on foot (heel, toe tip, left side, right side)
- Auto-scale insole based on foot dimensions
- Mirror insole for left/right feet
- Add text labels (Name, Side, Date)
- Export adapted insole as new STL

Author: Mostafa Abdelaziz
License: MIT
"""

import sys
import os
from datetime import datetime
from typing import Optional


def get_application_path() -> str:
    """
    Get the application base directory.
    Works correctly for both:
    - Running as Python script: returns directory containing main.py
    - Running as PyInstaller bundle: returns directory containing the .exe
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle - use the exe's directory
        return os.path.dirname(sys.executable)
    else:
        # Running as Python script - use the script's directory
        return os.path.dirname(os.path.abspath(__file__))


# PySide6 imports for GUI
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QPushButton, QLabel, QLineEdit, QComboBox, QSpinBox,
    QDoubleSpinBox, QFileDialog, QMessageBox, QStatusBar, QSplitter,
    QFrame, QGridLayout, QCheckBox, QProgressBar, QSlider, QColorDialog,
    QScrollArea
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QFont, QAction, QIcon, QColor

# Import our custom modules
from src.stl_processor import STLProcessor
from src.mesh_viewer import SimpleMeshViewer

import numpy as np


class NoWheelSlider(QSlider):
    """QSlider that ignores mouse wheel events to prevent accidental changes."""
    
    def wheelEvent(self, event):
        # Ignore wheel events - only allow click/drag or keyboard
        event.ignore()


class MainWindow(QMainWindow):
    """
    Main application window for the STL Insole Adapter.
    Provides all GUI controls for loading, adapting, and exporting insoles.
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize processor
        self.processor = STLProcessor()
        
        # Settings for remembering last directory
        self.settings = QSettings('InsoleAdapter', 'STLAdapter')
        self.last_directory = self.settings.value('last_directory', '')
        
        # Current file paths
        self.foot_file_path: Optional[str] = None
        self.insole_file_path: Optional[str] = None
        
        # Label placement state
        self._label_position: Optional[np.ndarray] = None  # Picked position
        self._label_normal: Optional[np.ndarray] = None    # Surface normal at position
        
        # Setup UI
        self._setup_window()
        self._create_menu_bar()
        self._create_central_widget()
        self._create_status_bar()
        
        # Connect signals
        self._connect_signals()
        
        # Initial state
        self._update_ui_state()
    
    def _setup_window(self):
        """Configure main window properties."""
        self.setWindowTitle("3D Insole Adapter - STL Processing Tool")
        self.setMinimumSize(1200, 800)
        
        # Try to restore window geometry
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
        
        open_foot_action = QAction('Open &Foot STL...', self)
        open_foot_action.setShortcut('Ctrl+O')
        open_foot_action.triggered.connect(self._open_foot_stl)
        file_menu.addAction(open_foot_action)
        
        open_insole_action = QAction('Open &Insole STL...', self)
        open_insole_action.setShortcut('Ctrl+I')
        open_insole_action.triggered.connect(self._open_insole_stl)
        file_menu.addAction(open_insole_action)
        
        file_menu.addSeparator()
        
        export_action = QAction('&Export Insole...', self)
        export_action.setShortcut('Ctrl+E')
        export_action.triggered.connect(self._export_insole)
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
        
        side_view_action = QAction('&Side View', self)
        side_view_action.triggered.connect(lambda: self.viewer.set_view('side'))
        view_menu.addAction(side_view_action)
        
        iso_view_action = QAction('&Isometric View', self)
        iso_view_action.setShortcut('I')
        iso_view_action.triggered.connect(lambda: self.viewer.set_view('iso'))
        view_menu.addAction(iso_view_action)
        
        view_menu.addSeparator()
        
        # Render mode submenu
        render_menu = view_menu.addMenu('Render &Mode')
        
        self.wireframe_action = QAction('&Wireframe', self)
        self.wireframe_action.setShortcut('1')
        self.wireframe_action.setCheckable(True)
        self.wireframe_action.setChecked(True)
        self.wireframe_action.triggered.connect(lambda: self._set_render_mode('wireframe'))
        render_menu.addAction(self.wireframe_action)
        
        self.solid_action = QAction('&Solid', self)
        self.solid_action.setShortcut('2')
        self.solid_action.setCheckable(True)
        self.solid_action.triggered.connect(lambda: self._set_render_mode('solid'))
        render_menu.addAction(self.solid_action)
        
        self.points_action = QAction('&Points', self)
        self.points_action.setShortcut('3')
        self.points_action.setCheckable(True)
        self.points_action.triggered.connect(lambda: self._set_render_mode('points'))
        render_menu.addAction(self.points_action)
        
        view_menu.addSeparator()
        
        # Panel toggle
        self.toggle_panel_action = QAction('&Hide Settings Panel', self)
        self.toggle_panel_action.setShortcut('P')
        self.toggle_panel_action.triggered.connect(self._toggle_settings_panel)
        view_menu.addAction(self.toggle_panel_action)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        about_action = QAction('&About', self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
        help_action = QAction('&Instructions', self)
        help_action.setShortcut('F1')
        help_action.triggered.connect(self._show_help)
        help_menu.addAction(help_action)
    
    def _create_central_widget(self):
        """Create the main central widget with all controls."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main horizontal layout with splitter
        main_layout = QHBoxLayout(central_widget)
        
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)
        
        # Left panel - Controls (store reference for toggle)
        control_panel_content = self._create_control_panel()
        
        # Wrap in scroll area
        self.control_panel = QScrollArea()
        self.control_panel.setWidgetResizable(True)
        self.control_panel.setWidget(control_panel_content)
        self.control_panel.setMinimumWidth(350)
        self.control_panel.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.splitter.addWidget(self.control_panel)
        
        # Right panel - 3D Viewer
        self.viewer = SimpleMeshViewer()
        viewer_frame = QFrame()
        viewer_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
        viewer_layout = QVBoxLayout(viewer_frame)
        viewer_layout.setContentsMargins(0, 0, 0, 0)
        viewer_layout.addWidget(self.viewer)
        self.splitter.addWidget(viewer_frame)
        
        # Set splitter proportions (1:2 ratio)
        self.splitter.setSizes([400, 800])
    
    def _create_control_panel(self) -> QWidget:
        """Create the left control panel with all settings."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        
        # === File Loading Group ===
        file_group = QGroupBox("File Loading")
        file_layout = QGridLayout(file_group)
        
        # Foot STL
        file_layout.addWidget(QLabel("Foot STL:"), 0, 0)
        self.foot_path_label = QLabel("No file loaded")
        self.foot_path_label.setStyleSheet("color: gray; font-style: italic;")
        self.foot_path_label.setWordWrap(True)
        file_layout.addWidget(self.foot_path_label, 0, 1)
        
        self.load_foot_btn = QPushButton("Load Foot")
        self.load_foot_btn.setStyleSheet("font-weight: bold;")
        self.load_foot_btn.clicked.connect(self._open_foot_stl)
        file_layout.addWidget(self.load_foot_btn, 0, 2)
        
        # Insole STL
        file_layout.addWidget(QLabel("Insole STL:"), 1, 0)
        self.insole_path_label = QLabel("No file loaded")
        self.insole_path_label.setStyleSheet("color: gray; font-style: italic;")
        self.insole_path_label.setWordWrap(True)
        file_layout.addWidget(self.insole_path_label, 1, 1)
        
        self.load_insole_btn = QPushButton("Load Insole")
        self.load_insole_btn.setStyleSheet("font-weight: bold;")
        self.load_insole_btn.clicked.connect(self._open_insole_stl)
        file_layout.addWidget(self.load_insole_btn, 1, 2)
        
        layout.addWidget(file_group)
        
        # === Reference Points Group ===
        ref_group = QGroupBox("Reference Points")
        ref_layout = QVBoxLayout(ref_group)
        
        ref_info = QLabel(
            "Place 5 reference points:\n"
            "On FOOT:\n"
            "  1. Heel (back center)\n"
            "  2. Toe tip (front center)\n"
            "  3. Left side (widest point)\n"
            "  4. Right side (widest point)\n"
            "On INSOLE:\n"
            "  5. Internal surface (top touching foot)"
        )
        ref_info.setStyleSheet("color: #666;")
        ref_layout.addWidget(ref_info)
        
        ref_btn_layout = QHBoxLayout()
        
        self.start_picking_btn = QPushButton("Start Picking Points")
        self.start_picking_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.start_picking_btn.clicked.connect(self._start_picking)
        ref_btn_layout.addWidget(self.start_picking_btn)
        
        self.clear_points_btn = QPushButton("Clear Points")
        self.clear_points_btn.setStyleSheet("font-weight: bold;")
        self.clear_points_btn.clicked.connect(self._clear_points)
        ref_btn_layout.addWidget(self.clear_points_btn)
        
        ref_layout.addLayout(ref_btn_layout)
        
        # Current picking target label (shows which point to pick next)
        self.pick_target_label = QLabel("")
        self.pick_target_label.setStyleSheet("color: #FF9800; font-weight: bold; font-size: 11px;")
        ref_layout.addWidget(self.pick_target_label)
        
        # Point status display
        self.point_status_label = QLabel("Points: 0/5")
        ref_layout.addWidget(self.point_status_label)
        
        # Calculated dimensions
        self.dimensions_label = QLabel("Foot dimensions: --")
        ref_layout.addWidget(self.dimensions_label)
        
        # Align button
        self.align_insole_btn = QPushButton("Align Insole to Foot")
        self.align_insole_btn.setStyleSheet("background-color: #9C27B0; color: white; padding: 6px; font-weight: bold;")
        self.align_insole_btn.clicked.connect(self._align_insole)
        ref_layout.addWidget(self.align_insole_btn)
        
        # Link status indicator
        self.link_status_label = QLabel("Insole: Not linked")
        self.link_status_label.setStyleSheet("color: gray;")
        ref_layout.addWidget(self.link_status_label)
        
        layout.addWidget(ref_group)
        
        # === Scaling Group ===
        scale_group = QGroupBox("Scaling")
        scale_layout = QGridLayout(scale_group)
        
        # Current insole dimensions
        scale_layout.addWidget(QLabel("Current Insole Size:"), 0, 0, 1, 2)
        self.current_dims_label = QLabel("X: -- mm  Y: -- mm  Z: -- mm")
        self.current_dims_label.setStyleSheet("font-family: monospace;")
        scale_layout.addWidget(self.current_dims_label, 1, 0, 1, 3)
        
        # Auto scale button
        self.auto_scale_btn = QPushButton("Auto Scale to Foot")
        self.auto_scale_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px; font-weight: bold;")
        self.auto_scale_btn.clicked.connect(self._auto_scale)
        scale_layout.addWidget(self.auto_scale_btn, 2, 0, 1, 3)
        
        # Manual scale inputs for insole
        # X axis: absolute mm value (target length)
        scale_layout.addWidget(QLabel("Insole Length (X):"), 3, 0)
        self.scale_x_spin = QDoubleSpinBox()
        self.scale_x_spin.setRange(50.0, 500.0)  # 50mm to 500mm
        self.scale_x_spin.setValue(250.0)  # Default 250mm
        self.scale_x_spin.setSingleStep(1.0)
        self.scale_x_spin.setDecimals(1)
        self.scale_x_spin.setSuffix(" mm")
        scale_layout.addWidget(self.scale_x_spin, 3, 1)
        
        # Y axis: absolute mm value (target width)
        scale_layout.addWidget(QLabel("Insole Width (Y):"), 4, 0)
        self.scale_y_spin = QDoubleSpinBox()
        self.scale_y_spin.setRange(20.0, 300.0)  # 20mm to 300mm
        self.scale_y_spin.setValue(100.0)  # Default 100mm
        self.scale_y_spin.setSingleStep(1.0)
        self.scale_y_spin.setDecimals(1)
        self.scale_y_spin.setSuffix(" mm")
        scale_layout.addWidget(self.scale_y_spin, 4, 1)
        
        # Z axis: absolute mm value (target height)
        scale_layout.addWidget(QLabel("Insole Height (Z):"), 5, 0)
        self.scale_z_spin = QDoubleSpinBox()
        self.scale_z_spin.setRange(5.0, 100.0)  # 5mm to 100mm
        self.scale_z_spin.setValue(30.0)  # Default 30mm
        self.scale_z_spin.setSingleStep(1.0)
        self.scale_z_spin.setDecimals(1)
        self.scale_z_spin.setSuffix(" mm")
        scale_layout.addWidget(self.scale_z_spin, 5, 1)
        
        self.apply_scale_btn = QPushButton("Apply Insole Scale")
        self.apply_scale_btn.setStyleSheet("font-weight: bold;")
        self.apply_scale_btn.clicked.connect(self._apply_manual_scale)
        scale_layout.addWidget(self.apply_scale_btn, 6, 0, 1, 2)
        
        self.reset_insole_btn = QPushButton("Reset Insole")
        self.reset_insole_btn.setStyleSheet("font-weight: bold;")
        self.reset_insole_btn.clicked.connect(self._reset_insole)
        scale_layout.addWidget(self.reset_insole_btn, 6, 2)
        
        layout.addWidget(scale_group)
        
        # === Mirror Group ===
        mirror_group = QGroupBox("Mirror (Left/Right)")
        mirror_layout = QHBoxLayout(mirror_group)
        
        self.mirror_x_btn = QPushButton("Mirror X")
        self.mirror_x_btn.setStyleSheet("font-weight: bold;")
        self.mirror_x_btn.clicked.connect(lambda: self._mirror('x'))
        mirror_layout.addWidget(self.mirror_x_btn)
        
        self.mirror_y_btn = QPushButton("Mirror Y (L↔R)")
        self.mirror_y_btn.setStyleSheet("font-weight: bold;")
        self.mirror_y_btn.clicked.connect(lambda: self._mirror('y'))
        mirror_layout.addWidget(self.mirror_y_btn)
        
        layout.addWidget(mirror_group)
        
        # === Insole Position/Rotation Group ===
        position_group = QGroupBox("Insole Position and Rotation")
        position_layout = QGridLayout(position_group)
        
        # Translation sliders
        position_layout.addWidget(QLabel("Translation (mm):"), 0, 0, 1, 3)
        
        position_layout.addWidget(QLabel("X:"), 1, 0)
        self.translate_x_slider = NoWheelSlider(Qt.Orientation.Horizontal)
        self.translate_x_slider.setRange(-2000, 2000)  # -200mm to 200mm in 0.1mm steps
        self.translate_x_slider.setValue(0)
        self.translate_x_slider.valueChanged.connect(self._on_position_changed)
        position_layout.addWidget(self.translate_x_slider, 1, 1)
        self.translate_x_label = QLabel("0.0")
        self.translate_x_label.setFixedWidth(40)
        position_layout.addWidget(self.translate_x_label, 1, 2)
        
        position_layout.addWidget(QLabel("Y:"), 2, 0)
        self.translate_y_slider = NoWheelSlider(Qt.Orientation.Horizontal)
        self.translate_y_slider.setRange(-2000, 2000)  # -200mm to 200mm in 0.1mm steps
        self.translate_y_slider.setValue(0)
        self.translate_y_slider.valueChanged.connect(self._on_position_changed)
        position_layout.addWidget(self.translate_y_slider, 2, 1)
        self.translate_y_label = QLabel("0.0")
        self.translate_y_label.setFixedWidth(40)
        position_layout.addWidget(self.translate_y_label, 2, 2)
        
        position_layout.addWidget(QLabel("Z:"), 3, 0)
        self.translate_z_slider = NoWheelSlider(Qt.Orientation.Horizontal)
        self.translate_z_slider.setRange(-2000, 2000)  # -200mm to 200mm in 0.1mm steps
        self.translate_z_slider.setValue(0)
        self.translate_z_slider.valueChanged.connect(self._on_position_changed)
        position_layout.addWidget(self.translate_z_slider, 3, 1)
        self.translate_z_label = QLabel("0.0")
        self.translate_z_label.setFixedWidth(40)
        position_layout.addWidget(self.translate_z_label, 3, 2)
        
        # Rotation sliders
        position_layout.addWidget(QLabel("Rotation (degrees):"), 4, 0, 1, 3)
        
        position_layout.addWidget(QLabel("X:"), 5, 0)
        self.rotate_x_slider = QSlider(Qt.Orientation.Horizontal)
        self.rotate_x_slider.setRange(-180, 180)
        self.rotate_x_slider.setValue(0)
        self.rotate_x_slider.valueChanged.connect(self._on_position_changed)
        position_layout.addWidget(self.rotate_x_slider, 5, 1)
        self.rotate_x_label = QLabel("0")
        self.rotate_x_label.setFixedWidth(35)
        position_layout.addWidget(self.rotate_x_label, 5, 2)
        
        position_layout.addWidget(QLabel("Y:"), 6, 0)
        self.rotate_y_slider = QSlider(Qt.Orientation.Horizontal)
        self.rotate_y_slider.setRange(-180, 180)
        self.rotate_y_slider.setValue(0)
        self.rotate_y_slider.valueChanged.connect(self._on_position_changed)
        position_layout.addWidget(self.rotate_y_slider, 6, 1)
        self.rotate_y_label = QLabel("0")
        self.rotate_y_label.setFixedWidth(35)
        position_layout.addWidget(self.rotate_y_label, 6, 2)
        
        position_layout.addWidget(QLabel("Z:"), 7, 0)
        self.rotate_z_slider = QSlider(Qt.Orientation.Horizontal)
        self.rotate_z_slider.setRange(-180, 180)
        self.rotate_z_slider.setValue(0)
        self.rotate_z_slider.valueChanged.connect(self._on_position_changed)
        position_layout.addWidget(self.rotate_z_slider, 7, 1)
        self.rotate_z_label = QLabel("0")
        self.rotate_z_label.setFixedWidth(35)
        position_layout.addWidget(self.rotate_z_label, 7, 2)
        
        # Reset position button
        self.reset_position_btn = QPushButton("Reset Position/Rotation")
        self.reset_position_btn.setStyleSheet("font-weight: bold;")
        self.reset_position_btn.clicked.connect(self._reset_position_sliders)
        position_layout.addWidget(self.reset_position_btn, 8, 0, 1, 3)
        
        layout.addWidget(position_group)
        
        # === Label Group ===
        label_group = QGroupBox("Text Label")
        label_layout = QGridLayout(label_group)
        
        label_layout.addWidget(QLabel("Name:"), 0, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Patient/Client Name")
        label_layout.addWidget(self.name_input, 0, 1, 1, 2)
        
        label_layout.addWidget(QLabel("Side:"), 1, 0)
        self.side_combo = QComboBox()
        self.side_combo.addItems(["L (Left)", "R (Right)"])
        self.side_combo.setCurrentIndex(1)  # Default to R (Right)
        label_layout.addWidget(self.side_combo, 1, 1, 1, 2)
        
        label_layout.addWidget(QLabel("Date:"), 2, 0)
        self.date_input = QLineEdit()
        self.date_input.setText(datetime.now().strftime("%Y-%m-%d"))
        label_layout.addWidget(self.date_input, 2, 1, 1, 2)
        
        # Engrave option
        self.engrave_check = QCheckBox("Engrave label (cut into surface)")
        self.engrave_check.setChecked(False)  # Default to emboss (extrude)
        label_layout.addWidget(self.engrave_check, 3, 0, 1, 3)
        
        # Mirror options
        mirror_layout = QHBoxLayout()
        self.mirror_h_check = QCheckBox("Mirror Horizontal")
        self.mirror_h_check.setToolTip("Flip label left-right if text appears backwards")
        self.mirror_h_check.stateChanged.connect(self._on_label_slider_value_changed)
        mirror_layout.addWidget(self.mirror_h_check)
        
        self.mirror_v_check = QCheckBox("Mirror Vertical")
        self.mirror_v_check.setToolTip("Flip label up-down if text appears upside down")
        self.mirror_v_check.stateChanged.connect(self._on_label_slider_value_changed)
        mirror_layout.addWidget(self.mirror_v_check)
        label_layout.addLayout(mirror_layout, 4, 0, 1, 3)
        
        # Font size slider
        row_fs = 5
        label_layout.addWidget(QLabel("Font Size:"), row_fs, 0)
        self.font_size_slider = NoWheelSlider(Qt.Orientation.Horizontal)
        self.font_size_slider.setRange(10, 100)  # 1.0 to 10.0 mm (value / 10)
        self.font_size_slider.setValue(30)  # Default 3.0mm
        self.font_size_slider.valueChanged.connect(self._on_label_slider_value_changed)
        label_layout.addWidget(self.font_size_slider, row_fs, 1)
        self.font_size_label = QLabel("3.0")
        self.font_size_label.setFixedWidth(30)
        label_layout.addWidget(self.font_size_label, row_fs, 2)
        
        # Engrave depth slider
        row_depth = 6
        label_layout.addWidget(QLabel("Depth (mm):"), row_depth, 0)
        self.engrave_depth_slider = NoWheelSlider(Qt.Orientation.Horizontal)
        self.engrave_depth_slider.setRange(1, 30)  # 0.1 to 3.0 mm (value / 10)
        self.engrave_depth_slider.setValue(6)  # Default 0.6mm
        self.engrave_depth_slider.valueChanged.connect(self._on_label_slider_value_changed)
        label_layout.addWidget(self.engrave_depth_slider, row_depth, 1)
        self.engrave_depth_label = QLabel("0.6")
        self.engrave_depth_label.setFixedWidth(30)
        label_layout.addWidget(self.engrave_depth_label, row_depth, 2)
        
        # Z offset slider
        row_zoff = 7
        label_layout.addWidget(QLabel("Z Offset:"), row_zoff, 0)
        self.z_offset_slider = NoWheelSlider(Qt.Orientation.Horizontal)
        self.z_offset_slider.setRange(-50, 50)  # -5.0 to 5.0 mm (value / 10)
        self.z_offset_slider.setValue(0)
        self.z_offset_slider.valueChanged.connect(self._on_label_slider_value_changed)
        label_layout.addWidget(self.z_offset_slider, row_zoff, 1)
        self.z_offset_label = QLabel("0.0")
        self.z_offset_label.setFixedWidth(30)
        label_layout.addWidget(self.z_offset_label, row_zoff, 2)
        
        # Pick label position button
        self.pick_label_pos_btn = QPushButton("Pick Label Position")
        self.pick_label_pos_btn.setStyleSheet("font-weight: bold;")
        self.pick_label_pos_btn.setToolTip("Click on insole surface to place label")
        self.pick_label_pos_btn.clicked.connect(self._start_label_picking)
        label_layout.addWidget(self.pick_label_pos_btn, 8, 0, 1, 3)
        
        # Label position info
        self.label_pos_info = QLabel("Position: Not set")
        self.label_pos_info.setStyleSheet("color: gray;")
        label_layout.addWidget(self.label_pos_info, 9, 0, 1, 3)
        
        # Label offset sliders
        row = 10
        label_layout.addWidget(QLabel("Offset X:"), row, 0)
        self.label_offset_x_slider = NoWheelSlider(Qt.Orientation.Horizontal)
        self.label_offset_x_slider.setRange(-50, 50)
        self.label_offset_x_slider.setValue(0)
        self.label_offset_x_slider.valueChanged.connect(self._on_label_slider_value_changed)
        label_layout.addWidget(self.label_offset_x_slider, row, 1)
        self.label_offset_x_label = QLabel("0")
        self.label_offset_x_label.setFixedWidth(30)
        label_layout.addWidget(self.label_offset_x_label, row, 2)
        
        row += 1
        label_layout.addWidget(QLabel("Offset Y:"), row, 0)
        self.label_offset_y_slider = NoWheelSlider(Qt.Orientation.Horizontal)
        self.label_offset_y_slider.setRange(-50, 50)
        self.label_offset_y_slider.setValue(0)
        self.label_offset_y_slider.valueChanged.connect(self._on_label_slider_value_changed)
        label_layout.addWidget(self.label_offset_y_slider, row, 1)
        self.label_offset_y_label = QLabel("0")
        self.label_offset_y_label.setFixedWidth(30)
        label_layout.addWidget(self.label_offset_y_label, row, 2)
        
        row += 1
        label_layout.addWidget(QLabel("Rotation:"), row, 0)
        self.label_rotation_slider = NoWheelSlider(Qt.Orientation.Horizontal)
        self.label_rotation_slider.setRange(-180, 180)
        self.label_rotation_slider.setValue(0)
        self.label_rotation_slider.valueChanged.connect(self._on_label_slider_value_changed)
        label_layout.addWidget(self.label_rotation_slider, row, 1)
        self.label_rotation_label = QLabel("0°")
        self.label_rotation_label.setFixedWidth(30)
        label_layout.addWidget(self.label_rotation_label, row, 2)
        
        row += 1
        self.apply_label_btn = QPushButton("Apply Label to Insole")
        self.apply_label_btn.setStyleSheet("font-weight: bold;")
        self.apply_label_btn.clicked.connect(self._apply_label)
        label_layout.addWidget(self.apply_label_btn, row, 0, 1, 3)
        
        layout.addWidget(label_group)
        
        # === Export Group ===
        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout(export_group)
        
        self.auto_filename_check = QCheckBox("Auto-generate filename")
        self.auto_filename_check.setChecked(True)
        export_layout.addWidget(self.auto_filename_check)
        
        self.export_btn = QPushButton("Export Adapted Insole as STL")
        self.export_btn.setStyleSheet(
            "background-color: #FF9800; color: white; padding: 10px; font-weight: bold;"
        )
        self.export_btn.clicked.connect(self._export_insole)
        export_layout.addWidget(self.export_btn)
        
        layout.addWidget(export_group)
        
        # === View Settings Group ===
        view_group = QGroupBox("View Settings")
        view_layout = QGridLayout(view_group)
        
        # Render mode
        view_layout.addWidget(QLabel("Render Mode:"), 0, 0)
        self.render_mode_combo = QComboBox()
        self.render_mode_combo.addItems(["Solid", "Solid + Edges", "Wireframe", "Points"])
        self.render_mode_combo.setCurrentIndex(0)  # Default to Solid
        self.render_mode_combo.currentTextChanged.connect(self._on_render_mode_changed)
        view_layout.addWidget(self.render_mode_combo, 0, 1, 1, 2)
        
        # Foot opacity
        view_layout.addWidget(QLabel("Foot Opacity:"), 1, 0)
        self.foot_opacity_slider = NoWheelSlider(Qt.Orientation.Horizontal)
        self.foot_opacity_slider.setRange(0, 100)
        self.foot_opacity_slider.setValue(100)
        self.foot_opacity_slider.valueChanged.connect(self._on_foot_opacity_changed)
        view_layout.addWidget(self.foot_opacity_slider, 1, 1)
        self.foot_opacity_label = QLabel("100%")
        self.foot_opacity_label.setFixedWidth(40)
        view_layout.addWidget(self.foot_opacity_label, 1, 2)
        
        # Foot color
        view_layout.addWidget(QLabel("Foot Color:"), 2, 0)
        self.foot_color_btn = QPushButton()
        self.foot_color_btn.setFixedSize(60, 25)
        self.foot_color_btn.setStyleSheet("background-color: rgb(217, 191, 166);")
        self.foot_color_btn.clicked.connect(self._pick_foot_color)
        self._foot_color = QColor(217, 191, 166)  # Default skin-like
        view_layout.addWidget(self.foot_color_btn, 2, 1, 1, 2)
        
        # Insole opacity
        view_layout.addWidget(QLabel("Insole Opacity:"), 3, 0)
        self.insole_opacity_slider = NoWheelSlider(Qt.Orientation.Horizontal)
        self.insole_opacity_slider.setRange(0, 100)
        self.insole_opacity_slider.setValue(100)
        self.insole_opacity_slider.valueChanged.connect(self._on_insole_opacity_changed)
        view_layout.addWidget(self.insole_opacity_slider, 3, 1)
        self.insole_opacity_label = QLabel("100%")
        self.insole_opacity_label.setFixedWidth(40)
        view_layout.addWidget(self.insole_opacity_label, 3, 2)
        
        # Insole color
        view_layout.addWidget(QLabel("Insole Color:"), 4, 0)
        self.insole_color_btn = QPushButton()
        self.insole_color_btn.setFixedSize(60, 25)
        self.insole_color_btn.setStyleSheet("background-color: rgb(102, 153, 217);")
        self.insole_color_btn.clicked.connect(self._pick_insole_color)
        self._insole_color = QColor(102, 153, 217)  # Default blue
        view_layout.addWidget(self.insole_color_btn, 4, 1, 1, 2)
        
        layout.addWidget(view_group)
        
        # Spacer to push everything up
        layout.addStretch()
        
        return panel
    
    def _create_status_bar(self):
        """Create the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. Load a foot STL to begin.")
    
    def _connect_signals(self):
        """Connect widget signals to handlers."""
        # Point picking signal (foot points)
        self.viewer.point_picked.connect(self._on_point_picked)
        # Insole surface point picking signal
        self.viewer.insole_point_picked.connect(self._on_insole_point_picked)
        # Label position picking signal
        self.viewer.label_point_picked.connect(self._on_label_point_picked)
    
    def _on_position_changed(self):
        """Handle position/rotation slider changes."""
        if self.processor.insole_mesh is None:
            return
        
        # Update labels - translation values are in 0.1mm steps
        tx = self.translate_x_slider.value() / 10.0  # Convert to mm
        ty = self.translate_y_slider.value() / 10.0
        tz = self.translate_z_slider.value() / 10.0
        rx = self.rotate_x_slider.value()
        ry = self.rotate_y_slider.value()
        rz = self.rotate_z_slider.value()
        
        self.translate_x_label.setText(f"{tx:.1f}")
        self.translate_y_label.setText(f"{ty:.1f}")
        self.translate_z_label.setText(f"{tz:.1f}")
        self.rotate_x_label.setText(str(rx))
        self.rotate_y_label.setText(str(ry))
        self.rotate_z_label.setText(str(rz))
        
        # Apply transformation to insole
        self._apply_insole_transform(tx, ty, tz, rx, ry, rz)
    
    def _apply_insole_transform(self, tx, ty, tz, rx, ry, rz):
        """Apply translation and rotation to insole mesh."""
        import trimesh
        
        if self.processor.original_insole_mesh is None:
            return
        
        # Start from original mesh to avoid cumulative errors
        mesh_copy = self.processor.original_insole_mesh.copy()
        
        # Create rotation matrix (in degrees, convert to radians)
        rotation = trimesh.transformations.euler_matrix(
            np.radians(rx), np.radians(ry), np.radians(rz), 'sxyz'
        )
        
        # Apply rotation around mesh centroid
        centroid = mesh_copy.centroid.copy()
        mesh_copy.vertices -= centroid
        mesh_copy.apply_transform(rotation)
        mesh_copy.vertices += centroid
        
        # Apply translation
        translation = np.array([tx, ty, tz])
        mesh_copy.vertices += translation
        
        # Update processor and viewer
        self.processor.insole_mesh = mesh_copy
        self.viewer.set_insole_mesh(mesh_copy)
        
        # Update insole surface point position if it exists
        if self.viewer.insole_surface_point is not None and self.processor.insole_surface_point is not None:
            # Get original insole surface point (relative to original mesh)
            original_point = self.processor.insole_surface_point.copy()
            
            # Apply same transformation: rotation then translation
            # First translate to origin (relative to centroid)
            point_centered = original_point - centroid
            # Apply rotation
            point_rotated = rotation[:3, :3] @ point_centered
            # Translate back and apply slider translation
            new_point = point_rotated + centroid + translation
            
            # Update viewer's insole surface point marker
            self.viewer.insole_surface_point = new_point
            if self.viewer.insole_surface_actor is not None:
                # Recreate the marker at new position
                self.viewer.set_insole_surface_point(new_point)
    
    def _reset_position_sliders_ui_only(self):
        """Reset all position/rotation sliders to zero (UI only, no mesh update)."""
        # Block signals to avoid triggering position changes
        for slider in [self.translate_x_slider, self.translate_y_slider, self.translate_z_slider,
                       self.rotate_x_slider, self.rotate_y_slider, self.rotate_z_slider]:
            slider.blockSignals(True)
            slider.setValue(0)
            slider.blockSignals(False)
        
        # Update translation labels with 0.1mm precision
        for label in [self.translate_x_label, self.translate_y_label, self.translate_z_label]:
            label.setText("0.0")
        # Update rotation labels as integers
        for label in [self.rotate_x_label, self.rotate_y_label, self.rotate_z_label]:
            label.setText("0")
    
    def _reset_position_sliders(self):
        """Reset all position/rotation sliders to zero and reset mesh position."""
        # Reset slider UI
        self._reset_position_sliders_ui_only()
        
        # Reset insole to original position
        if self.processor.original_insole_mesh is not None:
            self.processor.insole_mesh = self.processor.original_insole_mesh.copy()
            self.viewer.set_insole_mesh(self.processor.insole_mesh)
            
            # Reset insole surface point to its original position (stored in processor)
            if self.processor.insole_surface_point is not None:
                self.viewer.set_insole_surface_point(self.processor.insole_surface_point)
            
            self.status_bar.showMessage("Insole position reset")
    
    def _update_ui_state(self):
        """Update UI element enabled states based on current state."""
        has_foot = self.processor.foot_mesh is not None
        has_insole = self.processor.insole_mesh is not None
        has_points = len(self.processor.reference_points) == 4
        has_insole_point = self.viewer.insole_surface_point is not None
        
        # Reference points require foot
        self.start_picking_btn.setEnabled(has_foot or (has_points and has_insole and not has_insole_point))
        self.clear_points_btn.setEnabled(len(self.viewer.reference_points) > 0 or has_insole_point)
        
        # Align requires foot, insole, and 4 foot points (5th point optional but recommended)
        self.align_insole_btn.setEnabled(has_foot and has_insole and has_points)
        
        # Scaling requires insole
        self.auto_scale_btn.setEnabled(has_insole and has_points)
        self.apply_scale_btn.setEnabled(has_insole)
        self.reset_insole_btn.setEnabled(has_insole)
        
        # Mirror requires insole
        self.mirror_x_btn.setEnabled(has_insole)
        self.mirror_y_btn.setEnabled(has_insole)
        
        # Position/rotation sliders require insole
        position_widgets = [
            self.translate_x_slider, self.translate_y_slider, self.translate_z_slider,
            self.rotate_x_slider, self.rotate_y_slider, self.rotate_z_slider,
            self.reset_position_btn
        ]
        for widget in position_widgets:
            widget.setEnabled(has_insole)
        
        # Label widgets require insole
        self.apply_label_btn.setEnabled(has_insole)
        self.pick_label_pos_btn.setEnabled(has_insole)
        self.label_offset_x_slider.setEnabled(has_insole)
        self.label_offset_y_slider.setEnabled(has_insole)
        self.label_rotation_slider.setEnabled(has_insole)
        
        # Export requires insole
        self.export_btn.setEnabled(has_insole)
        
        # Update dimensions display
        if has_insole:
            dims = self.processor.get_insole_dimensions()
            self.current_dims_label.setText(
                f"X: {dims[0]:.1f} mm  Y: {dims[1]:.1f} mm  Z: {dims[2]:.1f} mm"
            )
        else:
            self.current_dims_label.setText("X: -- mm  Y: -- mm  Z: -- mm")
        
        # Update point count (4 foot points + 1 insole point = 5 total)
        point_count = len(self.viewer.reference_points)
        total_points = point_count + (1 if has_insole_point else 0)
        self.point_status_label.setText(f"Points: {total_points}/5")
        
        if total_points == 5:
            self.point_status_label.setStyleSheet("color: green; font-weight: bold;")
        elif point_count == 4:
            self.point_status_label.setStyleSheet("color: #2196F3; font-weight: bold;")  # Blue - foot done, need insole
        else:
            self.point_status_label.setStyleSheet("color: orange;")
        
        # Update link status
        self._update_link_status()
    
    def _update_link_status(self):
        """Update the insole-foot link status display."""
        if self.processor.is_insole_linked():
            self.link_status_label.setText("Insole: Linked to foot")
            self.link_status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.link_status_label.setText("Insole: Not linked")
            self.link_status_label.setStyleSheet("color: gray;")
    
    def _set_render_mode(self, mode: str):
        """Set the 3D viewer render mode."""
        self.viewer.set_render_mode(mode)
        
        # Update checkmarks in menu
        self.wireframe_action.setChecked(mode == 'wireframe')
        self.solid_action.setChecked(mode == 'solid' or mode == 'solid_edges')
        self.points_action.setChecked(mode == 'points')
        
        # Sync combo box (block signals to prevent loop)
        self.render_mode_combo.blockSignals(True)
        mode_map = {'solid': 0, 'solid_edges': 1, 'wireframe': 2, 'points': 3}
        self.render_mode_combo.setCurrentIndex(mode_map.get(mode, 0))
        self.render_mode_combo.blockSignals(False)
        
        display_name = mode.replace('_', ' + ').title() if '_' in mode else mode.capitalize()
        self.status_bar.showMessage(f"Render mode: {display_name}", 2000)
    
    def _on_render_mode_changed(self, text: str):
        """Handle render mode combo box change."""
        mode = text.lower().replace(" ", "_").replace("+", "").replace("__", "_")
        if mode == "solid_edges":
            mode = "solid_edges"
        self._set_render_mode(mode)
    
    def _on_foot_scale_changed(self, value: int):
        """Handle foot scale slider change - scales both foot and linked insole."""
        scale_percent = value
        self.foot_scale_label.setText(f"{scale_percent}%")
        
        if self.processor.foot_mesh is None:
            return
        
        # Calculate scale factor relative to original (slider value / 100)
        scale_factor = scale_percent / 100.0
        
        # Store original meshes if not already stored
        if not hasattr(self, '_original_foot_mesh'):
            self._original_foot_mesh = None
        if not hasattr(self, '_foot_scale_base'):
            self._foot_scale_base = 100
        
        if self._original_foot_mesh is None:
            self._original_foot_mesh = self.processor.foot_mesh.copy()
            self._foot_scale_base = 100
        
        # Calculate scale relative to last scale
        relative_scale = scale_percent / self._foot_scale_base
        self._foot_scale_base = scale_percent
        
        # Apply uniform scale to foot
        scale_factors = (relative_scale, relative_scale, relative_scale)
        self.processor.scale_foot(scale_factors)
        
        # Update viewer
        self.viewer.set_foot_mesh(self.processor.foot_mesh)
        if self.processor.insole_mesh is not None:
            self.viewer.set_insole_mesh(self.processor.insole_mesh)
        
        self._update_ui_state()
    
    def _on_foot_opacity_changed(self, value: int):
        """Handle foot opacity slider change."""
        opacity = value / 100.0
        self.foot_opacity_label.setText(f"{value}%")
        self.viewer.set_foot_opacity(opacity)
    
    def _on_insole_opacity_changed(self, value: int):
        """Handle insole opacity slider change."""
        opacity = value / 100.0
        self.insole_opacity_label.setText(f"{value}%")
        self.viewer.set_insole_opacity(opacity)
    
    def _pick_foot_color(self):
        """Open color picker for foot mesh."""
        color = QColorDialog.getColor(self._foot_color, self, "Select Foot Color")
        if color.isValid():
            self._foot_color = color
            self.foot_color_btn.setStyleSheet(f"background-color: {color.name()};")
            self.viewer.set_foot_color(color.redF(), color.greenF(), color.blueF())
    
    def _pick_insole_color(self):
        """Open color picker for insole mesh."""
        color = QColorDialog.getColor(self._insole_color, self, "Select Insole Color")
        if color.isValid():
            self._insole_color = color
            self.insole_color_btn.setStyleSheet(f"background-color: {color.name()};")
            self.viewer.set_insole_color(color.redF(), color.greenF(), color.blueF())
    
    def _toggle_settings_panel(self):
        """Toggle visibility of the settings panel."""
        is_visible = self.control_panel.isVisible()
        self.control_panel.setVisible(not is_visible)
        
        if is_visible:
            self.toggle_panel_action.setText('&Show Settings Panel')
            self.status_bar.showMessage("Settings panel hidden. Press P to show.", 3000)
        else:
            self.toggle_panel_action.setText('&Hide Settings Panel')
            self.status_bar.showMessage("Settings panel shown.", 2000)

    def _get_models_foot_dir(self) -> str:
        """Get the default foot models directory."""
        # Check for models/foot directory relative to application
        app_dir = get_application_path()
        models_foot_dir = os.path.join(app_dir, "models", "foot")
        if os.path.isdir(models_foot_dir):
            return models_foot_dir
        return self.last_directory
    
    def _get_models_insole_dir(self) -> str:
        """Get the default insole models directory."""
        # Check for models/insole directory relative to application
        app_dir = get_application_path()
        models_insole_dir = os.path.join(app_dir, "models", "insole")
        if os.path.isdir(models_insole_dir):
            return models_insole_dir
        return self.last_directory
    
    def _open_foot_stl(self):
        """Open file dialog to load foot STL."""
        # Use models/foot directory as default
        default_dir = self._get_models_foot_dir()
        
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open Foot STL File",
            default_dir,
            "STL Files (*.stl);;All Files (*.*)"
        )
        
        if filepath:
            try:
                self.status_bar.showMessage(f"Loading {filepath}...")
                QApplication.processEvents()
                
                mesh = self.processor.load_foot_stl(filepath)
                self.viewer.set_foot_mesh(mesh)
                
                # Set isometric view for better 3D visualization
                self.viewer.set_view('iso')
                
                self.foot_file_path = filepath
                self.foot_path_label.setText(os.path.basename(filepath))
                self.foot_path_label.setStyleSheet("color: green;")
                self.foot_path_label.setToolTip(filepath)
                
                # Save directory
                self.last_directory = os.path.dirname(filepath)
                self.settings.setValue('last_directory', self.last_directory)
                
                # Clear any existing reference points
                self._clear_points()
                
                # Get foot length and display
                foot_length = self.processor.get_foot_length()
                self.dimensions_label.setText(f"Foot length (X): {foot_length:.1f} mm")
                
                # Auto-select best matching insole
                self._auto_select_insole()
                
                self.status_bar.showMessage(f"Loaded foot: {len(mesh.vertices)} vertices, length: {foot_length:.1f}mm", 5000)
                self._update_ui_state()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load foot STL:\n{str(e)}")
                self.status_bar.showMessage("Failed to load foot STL")
    
    def _auto_select_insole(self):
        """Automatically find and load the best matching insole for the current foot."""
        if self.processor.foot_mesh is None:
            return
        
        insole_dir = self._get_models_insole_dir()
        if not os.path.isdir(insole_dir):
            return
        
        try:
            self.status_bar.showMessage("Detecting foot side and finding best matching insole...")
            QApplication.processEvents()
            
            # Detect if foot is left or right (check filename first, then geometry)
            foot_side = self.processor.detect_foot_side(self.foot_file_path)
            
            # Update side selector in UI
            if foot_side == 'L':
                self.side_combo.setCurrentIndex(0)  # L (Left)
            else:
                self.side_combo.setCurrentIndex(1)  # R (Right)
            
            # Find best matching insole for this side
            best_insole = self.processor.find_best_matching_insole(insole_dir, foot_side)
            
            if best_insole:
                # Load the best matching insole and position it below foot
                mesh = self.processor.load_insole_stl(best_insole)
                
                # Position insole below foot
                self.processor.position_insole_below_foot()
                mesh = self.processor.insole_mesh
                
                self.viewer.set_insole_mesh(mesh)
                
                self.insole_file_path = best_insole
                self.insole_path_label.setText(os.path.basename(best_insole))
                self.insole_path_label.setStyleSheet("color: green;")
                self.insole_path_label.setToolTip(best_insole)
                
                # Reset position sliders
                self._reset_position_sliders_ui_only()
                
                # Update scale spinboxes - all get current dimensions in mm
                current_dims = self.processor.get_insole_dimensions()
                self.scale_x_spin.setValue(current_dims[0])
                self.scale_y_spin.setValue(current_dims[1])
                self.scale_z_spin.setValue(current_dims[2])
                
                # Get insole length for display
                insole_bounds = mesh.bounds
                insole_length = insole_bounds[1][0] - insole_bounds[0][0]
                
                self.status_bar.showMessage(
                    f"Detected {foot_side} foot - Auto-selected: {os.path.basename(best_insole)} (length: {insole_length:.1f}mm)", 
                    5000
                )
            else:
                self.status_bar.showMessage(f"Detected {foot_side} foot - No matching insole found", 3000)
                
        except Exception as e:
            print(f"Auto-select insole failed: {e}")
            self.status_bar.showMessage("Could not auto-select insole", 3000)

    def _open_insole_stl(self):
        """Open file dialog to load insole STL."""
        # Use models/insole directory as default
        default_dir = self._get_models_insole_dir()
        
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open Insole STL File",
            default_dir,
            "STL Files (*.stl);;All Files (*.*)"
        )
        
        if filepath:
            self._load_insole_file(filepath)
    
    def _load_insole_file(self, filepath: str):
        """Load an insole STL file and position it below the foot."""
        try:
            self.status_bar.showMessage(f"Loading {filepath}...")
            QApplication.processEvents()
            
            # Reset position sliders first (just reset UI, not mesh)
            self._reset_position_sliders_ui_only()
            
            mesh = self.processor.load_insole_stl(filepath)
            
            # If foot is loaded, position insole below it
            if self.processor.foot_mesh is not None:
                self.processor.position_insole_below_foot()
                mesh = self.processor.insole_mesh
            
            self.viewer.set_insole_mesh(mesh)
            
            # Update scale spinboxes - all get current dimensions in mm
            current_dims = self.processor.get_insole_dimensions()
            self.scale_x_spin.setValue(current_dims[0])
            self.scale_y_spin.setValue(current_dims[1])
            self.scale_z_spin.setValue(current_dims[2])
            
            # Set isometric view for better 3D visualization
            self.viewer.set_view('iso')
            
            self.insole_file_path = filepath
            self.insole_path_label.setText(os.path.basename(filepath))
            self.insole_path_label.setStyleSheet("color: green;")
            self.insole_path_label.setToolTip(filepath)
            
            # Save directory
            self.last_directory = os.path.dirname(filepath)
            self.settings.setValue('last_directory', self.last_directory)
            
            self.status_bar.showMessage(f"Loaded insole: {len(mesh.vertices)} vertices", 5000)
            
            self._update_ui_state()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load insole STL:\n{str(e)}")
            self.status_bar.showMessage("Failed to load insole STL")
    
    def _start_picking(self):
        """Start reference point picking mode."""
        if self.processor.foot_mesh is None:
            QMessageBox.warning(self, "Warning", "Please load a foot STL first.")
            return
        
        # Clear existing points
        self._clear_points()
        
        # Enable picking mode
        self.viewer.set_picking_mode(True)
        self._update_pick_target_label()
        self.status_bar.showMessage("Click on the foot to place reference points (Heel first)")
        
        self.start_picking_btn.setText("Picking... (ESC to cancel)")
        self.start_picking_btn.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
    
    def _update_pick_target_label(self):
        """Update the label showing which point to pick next."""
        point_count = len(self.viewer.reference_points)
        has_insole_point = self.viewer.insole_surface_point is not None
        
        if self.viewer.picking_enabled:
            targets = ["→ Pick: HEEL (back center on foot)",
                      "→ Pick: TOE TIP (front center on foot)",
                      "→ Pick: LEFT SIDE (widest point on foot)",
                      "→ Pick: RIGHT SIDE (widest point on foot)"]
            if point_count < 4:
                self.pick_target_label.setText(targets[point_count])
            else:
                self.pick_target_label.setText("")
        elif self.viewer.insole_picking_enabled:
            self.pick_target_label.setText("→ Pick: INSOLE INTERNAL SURFACE (top face)")
        elif point_count == 4 and not has_insole_point:
            self.pick_target_label.setText("Load insole to pick 5th point")
            self.pick_target_label.setStyleSheet("color: #2196F3; font-weight: bold; font-size: 11px;")
        else:
            self.pick_target_label.setText("")
            self.pick_target_label.setStyleSheet("color: #FF9800; font-weight: bold; font-size: 11px;")
    
    def _on_point_picked(self, point):
        """Handle point picked from viewer (foot points)."""
        point_count = len(self.viewer.reference_points)
        
        self._update_pick_target_label()
        
        if point_count == 1:
            self.status_bar.showMessage("Heel placed. Now click on the Toe tip (front center)")
        elif point_count == 2:
            self.status_bar.showMessage("Toe placed. Now click on the Left side (widest point)")
        elif point_count == 3:
            self.status_bar.showMessage("Left side placed. Now click on the Right side (widest point)")
        elif point_count == 4:
            # Set points in processor
            self.processor.set_reference_points(self.viewer.reference_points)
            
            # Calculate and display dimensions
            try:
                length, width = self.processor.calculate_foot_dimensions()
                self.dimensions_label.setText(f"Foot: Length={length:.1f}mm, Width={width:.1f}mm")
                self.dimensions_label.setStyleSheet("color: green;")
            except Exception as e:
                self.dimensions_label.setText(f"Error calculating dimensions: {e}")
            
            # Check if we have an insole loaded to pick the 5th point
            if self.processor.insole_mesh is not None:
                # Automatically start insole surface picking
                self.status_bar.showMessage("Foot points done! Now click on insole internal surface")
                self._start_insole_picking()
            else:
                self.status_bar.showMessage("4 foot points placed! Load insole to pick 5th point")
                self.start_picking_btn.setText("Start Picking Points")
                self.start_picking_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
            
            self._update_pick_target_label()
        
        self._update_ui_state()
    
    def _start_insole_picking(self):
        """Start picking the insole surface reference point (5th point)."""
        if self.processor.insole_mesh is None:
            QMessageBox.warning(self, "Warning", "Please load an insole STL first.")
            return
        
        # Enable insole picking mode
        self.viewer.set_insole_picking_mode(True)
        self._update_pick_target_label()
        self.status_bar.showMessage("Click on the INSOLE's internal/top surface (the side that touches the foot)")
        
        self.start_picking_btn.setText("Picking Insole... (ESC to cancel)")
        self.start_picking_btn.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
    
    def _on_insole_point_picked(self, point):
        """Handle insole surface point picked (5th point)."""
        self.status_bar.showMessage("All 5 reference points placed! Ready to align.")
        
        # Store the insole surface point in processor
        self.processor.insole_surface_point = np.array(point)
        
        # Reset button state
        self.start_picking_btn.setText("Start Picking Points")
        self.start_picking_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.start_picking_btn.clicked.disconnect()
        self.start_picking_btn.clicked.connect(self._start_picking)
        
        self._update_pick_target_label()
        self._update_ui_state()
    
    def _clear_points(self):
        """Clear all reference points including insole surface point."""
        self.viewer.clear_reference_points()
        self.viewer.clear_insole_surface_point()
        self.viewer.set_picking_mode(False)
        self.viewer.set_insole_picking_mode(False)
        self.processor.reference_points = []
        self.processor.insole_surface_point = None
        
        # Reset button to initial state
        try:
            self.start_picking_btn.clicked.disconnect()
        except:
            pass
        self.start_picking_btn.clicked.connect(self._start_picking)
        self.start_picking_btn.setText("Start Picking Points")
        self.start_picking_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        
        self.dimensions_label.setText("Foot dimensions: --")
        self.dimensions_label.setStyleSheet("")
        self.pick_target_label.setText("")
        
        self._update_ui_state()
        self.status_bar.showMessage("Reference points cleared")
    
    def _align_insole(self):
        """Align the insole to the foot using reference points."""
        if len(self.processor.reference_points) != 4:
            QMessageBox.warning(self, "Warning", "Please set all 4 foot reference points first.")
            return
        
        if self.processor.insole_mesh is None:
            QMessageBox.warning(self, "Warning", "Please load an insole first.")
            return
        
        # Check for insole surface point (5th point) - optional but recommended
        if self.processor.insole_surface_point is None:
            reply = QMessageBox.question(
                self, "Missing Insole Surface Point",
                "The 5th reference point (insole internal surface) is not set.\n\n"
                "This point helps align the insole's internal surface to touch the foot.\n\n"
                "Continue without it? (Alignment may be less accurate)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        try:
            # Align insole to foot (uses 5th point if available for better Z positioning)
            self.processor.align_insole_to_foot()
            
            # Update viewer
            self.viewer.set_insole_mesh(self.processor.insole_mesh)
            
            # Update insole surface point to the new position from processor
            # Use set (absolute position) instead of update (translation) for accuracy
            if self.processor.insole_surface_point is not None:
                self.viewer.set_insole_surface_point(self.processor.insole_surface_point)
            
            # Reset position sliders since alignment creates new reference position
            self._reset_position_sliders_ui_only()
            
            # Update link status
            self._update_link_status()
            
            self.status_bar.showMessage("Insole aligned to foot axis and positioned")
            self._update_ui_state()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to align insole:\n{str(e)}")
    
    def _auto_scale(self):
        """Automatically scale and position insole to cover all reference points."""
        if len(self.processor.reference_points) != 4:
            QMessageBox.warning(self, "Warning", "Please set all 4 reference points first.")
            return
        
        try:
            # Use the new method that scales AND positions to cover all reference points
            # No margin needed - the insole will be scaled to exactly cover the points
            scale_x, scale_y, scale_z = self.processor.auto_scale_insole_to_cover_points(1.0)
            
            # Update viewer
            self.viewer.set_insole_mesh(self.processor.insole_mesh)
            
            # Update insole surface point visualization if it exists
            # Use set_insole_surface_point (absolute position), not update (translation)
            if self.processor.insole_surface_point is not None:
                self.viewer.set_insole_surface_point(self.processor.insole_surface_point)
            
            # Update scale spinboxes:
            # All axes show the new dimensions in mm
            new_dims = self.processor.get_insole_dimensions()
            self.scale_x_spin.blockSignals(True)
            self.scale_y_spin.blockSignals(True)
            self.scale_z_spin.blockSignals(True)
            
            self.scale_x_spin.setValue(new_dims[0])  # Show length in mm
            self.scale_y_spin.setValue(new_dims[1])  # Show width in mm
            self.scale_z_spin.setValue(new_dims[2])  # Show height in mm
            
            self.scale_x_spin.blockSignals(False)
            self.scale_y_spin.blockSignals(False)
            self.scale_z_spin.blockSignals(False)
            
            self.status_bar.showMessage(
                f"Auto-scaled to cover reference points: {new_dims[0]:.1f}mm x {new_dims[1]:.1f}mm"
            )
            self._update_ui_state()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to auto-scale:\n{str(e)}")
    
    def _apply_manual_scale(self):
        """Apply manual scale factors to insole without resetting position."""
        try:
            # Get the current insole dimensions BEFORE scaling
            current_dims = self.processor.get_insole_dimensions()
            current_x_mm = current_dims[0]
            current_y_mm = current_dims[1]
            current_z_mm = current_dims[2]
            
            # Get target dimensions in mm for all axes
            target_x_mm = self.scale_x_spin.value()
            target_y_mm = self.scale_y_spin.value()
            target_z_mm = self.scale_z_spin.value()
            
            # Calculate scale factors from mm targets
            scale_x = target_x_mm / current_x_mm if current_x_mm > 0 else 1.0
            scale_y = target_y_mm / current_y_mm if current_y_mm > 0 else 1.0
            scale_z = target_z_mm / current_z_mm if current_z_mm > 0 else 1.0
            
            # Only apply if there's actually a change
            if abs(scale_x - 1.0) > 0.001 or abs(scale_y - 1.0) > 0.001 or abs(scale_z - 1.0) > 0.001:
                self.processor.scale_insole(scale_x, scale_y, scale_z)
                
                # Update viewer
                self.viewer.set_insole_mesh(self.processor.insole_mesh)
                
                # Update all spinboxes to show actual new dimensions
                new_dims = self.processor.get_insole_dimensions()
                self.scale_x_spin.blockSignals(True)
                self.scale_y_spin.blockSignals(True)
                self.scale_z_spin.blockSignals(True)
                self.scale_x_spin.setValue(new_dims[0])
                self.scale_y_spin.setValue(new_dims[1])
                self.scale_z_spin.setValue(new_dims[2])
                self.scale_x_spin.blockSignals(False)
                self.scale_y_spin.blockSignals(False)
                self.scale_z_spin.blockSignals(False)
                
                self.status_bar.showMessage(
                    f"Scaled: L={new_dims[0]:.1f}mm W={new_dims[1]:.1f}mm H={new_dims[2]:.1f}mm (position preserved)"
                )
            else:
                self.status_bar.showMessage("No scaling change applied")
            
            self._update_ui_state()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply scale:\n{str(e)}")
    
    def _reset_insole(self):
        """Reset insole to original size while keeping current position."""
        try:
            mesh = self.processor.reset_insole()
            if mesh is not None:
                self.viewer.set_insole_mesh(mesh)
                
                # Update insole surface point if it exists
                if self.processor.insole_surface_point is not None:
                    self.viewer.set_insole_surface_point(self.processor.insole_surface_point)
                
                # Reset scale spinboxes - all get current dimensions in mm
                current_dims = self.processor.get_insole_dimensions()
                self.scale_x_spin.setValue(current_dims[0])
                self.scale_y_spin.setValue(current_dims[1])
                self.scale_z_spin.setValue(current_dims[2])
                
                # Reset position sliders to zero (mesh position is preserved, sliders are relative)
                self._reset_position_sliders_ui_only()
                
                self.status_bar.showMessage("Insole scale reset to original size")
                self._update_ui_state()
            else:
                QMessageBox.warning(self, "Warning", "No original insole to reset to.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to reset insole:\n{str(e)}")
    
    def _mirror(self, axis: str):
        """Mirror the insole along specified axis. Preserves label at mirrored position."""
        try:
            had_label = self.processor._insole_before_label is not None
            
            self.processor.mirror_insole(axis)
            self.viewer.set_insole_mesh(self.processor.insole_mesh)
            
            # Reset position sliders since original mesh changed
            self._reset_position_sliders_ui_only()
            
            # Update the stored label position in main.py to match the mirrored position
            if had_label and self._label_position is not None:
                if axis.lower() == 'x':
                    self._label_position[0] = -self._label_position[0]
                    if self._label_normal is not None:
                        self._label_normal[0] = -self._label_normal[0]
                elif axis.lower() == 'y':
                    self._label_position[1] = -self._label_position[1]
                    if self._label_normal is not None:
                        self._label_normal[1] = -self._label_normal[1]
                else:  # z
                    self._label_position[2] = -self._label_position[2]
                    if self._label_normal is not None:
                        self._label_normal[2] = -self._label_normal[2]
            
            if had_label:
                self.status_bar.showMessage(
                    f"Insole mirrored along {axis.upper()} axis - label preserved at mirrored position",
                    8000
                )
            else:
                self.status_bar.showMessage(f"Insole mirrored along {axis.upper()} axis")
            
            self._update_ui_state()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to mirror:\n{str(e)}")
    
    def _start_label_picking(self):
        """Start label position picking mode. Removes any existing label first."""
        if self.processor.insole_mesh is None:
            QMessageBox.warning(self, "Warning", "Please load an insole first.")
            return
        
        # Remove existing label by restoring pre-label state
        if self.processor._insole_before_label is not None:
            self.processor.insole_mesh = self.processor._insole_before_label.copy()
            self.processor._current_label = None
            self.viewer.set_insole_mesh(self.processor.insole_mesh)
            self.status_bar.showMessage("Previous label removed. Click on insole to place new label.")
        
        # Clear previous label position
        self._label_position = None
        self._label_normal = None
        
        # Remove existing marker
        self.viewer.remove_label_marker()
        
        # Reset label position info
        self.label_pos_info.setText("Position: Not set")
        self.label_pos_info.setStyleSheet("color: gray;")
        
        self.viewer.set_label_picking_mode(True)
        self.pick_label_pos_btn.setText("Click on insole...")
        self.pick_label_pos_btn.setStyleSheet("background-color: #FFA500;")
        if self.processor._insole_before_label is None:
            self.status_bar.showMessage("Click on the insole surface to place the label")
    
    def _on_label_point_picked(self, point: np.ndarray, normal: np.ndarray):
        """Handle label position picked on insole."""
        self._label_position = point
        self._label_normal = normal
        
        # Update UI
        self.pick_label_pos_btn.setText("Pick Label Position")
        self.pick_label_pos_btn.setStyleSheet("")
        self.label_pos_info.setText(f"Position: ({point[0]:.1f}, {point[1]:.1f}, {point[2]:.1f})")
        self.label_pos_info.setStyleSheet("color: green;")
        
        # Reset offset sliders
        self.label_offset_x_slider.setValue(0)
        self.label_offset_y_slider.setValue(0)
        self.label_rotation_slider.setValue(0)
        
        self.status_bar.showMessage("Label position set. Adjust offsets if needed, then apply label.")
    
    def _on_label_slider_value_changed(self):
        """Handle label slider changes - update display labels only (no live preview)."""
        ox = self.label_offset_x_slider.value()
        oy = self.label_offset_y_slider.value()
        rot = self.label_rotation_slider.value()
        depth = self.engrave_depth_slider.value() / 10.0  # Convert to mm
        font_size = self.font_size_slider.value() / 10.0  # Convert to mm
        z_offset = self.z_offset_slider.value() / 10.0  # Convert to mm
        
        self.label_offset_x_label.setText(str(ox))
        self.label_offset_y_label.setText(str(oy))
        self.label_rotation_label.setText(f"{rot}°")
        self.engrave_depth_label.setText(f"{depth:.1f}")
        self.font_size_label.setText(f"{font_size:.1f}")
        self.z_offset_label.setText(f"{z_offset:.1f}")
    
    def _apply_label_silent(self):
        """Apply label without showing message boxes (for live preview)."""
        name = self.name_input.text().strip()
        if not name:
            return
            
        side = "L" if "L" in self.side_combo.currentText() else "R"
        date = self.date_input.text().strip()
        engrave = self.engrave_check.isChecked()
        depth = self.engrave_depth_slider.value() / 10.0  # Convert to mm
        font_size = self.font_size_slider.value() / 10.0  # Convert to mm
        z_offset = self.z_offset_slider.value() / 10.0  # Convert to mm
        mirror_h = self.mirror_h_check.isChecked()
        mirror_v = self.mirror_v_check.isChecked()
        
        offset_x = self.label_offset_x_slider.value()
        offset_y = self.label_offset_y_slider.value()
        rotation = self.label_rotation_slider.value()
        
        try:
            label_text = f"{name} {side} {date}"
            
            if self._label_position is not None:
                self.processor.add_text_label(
                    label_text, 
                    position='custom',
                    custom_position=self._label_position,
                    custom_normal=self._label_normal,
                    offset_x=offset_x,
                    offset_y=offset_y,
                    rotation=rotation,
                    depth=depth,
                    font_size=font_size,
                    z_offset=z_offset,
                    engrave=engrave,
                    mirror_horizontal=mirror_h,
                    mirror_vertical=mirror_v
                )
            else:
                self.processor.add_text_label(label_text, position='heel', depth=depth, font_size=font_size, z_offset=z_offset, engrave=engrave)
            
            self.viewer.set_insole_mesh(self.processor.insole_mesh)
        except Exception as e:
            print(f"Label preview failed: {e}")
    
    def _apply_label(self):
        """Apply text label to insole."""
        name = self.name_input.text().strip()
        side = "L" if "L" in self.side_combo.currentText() else "R"
        date = self.date_input.text().strip()
        engrave = self.engrave_check.isChecked()
        depth = self.engrave_depth_slider.value() / 10.0  # Convert to mm
        font_size = self.font_size_slider.value() / 10.0  # Convert to mm
        z_offset = self.z_offset_slider.value() / 10.0  # Convert to mm
        mirror_h = self.mirror_h_check.isChecked()
        mirror_v = self.mirror_v_check.isChecked()
        
        if not name:
            QMessageBox.warning(self, "Warning", "Please enter a name for the label.")
            return
        
        # Get offsets and rotation from sliders
        offset_x = self.label_offset_x_slider.value()
        offset_y = self.label_offset_y_slider.value()
        rotation = self.label_rotation_slider.value()
        
        try:
            # Create label text (single line)
            label_text = f"{name} {side} {date}"
            
            # Apply to insole with position if set
            if self._label_position is not None:
                self.processor.add_text_label(
                    label_text, 
                    position='custom',
                    custom_position=self._label_position,
                    custom_normal=self._label_normal,
                    offset_x=offset_x,
                    offset_y=offset_y,
                    rotation=rotation,
                    depth=depth,
                    font_size=font_size,
                    z_offset=z_offset,
                    engrave=engrave,
                    mirror_horizontal=mirror_h,
                    mirror_vertical=mirror_v
                )
            else:
                # Fallback to heel position
                self.processor.add_text_label(label_text, position='heel', depth=depth, font_size=font_size, z_offset=z_offset, engrave=engrave)
            
            self.viewer.set_insole_mesh(self.processor.insole_mesh)
            
            # Remove the marker
            self.viewer.remove_label_marker()
            
            mode = "engraved" if engrave else "embossed"
            self.status_bar.showMessage(f"Label {mode}: {name} / {side} / {date}")
            
        except Exception as e:
            QMessageBox.warning(
                self, 
                "Warning", 
                f"Label could not be applied.\n\n"
                f"Technical details: {str(e)}"
            )
    
    def _export_insole(self):
        """Export the adapted insole as STL."""
        if self.processor.insole_mesh is None:
            QMessageBox.warning(self, "Warning", "No insole loaded to export.")
            return
        
        # Generate filename
        if self.auto_filename_check.isChecked():
            name = self.name_input.text().strip() or "unnamed"
            side = "L" if "L" in self.side_combo.currentText() else "R"
            date = self.date_input.text().strip() or datetime.now().strftime("%Y-%m-%d")
            
            suggested_name = self.processor.generate_filename(name, side, date)
        else:
            suggested_name = "insole_adapted.stl"
        
        # Get save path
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Insole STL",
            os.path.join(self.last_directory, suggested_name),
            "STL Files (*.stl);;All Files (*.*)"
        )
        
        if filepath:
            try:
                self.status_bar.showMessage("Exporting...")
                QApplication.processEvents()
                
                saved_path = self.processor.save_stl(filepath)
                
                self.last_directory = os.path.dirname(saved_path)
                self.settings.setValue('last_directory', self.last_directory)
                
                self.status_bar.showMessage(f"Exported: {saved_path}", 10000)
                
                QMessageBox.information(
                    self,
                    "Export Complete",
                    f"Insole exported successfully!\n\nFile: {saved_path}"
                )
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export:\n{str(e)}")
                self.status_bar.showMessage("Export failed")
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About 3D Insole Adapter",
            "<h2>3D Insole Adapter</h2>"
            "<p>Version 1.0.0</p>"
            "<p>A Windows application for adapting predefined insole STL files "
            "to 3D foot scans.</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Load foot and insole STL files</li>"
            "<li>Place reference points for measurements</li>"
            "<li>Auto-scale insole to foot dimensions</li>"
            "<li>Mirror for left/right feet</li>"
            "<li>Add text labels</li>"
            "<li>Export adapted insole</li>"
            "</ul>"
            "<p>Built with Python, PySide6, and Trimesh</p>"
        )
    
    def _show_help(self):
        """Show help/instructions dialog."""
        QMessageBox.information(
            self,
            "Instructions",
            "<h3>Quick Start Guide</h3>"
            "<ol>"
            "<li><b>Load Foot STL:</b> Load the 3D scan of the patient's foot</li>"
            "<li><b>Load Insole STL:</b> Load your predefined insole template</li>"
            "<li><b>Place Reference Points:</b><br>"
            "   - Click 'Start Picking Points'<br>"
            "   - Click on the heel (back center)<br>"
            "   - Click on 1st metatarsal (big toe joint)<br>"
            "   - Click on 5th metatarsal (pinky toe joint)</li>"
            "<li><b>Scale Insole:</b> Click 'Auto Scale to Foot' or adjust manually</li>"
            "<li><b>Mirror if Needed:</b> Click 'Mirror Y' to flip left/right</li>"
            "<li><b>Add Label:</b> Enter name, side, date and click 'Apply Label'</li>"
            "<li><b>Export:</b> Click 'Export Adapted Insole as STL'</li>"
            "</ol>"
            "<p><b>View Controls:</b></p>"
            "<ul>"
            "<li>Left-drag: Rotate view</li>"
            "<li>Right-drag: Pan view</li>"
            "<li>Scroll wheel: Zoom</li>"
            "<li>R: Reset view | T: Top view | F: Front view | I: Isometric</li>"
            "</ul>"
        )
    
    def closeEvent(self, event):
        """Handle window close - save settings."""
        self.settings.setValue('geometry', self.saveGeometry())
        event.accept()


def main():
    """Application entry point."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    
    # Set application info
    app.setApplicationName("3D Insole Adapter")
    app.setOrganizationName("InsoleAdapter")
    app.setApplicationVersion("1.0.0")
    
    # Set style
    app.setStyle("Fusion")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
