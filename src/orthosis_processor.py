"""
Orthosis Processor Module
=========================
Handles all orthosis STL file operations including:
- Loading and saving STL files
- Mirroring meshes (left/right automatic generation)
- Loading and positioning logos
- Adding text labels/engravings to meshes
- Edge distance checking for safe placement
- Dual export (Left and Right versions)

Uses trimesh library for mesh operations.
"""

import numpy as np
import trimesh
from typing import Tuple, Optional, List
import os
from concurrent.futures import ThreadPoolExecutor, as_completed


# Define simple 3D letter shapes as 2D polygons (to be extruded)
# Each letter is defined as a list of polygons (for letters with holes like O, A, etc.)
# Coordinates are normalized to a 1x1 bounding box
LETTER_PATHS = {
    'A': [[(0, 0), (0.5, 1), (1, 0), (0.75, 0), (0.625, 0.25), (0.375, 0.25), (0.25, 0), (0, 0)],
          [(0.5, 0.75), (0.4, 0.5), (0.6, 0.5), (0.5, 0.75)]],  # hole
    'B': [[(0, 0), (0, 1), (0.6, 1), (0.8, 0.85), (0.8, 0.65), (0.6, 0.5), (0.8, 0.35), (0.8, 0.15), (0.6, 0), (0, 0)],
          [(0.2, 0.2), (0.5, 0.2), (0.5, 0.4), (0.2, 0.4)],  # lower hole
          [(0.2, 0.6), (0.5, 0.6), (0.5, 0.8), (0.2, 0.8)]],  # upper hole
    'C': [[(0.8, 0.2), (0.6, 0), (0.2, 0), (0, 0.2), (0, 0.8), (0.2, 1), (0.6, 1), (0.8, 0.8),
           (0.6, 0.8), (0.5, 0.85), (0.3, 0.85), (0.2, 0.75), (0.2, 0.25), (0.3, 0.15), (0.5, 0.15), (0.6, 0.2), (0.8, 0.2)]],
    'D': [[(0, 0), (0, 1), (0.5, 1), (0.8, 0.8), (0.8, 0.2), (0.5, 0), (0, 0)],
          [(0.2, 0.2), (0.4, 0.2), (0.55, 0.35), (0.55, 0.65), (0.4, 0.8), (0.2, 0.8)]],  # hole
    'E': [[(0, 0), (0, 1), (0.8, 1), (0.8, 0.8), (0.2, 0.8), (0.2, 0.6), (0.6, 0.6), (0.6, 0.4), (0.2, 0.4), (0.2, 0.2), (0.8, 0.2), (0.8, 0), (0, 0)]],
    'F': [[(0, 0), (0, 1), (0.8, 1), (0.8, 0.8), (0.2, 0.8), (0.2, 0.55), (0.6, 0.55), (0.6, 0.35), (0.2, 0.35), (0.2, 0), (0, 0)]],
    'G': [[(0.8, 0.3), (0.5, 0.3), (0.5, 0.5), (0.6, 0.5), (0.6, 0.2), (0.4, 0.15), (0.2, 0.25), (0.15, 0.5), (0.2, 0.75), (0.4, 0.85), (0.7, 0.85), (0.8, 0.7), (0.6, 0.7), (0.55, 0.75), (0.35, 0.75), (0.25, 0.65), (0.25, 0.35), (0.35, 0.25), (0.8, 0.25), (0.8, 0.3)]],
    'H': [[(0, 0), (0, 1), (0.2, 1), (0.2, 0.6), (0.6, 0.6), (0.6, 1), (0.8, 1), (0.8, 0), (0.6, 0), (0.6, 0.4), (0.2, 0.4), (0.2, 0), (0, 0)]],
    'I': [[(0.3, 0), (0.3, 1), (0.7, 1), (0.7, 0), (0.3, 0)]],
    'J': [[(0.2, 0.3), (0.3, 0.15), (0.5, 0.15), (0.55, 0.3), (0.55, 1), (0.75, 1), (0.75, 0.25), (0.6, 0), (0.2, 0), (0.05, 0.2), (0.2, 0.3)]],
    'K': [[(0, 0), (0, 1), (0.2, 1), (0.2, 0.6), (0.6, 1), (0.85, 1), (0.4, 0.5), (0.85, 0), (0.6, 0), (0.2, 0.4), (0.2, 0), (0, 0)]],
    'L': [[(0, 0), (0, 1), (0.2, 1), (0.2, 0.2), (0.8, 0.2), (0.8, 0), (0, 0)]],
    'M': [[(0, 0), (0, 1), (0.2, 1), (0.5, 0.5), (0.8, 1), (1, 1), (1, 0), (0.8, 0), (0.8, 0.6), (0.5, 0.2), (0.2, 0.6), (0.2, 0), (0, 0)]],
    'N': [[(0, 0), (0, 1), (0.2, 1), (0.6, 0.4), (0.6, 1), (0.8, 1), (0.8, 0), (0.6, 0), (0.2, 0.6), (0.2, 0), (0, 0)]],
    'O': [[(0.2, 0), (0, 0.2), (0, 0.8), (0.2, 1), (0.6, 1), (0.8, 0.8), (0.8, 0.2), (0.6, 0), (0.2, 0)],
          [(0.3, 0.2), (0.5, 0.2), (0.6, 0.3), (0.6, 0.7), (0.5, 0.8), (0.3, 0.8), (0.2, 0.7), (0.2, 0.3), (0.3, 0.2)]],  # hole
    'P': [[(0, 0), (0, 1), (0.6, 1), (0.8, 0.85), (0.8, 0.55), (0.6, 0.4), (0.2, 0.4), (0.2, 0), (0, 0)],
          [(0.2, 0.55), (0.5, 0.55), (0.55, 0.65), (0.55, 0.75), (0.5, 0.85), (0.2, 0.85)]],  # hole
    'Q': [[(0.2, 0), (0, 0.2), (0, 0.8), (0.2, 1), (0.6, 1), (0.8, 0.8), (0.8, 0.3), (0.9, 0.1), (1, 0), (0.7, 0), (0.6, 0.15), (0.2, 0)],
          [(0.3, 0.2), (0.5, 0.2), (0.6, 0.3), (0.6, 0.7), (0.5, 0.8), (0.3, 0.8), (0.2, 0.7), (0.2, 0.3), (0.3, 0.2)]],  # hole
    'R': [[(0, 0), (0, 1), (0.6, 1), (0.8, 0.85), (0.8, 0.55), (0.6, 0.4), (0.8, 0), (0.55, 0), (0.4, 0.4), (0.2, 0.4), (0.2, 0), (0, 0)],
          [(0.2, 0.55), (0.5, 0.55), (0.55, 0.65), (0.55, 0.75), (0.5, 0.85), (0.2, 0.85)]],  # hole
    'S': [[(0.1, 0.15), (0.3, 0), (0.7, 0), (0.85, 0.15), (0.85, 0.4), (0.2, 0.55), (0.2, 0.7), (0.6, 0.8), (0.6, 0.85), (0.1, 0.85), (0.1, 0.7), (0.35, 0.7), (0.35, 0.65), (0.7, 0.55), (0.65, 0.4), (0.65, 0.2), (0.55, 0.15), (0.35, 0.15), (0.3, 0.2), (0.3, 0.3), (0.1, 0.3), (0.1, 0.15)]],
    'T': [[(0, 0.8), (0, 1), (1, 1), (1, 0.8), (0.6, 0.8), (0.6, 0), (0.4, 0), (0.4, 0.8), (0, 0.8)]],
    'U': [[(0, 0.3), (0, 1), (0.2, 1), (0.2, 0.3), (0.3, 0.15), (0.5, 0.15), (0.6, 0.3), (0.6, 1), (0.8, 1), (0.8, 0.3), (0.65, 0), (0.15, 0), (0, 0.3)]],
    'V': [[(0, 1), (0.25, 1), (0.5, 0.3), (0.75, 1), (1, 1), (0.6, 0), (0.4, 0), (0, 1)]],
    'W': [[(0, 1), (0.2, 1), (0.35, 0.3), (0.5, 0.7), (0.65, 0.3), (0.8, 1), (1, 1), (0.75, 0), (0.55, 0), (0.5, 0.25), (0.45, 0), (0.25, 0), (0, 1)]],
    'X': [[(0, 0), (0.35, 0.45), (0, 1), (0.25, 1), (0.5, 0.6), (0.75, 1), (1, 1), (0.65, 0.45), (1, 0), (0.75, 0), (0.5, 0.35), (0.25, 0), (0, 0)]],
    'Y': [[(0, 1), (0.25, 1), (0.5, 0.55), (0.75, 1), (1, 1), (0.6, 0.4), (0.6, 0), (0.4, 0), (0.4, 0.4), (0, 1)]],
    'Z': [[(0, 0), (0, 0.2), (0.55, 0.8), (0, 0.8), (0, 1), (1, 1), (1, 0.8), (0.45, 0.2), (1, 0.2), (1, 0), (0, 0)]],
    '0': [[(0.2, 0), (0, 0.2), (0, 0.8), (0.2, 1), (0.6, 1), (0.8, 0.8), (0.8, 0.2), (0.6, 0), (0.2, 0)],
          [(0.3, 0.2), (0.5, 0.2), (0.6, 0.3), (0.6, 0.7), (0.5, 0.8), (0.3, 0.8), (0.2, 0.7), (0.2, 0.3), (0.3, 0.2)]],
    '1': [[(0.2, 0), (0.2, 0.2), (0.4, 0.2), (0.4, 0.8), (0.2, 0.7), (0.2, 0.9), (0.6, 1), (0.6, 0.2), (0.8, 0.2), (0.8, 0), (0.2, 0)]],
    '2': [[(0, 0), (0, 0.2), (0.5, 0.55), (0.2, 0.7), (0.2, 0.85), (0.35, 1), (0.65, 1), (0.8, 0.85), (0.8, 0.6), (0.6, 0.4), (0.25, 0.2), (0.8, 0.2), (0.8, 0), (0, 0)]],
    '3': [[(0.1, 0.15), (0.3, 0), (0.7, 0), (0.85, 0.15), (0.85, 0.4), (0.7, 0.5), (0.85, 0.6), (0.85, 0.85), (0.7, 1), (0.3, 1), (0.1, 0.85), (0.1, 0.7), (0.3, 0.85), (0.55, 0.85), (0.6, 0.7), (0.6, 0.6), (0.4, 0.55), (0.4, 0.45), (0.6, 0.4), (0.6, 0.25), (0.55, 0.15), (0.3, 0.15), (0.1, 0.3), (0.1, 0.15)]],
    '4': [[(0.5, 0), (0.5, 0.35), (0, 0.35), (0, 0.55), (0.5, 1), (0.7, 1), (0.7, 0.55), (0.85, 0.55), (0.85, 0.35), (0.7, 0.35), (0.7, 0), (0.5, 0)],
          [(0.5, 0.55), (0.25, 0.55), (0.5, 0.8)]],  # cutout
    '5': [[(0.1, 0.15), (0.3, 0), (0.7, 0), (0.85, 0.15), (0.85, 0.45), (0.7, 0.6), (0.25, 0.6), (0.25, 0.8), (0.8, 0.8), (0.8, 1), (0.1, 1), (0.1, 0.5), (0.6, 0.5), (0.6, 0.25), (0.55, 0.15), (0.3, 0.15), (0.25, 0.25), (0.1, 0.25), (0.1, 0.15)]],
    '6': [[(0.35, 0), (0.15, 0.15), (0.1, 0.5), (0.15, 0.85), (0.35, 1), (0.5, 1), (0.3, 0.7), (0.65, 0.6), (0.85, 0.45), (0.85, 0.15), (0.65, 0), (0.35, 0)],
          [(0.35, 0.2), (0.5, 0.2), (0.6, 0.3), (0.6, 0.4), (0.5, 0.5), (0.35, 0.5), (0.25, 0.4), (0.25, 0.3), (0.35, 0.2)]],
    '7': [[(0.1, 0.8), (0.1, 1), (0.9, 1), (0.9, 0.8), (0.5, 0), (0.3, 0), (0.65, 0.8), (0.1, 0.8)]],
    '8': [[(0.25, 0), (0.1, 0.15), (0.1, 0.4), (0.25, 0.5), (0.1, 0.6), (0.1, 0.85), (0.25, 1), (0.75, 1), (0.9, 0.85), (0.9, 0.6), (0.75, 0.5), (0.9, 0.4), (0.9, 0.15), (0.75, 0), (0.25, 0)],
          [(0.35, 0.15), (0.65, 0.15), (0.7, 0.25), (0.7, 0.35), (0.55, 0.45), (0.45, 0.45), (0.3, 0.35), (0.3, 0.25), (0.35, 0.15)],
          [(0.35, 0.55), (0.65, 0.55), (0.7, 0.65), (0.7, 0.8), (0.65, 0.85), (0.35, 0.85), (0.3, 0.8), (0.3, 0.65), (0.35, 0.55)]],
    '9': [[(0.5, 0), (0.7, 0.3), (0.35, 0.4), (0.15, 0.55), (0.15, 0.85), (0.35, 1), (0.65, 1), (0.85, 0.85), (0.9, 0.5), (0.85, 0.15), (0.65, 0), (0.5, 0)],
          [(0.4, 0.5), (0.65, 0.5), (0.75, 0.6), (0.75, 0.7), (0.65, 0.8), (0.4, 0.8), (0.35, 0.7), (0.35, 0.6), (0.4, 0.5)]],
    '-': [[(0.15, 0.4), (0.15, 0.6), (0.85, 0.6), (0.85, 0.4), (0.15, 0.4)]],
    '/': [[(0.1, 0), (0.3, 0), (0.9, 1), (0.7, 1), (0.1, 0)]],
    ' ': [],  # Space - empty
    '.': [[(0.35, 0), (0.35, 0.2), (0.65, 0.2), (0.65, 0), (0.35, 0)]],
    ':': [[(0.35, 0.1), (0.35, 0.3), (0.65, 0.3), (0.65, 0.1), (0.35, 0.1)],
          [(0.35, 0.7), (0.35, 0.9), (0.65, 0.9), (0.65, 0.7), (0.35, 0.7)]],
    '(': [[(0.6, 0), (0.4, 0.15), (0.3, 0.5), (0.4, 0.85), (0.6, 1), (0.75, 0.9), (0.55, 0.8), (0.45, 0.5), (0.55, 0.2), (0.75, 0.1), (0.6, 0)]],
    ')': [[(0.4, 0), (0.25, 0.1), (0.45, 0.2), (0.55, 0.5), (0.45, 0.8), (0.25, 0.9), (0.4, 1), (0.6, 0.85), (0.7, 0.5), (0.6, 0.15), (0.4, 0)]],
    '_': [[(0.1, 0), (0.1, 0.15), (0.9, 0.15), (0.9, 0), (0.1, 0)]],
}


