"""
3D STL Insole Adapter - Main Application
=========================================
A Windows desktop application for adapting predefined insole STL files
to 3D foot STL models.

Features:
- Load foot and insole STL files
- Place 3 reference points on foot (heel, 1st metatarsal, 5th metatarsal)
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
        self.load_foot_btn.clicked.connect(self._open_foot_stl)
        file_layout.addWidget(self.load_foot_btn, 0, 2)
        
        # Insole STL
        file_layout.addWidget(QLabel("Insole STL:"), 1, 0)
        self.insole_path_label = QLabel("No file loaded")
        self.insole_path_label.setStyleSheet("color: gray; font-style: italic;")
        self.insole_path_label.setWordWrap(True)
        file_layout.addWidget(self.insole_path_label, 1, 1)
        
        self.load_insole_btn = QPushButton("Load Insole")
        self.load_insole_btn.clicked.connect(self._open_insole_stl)
        file_layout.addWidget(self.load_insole_btn, 1, 2)
        
        layout.addWidget(file_group)
        
        # === Reference Points Group ===
        ref_group = QGroupBox("Reference Points")
        ref_layout = QVBoxLayout(ref_group)
        
        ref_info = QLabel(
            "Place 3 points on the foot:\n"
            "1. Heel (back center)\n"
            "2. 1st Metatarsal (big toe joint)\n"
            "3. 5th Metatarsal (pinky toe joint)"
        )
        ref_info.setStyleSheet("color: #666;")
        ref_layout.addWidget(ref_info)
        
        ref_btn_layout = QHBoxLayout()
        
        self.start_picking_btn = QPushButton("Start Picking Points")
        self.start_picking_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        self.start_picking_btn.clicked.connect(self._start_picking)
        ref_btn_layout.addWidget(self.start_picking_btn)
        
        self.clear_points_btn = QPushButton("Clear Points")
        self.clear_points_btn.clicked.connect(self._clear_points)
        ref_btn_layout.addWidget(self.clear_points_btn)
        
        ref_layout.addLayout(ref_btn_layout)
        
        # Point status display
        self.point_status_label = QLabel("Points: 0/3")
        ref_layout.addWidget(self.point_status_label)
        
        # Calculated dimensions
        self.dimensions_label = QLabel("Foot dimensions: --")
        ref_layout.addWidget(self.dimensions_label)
        
        # Align button
        self.align_insole_btn = QPushButton("Align Insole to Foot")
        self.align_insole_btn.setStyleSheet("background-color: #9C27B0; color: white; padding: 6px;")
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
        
        # Foot uniform scale (scales both foot and linked insole)
        scale_layout.addWidget(QLabel("Foot Scale:"), 0, 0)
        self.foot_scale_slider = NoWheelSlider(Qt.Orientation.Horizontal)
        self.foot_scale_slider.setRange(50, 150)  # 50% to 150%
        self.foot_scale_slider.setValue(100)
        self.foot_scale_slider.valueChanged.connect(self._on_foot_scale_changed)
        scale_layout.addWidget(self.foot_scale_slider, 0, 1)
        self.foot_scale_label = QLabel("100%")
        self.foot_scale_label.setFixedWidth(45)
        scale_layout.addWidget(self.foot_scale_label, 0, 2)
        
        # Foot scale info
        foot_scale_info = QLabel("(Scales foot + linked insole)")
        foot_scale_info.setStyleSheet("color: #666; font-size: 10px;")
        scale_layout.addWidget(foot_scale_info, 1, 0, 1, 3)
        
        # Current insole dimensions
        scale_layout.addWidget(QLabel("Current Insole Size:"), 2, 0, 1, 2)
        self.current_dims_label = QLabel("X: -- mm  Y: -- mm  Z: -- mm")
        self.current_dims_label.setStyleSheet("font-family: monospace;")
        scale_layout.addWidget(self.current_dims_label, 3, 0, 1, 3)
        
        # Auto scale button
        self.auto_scale_btn = QPushButton("Auto Scale to Foot")
        self.auto_scale_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
        self.auto_scale_btn.clicked.connect(self._auto_scale)
        scale_layout.addWidget(self.auto_scale_btn, 4, 0, 1, 3)
        
        # Manual scale inputs for insole
        scale_layout.addWidget(QLabel("Insole Scale X:"), 5, 0)
        self.scale_x_spin = QDoubleSpinBox()
        self.scale_x_spin.setRange(0.1, 10.0)
        self.scale_x_spin.setValue(1.0)
        self.scale_x_spin.setSingleStep(0.05)
        self.scale_x_spin.setDecimals(3)
        scale_layout.addWidget(self.scale_x_spin, 5, 1)
        
        scale_layout.addWidget(QLabel("Insole Scale Y:"), 6, 0)
        self.scale_y_spin = QDoubleSpinBox()
        self.scale_y_spin.setRange(0.1, 10.0)
        self.scale_y_spin.setValue(1.0)
        self.scale_y_spin.setSingleStep(0.05)
        self.scale_y_spin.setDecimals(3)
        scale_layout.addWidget(self.scale_y_spin, 6, 1)
        
        scale_layout.addWidget(QLabel("Insole Scale Z:"), 7, 0)
        self.scale_z_spin = QDoubleSpinBox()
        self.scale_z_spin.setRange(0.1, 10.0)
        self.scale_z_spin.setValue(1.0)
        self.scale_z_spin.setSingleStep(0.05)
        self.scale_z_spin.setDecimals(3)
        scale_layout.addWidget(self.scale_z_spin, 7, 1)
        
        self.apply_scale_btn = QPushButton("Apply Insole Scale")
        self.apply_scale_btn.clicked.connect(self._apply_manual_scale)
        scale_layout.addWidget(self.apply_scale_btn, 8, 0, 1, 2)
        
        self.reset_insole_btn = QPushButton("Reset Insole")
        self.reset_insole_btn.clicked.connect(self._reset_insole)
        scale_layout.addWidget(self.reset_insole_btn, 8, 2)
        
        layout.addWidget(scale_group)
        
        # === Mirror Group ===
        mirror_group = QGroupBox("Mirror (Left/Right)")
        mirror_layout = QHBoxLayout(mirror_group)
        
        self.mirror_x_btn = QPushButton("Mirror X")
        self.mirror_x_btn.clicked.connect(lambda: self._mirror('x'))
        mirror_layout.addWidget(self.mirror_x_btn)
        
        self.mirror_y_btn = QPushButton("Mirror Y (L↔R)")
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
        self.translate_x_slider.setRange(-200, 200)
        self.translate_x_slider.setValue(0)
        self.translate_x_slider.valueChanged.connect(self._on_position_changed)
        position_layout.addWidget(self.translate_x_slider, 1, 1)
        self.translate_x_label = QLabel("0")
        self.translate_x_label.setFixedWidth(35)
        position_layout.addWidget(self.translate_x_label, 1, 2)
        
        position_layout.addWidget(QLabel("Y:"), 2, 0)
        self.translate_y_slider = NoWheelSlider(Qt.Orientation.Horizontal)
        self.translate_y_slider.setRange(-200, 200)
        self.translate_y_slider.setValue(0)
        self.translate_y_slider.valueChanged.connect(self._on_position_changed)
        position_layout.addWidget(self.translate_y_slider, 2, 1)
        self.translate_y_label = QLabel("0")
        self.translate_y_label.setFixedWidth(35)
        position_layout.addWidget(self.translate_y_label, 2, 2)
        
        position_layout.addWidget(QLabel("Z:"), 3, 0)
        self.translate_z_slider = NoWheelSlider(Qt.Orientation.Horizontal)
        self.translate_z_slider.setRange(-200, 200)
        self.translate_z_slider.setValue(0)
        self.translate_z_slider.valueChanged.connect(self._on_position_changed)
        position_layout.addWidget(self.translate_z_slider, 3, 1)
        self.translate_z_label = QLabel("0")
        self.translate_z_label.setFixedWidth(35)
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
        # Point picking signal
        self.viewer.point_picked.connect(self._on_point_picked)
        # Label position picking signal
        self.viewer.label_point_picked.connect(self._on_label_point_picked)
    
    def _on_position_changed(self):
        """Handle position/rotation slider changes."""
        if self.processor.insole_mesh is None:
            return
        
        # Update labels
        tx = self.translate_x_slider.value()
        ty = self.translate_y_slider.value()
        tz = self.translate_z_slider.value()
        rx = self.rotate_x_slider.value()
        ry = self.rotate_y_slider.value()
        rz = self.rotate_z_slider.value()
        
        self.translate_x_label.setText(str(tx))
        self.translate_y_label.setText(str(ty))
        self.translate_z_label.setText(str(tz))
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
        mesh_copy.vertices += np.array([tx, ty, tz])
        
        # Update processor and viewer
        self.processor.insole_mesh = mesh_copy
        self.viewer.set_insole_mesh(mesh_copy)
    
    def _reset_position_sliders_ui_only(self):
        """Reset all position/rotation sliders to zero (UI only, no mesh update)."""
        # Block signals to avoid triggering position changes
        for slider in [self.translate_x_slider, self.translate_y_slider, self.translate_z_slider,
                       self.rotate_x_slider, self.rotate_y_slider, self.rotate_z_slider]:
            slider.blockSignals(True)
            slider.setValue(0)
            slider.blockSignals(False)
        
        # Update labels
        for label in [self.translate_x_label, self.translate_y_label, self.translate_z_label,
                      self.rotate_x_label, self.rotate_y_label, self.rotate_z_label]:
            label.setText("0")
    
    def _reset_position_sliders(self):
        """Reset all position/rotation sliders to zero and reset mesh position."""
        # Reset slider UI
        self._reset_position_sliders_ui_only()
        
        # Reset insole to original position
        if self.processor.original_insole_mesh is not None:
            self.processor.insole_mesh = self.processor.original_insole_mesh.copy()
            self.viewer.set_insole_mesh(self.processor.insole_mesh)
            self.status_bar.showMessage("Insole position reset")
    
    def _update_ui_state(self):
        """Update UI element enabled states based on current state."""
        has_foot = self.processor.foot_mesh is not None
        has_insole = self.processor.insole_mesh is not None
        has_points = len(self.processor.reference_points) == 3
        
        # Reference points require foot
        self.start_picking_btn.setEnabled(has_foot)
        self.clear_points_btn.setEnabled(len(self.viewer.reference_points) > 0)
        
        # Align requires foot, insole, and 3 points
        self.align_insole_btn.setEnabled(has_foot and has_insole and has_points)
        
        # Foot scale slider requires foot
        self.foot_scale_slider.setEnabled(has_foot)
        
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
        
        # Update point count
        point_count = len(self.viewer.reference_points)
        self.point_status_label.setText(f"Points: {point_count}/3")
        
        if point_count == 3:
            self.point_status_label.setStyleSheet("color: green; font-weight: bold;")
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
                
                # Reset foot scale slider
                self.foot_scale_slider.blockSignals(True)
                self.foot_scale_slider.setValue(100)
                self.foot_scale_slider.blockSignals(False)
                self.foot_scale_label.setText("100%")
                self._original_foot_mesh = None
                self._foot_scale_base = 100
                
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
            
            # Detect if foot is left or right
            foot_side = self.processor.detect_foot_side()
            
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
        self.status_bar.showMessage("Click on the foot to place reference points (Heel first)")
        
        self.start_picking_btn.setText("Picking... (ESC to cancel)")
        self.start_picking_btn.setStyleSheet("background-color: #FF9800; color: white;")
    
    def _on_point_picked(self, point):
        """Handle point picked from viewer."""
        point_count = len(self.viewer.reference_points)
        
        if point_count == 1:
            self.status_bar.showMessage("Heel placed. Now click on the 1st Metatarsal (big toe joint)")
        elif point_count == 2:
            self.status_bar.showMessage("1st Metatarsal placed. Now click on the 5th Metatarsal (pinky toe joint)")
        elif point_count == 3:
            self.status_bar.showMessage("All reference points placed!")
            self.start_picking_btn.setText("Start Picking Points")
            self.start_picking_btn.setStyleSheet("background-color: #4CAF50; color: white;")
            
            # Set points in processor
            self.processor.set_reference_points(self.viewer.reference_points)
            
            # Calculate and display dimensions
            try:
                length, width = self.processor.calculate_foot_dimensions()
                self.dimensions_label.setText(f"Foot: Length={length:.1f}mm, Width={width:.1f}mm")
                self.dimensions_label.setStyleSheet("color: green;")
            except Exception as e:
                self.dimensions_label.setText(f"Error calculating dimensions: {e}")
        
        self._update_ui_state()
    
    def _clear_points(self):
        """Clear all reference points."""
        self.viewer.clear_reference_points()
        self.processor.reference_points = []
        self.viewer.set_picking_mode(False)
        
        self.start_picking_btn.setText("Start Picking Points")
        self.start_picking_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        
        self.dimensions_label.setText("Foot dimensions: --")
        self.dimensions_label.setStyleSheet("")
        
        self._update_ui_state()
        self.status_bar.showMessage("Reference points cleared")
    
    def _align_insole(self):
        """Align the insole to the foot using reference points."""
        if len(self.processor.reference_points) != 3:
            QMessageBox.warning(self, "Warning", "Please set all 3 reference points first.")
            return
        
        if self.processor.insole_mesh is None:
            QMessageBox.warning(self, "Warning", "Please load an insole first.")
            return
        
        try:
            # Align insole to foot (this also links them)
            self.processor.align_insole_to_foot()
            
            # Update viewer
            self.viewer.set_insole_mesh(self.processor.insole_mesh)
            
            # Update link status
            self._update_link_status()
            
            self.status_bar.showMessage("Insole aligned and linked to foot")
            self._update_ui_state()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to align insole:\n{str(e)}")
    
    def _auto_scale(self):
        """Automatically scale insole to match foot dimensions."""
        if len(self.processor.reference_points) != 3:
            QMessageBox.warning(self, "Warning", "Please set all 3 reference points first.")
            return
        
        try:
            # Calculate target dimensions from reference points
            length, width = self.processor.calculate_foot_dimensions()
            
            # Add some margin (optional, can be adjusted)
            margin = 1.05  # 5% larger than measured
            target_length = length * margin
            target_width = width * margin
            
            # Get Z scale if checkbox or spin value indicates custom Z
            z_scale = self.scale_z_spin.value() if self.scale_z_spin.value() != 1.0 else None
            
            # Apply auto scaling
            scale_x, scale_y, scale_z = self.processor.auto_scale_insole(
                target_length, target_width, z_scale
            )
            
            # Update viewer
            self.viewer.set_insole_mesh(self.processor.insole_mesh)
            
            # Update scale spinboxes to reflect applied scale
            self.scale_x_spin.setValue(scale_x)
            self.scale_y_spin.setValue(scale_y)
            self.scale_z_spin.setValue(scale_z)
            
            self.status_bar.showMessage(
                f"Auto-scaled: X={scale_x:.3f}, Y={scale_y:.3f}, Z={scale_z:.3f}"
            )
            self._update_ui_state()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to auto-scale:\n{str(e)}")
    
    def _apply_manual_scale(self):
        """Apply manual scale factors to insole."""
        try:
            # Reset to original first to get consistent results
            self.processor.reset_insole()
            
            # Apply scale
            scale_x = self.scale_x_spin.value()
            scale_y = self.scale_y_spin.value()
            scale_z = self.scale_z_spin.value()
            
            self.processor.scale_insole(scale_x, scale_y, scale_z)
            
            # Update viewer
            self.viewer.set_insole_mesh(self.processor.insole_mesh)
            
            self.status_bar.showMessage(
                f"Manual scale applied: X={scale_x:.3f}, Y={scale_y:.3f}, Z={scale_z:.3f}"
            )
            self._update_ui_state()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply scale:\n{str(e)}")
    
    def _reset_insole(self):
        """Reset insole to original loaded state."""
        try:
            mesh = self.processor.reset_insole()
            if mesh is not None:
                self.viewer.set_insole_mesh(mesh)
                
                # Reset scale spinboxes
                self.scale_x_spin.setValue(1.0)
                self.scale_y_spin.setValue(1.0)
                self.scale_z_spin.setValue(1.0)
                
                # Reset position sliders
                self._reset_position_sliders()
                
                self.status_bar.showMessage("Insole reset to original state")
                self._update_ui_state()
            else:
                QMessageBox.warning(self, "Warning", "No original insole to reset to.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to reset insole:\n{str(e)}")
    
    def _mirror(self, axis: str):
        """Mirror the insole along specified axis."""
        try:
            self.processor.mirror_insole(axis)
            self.viewer.set_insole_mesh(self.processor.insole_mesh)
            
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
