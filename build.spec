# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File for Orthosis Customizer
==============================================
Creates a standalone Windows executable with all dependencies bundled.
No Python or development environment required to run.

Build with: pyinstaller build.spec --clean
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_all

block_cipher = None

# Collect all required data files and submodules
trimesh_datas, trimesh_binaries, trimesh_hiddenimports = collect_all('trimesh')
shapely_datas, shapely_binaries, shapely_hiddenimports = collect_all('shapely')
vtk_datas, vtk_binaries, vtk_hiddenimports = collect_all('vtk')
matplotlib_datas = collect_data_files('matplotlib')

# Collect OpenCV
try:
    cv2_datas, cv2_binaries, cv2_hiddenimports = collect_all('cv2')
except:
    cv2_datas, cv2_binaries, cv2_hiddenimports = [], [], []

# Collect Pillow
try:
    pil_datas, pil_binaries, pil_hiddenimports = collect_all('PIL')
except:
    pil_datas, pil_binaries, pil_hiddenimports = [], [], []

# Try to collect MeshLib if available
try:
    meshlib_datas, meshlib_binaries, meshlib_hiddenimports = collect_all('meshlib')
except:
    meshlib_datas, meshlib_binaries, meshlib_hiddenimports = [], [], []

# Try to collect manifold3d if available  
try:
    manifold_datas, manifold_binaries, manifold_hiddenimports = collect_all('manifold3d')
except:
    manifold_datas, manifold_binaries, manifold_hiddenimports = [], [], []

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[
        *vtk_binaries,
        *shapely_binaries,
        *cv2_binaries,
        *pil_binaries,
        *meshlib_binaries,
        *manifold_binaries,
    ],
    datas=[
        *trimesh_datas,
        *shapely_datas,
        *vtk_datas,
        *matplotlib_datas,
        *meshlib_datas,
        *manifold_datas,
        *cv2_datas,
        *pil_datas,
        # Include documentation
        ('docs', 'docs'),
        # Include logos directory
        ('logos', 'logos'),
    ],
    hiddenimports=[
        # Trimesh and dependencies
        *trimesh_hiddenimports,
        'trimesh.exchange.stl',
        'trimesh.exchange.load',
        'trimesh.creation',
        'trimesh.transformations',
        'trimesh.util',
        'trimesh.geometry',
        'trimesh.proximity',
        'trimesh.ray',
        'trimesh.ray.ray_triangle',
        
        # VTK
        *vtk_hiddenimports,
        'vtkmodules',
        'vtkmodules.all',
        'vtkmodules.qt',
        'vtkmodules.qt.QVTKRenderWindowInteractor',
        'vtkmodules.util',
        'vtkmodules.util.numpy_support',
        
        # Shapely
        *shapely_hiddenimports,
        'shapely',
        'shapely.geometry',
        'shapely.ops',
        'shapely.validation',
        
        # Scientific computing
        'numpy',
        'numpy.core._methods',
        'numpy.lib.format',
        'scipy',
        'scipy.spatial',
        'scipy.spatial.transform',
        'scipy.sparse',
        
        # Network/graph
        'networkx',
        
        # Qt/PySide6
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui', 
        'PySide6.QtWidgets',
        'PySide6.QtOpenGL',
        'PySide6.QtOpenGLWidgets',
        
        # Matplotlib for font rendering
        'matplotlib',
        'matplotlib.font_manager',
        'matplotlib.textpath',
        'matplotlib.path',
        
        # Polygon triangulation
        'mapbox_earcut',
        
        # Boolean operations
        *meshlib_hiddenimports,
        *manifold_hiddenimports,
        
        # Image processing for logo extraction
        *cv2_hiddenimports,
        'cv2',
        *pil_hiddenimports,
        'PIL',
        'PIL.Image',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary packages to reduce size
        'tkinter',
        '_tkinter',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'sphinx',
    ],
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
    name='OrthosisCustomizer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Windowed application (no console)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