class OrthosisProcessor:
    """
    Main class for processing orthosis STL files.
    Provides methods for loading, mirroring, engraving, and saving 3D meshes.
    """
    
    # Constants
    MIN_EDGE_DISTANCE: float = 5.0  # mm - minimum safe distance from edges
    ENGRAVE_DEPTH: float = 0.6  # mm - fixed engraving depth
    
    def __init__(self):
        """Initialize the Orthosis processor."""
        # Main orthosis mesh (the one being worked on)
        self.orthosis_mesh: Optional[trimesh.Trimesh] = None
        
        # Original orthosis as loaded (RIGHT side, never modified except by reload)
        self.orthosis_original: Optional[trimesh.Trimesh] = None
        
        # Mirrored orthosis (LEFT side, auto-generated)
        self.orthosis_mirrored: Optional[trimesh.Trimesh] = None
        
        # Logo meshes (preloaded)
        self.logo_v1: Optional[trimesh.Trimesh] = None
        self.logo_v2: Optional[trimesh.Trimesh] = None
        
        # Currently selected logo
        self.logo_mesh: Optional[trimesh.Trimesh] = None
        self.current_logo_version: int = 1
        
        # User-picked positions for logo and text
        self.logo_position: Optional[np.ndarray] = None
        self.logo_normal: Optional[np.ndarray] = None
        self.text_position: Optional[np.ndarray] = None
        self.text_normal: Optional[np.ndarray] = None
        
        # State tracking
        self.is_engraved: bool = False
        self.logo_applied: bool = False
        self.text_applied: bool = False
        
        # Store mesh before engraving for reset
        self._mesh_before_engrave: Optional[trimesh.Trimesh] = None
        
        # Pristine mesh (as loaded, never modified) for complete reset
        self._pristine_mesh: Optional[trimesh.Trimesh] = None
        
        # Mesh state after logo is applied (for text reset)
        self._mesh_after_logo: Optional[trimesh.Trimesh] = None
        self._mirrored_after_logo: Optional[trimesh.Trimesh] = None
        
        # Store last text parameters so we can reapply after logo update
        self._last_text_params: Optional[dict] = None
        
    def load_orthosis_stl(self, filepath: str) -> trimesh.Trimesh:
        """
        Load an orthosis STL file.
        
        Args:
            filepath: Path to the STL file
            
        Returns:
            Loaded mesh object
        """
        try:
            self.orthosis_mesh = trimesh.load(filepath, force='mesh')
            # Center the mesh at origin
            self.orthosis_mesh.vertices -= self.orthosis_mesh.centroid
            
            # Store as original (RIGHT side)
            self.orthosis_original = self.orthosis_mesh.copy()
            
            # Store pristine copy for reset
            self._pristine_mesh = self.orthosis_mesh.copy()
            
            # Reset state
            self.is_engraved = False
            self.logo_applied = False
            self.text_applied = False
            self.logo_position = None
            self.logo_normal = None
            self.text_position = None
            self.text_normal = None
            self._mesh_before_engrave = None
            
            return self.orthosis_mesh
        except Exception as e:
            raise ValueError(f"Failed to load orthosis STL: {str(e)}")
    
    def load_logos(self, logo_dir: str) -> None:
        """
        Load logo images (PNG/JPG) from the specified directory and convert to 3D meshes.
        Extracts dark regions from the images to create engravable logo meshes.
        
        Supported formats:
        - logo_v1.png or logo_v1.jpg
        - logo_v2.png or logo_v2.jpg
        
        Args:
            logo_dir: Directory containing logo image files
        """
        # Try to find logo files (PNG or JPG)
        logo1_path = self._find_logo_file(logo_dir, "logo_v1")
        logo2_path = self._find_logo_file(logo_dir, "logo_v2")
        
        if logo1_path:
            try:
                self.logo_v1 = self._image_to_mesh(logo1_path)
                if self.logo_v1 is not None:
                    print(f"Loaded logo_v1 from image: {len(self.logo_v1.vertices)} vertices")
            except Exception as e:
                print(f"Failed to load logo_v1: {e}")
                self.logo_v1 = None
        
        if logo2_path:
            try:
                self.logo_v2 = self._image_to_mesh(logo2_path)
                if self.logo_v2 is not None:
                    print(f"Loaded logo_v2 from image: {len(self.logo_v2.vertices)} vertices")
            except Exception as e:
                print(f"Failed to load logo_v2: {e}")
                self.logo_v2 = None
        
        # Select first available logo
        self.select_logo(1)
    
    def _find_logo_file(self, logo_dir: str, base_name: str) -> Optional[str]:
        """Find logo file with supported extensions and case variations."""
        extensions = ['.png', '.jpg', '.jpeg', '.stl']
        # Try different case variations
        name_variations = [
            base_name,                    # logo_v1
            base_name.capitalize(),       # Logo_v1
            base_name.replace('_v', '_V'), # logo_V1
            base_name.capitalize().replace('_v', '_V'), # Logo_V1
        ]
        for name in name_variations:
            for ext in extensions:
                path = os.path.join(logo_dir, name + ext)
                if os.path.exists(path):
                    return path
        return None
    
    def _image_to_mesh(self, image_path: str, logo_size_mm: float = 25.0) -> Optional[trimesh.Trimesh]:
        """
        Convert a logo image to a 3D mesh by extracting dark regions.
        
        Args:
            image_path: Path to the image file (PNG/JPG)
            logo_size_mm: Target size of the logo in mm (width)
            
        Returns:
            3D mesh of the logo, or None if conversion fails
        """
        # Check if it's an STL file (legacy support)
        if image_path.lower().endswith('.stl'):
            mesh = trimesh.load(image_path, force='mesh')
            mesh.vertices -= mesh.centroid
            return mesh
        
        try:
            from PIL import Image
            import cv2
            from shapely.geometry import Polygon, MultiPolygon
            from shapely.ops import unary_union
        except ImportError as e:
            print(f"Required libraries not available: {e}")
            return None
        
        # Load image
        img = Image.open(image_path)
        
        # Convert to RGB if necessary (handle RGBA PNG)
        if img.mode == 'RGBA':
            # Create white background for transparent areas
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Convert to numpy array
        img_array = np.array(img)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Threshold to extract dark regions (logo)
        # Dark pixels (< 128) become white (foreground), light pixels become black (background)
        _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV)
        
        # Find contours
        contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            print("No contours found in logo image")
            return None
        
        # Get image dimensions for scaling
        img_height, img_width = binary.shape
        
        # Scale factor to convert pixels to mm
        scale = logo_size_mm / max(img_width, img_height)
        
        # Process contours into polygons - KEEP ORIGINAL INDEX for hierarchy
        polygons = []
        for i, contour in enumerate(contours):
            if len(contour) < 3:
                continue
            
            # Simplify contour
            epsilon = 0.5  # Simplification tolerance in pixels
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            if len(approx) < 3:
                continue
            
            # Convert to polygon coordinates (scale and center)
            # MIRROR X axis so logo reads correctly when engraved (like a rubber stamp)
            points = []
            for pt in approx:
                x = -(pt[0][0] - img_width / 2) * scale  # NEGATIVE X to mirror horizontally
                y = (img_height / 2 - pt[0][1]) * scale  # Flip Y axis
                points.append((x, y))
            
            try:
                poly = Polygon(points)
                if poly.is_valid and poly.area > 0.1:  # Minimum area threshold
                    # Store (polygon, hierarchy_info, ORIGINAL_INDEX)
                    polygons.append((poly, hierarchy[0][i], i))
            except:
                continue
        
        if not polygons:
            print("No valid polygons created from logo contours")
            return None
        
        # Build polygon hierarchy (handle holes)
        final_polygons = self._build_polygon_hierarchy(polygons)
        
        if not final_polygons:
            print("Failed to build polygon hierarchy")
            return None
        
        # Extrude polygons to 3D mesh
        # Use large extrusion height for proper boolean cutting through curved surfaces
        extrusion_height = 30.0  # Large enough to ensure clean boolean
        meshes = []
        for poly in final_polygons:
            try:
                if isinstance(poly, MultiPolygon):
                    for p in poly.geoms:
                        if p.is_valid and p.area > 0.1:
                            m = trimesh.creation.extrude_polygon(p, height=extrusion_height, engine='earcut')
                            if m:
                                meshes.append(m)
                else:
                    if poly.is_valid and poly.area > 0.1:
                        m = trimesh.creation.extrude_polygon(poly, height=extrusion_height, engine='earcut')
                        if m:
                            meshes.append(m)
            except Exception as e:
                print(f"Failed to extrude polygon: {e}")
                continue
        
        if not meshes:
            print("No meshes created from logo")
            return None
        
        # Combine all meshes
        combined = trimesh.util.concatenate(meshes)
        combined.vertices -= combined.centroid
        
        return combined
    
    def _build_polygon_hierarchy(self, polygons_with_hierarchy: list) -> list:
        """
        Build proper polygon hierarchy with holes from OpenCV contour hierarchy.
        
        OpenCV RETR_TREE creates a hierarchy where:
        - Level 0 (parent=-1): outermost contours (solid)
        - Level 1 (parent=level0): holes in level 0
        - Level 2 (parent=level1): solid regions inside holes
        
        Args:
            polygons_with_hierarchy: List of (polygon, hierarchy_info, original_index) tuples
            
        Returns:
            List of polygons with holes properly set
        """
        from shapely.geometry import Polygon
        
        if not polygons_with_hierarchy:
            return []
        
        # Build a map from ORIGINAL contour index to polygon data
        orig_idx_map = {}
        for poly, hier, orig_idx in polygons_with_hierarchy:
            orig_idx_map[orig_idx] = {'poly': poly, 'hier': hier}
        
        # Determine level for each polygon by counting parents
        def get_level(orig_idx):
            level = 0
            current = orig_idx
            while current in orig_idx_map:
                parent = int(orig_idx_map[current]['hier'][3])
                if parent == -1:
                    break
                if parent not in orig_idx_map:
                    # Parent was filtered out - treat this as top level
                    break
                level += 1
                current = parent
            return level
        
        # Assign levels
        for orig_idx in orig_idx_map:
            orig_idx_map[orig_idx]['level'] = get_level(orig_idx)
        
        # Group by parent (using original indices)
        children_by_parent = {}
        for orig_idx, data in orig_idx_map.items():
            parent = int(data['hier'][3])
            if parent not in children_by_parent:
                children_by_parent[parent] = []
            children_by_parent[parent].append(orig_idx)
        
        # Process level 0 polygons (outermost)
        final_polygons = []
        level_0 = [idx for idx, data in orig_idx_map.items() if data['level'] == 0]
        
        for idx in level_0:
            outer = orig_idx_map[idx]['poly']
            
            # Find holes (level 1 children)
            hole_indices = [c for c in children_by_parent.get(idx, []) 
                           if c in orig_idx_map and orig_idx_map[c]['level'] == 1]
            
            if hole_indices:
                try:
                    exterior = list(outer.exterior.coords)
                    holes = []
                    
                    for hole_idx in hole_indices:
                        hole_poly = orig_idx_map[hole_idx]['poly']
                        if hole_poly.is_valid:
                            holes.append(list(hole_poly.exterior.coords))
                        
                        # Level 2 children are solid regions inside holes
                        solid_in_hole = [c for c in children_by_parent.get(hole_idx, [])
                                        if c in orig_idx_map and orig_idx_map[c]['level'] == 2]
                        for solid_idx in solid_in_hole:
                            solid_poly = orig_idx_map[solid_idx]['poly']
                            if solid_poly.is_valid and solid_poly.area > 0.1:
                                # Check for level 3 holes in this solid
                                l3_holes = [c for c in children_by_parent.get(solid_idx, [])
                                           if c in orig_idx_map and orig_idx_map[c]['level'] == 3]
                                if l3_holes:
                                    l3_hole_coords = [list(orig_idx_map[h]['poly'].exterior.coords)
                                                     for h in l3_holes if orig_idx_map[h]['poly'].is_valid]
                                    solid_with_holes = Polygon(list(solid_poly.exterior.coords), l3_hole_coords)
                                    if solid_with_holes.is_valid:
                                        final_polygons.append(solid_with_holes)
                                    else:
                                        final_polygons.append(solid_poly)
                                else:
                                    final_polygons.append(solid_poly)
                    
                    poly_with_holes = Polygon(exterior, holes)
                    if poly_with_holes.is_valid and not poly_with_holes.is_empty:
                        final_polygons.append(poly_with_holes)
                    else:
                        final_polygons.append(outer)
                except Exception as e:
                    print(f"Error creating polygon with holes: {e}")
                    final_polygons.append(outer)
            else:
                final_polygons.append(outer)
        
        return final_polygons
    
    def select_logo(self, version: int) -> None:
        """
        Select which logo version to use (1 or 2).
        
        Args:
            version: 1 or 2
        """
        self.current_logo_version = version
        if version == 1 and self.logo_v1 is not None:
            self.logo_mesh = self.logo_v1.copy()
        elif version == 2 and self.logo_v2 is not None:
            self.logo_mesh = self.logo_v2.copy()
        elif self.logo_v1 is not None:
            self.logo_mesh = self.logo_v1.copy()
        elif self.logo_v2 is not None:
            self.logo_mesh = self.logo_v2.copy()
        else:
            self.logo_mesh = None
    
    def set_logo_position(self, position: np.ndarray) -> None:
        """
        Store user-picked logo placement position.
        
        Args:
            position: 3D point on orthosis surface
        """
        self.logo_position = position.copy()
        self.logo_normal = self.get_surface_normal_at(position)
    
    def set_text_position(self, position: np.ndarray) -> None:
        """
        Store user-picked text placement position.
        
        Args:
            position: 3D point on orthosis surface
        """
        self.text_position = position.copy()
        self.text_normal = self.get_surface_normal_at(position)
    
    def get_surface_normal_at(self, position: np.ndarray) -> np.ndarray:
        """
        Get the surface normal at the given position on the orthosis.
        
        Args:
            position: 3D point near the mesh surface
            
        Returns:
            Unit normal vector pointing outward from surface
        """
        if self.orthosis_mesh is None:
            return np.array([0, 0, 1])
        
        # Find closest point on mesh surface
        closest_points, distances, face_ids = self.orthosis_mesh.nearest.on_surface([position])
        
        if len(face_ids) > 0:
            normal = self.orthosis_mesh.face_normals[face_ids[0]]
            # Ensure it points outward (away from mesh center)
            to_point = position - self.orthosis_mesh.centroid
            if np.dot(normal, to_point) < 0:
                normal = -normal
            return normal / np.linalg.norm(normal)
        
        return np.array([0, 0, 1])
    
    def check_edge_distances(self, position: np.ndarray) -> Tuple[bool, float, str]:
        """
        Check if the proposed position maintains safe distances from edges and holes.
        Uses optimized edge detection for better performance.
        
        Args:
            position: Proposed center point for logo/text
            
        Returns:
            Tuple of (is_safe, minimum_distance_mm, warning_message)
        """
        if self.orthosis_mesh is None:
            return (True, float('inf'), "")
        
        try:
            # Use trimesh's built-in boundary detection (much faster)
            # Boundary edges appear in only one face
            edges = self.orthosis_mesh.edges_sorted
            edge_face_count = np.bincount(
                self.orthosis_mesh.edges_sorted_unique_idx,
                minlength=len(self.orthosis_mesh.edges_unique)
            )
            
            # Boundary edges appear in only one face
            boundary_mask = edge_face_count == 1
            boundary_edges = self.orthosis_mesh.edges_unique[boundary_mask]
            
            if len(boundary_edges) == 0:
                return (True, float('inf'), "")
            
            # Get all boundary vertices
            boundary_vertices = np.unique(boundary_edges.flatten())
            boundary_points = self.orthosis_mesh.vertices[boundary_vertices]
            
            # Calculate distance from position to each boundary point
            distances = np.linalg.norm(boundary_points - position, axis=1)
            min_distance = float(np.min(distances))
            
            if min_distance < self.MIN_EDGE_DISTANCE:
                warning = f"Too close to edge: {min_distance:.1f}mm (minimum {self.MIN_EDGE_DISTANCE}mm required)"
                return (False, min_distance, warning)
            
            return (True, min_distance, "")
        except Exception as e:
            # If edge detection fails, allow placement (non-critical)
            print(f"Edge distance check skipped: {e}")
            return (True, float('inf'), "")
    
    def mirror_orthosis(self, mesh: trimesh.Trimesh, axis: str = 'y') -> trimesh.Trimesh:
        """
        Mirror a mesh along specified axis.
        
        Args:
            mesh: Mesh to mirror
            axis: 'x', 'y', or 'z'
            
        Returns:
            Mirrored mesh copy
        """
        mirrored = mesh.copy()
        
        if axis.lower() == 'x':
            reflection_matrix = np.array([
                [-1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1]
            ])
        elif axis.lower() == 'y':
            reflection_matrix = np.array([
                [1, 0, 0, 0],
                [0, -1, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1]
            ])
        else:  # z
            reflection_matrix = np.array([
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, -1, 0],
                [0, 0, 0, 1]
            ])
        
        mirrored.apply_transform(reflection_matrix)
        mirrored.fix_normals()
        
        return mirrored
    
    def mirror_for_dual_display(self) -> Tuple[trimesh.Trimesh, trimesh.Trimesh]:
        """
        Create both left (mirrored) and right (original) versions.
        
        Returns:
            Tuple of (left_mirrored, right_original)
        """
        if self.orthosis_mesh is None:
            raise ValueError("No orthosis loaded")
        
        # Store original as RIGHT
        self.orthosis_original = self.orthosis_mesh.copy()
        
        # Create mirrored as LEFT (mirror about Y axis only, no rotation)
        self.orthosis_mirrored = self.mirror_orthosis(self.orthosis_original, axis='y')
        
        return (self.orthosis_mirrored, self.orthosis_original)
    
    def _mirror_point(self, position: np.ndarray, axis: str = 'y') -> np.ndarray:
        """Mirror a point about the specified axis."""
        mirrored = position.copy()
        if axis.lower() == 'x':
            mirrored[0] = -mirrored[0]
        elif axis.lower() == 'y':
            mirrored[1] = -mirrored[1]
        else:
            mirrored[2] = -mirrored[2]
        return mirrored
    
    def _rotate_point_z(self, point: np.ndarray, angle_deg: float) -> np.ndarray:
        """Rotate a point around the Z axis by angle in degrees."""
        angle_rad = np.radians(angle_deg)
        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)
        x, y, z = point[0], point[1], point[2]
        return np.array([cos_a * x - sin_a * y, sin_a * x + cos_a * y, z])
    
    def apply_logo_and_text(self, patient_name: str, date: str) -> Tuple[trimesh.Trimesh, trimesh.Trimesh]:
        """
        Apply logo and text engraving to both L and R versions.
        
        Args:
            patient_name: Patient's name
            date: Manufacturing date string
            
        Returns:
            Tuple of (left_engraved, right_engraved)
        """
        if self.orthosis_original is None:
            raise ValueError("No orthosis loaded")
        if self.logo_position is None:
            raise ValueError("Logo position not set")
        if self.text_position is None:
            raise ValueError("Text position not set")
        
        # Store state before engraving
        self._mesh_before_engrave = self.orthosis_original.copy()
        
        # --- Process RIGHT version (original) ---
        right_mesh = self.orthosis_original.copy()
        
        # Apply logo to right mesh
        if self.logo_mesh is not None:
            right_mesh = self._apply_logo_to_mesh(
                right_mesh, 
                self.logo_mesh.copy(),
                self.logo_position,
                self.logo_normal
            )
        
        # Apply text to right mesh (patient name + date)
        text = f"{patient_name}\n{date}"
        right_mesh = self._apply_text_to_mesh(
            right_mesh,
            text,
            self.text_position,
            self.text_normal
        )
        
        # --- Process LEFT version (mirrored) ---
        # Mirror the original first, then apply mirrored logo/text positions
        left_mesh = self.mirror_orthosis(self.orthosis_original, axis='y')
        
        # Mirror logo position and normal
        logo_pos_mirrored = self._mirror_point(self.logo_position, 'y')
        logo_normal_mirrored = self._mirror_point(self.logo_normal, 'y')
        
        # Apply logo to left mesh
        if self.logo_mesh is not None:
            left_mesh = self._apply_logo_to_mesh(
                left_mesh,
                self.logo_mesh.copy(),
                logo_pos_mirrored,
                logo_normal_mirrored
            )
        
        # Mirror text position and normal
        text_pos_mirrored = self._mirror_point(self.text_position, 'y')
        text_normal_mirrored = self._mirror_point(self.text_normal, 'y')
        
        # Apply text to left mesh
        left_mesh = self._apply_text_to_mesh(
            left_mesh,
            text,
            text_pos_mirrored,
            text_normal_mirrored
        )
        
        # Store results
        self.orthosis_mirrored = left_mesh
        self.orthosis_original = right_mesh
        self.is_engraved = True
        
        return (left_mesh, right_mesh)
    
    def apply_logo(self, 
                   position: np.ndarray,
                   normal: np.ndarray,
                   offset_x: float = 0,
                   offset_y: float = 0,
                   rotation: float = 0,
                   scale: float = 1.0,
                   depth: float = 0.6) -> Tuple[trimesh.Trimesh, trimesh.Trimesh]:
        """
        Apply logo engraving only to both L and R versions.
        If logo was already applied, restores mesh first to prevent overlap.
        
        OPTIMIZED: Uses parallel processing for L/R sides when possible.
        
        Args:
            position: 3D position for logo placement
            normal: Surface normal at the position
            offset_x: X offset in mm
            offset_y: Y offset in mm
            rotation: Rotation angle in degrees
            scale: Scale factor (1.0 = 100%)
            depth: Engraving depth in mm (default 0.6mm)
            
        Returns:
            Tuple of (left_engraved, right_engraved)
        """
        import time
        start_time = time.perf_counter()
        
        if self._pristine_mesh is None:
            raise ValueError("No orthosis loaded")
        if self.logo_mesh is None:
            raise ValueError("No logo loaded")
        
        # Restore to pristine state before applying to avoid overlap
        self._restore_to_pristine()
        
        # Set the engrave depth for this operation
        engrave_depth = depth
        
        # Store position for export
        self.logo_position = position.copy()
        self.logo_normal = normal.copy()
        
        print(f"apply_logo: position={position}, normal={normal}")
        print(f"apply_logo: offset_x={offset_x}, offset_y={offset_y}, rotation={rotation}, scale={scale}")
        print(f"Logo mesh original bounds: {self.logo_mesh.bounds}")
        print(f"Logo mesh original size: {self.logo_mesh.bounds[1] - self.logo_mesh.bounds[0]}")
        
        # Prepare logo copies for both sides
        # RIGHT side logo
        logo_copy_right = self.logo_mesh.copy()
        if scale != 1.0:
            scale_matrix = np.diag([scale, scale, 1, 1])
            logo_copy_right.apply_transform(scale_matrix)
        if rotation != 0:
            rot_rad = np.radians(rotation)
            rot_matrix = trimesh.transformations.rotation_matrix(rot_rad, [0, 0, 1])
            logo_copy_right.apply_transform(rot_matrix)
        
        # LEFT side logo (NOT mirrored - logo should be readable)
        logo_copy_left = self.logo_mesh.copy()
        if scale != 1.0:
            scale_matrix = np.diag([scale, scale, 1, 1])
            logo_copy_left.apply_transform(scale_matrix)
        # NEGATE rotation for mirrored side
        if rotation != 0:
            rot_rad = np.radians(-rotation)
            rot_matrix = trimesh.transformations.rotation_matrix(rot_rad, [0, 0, 1])
            logo_copy_left.apply_transform(rot_matrix)
        
        # Prepare meshes and positions
        right_mesh = self.orthosis_original.copy()
        left_mesh = self.mirror_orthosis(self.orthosis_original, axis='y')
        
        offset_pos = self._apply_tangent_offset(position, normal, offset_x, offset_y)
        logo_pos_mirrored = self._mirror_point(offset_pos, 'y')
        logo_normal_mirrored = self._mirror_point(normal, 'y')
        
        # Process both sides in parallel for potential speedup
        def process_right():
            return self._apply_logo_to_mesh(
                right_mesh, 
                logo_copy_right,
                offset_pos,
                normal,
                engrave_depth
            )
        
        def process_left():
            return self._apply_logo_to_mesh(
                left_mesh,
                logo_copy_left,
                logo_pos_mirrored,
                logo_normal_mirrored,
                engrave_depth
            )
        
        # Use ThreadPoolExecutor for parallel processing
        # Note: Due to Python GIL, this mainly helps with I/O-bound operations
        # The MeshLib boolean operations release GIL so we get some benefit
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_right = executor.submit(process_right)
            future_left = executor.submit(process_left)
            
            right_mesh = future_right.result()
            left_mesh = future_left.result()
        
        # Store results
        self.orthosis_mirrored = left_mesh
        self.orthosis_original = right_mesh
        self.is_engraved = True
        self.logo_applied = True
        
        # Save state after logo for text reset
        self._mesh_after_logo = right_mesh.copy()
        self._mirrored_after_logo = left_mesh.copy()
        
        elapsed = time.perf_counter() - start_time
        print(f"Logo applied in {elapsed*1000:.1f}ms (parallel L/R)")
        
        # If text was previously applied, reapply it with stored parameters
        if self._last_text_params is not None:
            params = self._last_text_params
            print("Reapplying text after logo update...")
            return self.apply_text(
                text=params['text'],
                position=params['position'],
                normal=params['normal'],
                offset_x=params['offset_x'],
                offset_y=params['offset_y'],
                rotation=params['rotation'],
                font_size=params['font_size'],
                depth=params.get('depth', 0.6)
            )
        
        return (left_mesh, right_mesh)
    
    def _restore_to_pristine(self) -> None:
        """Restore orthosis mesh to pristine state (as loaded, no engravings)."""
        if self._pristine_mesh is None:
            return
        
        self.orthosis_mesh = self._pristine_mesh.copy()
        self.orthosis_original = self._pristine_mesh.copy()
        
        # Regenerate mirrored version (Y-axis mirror only, no rotation)
        self.orthosis_mirrored = self.mirror_orthosis(self.orthosis_original, axis='y')
        
        self.is_engraved = False
        self.logo_applied = False
        self.text_applied = False
        
        # Clear the after-logo state as well
        self._mesh_after_logo = None
        self._mirrored_after_logo = None
        
        print("Restored to pristine mesh state")
    
    def apply_text(self,
                   text: str,
                   position: np.ndarray,
                   normal: np.ndarray,
                   offset_x: float = 0,
                   offset_y: float = 0,
                   rotation: float = 0,
                   font_size: float = 4.0,
                   depth: float = 0.6) -> Tuple[trimesh.Trimesh, trimesh.Trimesh]:
        """
        Apply text engraving only to both L and R versions.
        If text was already applied, restores mesh first to prevent overlap.
        
        OPTIMIZED: Uses parallel processing for L/R sides.
        
        Args:
            text: Text to engrave
            position: 3D position for text placement
            normal: Surface normal at the position
            offset_x: X offset in mm
            offset_y: Y offset in mm
            rotation: Rotation angle in degrees
            font_size: Font size in mm
            depth: Engraving depth in mm
            
        Returns:
            Tuple of (left_engraved, right_engraved)
        """
        import time
        start_time = time.perf_counter()
        
        if self._pristine_mesh is None:
            raise ValueError("No orthosis loaded")
        
        # Restore mesh before applying text to prevent overlap
        # If logo was applied, restore to after-logo state
        # Otherwise restore to pristine state
        if self._mesh_after_logo is not None:
            self.orthosis_original = self._mesh_after_logo.copy()
            self.orthosis_mirrored = self._mirrored_after_logo.copy()
            print("Restored to post-logo state before applying text")
        else:
            self._restore_to_pristine()
            print("Restored to pristine state before applying text")
        
        # Store position for export
        self.text_position = position.copy()
        self.text_normal = normal.copy()
        
        # Apply offsets in local tangent plane
        offset_pos = self._apply_tangent_offset(position, normal, offset_x, offset_y)
        
        # Prepare meshes
        right_mesh = self.orthosis_original.copy()
        left_mesh = self.orthosis_mirrored.copy()
        
        # Mirror the position (Y axis)
        text_pos_mirrored = self._mirror_point(offset_pos, 'y')
        text_normal_mirrored = self._mirror_point(normal, 'y')
        
        # Process both sides in parallel
        def process_right():
            return self._apply_text_to_mesh_with_params(
                right_mesh,
                text,
                offset_pos,
                normal,
                rotation,
                font_size,
                depth
            )
        
        def process_left():
            return self._apply_text_to_mesh_with_params(
                left_mesh,
                text,
                text_pos_mirrored,
                text_normal_mirrored,
                -rotation,  # Negative rotation for mirrored side
                font_size,
                depth
            )
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_right = executor.submit(process_right)
            future_left = executor.submit(process_left)
            
            right_mesh = future_right.result()
            left_mesh = future_left.result()
        
        # Store results
        self.orthosis_mirrored = left_mesh
        self.orthosis_original = right_mesh
        self.is_engraved = True
        self.text_applied = True
        
        # Store text parameters for reapplication after logo update
        self._last_text_params = {
            'text': text,
            'position': position.copy(),
            'normal': normal.copy(),
            'offset_x': offset_x,
            'offset_y': offset_y,
            'rotation': rotation,
            'font_size': font_size,
            'depth': depth
        }
        
        elapsed = time.perf_counter() - start_time
        print(f"Text applied in {elapsed*1000:.1f}ms (parallel L/R)")
        
        return (left_mesh, right_mesh)

    def apply_engraving(self,
                        position: np.ndarray,
                        normal: np.ndarray,
                        offset_x: float = 0,
                        offset_y: float = 0,
                        rotation: float = 0,
                        logo_scale: float = 1.0,
                        logo_depth: float = 0.6,
                        text: Optional[str] = None,
                        text_font_size: float = 4.0,
                        text_depth: float = 0.6,
                        text_spacing: float = 2.0) -> Tuple[trimesh.Trimesh, trimesh.Trimesh]:
        """
        Apply combined logo and text engraving in a single operation.
        
        Logo is placed at the specified position. Text (if provided) is placed
        below the logo with configurable spacing. Both share the same offset
        and rotation values.
        
        Args:
            position: 3D position for engraving placement (logo center)
            normal: Surface normal at the position
            offset_x: X offset in mm (moves entire engraving)
            offset_y: Y offset in mm (moves entire engraving)
            rotation: Rotation angle in degrees (rotates entire engraving)
            logo_scale: Scale factor for logo (1.0 = 100%)
            logo_depth: Engraving depth for logo in mm
            text: Optional text to engrave below logo (None = no text)
            text_font_size: Font size for text in mm
            text_depth: Engraving depth for text in mm
            text_spacing: Spacing between logo bottom and text top in mm
            
        Returns:
            Tuple of (left_engraved, right_engraved)
        """
        import time
        start_time = time.perf_counter()
        
        if self._pristine_mesh is None:
            raise ValueError("No orthosis loaded")
        if self.logo_mesh is None:
            raise ValueError("No logo loaded")
        
        # Restore to pristine state before applying
        self._restore_to_pristine()
        
        # Store position for export
        self.logo_position = position.copy()
        self.logo_normal = normal.copy()
        
        print(f"apply_engraving: position={position}, normal={normal}")
        print(f"apply_engraving: offset=({offset_x}, {offset_y}), rotation={rotation}")
        print(f"apply_engraving: logo_scale={logo_scale}, text='{text}', spacing={text_spacing}")
        
        # Apply offsets in local tangent plane
        offset_pos = self._apply_tangent_offset(position, normal, offset_x, offset_y)
        
        # Calculate local coordinate system for positioning text below logo
        up = np.array([0, 0, 1])
        if abs(np.dot(normal, up)) > 0.99:
            up = np.array([0, 1, 0])
        tangent_x = np.cross(up, normal)
        tangent_x = tangent_x / np.linalg.norm(tangent_x)
        tangent_y = np.cross(normal, tangent_x)
        tangent_y = tangent_y / np.linalg.norm(tangent_y)
        
        # Get logo dimensions to calculate text position
        logo_copy = self.logo_mesh.copy()
        if logo_scale != 1.0:
            scale_matrix = np.diag([logo_scale, logo_scale, 1, 1])
            logo_copy.apply_transform(scale_matrix)
        logo_bounds = logo_copy.bounds
        logo_height = logo_bounds[1][1] - logo_bounds[0][1]  # Y dimension in local coords
        
        # Prepare meshes for both sides
        right_mesh = self.orthosis_original.copy()
        left_mesh = self.mirror_orthosis(self.orthosis_original, axis='y')
        
        # Mirror positions for left side
        offset_pos_mirrored = self._mirror_point(offset_pos, 'y')
        normal_mirrored = self._mirror_point(normal, 'y')
        
        def process_side(mesh, pos, norm, is_right_side):
            """Process one side (logo + text)."""
            result_mesh = mesh
            
            # --- Apply Logo ---
            logo_copy_side = self.logo_mesh.copy()
            if logo_scale != 1.0:
                scale_matrix = np.diag([logo_scale, logo_scale, 1, 1])
                logo_copy_side.apply_transform(scale_matrix)
            if rotation != 0:
                rot_rad = np.radians(rotation if is_right_side else -rotation)
                rot_matrix = trimesh.transformations.rotation_matrix(rot_rad, [0, 0, 1])
                logo_copy_side.apply_transform(rot_matrix)
            
            result_mesh = self._apply_logo_to_mesh(
                result_mesh,
                logo_copy_side,
                pos,
                norm,
                logo_depth
            )
            
            # --- Apply Text (if provided) ---
            if text and text.strip():
                # Calculate text position below logo
                # Move down by half logo height + spacing + some margin
                text_offset_y = -(logo_height / 2 + text_spacing + text_font_size / 2)
                
                # Apply the rotation to get the correct down direction
                rot_rad = np.radians(rotation if is_right_side else -rotation)
                cos_r, sin_r = np.cos(rot_rad), np.sin(rot_rad)
                
                # Rotated tangent vectors
                local_tangent_x = tangent_x if is_right_side else self._mirror_point(tangent_x, 'y')
                local_tangent_y = tangent_y if is_right_side else self._mirror_point(tangent_y, 'y')
                
                # Apply rotation to get actual offset direction
                rotated_offset_x = cos_r * 0 - sin_r * text_offset_y
                rotated_offset_y = sin_r * 0 + cos_r * text_offset_y
                
                text_pos = pos + local_tangent_x * rotated_offset_x + local_tangent_y * rotated_offset_y
                
                result_mesh = self._apply_text_to_mesh_with_params(
                    result_mesh,
                    text,
                    text_pos,
                    norm,
                    rotation if is_right_side else -rotation,
                    text_font_size,
                    text_depth
                )
            
            return result_mesh
        
        # Process both sides in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_right = executor.submit(process_side, right_mesh, offset_pos, normal, True)
            future_left = executor.submit(process_side, left_mesh, offset_pos_mirrored, normal_mirrored, False)
            
            right_mesh = future_right.result()
            left_mesh = future_left.result()
        
        # Store results
        self.orthosis_mirrored = left_mesh
        self.orthosis_original = right_mesh
        self.is_engraved = True
        self.logo_applied = True
        if text and text.strip():
            self.text_applied = True
        
        # Store state for potential re-engraving
        self._mesh_after_logo = right_mesh.copy()
        self._mirrored_after_logo = left_mesh.copy()
        
        elapsed = time.perf_counter() - start_time
        print(f"Combined engraving applied in {elapsed*1000:.1f}ms (parallel L/R)")
        
        return (left_mesh, right_mesh)
    
    def _apply_tangent_offset(self, position: np.ndarray, normal: np.ndarray, 
                               offset_x: float, offset_y: float) -> np.ndarray:
        """Apply offset in the tangent plane at the given surface point."""
        # Create local coordinate system on the surface
        # X-axis: perpendicular to normal and up
        up = np.array([0, 0, 1])
        if abs(np.dot(normal, up)) > 0.99:
            up = np.array([0, 1, 0])
        
        tangent_x = np.cross(up, normal)
        tangent_x = tangent_x / np.linalg.norm(tangent_x)
        tangent_y = np.cross(normal, tangent_x)
        tangent_y = tangent_y / np.linalg.norm(tangent_y)
        
        # Apply offset
        return position + tangent_x * offset_x + tangent_y * offset_y
    
    def _apply_text_to_mesh_with_params(self,
                                        mesh: trimesh.Trimesh,
                                        text: str,
                                        position: np.ndarray,
                                        normal: np.ndarray,
                                        rotation: float,
                                        font_size: float,
                                        depth: float = 0.6) -> trimesh.Trimesh:
        """
        Apply text engraving with custom parameters.
        Uses surface wrapping to follow curved surfaces.
        """
        # Create text mesh with large extrusion for proper boolean cutting
        # The wrapping function will position it correctly relative to the surface
        extrusion_height = 30.0  # Large enough to ensure clean boolean through curved surfaces
        text_mesh = self._create_multiline_text_mesh(text.upper(), font_size=font_size, depth=extrusion_height)
        
        if text_mesh is None or len(text_mesh.vertices) == 0:
            print("Failed to create text mesh")
            return mesh
        
        # Center the text mesh first
        text_center = (text_mesh.bounds[0] + text_mesh.bounds[1]) / 2
        text_mesh.vertices -= text_center
        
        # Apply rotation around Z axis before placement
        if rotation != 0:
            rot_rad = np.radians(rotation)
            rot_matrix = trimesh.transformations.rotation_matrix(rot_rad, [0, 0, 1])
            text_mesh.apply_transform(rot_matrix)
        
        print(f"Text position: {position}, normal: {normal}")
        print(f"Text bounds before wrap: {text_mesh.bounds}")
        
        # Wrap the text to follow the curved surface
        wrapped_text = self._wrap_mesh_to_surface(
            flat_mesh=text_mesh,
            target_mesh=mesh,
            center_pos=position,
            surface_normal=normal,
            depth=depth
        )
        
        print(f"Text bounds after wrap: {wrapped_text.bounds}")
        
        # Boolean subtraction
        try:
            result = self._meshlib_boolean_difference_on_mesh(mesh, wrapped_text)
            if result is not None:
                return result
        except Exception as e:
            print(f"Text boolean failed: {e}")
        
        return mesh
        
        return mesh
    def _wrap_mesh_to_surface(self, 
                              flat_mesh: trimesh.Trimesh,
                              target_mesh: trimesh.Trimesh,
                              center_pos: np.ndarray,
                              surface_normal: np.ndarray,
                              depth: float) -> trimesh.Trimesh:
        """
        Wrap a flat mesh (logo/text) to follow a curved surface for engraving.
        
        Uses grid-based surface sampling with bilinear interpolation to follow
        the surface curvature, but uses a SINGLE normal direction for the depth
        to ensure flat-bottomed engravings without stair-step artifacts.
        
        OPTIMIZED: Uses fully vectorized NumPy operations for vertex transformation.
        
        Args:
            flat_mesh: Flat mesh (in XY plane, extruded in Z)
            target_mesh: The mesh surface to conform to
            center_pos: Center position on the surface
            surface_normal: Normal vector at the center position
            depth: Engraving depth in mm
            
        Returns:
            Transformed mesh wrapped to surface
        """
        import time
        start_time = time.perf_counter()
        
        # Get mesh dimensions
        bounds = flat_mesh.bounds
        mesh_width = bounds[1][0] - bounds[0][0]
        mesh_height = bounds[1][1] - bounds[0][1]
        mesh_depth_orig = bounds[1][2] - bounds[0][2]
        
        print(f"Mesh dimensions: width={mesh_width:.1f}, height={mesh_height:.1f}, depth={mesh_depth_orig:.1f}")
        print(f"Engraving depth: {depth:.2f}mm, vertices: {len(flat_mesh.vertices)}")
        
        # Normalize the surface normal (points outward from surface)
        normal = surface_normal / np.linalg.norm(surface_normal)
        
        # Build coordinate frame for placement
        world_up = np.array([0.0, 0.0, 1.0])
        mesh_up = world_up.copy()
        
        mesh_right = np.cross(mesh_up, normal)
        if np.linalg.norm(mesh_right) < 0.001:
            mesh_right = np.array([1.0, 0.0, 0.0])
        else:
            mesh_right = mesh_right / np.linalg.norm(mesh_right)
        
        # FLIP mesh_right to make text read LEFT-TO-RIGHT when viewed from outside
        mesh_right = -mesh_right
        
        # Check if the coordinate frame creates a left-handed system (mirrored)
        cross_check = np.cross(mesh_right, mesh_up)
        is_mirrored = np.dot(cross_check, normal) < 0
        
        # === ADAPTIVE GRID DENSITY ===
        # Use fewer samples for smaller meshes (optimization)
        min_samples = 10
        max_samples = 30
        samples_per_mm = 0.5  # Target ~2mm spacing between samples
        
        num_samples_x = int(np.clip(mesh_width * samples_per_mm, min_samples, max_samples))
        num_samples_y = int(np.clip(mesh_height * samples_per_mm, min_samples, max_samples))
        
        print(f"Using adaptive grid: {num_samples_x}x{num_samples_y} samples")
        
        # === VECTORIZED GRID CREATION ===
        # Create normalized grid coordinates using meshgrid
        tx_1d = np.linspace(-0.5, 0.5, num_samples_x)
        ty_1d = np.linspace(-0.5, 0.5, num_samples_y)
        tx_grid, ty_grid = np.meshgrid(tx_1d, ty_1d)  # Shape: (num_samples_y, num_samples_x)
        
        # Compute offsets
        x_offsets = tx_grid.ravel() * mesh_width * 1.2  # Flatten for ray casting
        y_offsets = ty_grid.ravel() * mesh_height * 1.2
        
        # Vectorized ray origin computation
        # sample_points = center_pos + mesh_right * x_offset + mesh_up * y_offset
        num_rays = num_samples_x * num_samples_y
        sample_points = (center_pos.reshape(1, 3) + 
                        np.outer(x_offsets, mesh_right) + 
                        np.outer(y_offsets, mesh_up))
        ray_origins = sample_points + normal * 100.0  # Shape: (num_rays, 3)
        ray_directions = np.tile(-normal, (num_rays, 1))
        
        # Batch ray cast to find surface positions
        locations, index_ray, index_tri = target_mesh.ray.intersects_location(
            ray_origins=ray_origins,
            ray_directions=ray_directions
        )
        
        # === VECTORIZED GRID BUILDING ===
        # Initialize grid with fallback positions (tangent plane)
        surface_grid = sample_points.reshape(num_samples_y, num_samples_x, 3).copy()
        
        if len(locations) > 0:
            # Find closest hit for each ray using vectorized operations
            # Compute distances for all hits
            hit_distances = np.linalg.norm(locations - ray_origins[index_ray], axis=1)
            
            # For each ray, find the minimum distance hit
            # Use pandas-style groupby approach with numpy
            unique_rays = np.unique(index_ray)
            for ray_idx in unique_rays:
                mask = index_ray == ray_idx
                if np.any(mask):
                    min_idx = np.argmin(hit_distances[mask])
                    hit_point = locations[mask][min_idx]
                    # Convert flat index to grid indices
                    gy = ray_idx // num_samples_x
                    gx = ray_idx % num_samples_x
                    surface_grid[gy, gx] = hit_point
        
        ray_time = time.perf_counter() - start_time
        print(f"Ray casting completed in {ray_time*1000:.1f}ms, {len(locations)} hits")
        
        # === FULLY VECTORIZED VERTEX TRANSFORMATION ===
        # Get original mesh bounds for mapping
        x_min, x_max = bounds[0][0], bounds[1][0]
        y_min, y_max = bounds[0][1], bounds[1][1]
        z_min, z_max = bounds[0][2], bounds[1][2]
        
        x_range = max(x_max - x_min, 1e-6)
        y_range = max(y_max - y_min, 1e-6)
        z_range = max(z_max - z_min, 1e-6)
        
        vertices = flat_mesh.vertices  # No copy needed, we create new array
        
        # Normalize all vertices to 0-1 range (vectorized)
        tx = np.clip((vertices[:, 0] - x_min) / x_range, 0, 1)
        ty = np.clip((vertices[:, 1] - y_min) / y_range, 0, 1)
        tz = (vertices[:, 2] - z_min) / z_range
        
        # Bilinear interpolation indices (vectorized)
        gx = tx * (num_samples_x - 1)
        gy = ty * (num_samples_y - 1)
        
        ix = np.clip(gx.astype(np.int32), 0, num_samples_x - 2)
        iy = np.clip(gy.astype(np.int32), 0, num_samples_y - 2)
        
        fx = gx - ix
        fy = gy - iy
        
        # Gather grid points for bilinear interpolation (vectorized)
        p00 = surface_grid[iy, ix]          # (N, 3)
        p10 = surface_grid[iy, ix + 1]      # (N, 3)
        p01 = surface_grid[iy + 1, ix]      # (N, 3)
        p11 = surface_grid[iy + 1, ix + 1]  # (N, 3)
        
        # Bilinear interpolation weights
        w00 = ((1 - fx) * (1 - fy)).reshape(-1, 1)
        w10 = (fx * (1 - fy)).reshape(-1, 1)
        w01 = ((1 - fx) * fy).reshape(-1, 1)
        w11 = (fx * fy).reshape(-1, 1)
        
        # Interpolated surface positions (vectorized)
        surf_pos = w00 * p00 + w10 * p10 + w01 * p01 + w11 * p11
        
        # Map Z to depth using SINGLE normal (for flat bottom)
        # tz=0 (bottom of extrusion) -> depth INTO surface
        # tz=1 (top of extrusion) -> outward_extension OUTSIDE surface
        outward_extension = 50.0
        z_offset = -depth + tz * (depth + outward_extension)
        
        # Final vertex positions (vectorized)
        new_vertices = surf_pos + np.outer(z_offset, normal)
        
        flat_mesh.vertices = new_vertices
        
        # If the coordinate frame is mirrored, flip face winding
        if is_mirrored:
            flat_mesh.faces = flat_mesh.faces[:, ::-1]
            print("Flipped face winding for mirrored coordinate frame")
        
        # Fix normals after transformation
        try:
            flat_mesh.fix_normals()
        except:
            pass
        
        # Ensure mesh is watertight
        if not flat_mesh.is_watertight:
            try:
                trimesh.repair.fill_holes(flat_mesh)
            except:
                pass
        
        try:
            flat_mesh.fix_normals()
        except:
            pass
        
        total_time = time.perf_counter() - start_time
        print(f"Surface wrapping completed in {total_time*1000:.1f}ms")
        
        return flat_mesh
    
    def _apply_logo_to_mesh(self, 
                            mesh: trimesh.Trimesh,
                            logo: trimesh.Trimesh,
                            position: np.ndarray,
                            normal: np.ndarray,
                            depth: float = 0.6) -> trimesh.Trimesh:
        """
        Apply logo engraving to a mesh at the specified position.
        Uses surface wrapping to follow curved surfaces.
        
        Args:
            mesh: Target mesh to engrave
            logo: Logo mesh to engrave
            position: Position on surface
            normal: Surface normal at position
            depth: Engraving depth in mm
        """
        # Center the logo first
        logo_center = (logo.bounds[0] + logo.bounds[1]) / 2
        logo.vertices -= logo_center
        
        print(f"Logo position: {position}, normal: {normal}, depth: {depth}mm")
        print(f"Logo bounds before wrap: {logo.bounds}")
        print(f"Mesh bounds: {mesh.bounds}")
        
        # Wrap the logo to follow the curved surface
        wrapped_logo = self._wrap_mesh_to_surface(
            flat_mesh=logo,
            target_mesh=mesh,
            center_pos=position,
            surface_normal=normal,
            depth=depth
        )
        
        print(f"Logo bounds after wrap: {wrapped_logo.bounds}")
        
        # Boolean subtraction
        try:
            result = self._meshlib_boolean_difference_on_mesh(mesh, wrapped_logo)
            if result is not None:
                return result
        except Exception as e:
            print(f"Logo boolean failed: {e}")
        
        return mesh
    
    def _apply_text_to_mesh(self,
                            mesh: trimesh.Trimesh,
                            text: str,
                            position: np.ndarray,
                            normal: np.ndarray) -> trimesh.Trimesh:
        """
        Apply text engraving to a mesh at the specified position.
        """
        # Create text mesh
        text_mesh = self._create_multiline_text_mesh(text.upper(), font_size=4.0, depth=self.ENGRAVE_DEPTH)
        
        if text_mesh is None or len(text_mesh.vertices) == 0:
            return mesh
        
        # Orient text to face along surface normal
        z_axis = np.array([0, 0, 1])
        target = -normal
        
        rotation_axis = np.cross(z_axis, target)
        if np.linalg.norm(rotation_axis) > 1e-6:
            rotation_axis = rotation_axis / np.linalg.norm(rotation_axis)
            angle = np.arccos(np.clip(np.dot(z_axis, target), -1, 1))
            rotation_matrix = trimesh.transformations.rotation_matrix(
                angle, rotation_axis, point=[0, 0, 0]
            )
            text_mesh.apply_transform(rotation_matrix)
        
        # Scale text depth for engraving
        bounds = text_mesh.bounds
        current_depth = bounds[1][2] - bounds[0][2]
        if current_depth > 0:
            scale_z = (self.ENGRAVE_DEPTH + 2.0) / current_depth
            centroid = text_mesh.centroid.copy()
            text_mesh.vertices -= centroid
            scale_matrix = np.diag([1, 1, scale_z, 1])
            text_mesh.apply_transform(scale_matrix)
            text_mesh.vertices += centroid
        
        # Position text at surface point
        text_mesh.vertices += position + normal * 1.0
        
        # Boolean subtraction
        try:
            result = self._meshlib_boolean_difference_on_mesh(mesh, text_mesh)
            if result is not None:
                return result
        except Exception as e:
            print(f"Text boolean failed: {e}")
        
        return mesh
    
    def _meshlib_boolean_difference_on_mesh(self, 
                                            target_mesh: trimesh.Trimesh,
                                            tool_mesh: trimesh.Trimesh) -> Optional[trimesh.Trimesh]:
        """
        Perform boolean difference using MeshLib.
        
        Args:
            target_mesh: The mesh to subtract from
            tool_mesh: The mesh to subtract
            
        Returns:
            Result mesh or None if failed
        """
        try:
            import meshlib.mrmeshpy as mr
            import tempfile
            
            print("Using MeshLib for boolean difference...")
            
            with tempfile.TemporaryDirectory() as tmpdir:
                target_path = os.path.join(tmpdir, "target.stl")
                tool_path = os.path.join(tmpdir, "tool.stl")
                result_path = os.path.join(tmpdir, "result.stl")
                
                target_mesh.export(target_path)
                tool_mesh.export(tool_path)
                
                target_mr = mr.loadMesh(target_path)
                tool_mr = mr.loadMesh(tool_path)
                
                # Check mesh validity before boolean
                print(f"Target mesh: {target_mr.topology.numValidFaces()} faces, {target_mr.topology.numValidVerts()} verts")
                print(f"Tool mesh: {tool_mr.topology.numValidFaces()} faces, {tool_mr.topology.numValidVerts()} verts")
                
                result = mr.boolean(target_mr, tool_mr, mr.BooleanOperation.DifferenceAB)
                
                # Check result status
                is_valid = result.valid()
                num_faces = result.mesh.topology.numValidFaces() if is_valid else 0
                print(f"Boolean result valid: {is_valid}, faces: {num_faces}")
                if hasattr(result, 'errorString') and result.errorString:
                    print(f"Boolean error: {result.errorString}")
                
                if is_valid and num_faces > 0:
                    mr.saveMesh(result.mesh, result_path)
                    result_mesh = trimesh.load(result_path, force='mesh')
                    if result_mesh is not None and hasattr(result_mesh, 'vertices') and len(result_mesh.vertices) > 0:
                        result_mesh.fix_normals()
                        print(f"MeshLib boolean success: {len(result_mesh.vertices)} vertices")
                        return result_mesh
                else:
                    # If MeshLib boolean failed, try alternate approach: use manifold tool mesh
                    print("MeshLib boolean produced invalid result - trying to repair meshes...")
                    
                    # Try fixing the tool mesh
                    try:
                        # Make tool mesh manifold by fixing self-intersections
                        # Use a small voxel size for higher precision repair
                        voxel_size = 0.1  # 0.1mm voxel size for repair
                        mr.fixSelfIntersections(tool_mr, voxel_size)
                        
                        result2 = mr.boolean(target_mr, tool_mr, mr.BooleanOperation.DifferenceAB)
                        if result2.valid() and result2.mesh.topology.numValidFaces() > 0:
                            mr.saveMesh(result2.mesh, result_path)
                            result_mesh = trimesh.load(result_path, force='mesh')
                            if result_mesh is not None and hasattr(result_mesh, 'vertices') and len(result_mesh.vertices) > 0:
                                result_mesh.fix_normals()
                                print(f"MeshLib boolean (after repair) success: {len(result_mesh.vertices)} vertices")
                                return result_mesh
                    except Exception as repair_err:
                        print(f"Repair attempt failed: {repair_err}")
                    
                    # Try using trimesh to simplify and repair the tool mesh
                    try:
                        print("Trying trimesh repair on tool mesh...")
                        tool_trimesh = trimesh.load(tool_path, force='mesh')
                        # Merge vertices that are very close
                        tool_trimesh.merge_vertices(merge_tex=True, merge_norm=True)
                        # Remove degenerate faces
                        tool_trimesh.remove_degenerate_faces()
                        tool_trimesh.remove_duplicate_faces()
                        tool_trimesh.fix_normals()
                        
                        # Save repaired mesh and reload
                        tool_trimesh.export(tool_path)
                        tool_mr2 = mr.loadMesh(tool_path)
                        
                        result3 = mr.boolean(target_mr, tool_mr2, mr.BooleanOperation.DifferenceAB)
                        if result3.valid() and result3.mesh.topology.numValidFaces() > 0:
                            mr.saveMesh(result3.mesh, result_path)
                            result_mesh = trimesh.load(result_path, force='mesh')
                            if result_mesh is not None and hasattr(result_mesh, 'vertices') and len(result_mesh.vertices) > 0:
                                result_mesh.fix_normals()
                                print(f"MeshLib boolean (after trimesh repair) success: {len(result_mesh.vertices)} vertices")
                                return result_mesh
                    except Exception as repair_err2:
                        print(f"Trimesh repair attempt failed: {repair_err2}")
                    
                    print("MeshLib boolean failed after repair - skipping this engraving")
                    return target_mesh
                        
        except ImportError:
            print("MeshLib not available, returning original mesh")
            return target_mesh
        except Exception as e:
            print(f"MeshLib boolean error: {e} - returning original mesh")
            return target_mesh
        
        return target_mesh
    
    def _create_multiline_text_mesh(self, text: str, font_size: float, depth: float) -> Optional[trimesh.Trimesh]:
        """
        Create a 3D mesh of multi-line text.
        
        Args:
            text: Text to create (can contain \\n for new lines)
            font_size: Height of each character
            depth: Extrusion depth
            
        Returns:
            Combined mesh of all characters
        """
        lines = text.split('\n')
        line_meshes = []
        line_spacing = font_size * 1.4
        
        for line_idx, line in enumerate(lines):
            line_text = line.strip()
            if not line_text:
                continue
            line_mesh = self._create_text_mesh(line_text, font_size, depth)
            if line_mesh is not None:
                y_offset = -line_idx * line_spacing
                line_mesh.vertices[:, 1] += y_offset
                line_meshes.append(line_mesh)
        
        if line_meshes:
            combined = trimesh.util.concatenate(line_meshes)
            return combined
        
        return None
    
    def _create_text_mesh(self, text: str, font_size: float, depth: float) -> Optional[trimesh.Trimesh]:
        """
        Create a 3D mesh of text using matplotlib or polygon fallback.
        """
        # Try matplotlib-based text path first
        try:
            mesh = self._create_text_mesh_matplotlib(text, font_size, depth)
            if mesh is not None:
                return mesh
        except Exception as e:
            print(f"Matplotlib text failed: {e}")
        
        # Fallback to polygon-based rendering
        return self._create_text_mesh_polygon(text.upper(), font_size, depth)
    
    def _create_text_mesh_matplotlib(self, text: str, font_size: float, depth: float) -> Optional[trimesh.Trimesh]:
        """Create 3D text mesh using matplotlib's TextPath."""
        from matplotlib.textpath import TextPath
        from matplotlib.font_manager import FontProperties
        from shapely.geometry import Polygon, MultiPolygon
        from shapely.ops import unary_union
        
        if not text.strip():
            return None
        
        font_props = FontProperties(family='sans-serif', weight='bold')
        text_path = TextPath((0, 0), text, size=font_size, prop=font_props)
        
        MOVETO, LINETO, CURVE3, CURVE4, CLOSEPOLY = 1, 2, 3, 4, 79
        
        polygons = []
        current_polygon = []
        vertices = text_path.vertices
        codes = text_path.codes
        
        t_samples_quad = np.linspace(0, 1, 12)[1:]
        t_samples_cubic = np.linspace(0, 1, 16)[1:]
        
        i = 0
        while i < len(codes):
            code = codes[i]
            
            if code == MOVETO:
                if len(current_polygon) >= 3:
                    try:
                        poly = Polygon(current_polygon)
                        if poly.is_valid and poly.area > 0.001:
                            polygons.append(poly)
                    except:
                        pass
                current_polygon = [tuple(vertices[i])]
                i += 1
                
            elif code == LINETO:
                current_polygon.append(tuple(vertices[i]))
                i += 1
                
            elif code == CURVE3:
                if len(current_polygon) > 0:
                    p0 = current_polygon[-1]
                    p1 = tuple(vertices[i])
                    p2 = tuple(vertices[i + 1])
                    for t in t_samples_quad:
                        x = (1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0]
                        y = (1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1]
                        current_polygon.append((x, y))
                i += 2
                
            elif code == CURVE4:
                if len(current_polygon) > 0:
                    p0 = current_polygon[-1]
                    p1 = tuple(vertices[i])
                    p2 = tuple(vertices[i + 1])
                    p3 = tuple(vertices[i + 2])
                    for t in t_samples_cubic:
                        x = (1-t)**3 * p0[0] + 3*(1-t)**2*t * p1[0] + 3*(1-t)*t**2 * p2[0] + t**3 * p3[0]
                        y = (1-t)**3 * p0[1] + 3*(1-t)**2*t * p1[1] + 3*(1-t)*t**2 * p2[1] + t**3 * p3[1]
                        current_polygon.append((x, y))
                i += 3
                
            elif code == CLOSEPOLY:
                if len(current_polygon) >= 3:
                    try:
                        poly = Polygon(current_polygon)
                        if poly.is_valid and poly.area > 0.001:
                            polygons.append(poly)
                    except:
                        pass
                current_polygon = []
                i += 1
            else:
                i += 1
        
        if len(current_polygon) >= 3:
            try:
                poly = Polygon(current_polygon)
                if poly.is_valid and poly.area > 0.001:
                    polygons.append(poly)
            except:
                pass
        
        if not polygons:
            return None
        
        # Clean and merge polygons
        raw_polygons = []
        for poly in polygons:
            try:
                cleaned = poly.buffer(0)
                if cleaned.is_valid and cleaned.area > 0.001:
                    raw_polygons.append(cleaned)
            except:
                continue
        
        if not raw_polygons:
            return None
        
        # Sort by area and handle holes
        raw_polygons.sort(key=lambda p: p.area, reverse=True)
        
        final_polygons = []
        used = set()
        
        for i, outer in enumerate(raw_polygons):
            if i in used:
                continue
            
            holes = []
            for j, inner in enumerate(raw_polygons):
                if j <= i or j in used:
                    continue
                if outer.contains(inner):
                    holes.append(inner)
                    used.add(j)
            
            if holes:
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
        
        # Extrude to 3D
        meshes = []
        for poly in final_polygons:
            try:
                if isinstance(poly, MultiPolygon):
                    for p in poly.geoms:
                        if p.is_valid and p.area > 0.01:
                            m = trimesh.creation.extrude_polygon(p, height=depth, engine='earcut')
                            if m:
                                meshes.append(m)
                else:
                    if poly.is_valid and poly.area > 0.01:
                        m = trimesh.creation.extrude_polygon(poly, height=depth, engine='earcut')
                        if m:
                            meshes.append(m)
            except:
                pass
        
        if meshes:
            combined = trimesh.util.concatenate(meshes)
            bounds = combined.bounds
            center_x = (bounds[0][0] + bounds[1][0]) / 2
            combined.vertices[:, 0] -= center_x
            # MIRROR X axis so text reads correctly when engraved (like a rubber stamp)
            combined.vertices[:, 0] = -combined.vertices[:, 0]
            return combined
        
        return None
    
    def _create_text_mesh_polygon(self, text: str, font_size: float, depth: float) -> Optional[trimesh.Trimesh]:
        """
        Fallback: Create 3D text using predefined polygon paths.
        """
        from shapely.geometry import Polygon
        
        meshes = []
        char_width = font_size * 0.7
        spacing = font_size * 0.15
        x_offset = 0
        
        for char in text:
            if char == ' ':
                x_offset += char_width * 0.5
                continue
            
            if char in LETTER_PATHS:
                paths = LETTER_PATHS[char]
            else:
                paths = [[(0.1, 0.1), (0.1, 0.9), (0.9, 0.9), (0.9, 0.1), (0.1, 0.1)]]
            
            if not paths:
                x_offset += char_width * 0.5
                continue
            
            try:
                outer_path = [(x * font_size, y * font_size) for x, y in paths[0]]
                polygon = Polygon(outer_path)
                
                if len(paths) > 1:
                    holes = []
                    for hole_path in paths[1:]:
                        if hole_path:
                            hole = [(x * font_size, y * font_size) for x, y in hole_path]
                            holes.append(hole)
                    if holes:
                        polygon = Polygon(outer_path, holes)
                
                if not polygon.is_valid:
                    polygon = polygon.buffer(0)
                
                if polygon.is_empty or polygon.area < 0.01:
                    continue
                
                char_mesh = trimesh.creation.extrude_polygon(polygon, height=depth, engine='earcut')
                
                if char_mesh is not None:
                    char_mesh.vertices[:, 0] += x_offset
                    meshes.append(char_mesh)
                
            except Exception as e:
                print(f"Warning: Could not create character '{char}': {e}")
            
            x_offset += char_width + spacing
        
        if meshes:
            combined = trimesh.util.concatenate(meshes)
            bounds = combined.bounds
            center_x = (bounds[0][0] + bounds[1][0]) / 2
            combined.vertices[:, 0] -= center_x
            # MIRROR X axis so text reads correctly when engraved (like a rubber stamp)
            combined.vertices[:, 0] = -combined.vertices[:, 0]
            return combined
        
        return None
    
    def export_both(self, output_dir: str, patient_name: str, date: str) -> Tuple[str, str]:
        """
        Export both Left and Right versions to STL files.
        
        Args:
            output_dir: Directory to save files
            patient_name: Patient name for filename
            date: Date string for filename
            
        Returns:
            Tuple of (left_path, right_path)
        """
        if self.orthosis_mirrored is None or self.orthosis_original is None:
            raise ValueError("No meshes to export")
        
        # Sanitize filename
        safe_name = self._sanitize_filename(patient_name)
        safe_date = date.replace('/', '-').replace('\\', '-').replace(':', '-')
        
        # Generate filenames
        left_filename = f"{safe_name}_{safe_date}_L.stl"
        right_filename = f"{safe_name}_{safe_date}_R.stl"
        
        left_path = os.path.join(output_dir, left_filename)
        right_path = os.path.join(output_dir, right_filename)
        
        # Export
        self.orthosis_mirrored.export(left_path, file_type='stl')
        self.orthosis_original.export(right_path, file_type='stl')
        
        print(f"Exported: {left_path}")
        print(f"Exported: {right_path}")
        
        return (left_path, right_path)
    
    def _sanitize_filename(self, name: str) -> str:
        """Remove invalid filename characters."""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '')
        return name.strip().replace(' ', '_')
    
    def get_mesh_info(self, mesh: Optional[trimesh.Trimesh] = None) -> dict:
        """Get information about a mesh."""
        if mesh is None:
            mesh = self.orthosis_mesh
        
        if mesh is None:
            return {}
        
        bounds = mesh.bounds
        dimensions = bounds[1] - bounds[0]
        
        return {
            'vertices': len(mesh.vertices),
            'faces': len(mesh.faces),
            'bounds_min': bounds[0].tolist(),
            'bounds_max': bounds[1].tolist(),
            'dimensions': {
                'x': float(dimensions[0]),
                'y': float(dimensions[1]),
                'z': float(dimensions[2])
            },
            'volume': float(mesh.volume) if mesh.is_watertight else None,
            'is_watertight': mesh.is_watertight,
            'centroid': mesh.centroid.tolist()
        }
