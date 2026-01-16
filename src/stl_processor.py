"""
STL Processor Module
====================
Handles all STL file operations including:
- Loading and saving STL files
- Scaling meshes in X, Y, Z dimensions
- Mirroring meshes (left/right flip)
- Adding text labels/engravings to meshes with proper letter shapes

Uses trimesh library for mesh operations.
"""

import numpy as np
import trimesh
from typing import Tuple, Optional, List
import os


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
}


class STLProcessor:
    """
    Main class for processing STL files.
    Provides methods for loading, transforming, and saving 3D meshes.
    """
    
    def __init__(self):
        """Initialize the STL processor."""
        self.foot_mesh: Optional[trimesh.Trimesh] = None
        self.insole_mesh: Optional[trimesh.Trimesh] = None
        self.original_insole_mesh: Optional[trimesh.Trimesh] = None
        
        # Store the insole before any label is applied
        # This allows us to replace labels by going back to this state
        self._insole_before_label: Optional[trimesh.Trimesh] = None
        
        # Currently applied label (to detect changes)
        self._current_label: Optional[str] = None
        
        # Store label parameters for re-application after mirroring
        self._label_params: Optional[dict] = None
        
        # Reference points on the foot (heel, toe tip, left side, right side)
        self.reference_points: List[np.ndarray] = []
        
        # Insole-foot linking state
        self._insole_linked = False  # Whether insole is linked to foot
        self._link_offset = None  # Relative offset from foot centroid to insole centroid
        self._link_rotation = None  # Relative rotation
        
    def load_foot_stl(self, filepath: str) -> trimesh.Trimesh:
        """
        Load a foot STL file.
        
        Args:
            filepath: Path to the STL file
            
        Returns:
            Loaded mesh object
        """
        try:
            self.foot_mesh = trimesh.load(filepath, force='mesh')
            self.foot_mesh.vertices -= self.foot_mesh.centroid
            return self.foot_mesh
        except Exception as e:
            raise ValueError(f"Failed to load foot STL: {str(e)}")
    
    def load_insole_stl(self, filepath: str) -> trimesh.Trimesh:
        """
        Load an insole STL file.
        
        Args:
            filepath: Path to the STL file
            
        Returns:
            Loaded mesh object
        """
        try:
            self.insole_mesh = trimesh.load(filepath, force='mesh')
            # Center the mesh at origin
            self.insole_mesh.vertices -= self.insole_mesh.centroid
            # Store centered mesh as original (so sliders use this as zero point)
            self.original_insole_mesh = self.insole_mesh.copy()
            
            # Reset label state when loading new insole
            self._insole_before_label = None
            self._current_label = None
            self._label_params = None
            
            return self.insole_mesh
        except Exception as e:
            raise ValueError(f"Failed to load insole STL: {str(e)}")
    
    def reset_insole(self) -> Optional[trimesh.Trimesh]:
        """Reset insole to original loaded state (after positioning)."""
        if self.original_insole_mesh is not None:
            self.insole_mesh = self.original_insole_mesh.copy()
            
            # Reset label state
            self._insole_before_label = None
            self._current_label = None
            self._label_params = None
            
            return self.insole_mesh
        return None
    
    def set_reference_points(self, points: List[np.ndarray]) -> None:
        """Set reference points on the foot (4 points: heel, toe, left, right)."""
        if len(points) != 4:
            raise ValueError("Exactly 4 reference points required")
        self.reference_points = [np.array(p) for p in points]
    
    def calculate_foot_dimensions(self) -> Tuple[float, float]:
        """
        Calculate foot dimensions based on 4 reference points.
        
        Points: heel, toe (front center), left side, right side
        The left/right points should be at the widest part of the foot,
        perpendicular (90 degrees) to the length axis.
        
        Returns:
            Tuple of (length, width)
        """
        if len(self.reference_points) != 4:
            raise ValueError("4 reference points required (heel, toe, left, right)")
        
        heel = self.reference_points[0]
        toe = self.reference_points[1]
        left_side = self.reference_points[2]
        right_side = self.reference_points[3]
        
        # Length is distance from heel to toe
        length = np.linalg.norm(toe - heel)
        
        # Width is distance from left to right side points
        width = np.linalg.norm(right_side - left_side)
        
        return float(length), float(width)
    
    def get_insole_dimensions(self) -> Tuple[float, float, float]:
        """Get current insole dimensions."""
        if self.insole_mesh is None:
            raise ValueError("No insole loaded")
        
        bounds = self.insole_mesh.bounds
        dimensions = bounds[1] - bounds[0]
        return tuple(dimensions)
    
    def scale_insole(self, scale_x: float, scale_y: float, scale_z: float = 1.0) -> trimesh.Trimesh:
        """Scale the insole mesh by given factors."""
        if self.insole_mesh is None:
            raise ValueError("No insole loaded")
        
        scale_matrix = np.array([
            [scale_x, 0, 0, 0],
            [0, scale_y, 0, 0],
            [0, 0, scale_z, 0],
            [0, 0, 0, 1]
        ])
        
        self.insole_mesh.apply_transform(scale_matrix)
        
        # Update original mesh so position sliders use scaled mesh as base
        # This prevents scaling from jumping back when moving the insole
        if self.original_insole_mesh is not None:
            self.original_insole_mesh = self.insole_mesh.copy()
        
        # If we had a label, we need to update the before-label state
        # because scaling should persist through label changes
        if self._insole_before_label is not None:
            self._insole_before_label = self.insole_mesh.copy()
            self._current_label = None  # Force re-application of label
        
        return self.insole_mesh
    
    def auto_scale_insole(self, target_length: float, target_width: float, 
                          scale_z: Optional[float] = None) -> Tuple[float, float, float]:
        """Automatically scale insole to match foot dimensions."""
        if self.insole_mesh is None:
            raise ValueError("No insole loaded")
        
        current_dims = self.get_insole_dimensions()
        current_length = current_dims[0]
        current_width = current_dims[1]
        
        scale_x = target_length / current_length if current_length > 0 else 1.0
        scale_y = target_width / current_width if current_width > 0 else 1.0
        final_scale_z = scale_z if scale_z is not None else 1.0
        
        self.scale_insole(scale_x, scale_y, final_scale_z)
        
        return scale_x, scale_y, final_scale_z
    
    def mirror_insole(self, axis: str = 'x') -> trimesh.Trimesh:
        """
        Mirror the insole mesh along specified axis.
        
        If a label exists, it is removed before mirroring to prevent
        backwards/upside-down text. User should add label after mirroring.
        """
        if self.insole_mesh is None:
            raise ValueError("No insole loaded")
        
        # Save label parameters before mirroring (if label exists)
        had_label = self._insole_before_label is not None
        saved_label_params = self._label_params.copy() if self._label_params else None
        
        # If there's a label, restore the pre-label state first
        # This prevents the label from being mirrored (which would make it backwards)
        if self._insole_before_label is not None:
            self.insole_mesh = self._insole_before_label.copy()
        
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
        else:
            reflection_matrix = np.array([
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, -1, 0],
                [0, 0, 0, 1]
            ])
        
        self.insole_mesh.apply_transform(reflection_matrix)
        self.insole_mesh.fix_normals()
        
        # Update original mesh so position sliders use mirrored mesh as base
        if self.original_insole_mesh is not None:
            self.original_insole_mesh = self.insole_mesh.copy()
        
        # Clear label state
        self._insole_before_label = None
        self._current_label = None
        
        # Re-apply label at mirrored position if it existed
        if had_label and saved_label_params:
            # Mirror the label position
            if saved_label_params.get('custom_position') is not None:
                pos = saved_label_params['custom_position'].copy()
                normal = saved_label_params.get('custom_normal')
                
                # Mirror the position based on axis
                if axis.lower() == 'x':
                    pos[0] = -pos[0]
                    if normal is not None:
                        normal = normal.copy()
                        normal[0] = -normal[0]
                elif axis.lower() == 'y':
                    pos[1] = -pos[1]
                    if normal is not None:
                        normal = normal.copy()
                        normal[1] = -normal[1]
                else:  # z
                    pos[2] = -pos[2]
                    if normal is not None:
                        normal = normal.copy()
                        normal[2] = -normal[2]
                
                saved_label_params['custom_position'] = pos
                saved_label_params['custom_normal'] = normal
            
            # Re-apply the label with mirrored position but readable text
            try:
                self.add_text_label(**saved_label_params)
            except Exception as e:
                print(f"Could not re-apply label after mirror: {e}")
                self._label_params = None
        
        return self.insole_mesh
    
    def align_insole_to_foot(self) -> trimesh.Trimesh:
        """
        Align the insole to the foot using 4 reference points.
        
        The insole is:
        1. Centered under the foot along the heel-toe axis
        2. Positioned very close to the bottom of the foot
        
        No rotation is applied - insole keeps its original orientation.
        
        Reference points:
        - Point 0: Heel (back center)
        - Point 1: Toe (front center) - defines length axis with heel
        - Point 2: Left side (widest point)
        - Point 3: Right side (widest point) - defines width axis
        
        Returns:
            Aligned insole mesh
        """
        if self.foot_mesh is None:
            raise ValueError("No foot mesh loaded")
        if self.insole_mesh is None:
            raise ValueError("No insole mesh loaded")
        if len(self.reference_points) < 4:
            raise ValueError("Need 4 reference points on foot (heel, toe, left side, right side)")
        
        # IMPORTANT: Reset to original insole first for consistent alignment
        if self.original_insole_mesh is not None:
            self.insole_mesh = self.original_insole_mesh.copy()
            self._insole_before_label = None
            self._current_label = None
        
        # Get foot reference points
        heel_pt = np.array(self.reference_points[0])
        toe_pt = np.array(self.reference_points[1])
        left_pt = np.array(self.reference_points[2])
        right_pt = np.array(self.reference_points[3])
        
        # Calculate foot center (midpoint between heel and toe)
        foot_center_xy = (heel_pt[:2] + toe_pt[:2]) / 2
        
        # Get foot sole position (lowest Z of the reference points)
        foot_bottom_z = min(heel_pt[2], toe_pt[2], left_pt[2], right_pt[2])
        
        # Get insole bounds
        insole_bounds = self.insole_mesh.bounds
        insole_center = (insole_bounds[0] + insole_bounds[1]) / 2
        insole_top_z = insole_bounds[1][2]
        
        # Position insole: center it under the foot, top surface very close to foot bottom
        translation = np.array([
            foot_center_xy[0] - insole_center[0],
            foot_center_xy[1] - insole_center[1],
            foot_bottom_z - insole_top_z - 0.1  # 0.1mm below foot (near-touching)
        ])
        
        self.insole_mesh.vertices += translation
        
        # Update original mesh to match - this becomes the new zero point for sliders
        self.original_insole_mesh = self.insole_mesh.copy()
        
        # Update before-label state
        self._insole_before_label = None
        self._current_label = None
        
        # Link the insole to the foot after alignment
        self._link_insole_to_foot()
        
        return self.insole_mesh
    
    def get_foot_length(self) -> float:
        """
        Get the length of the foot along the X axis.
        
        Returns:
            Foot length in mm (X axis dimension)
        """
        if self.foot_mesh is None:
            return 0.0
        
        bounds = self.foot_mesh.bounds
        return float(bounds[1][0] - bounds[0][0])
    
    def detect_foot_side(self, foot_filepath: Optional[str] = None) -> str:
        """
        Detect if the foot is left or right based on filename keywords.
        
        Checks filename for side indicators (L/R, left/right, links/rechts).
        Defaults to 'R' (right) if no indicators found.
        
        Args:
            foot_filepath: Optional path to check filename for side indicators
        
        Returns:
            'L' for left foot, 'R' for right foot (default)
        """
        # Check filename for side indicators
        if foot_filepath:
            fname = os.path.basename(foot_filepath).lower()
            # Check for left indicators
            if '_l_' in fname or '_l.' in fname or '_left' in fname or 'left_' in fname or fname.startswith('l_') or 'links' in fname or ' l ' in fname:
                return 'L'
            # Check for right indicators
            if '_r_' in fname or '_r.' in fname or '_right' in fname or 'right_' in fname or fname.startswith('r_') or 'rechts' in fname or ' r ' in fname:
                return 'R'
        
        # Default to right if no indicators found
        return 'R'
    
    def find_best_matching_insole(self, insole_dir: str, foot_side: Optional[str] = None) -> Optional[str]:
        """
        Find the insole with the closest matching length to the loaded foot.
        Uses fast bounding box reading with parallel processing.
        
        Args:
            insole_dir: Directory containing insole STL files
            foot_side: 'L' or 'R' to filter by side (looks for L/R or left/right in filename)
            
        Returns:
            Path to the best matching insole file, or None if no insoles found
        """
        import glob
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        if self.foot_mesh is None:
            return None
        
        foot_length = self.get_foot_length()
        if foot_length <= 0:
            return None
        
        # Find all STL files in the insole directory
        insole_files = glob.glob(os.path.join(insole_dir, "*.stl"))
        insole_files.extend(glob.glob(os.path.join(insole_dir, "*.STL")))
        
        # Remove duplicates (case-insensitive on Windows)
        seen = set()
        unique_files = []
        for f in insole_files:
            f_lower = f.lower()
            if f_lower not in seen:
                seen.add(f_lower)
                unique_files.append(f)
        insole_files = unique_files
        
        # Filter by foot side if specified
        if foot_side:
            side_filtered = []
            for f in insole_files:
                fname = os.path.basename(f).lower()
                if foot_side.lower() == 'l':
                    # Look for left indicators (including German 'links')
                    if '_l_' in fname or '_l.' in fname or '_left' in fname or 'left_' in fname or fname.startswith('l_') or 'links' in fname:
                        side_filtered.append(f)
                elif foot_side.lower() == 'r':
                    # Look for right indicators (including German 'rechts')
                    if '_r_' in fname or '_r.' in fname or '_right' in fname or 'right_' in fname or fname.startswith('r_') or 'rechts' in fname:
                        side_filtered.append(f)
            
            # If we found side-specific insoles, use only those
            if side_filtered:
                insole_files = side_filtered
            # Otherwise fall back to all insoles (may be universal)
        
        if not insole_files:
            return None
        
        # Process files in parallel for faster matching
        def get_length(path):
            try:
                length = self._get_stl_x_length_fast(path)
                return (path, length)
            except:
                return (path, None)
        
        results = []
        
        # Use ThreadPoolExecutor for parallel I/O
        with ThreadPoolExecutor(max_workers=min(8, len(insole_files))) as executor:
            futures = {executor.submit(get_length, path): path for path in insole_files}
            for future in as_completed(futures):
                results.append(future.result())
        
        # Find best match
        best_match = None
        best_diff = float('inf')
        
        for path, length in results:
            if length is not None:
                diff = abs(length - foot_length)
                if diff < best_diff:
                    best_diff = diff
                    best_match = path
        
        return best_match
    
    def _get_stl_x_length_fast(self, filepath: str) -> Optional[float]:
        """
        Fast read of STL file to get X-axis bounding box length.
        Uses NumPy bulk read for maximum speed.
        """
        import struct
        
        try:
            with open(filepath, 'rb') as f:
                # Read header (80 bytes)
                header = f.read(80)
                
                # Check if ASCII or binary
                if b'solid' in header[:5].lower():
                    # Might be ASCII - fall back to trimesh for ASCII files
                    f.seek(0)
                    content = f.read(1000)
                    if b'facet' in content:
                        # ASCII STL - use trimesh
                        mesh = trimesh.load(filepath, force='mesh')
                        return float(mesh.bounds[1][0] - mesh.bounds[0][0])
                
                # Binary STL - use NumPy bulk read for speed
                f.seek(80)
                num_triangles = struct.unpack('<I', f.read(4))[0]
                
                if num_triangles == 0:
                    return None
                
                # Each triangle: 50 bytes (12 floats * 4 bytes + 2 bytes attribute)
                # Structure: normal(3f) + v1(3f) + v2(3f) + v3(3f) + attr(H)
                triangle_dtype = np.dtype([
                    ('normal', np.float32, 3),
                    ('v1', np.float32, 3),
                    ('v2', np.float32, 3),
                    ('v3', np.float32, 3),
                    ('attr', np.uint16)
                ])
                
                # Read all triangles at once
                data = np.frombuffer(f.read(num_triangles * 50), dtype=triangle_dtype)
                
                # Extract only X coordinates from all 3 vertices
                x_coords = np.concatenate([
                    data['v1'][:, 0],
                    data['v2'][:, 0],
                    data['v3'][:, 0]
                ])
                
                return float(x_coords.max() - x_coords.min())
                
        except Exception as e:
            # Fall back to trimesh
            try:
                mesh = trimesh.load(filepath, force='mesh')
                return float(mesh.bounds[1][0] - mesh.bounds[0][0])
            except:
                return None
    
    def position_insole_below_foot(self) -> Optional[trimesh.Trimesh]:
        """
        Position the insole directly below the foot without using reference points.
        Centers the insole under the foot and places it very close to the foot surface.
        
        Returns:
            Positioned insole mesh, or None if meshes not loaded
        """
        if self.foot_mesh is None or self.insole_mesh is None:
            return None
        
        # Get foot bounds
        foot_bounds = self.foot_mesh.bounds
        foot_center_xy = (foot_bounds[0][:2] + foot_bounds[1][:2]) / 2
        foot_bottom_z = foot_bounds[0][2]  # Lowest Z of foot
        
        # Get insole bounds
        insole_bounds = self.insole_mesh.bounds
        insole_center = (insole_bounds[0] + insole_bounds[1]) / 2
        insole_top_z = insole_bounds[1][2]
        
        # Translate insole to be centered under foot, with top very close to foot bottom
        # Use 0.1mm gap for near-touching visual check
        translation = np.array([
            foot_center_xy[0] - insole_center[0],
            foot_center_xy[1] - insole_center[1],
            foot_bottom_z - insole_top_z - 0.1  # 0.1mm gap (near-touching)
        ])
        
        self.insole_mesh.vertices += translation
        
        # Update original mesh to match - this becomes the new zero point for sliders
        if self.original_insole_mesh is not None:
            self.original_insole_mesh = self.insole_mesh.copy()
        
        return self.insole_mesh

    def _link_insole_to_foot(self):
        """
        Establish the link between insole and foot.
        Stores the relative offset so insole follows foot transformations.
        """
        if self.foot_mesh is None or self.insole_mesh is None:
            return
        
        # Store the relative offset from foot centroid to insole centroid
        self._link_offset = self.insole_mesh.centroid - self.foot_mesh.centroid
        self._insole_linked = True
    
    def is_insole_linked(self) -> bool:
        """Check if insole is currently linked to foot."""
        return self._insole_linked
    
    def unlink_insole(self):
        """Unlink insole from foot."""
        self._insole_linked = False
        self._link_offset = None
        self._link_rotation = None
    
    def apply_foot_transform(self, transform_matrix: np.ndarray):
        """
        Apply a transformation to the foot and update linked insole.
        
        Args:
            transform_matrix: 4x4 transformation matrix
        """
        if self.foot_mesh is None:
            return
        
        # Store foot centroid before transform
        old_foot_centroid = self.foot_mesh.centroid.copy()
        
        # Apply to foot
        self.foot_mesh.apply_transform(transform_matrix)
        
        # If insole is linked, move it to follow the foot
        if self._insole_linked and self.insole_mesh is not None:
            # Calculate new insole position based on new foot position
            new_insole_centroid = self.foot_mesh.centroid + self._link_offset
            current_insole_centroid = self.insole_mesh.centroid
            
            # Translate insole
            translation = new_insole_centroid - current_insole_centroid
            self.insole_mesh.vertices += translation
            
            # Update before-label state if exists
            if self._insole_before_label is not None:
                self._insole_before_label.vertices += translation
    
    def scale_foot(self, scale_factors: Tuple[float, float, float]):
        """
        Scale the foot and update linked insole proportionally.
        
        Args:
            scale_factors: (scale_x, scale_y, scale_z) factors
        """
        if self.foot_mesh is None:
            return
        
        # Store foot centroid for scaling around it
        foot_centroid = self.foot_mesh.centroid.copy()
        
        # Scale foot around its centroid
        self.foot_mesh.vertices -= foot_centroid
        self.foot_mesh.vertices *= np.array(scale_factors)
        self.foot_mesh.vertices += foot_centroid
        
        # If insole is linked, scale it proportionally
        if self._insole_linked and self.insole_mesh is not None:
            insole_centroid = self.insole_mesh.centroid.copy()
            
            # Scale insole around its own centroid
            self.insole_mesh.vertices -= insole_centroid
            self.insole_mesh.vertices *= np.array(scale_factors)
            self.insole_mesh.vertices += insole_centroid
            
            # Update the offset based on the scale
            self._link_offset = self._link_offset * np.array(scale_factors)
            
            # Move insole to maintain relative position to scaled foot
            new_insole_centroid = self.foot_mesh.centroid + self._link_offset
            translation = new_insole_centroid - self.insole_mesh.centroid
            self.insole_mesh.vertices += translation
            
            # Update before-label state if exists
            if self._insole_before_label is not None:
                self._insole_before_label.vertices -= insole_centroid
                self._insole_before_label.vertices *= np.array(scale_factors)
                self._insole_before_label.vertices += self.insole_mesh.centroid
            
            # Update original mesh for resetting
            if self.original_insole_mesh is not None:
                orig_centroid = self.original_insole_mesh.centroid.copy()
                self.original_insole_mesh.vertices -= orig_centroid
                self.original_insole_mesh.vertices *= np.array(scale_factors)
                self.original_insole_mesh.vertices += orig_centroid

    def add_text_label(self, text: str, position: str = 'heel', 
                       depth: float = 0.6, font_size: float = 3.0,
                       z_offset: float = 0.0,
                       engrave: bool = True,
                       custom_position: Optional[np.ndarray] = None,
                       custom_normal: Optional[np.ndarray] = None,
                       offset_x: float = 0, offset_y: float = 0,
                       rotation: float = 0,
                       wrap_to_surface: bool = True,
                       mirror_horizontal: bool = False,
                       mirror_vertical: bool = False) -> trimesh.Trimesh:
        """
        Add text label to the insole. Replaces any existing label.
        
        The text is wrapped/conformed to the surface curvature for proper engraving
        on curved surfaces like the side of the insole.
        
        Args:
            text: Text to add (can be multi-line with \\n)
            position: Where to place text ('heel', 'top', 'center', 'custom')
            depth: Engraving depth in mm (0.6mm default)
            font_size: Height of characters in mm (3-4mm recommended)
            z_offset: Vertical offset from picked position in mm (+ = up, - = down)
            engrave: If True, cut into surface. If False, raise above surface.
            custom_position: Custom position for label (when position='custom')
            custom_normal: Surface normal at custom position
            offset_x: X offset from picked position (in surface plane)
            offset_y: Y offset from picked position (in surface plane)
            rotation: Rotation angle in degrees (around surface normal)
            wrap_to_surface: If True, wrap text to follow surface curvature
            mirror_horizontal: If True, flip text left-right (for backwards text)
            mirror_vertical: If True, flip text up-down (for upside-down text)
            
        Returns:
            Modified mesh with text label
        """
        if self.insole_mesh is None:
            raise ValueError("No insole loaded")
        
        if not text.strip():
            return self.insole_mesh
        
        # Store label parameters for re-application after mirroring
        self._label_params = {
            'text': text,
            'position': position,
            'depth': depth,
            'font_size': font_size,
            'z_offset': z_offset,
            'engrave': engrave,
            'custom_position': custom_position.copy() if custom_position is not None else None,
            'custom_normal': custom_normal.copy() if custom_normal is not None else None,
            'offset_x': offset_x,
            'offset_y': offset_y,
            'rotation': rotation,
            'wrap_to_surface': wrap_to_surface,
            'mirror_horizontal': mirror_horizontal,
            'mirror_vertical': mirror_vertical
        }
        
        # Force label re-creation if parameters changed
        label_key = f"{text}_{position}_{offset_x}_{offset_y}_{rotation}_{wrap_to_surface}_{mirror_horizontal}_{mirror_vertical}"
        if self._current_label == label_key:
            return self.insole_mesh
        
        # If we have a before-label state, restore it first
        # This ensures we replace the old label instead of adding to it
        if self._insole_before_label is not None:
            self.insole_mesh = self._insole_before_label.copy()
        else:
            # Save current state before adding label
            self._insole_before_label = self.insole_mesh.copy()
        
        try:
            # Create 3D text mesh (handles multi-line)
            # Text is created flat in X-Y plane, extruded in Z direction
            text_mesh = self._create_multiline_text_mesh(text.upper(), font_size, depth)
            
            if text_mesh is not None and len(text_mesh.vertices) > 0:
                # Ensure text mesh is watertight for boolean operations
                try:
                    text_mesh.fill_holes()
                    text_mesh.fix_normals()
                except:
                    pass  # Continue even if fix fails
                
                # Get insole bounds
                bounds = self.insole_mesh.bounds
                insole_center = self.insole_mesh.centroid
                
                # Center the text mesh at origin first
                text_bounds = text_mesh.bounds
                text_center = (text_bounds[0] + text_bounds[1]) / 2
                text_mesh.vertices -= text_center
                
                # Apply mirror transformations if requested
                if mirror_horizontal:
                    # Flip X axis (left-right mirror)
                    text_mesh.vertices[:, 0] *= -1
                    # Fix normals after mirroring
                    text_mesh.invert()
                    
                if mirror_vertical:
                    # Flip Y axis (up-down mirror)
                    text_mesh.vertices[:, 1] *= -1
                    # Fix normals after mirroring
                    text_mesh.invert()
                
                if position == 'custom' and custom_position is not None:
                    # Custom position with surface-conforming wrapping
                    print(f"Custom label: position={custom_position}, normal={custom_normal}, rotation={rotation}°, mirror_h={mirror_horizontal}, mirror_v={mirror_vertical}")
                    
                    # Apply user rotation around the surface normal
                    if rotation != 0:
                        rot_matrix = trimesh.transformations.rotation_matrix(
                            np.radians(rotation), [0, 0, 1], point=[0, 0, 0]
                        )
                        text_mesh.apply_transform(rot_matrix)
                        
                        # Re-center after rotation
                        text_bounds = text_mesh.bounds
                        text_center = (text_bounds[0] + text_bounds[1]) / 2
                        text_mesh.vertices -= text_center
                    
                    # Wrap text to surface curvature
                    if wrap_to_surface and custom_normal is not None:
                        text_mesh = self._wrap_text_to_surface(
                            text_mesh, 
                            custom_position, 
                            custom_normal,
                            offset_x, 
                            offset_y,
                            z_offset,
                            depth,
                            engrave
                        )
                    else:
                        # Fallback to flat placement (old method)
                        target_x = custom_position[0] + offset_x
                        target_y = custom_position[1] + offset_y
                        picked_z = custom_position[2] + z_offset
                        
                        if engrave:
                            text_mesh.vertices[:, 2] -= text_mesh.bounds[0][2]
                            current_height = text_mesh.bounds[1][2] - text_mesh.bounds[0][2]
                            desired_height = depth + 50.0
                            scale_z = desired_height / current_height if current_height > 0 else 1.0
                            text_mesh.vertices[:, 2] *= scale_z
                            text_mesh.vertices[:, 2] -= depth
                            target_pos = np.array([target_x, target_y, picked_z])
                        else:
                            target_pos = np.array([target_x, target_y, picked_z])
                        
                        text_mesh.vertices += target_pos
                    
                else:
                    # Standard positions (heel, center, front)
                    # Text is in X-Y plane - rotate 90 degrees around Z so text runs along Y axis
                    rotation_z = trimesh.transformations.rotation_matrix(
                        np.radians(-90), [0, 0, 1], point=[0, 0, 0]
                    )
                    text_mesh.apply_transform(rotation_z)
                    
                    # Calculate position - heel area on top surface
                    surface_z = bounds[1][2]
                    if position == 'heel':
                        target_x = insole_center[0]
                        target_y = bounds[0][1] + (bounds[1][1] - bounds[0][1]) * 0.15
                    elif position == 'center':
                        target_x = insole_center[0]
                        target_y = insole_center[1]
                    else:  # 'front' or 'top'
                        target_x = insole_center[0]
                        target_y = bounds[1][1] - (bounds[1][1] - bounds[0][1]) * 0.15
                    
                    if engrave:
                        # For engraving: Cut EVERYTHING above surface in the text shape
                        # Text extends from HIGH above down to surface_z - depth
                        text_mesh.vertices[:, 2] -= text_mesh.bounds[0][2]  # Bottom at z=0
                        current_height = text_mesh.bounds[1][2] - text_mesh.bounds[0][2]
                        
                        # Scale Z to cover from -depth to +50mm
                        desired_height = depth + 50.0
                        scale_z = desired_height / current_height if current_height > 0 else 1.0
                        text_mesh.vertices[:, 2] *= scale_z
                        
                        # Position: bottom at -depth relative to surface
                        text_mesh.vertices[:, 2] -= depth
                        target_pos = np.array([target_x, target_y, surface_z])
                    else:
                        target_pos = np.array([target_x, target_y, surface_z])
                    
                    text_mesh.vertices += target_pos
                
                # Debug: print mesh stats and position
                print(f"Text mesh: {len(text_mesh.vertices)} vertices, {len(text_mesh.faces)} faces")
                print(f"Text bounds: {text_mesh.bounds}")
                print(f"Insole before label: {len(self.insole_mesh.vertices)} vertices")
                
                if engrave:
                    # Use MeshLib for robust boolean subtraction
                    success = self._meshlib_boolean_difference(text_mesh)
                    
                    if success:
                        self._current_label = label_key
                        print("Engrave succeeded with MeshLib")
                    else:
                        # Fallback: try trimesh engines
                        print("MeshLib failed, trying trimesh engines...")
                        engines_to_try = ['manifold', 'blender']
                        
                        for engine in engines_to_try:
                            try:
                                print(f"Trying boolean subtraction with engine: {engine}")
                                result = self.insole_mesh.difference(text_mesh, engine=engine)
                                if result is not None and len(result.vertices) > 0:
                                    self.insole_mesh = result
                                    self._current_label = label_key
                                    print(f"Engrave succeeded with {engine} engine")
                                    success = True
                                    break
                            except Exception as e:
                                print(f"Boolean with {engine} failed: {e}")
                                continue
                        
                        if not success:
                            print("All boolean engines failed. Using visual engrave...")
                            # Visual engrave fallback:
                            # Invert the text mesh normals so the inside faces outward
                            text_mesh.invert()
                            combined = trimesh.util.concatenate([self.insole_mesh, text_mesh])
                            if combined is not None and len(combined.vertices) > 0:
                                self.insole_mesh = combined
                                self._current_label = label_key
                                print("Visual engrave applied (inverted normals fallback)")
                else:
                    # For embossing: just concatenate (text sticks up from surface)
                    combined = trimesh.util.concatenate([self.insole_mesh, text_mesh])
                    if combined is not None and len(combined.vertices) > 0:
                        self.insole_mesh = combined
                        self._current_label = label_key
                
                print(f"Final mesh: {len(self.insole_mesh.vertices)} vertices")
            
            return self.insole_mesh
            
        except Exception as e:
            print(f"Warning: Could not create 3D text: {e}")
            import traceback
            traceback.print_exc()
            return self.insole_mesh
    
    def _wrap_text_to_surface(self, text_mesh: trimesh.Trimesh, 
                               center_pos: np.ndarray,
                               surface_normal: np.ndarray,
                               offset_x: float, offset_y: float,
                               z_offset: float,
                               depth: float,
                               engrave: bool) -> trimesh.Trimesh:
        """
        Wrap/conform the flat text mesh to follow the curved surface of the insole.
        
        This method:
        1. Orients the text to face outward from the surface (using surface normal)
        2. Samples the surface along the text width to find the curvature
        3. Deforms each vertex to follow the surface curvature
        4. Creates proper depth for engraving/embossing
        
        Args:
            text_mesh: Flat text mesh (in XY plane, extruded in Z)
            center_pos: Center position on the insole surface
            surface_normal: Normal vector at the center position
            offset_x: X offset in the text's local coordinate system
            offset_y: Y offset (along text direction)  
            z_offset: Vertical offset
            depth: Engraving depth
            engrave: Whether this is engraving (True) or embossing (False)
            
        Returns:
            Transformed text mesh wrapped to surface
        """
        if self.insole_mesh is None:
            return text_mesh
        
        # Get text dimensions
        text_bounds = text_mesh.bounds
        text_width = text_bounds[1][0] - text_bounds[0][0]  # X extent (text runs along X)
        text_height = text_bounds[1][1] - text_bounds[0][1]  # Y extent (character height)
        text_depth = text_bounds[1][2] - text_bounds[0][2]  # Z extent (extrusion depth)
        
        print(f"Text dimensions: width={text_width:.1f}, height={text_height:.1f}, depth={text_depth:.1f}")
        
        # Normalize the surface normal (points outward from surface)
        normal = surface_normal / np.linalg.norm(surface_normal)
        
        # Determine coordinate frame for text placement
        # We need: text_right (along text), text_up (character height), normal (into/out of surface)
        world_up = np.array([0, 0, 1])
        
        # Check if the surface is mostly horizontal (top/bottom) or vertical (side)
        normal_z_component = abs(np.dot(normal, world_up))
        
        if normal_z_component > 0.7:
            # Surface is mostly horizontal (top or bottom of insole)
            # Text flows along Y, height along X
            text_right = np.array([0, 1, 0])  # Text flows in Y direction
            text_up = np.array([1, 0, 0])     # Height in X direction
            # Adjust normal to point in the dominant direction
            normal = np.array([0, 0, 1]) if normal[2] > 0 else np.array([0, 0, -1])
        else:
            # Surface is mostly vertical (side of insole)
            # Text flows horizontally around the side, height is vertical (Z)
            text_up = world_up  # Character height goes up in Z
            
            # Text_right should be tangent to the surface, perpendicular to both normal and up
            text_right = np.cross(text_up, normal)
            if np.linalg.norm(text_right) < 0.001:
                text_right = np.array([1, 0, 0])
            else:
                text_right = text_right / np.linalg.norm(text_right)
        
        print(f"Coordinate frame: normal={normal}, text_right={text_right}, text_up={text_up}")
        
        # Apply offsets to get the adjusted center position
        adjusted_center = (center_pos + 
                          text_right * offset_x + 
                          text_up * (offset_y + z_offset))
        
        # Sample surface points along the text width to capture curvature
        num_samples = 30
        sample_positions = []
        sample_normals = []
        
        for i in range(num_samples):
            # Sample from -0.5 to 0.5 of text width (centered)
            t = (i / (num_samples - 1)) - 0.5
            sample_offset = t * text_width * 1.1  # Slightly wider than text
            
            # Position along the text direction
            sample_point = adjusted_center + text_right * sample_offset
            
            # Cast ray from outside the mesh inward to find surface
            ray_origin = sample_point + normal * 100  # Start far outside
            ray_direction = -normal  # Point inward
            
            locations, index_ray, index_tri = self.insole_mesh.ray.intersects_location(
                ray_origins=[ray_origin],
                ray_directions=[ray_direction]
            )
            
            if len(locations) > 0:
                # Find the closest hit to our expected position
                distances = np.linalg.norm(locations - sample_point, axis=1)
                closest_idx = np.argmin(distances)
                hit_point = locations[closest_idx]
                hit_tri = index_tri[closest_idx]
                hit_normal = self.insole_mesh.face_normals[hit_tri]
                hit_normal = hit_normal / np.linalg.norm(hit_normal)
                
                sample_positions.append(hit_point)
                sample_normals.append(hit_normal)
            else:
                # No hit - use the center position projected along text_right
                sample_positions.append(sample_point)
                sample_normals.append(normal)
        
        # Get the original text mesh bounds for mapping
        x_min, x_max = text_bounds[0][0], text_bounds[1][0]
        y_min, y_max = text_bounds[0][1], text_bounds[1][1]
        z_min, z_max = text_bounds[0][2], text_bounds[1][2]
        x_range = x_max - x_min if x_max > x_min else 1.0
        z_range = z_max - z_min if z_max > z_min else 1.0
        
        # Transform each vertex
        vertices = text_mesh.vertices.copy()
        new_vertices = []
        
        for v in vertices:
            # Map X position (0 to 1) along the sampled surface curve
            t = (v[0] - x_min) / x_range
            t = np.clip(t, 0, 1)
            
            # Interpolate surface position and normal from samples
            sample_idx = t * (num_samples - 1)
            idx_low = int(sample_idx)
            idx_high = min(idx_low + 1, num_samples - 1)
            frac = sample_idx - idx_low
            
            surf_pos = (1 - frac) * np.array(sample_positions[idx_low]) + frac * np.array(sample_positions[idx_high])
            surf_normal = (1 - frac) * np.array(sample_normals[idx_low]) + frac * np.array(sample_normals[idx_high])
            surf_normal = surf_normal / (np.linalg.norm(surf_normal) + 1e-8)
            
            # Map Y position (character height) - offset along text_up direction
            height_offset = v[1] - (y_min + y_max) / 2  # Center the text vertically
            
            # Map Z position (depth into/out of surface)
            # Normalize Z to 0-1 range where 0 is bottom of text, 1 is top
            z_normalized = (v[2] - z_min) / z_range if z_range > 0 else 0
            
            if engrave:
                # For engraving: text cuts INTO the surface
                # We need to create a solid that extends from slightly outside to depth inside
                # z_normalized=0 (bottom of original text) -> depth mm inside surface
                # z_normalized=1 (top of original text) -> slightly outside surface (for clean boolean)
                max_inward = depth  # Only go as deep as specified (e.g., 0.6mm)
                max_outward = 0.5  # Small amount outside for clean boolean cut
                total_range = max_inward + max_outward
                # Map z: 0 -> max_inward inside, 1 -> max_outward outside
                distance_from_surface = max_outward - z_normalized * total_range
                new_pos = surf_pos + text_up * height_offset + surf_normal * distance_from_surface
            else:
                # For embossing: text comes OUT of the surface  
                # z_normalized=0 -> at surface
                # z_normalized=1 -> depth mm outside surface
                outward_distance = depth * z_normalized
                new_pos = surf_pos + text_up * height_offset + surf_normal * outward_distance
            
            new_vertices.append(new_pos)
        
        text_mesh.vertices = np.array(new_vertices)
        
        # Fix normals after deformation
        try:
            text_mesh.fix_normals()
        except:
            pass
        
        print(f"Wrapped text bounds: {text_mesh.bounds}")
        return text_mesh
    def _meshlib_boolean_difference(self, text_mesh: trimesh.Trimesh) -> bool:
        """
        Perform boolean difference using MeshLib for robust CSG operations.
        
        Args:
            text_mesh: The text mesh to subtract from the insole
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import meshlib.mrmeshpy as mr
            import tempfile
            import os
            
            print("Using MeshLib for boolean difference...")
            
            # Save meshes to temporary STL files (MeshLib works best with file I/O)
            with tempfile.TemporaryDirectory() as tmpdir:
                insole_path = os.path.join(tmpdir, "insole.stl")
                text_path = os.path.join(tmpdir, "text.stl")
                result_path = os.path.join(tmpdir, "result.stl")
                
                # Export trimesh to STL
                self.insole_mesh.export(insole_path)
                text_mesh.export(text_path)
                
                # Load into MeshLib
                insole_mr = mr.loadMesh(insole_path)
                text_mr = mr.loadMesh(text_path)
                
                print(f"MeshLib loaded: insole={insole_mr.topology.numValidFaces()} faces, text={text_mr.topology.numValidFaces()} faces")
                
                # Perform boolean difference (insole - text)
                result = mr.boolean(insole_mr, text_mr, mr.BooleanOperation.DifferenceAB)
                
                if result.valid() and result.mesh.topology.numValidFaces() > 0:
                    # Save result
                    mr.saveMesh(result.mesh, result_path)
                    
                    # Load back into trimesh
                    result_mesh = trimesh.load(result_path)
                    if result_mesh is not None and len(result_mesh.vertices) > 0:
                        # Fix normals for proper rendering
                        result_mesh.fix_normals()
                        self.insole_mesh = result_mesh
                        print(f"MeshLib boolean success: {len(result_mesh.vertices)} vertices, {len(result_mesh.faces)} faces")
                        return True
                    else:
                        print("MeshLib result mesh is empty")
                        return False
                else:
                    error_msg = result.errorString if hasattr(result, 'errorString') else "Unknown error"
                    print(f"MeshLib boolean failed: {error_msg}")
                    return False
                    
        except ImportError:
            print("MeshLib not available")
            return False
        except Exception as e:
            print(f"MeshLib boolean error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
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
        # Split on actual newline character
        lines = text.split('\n')
        line_meshes = []
        line_spacing = font_size * 1.4  # Space between lines
        
        for line_idx, line in enumerate(lines):
            line_text = line.strip()
            if not line_text:
                continue
            line_mesh = self._create_text_mesh(line_text, font_size, depth)
            if line_mesh is not None:
                # Offset each line vertically (in Y direction for top-down view)
                y_offset = -line_idx * line_spacing
                line_mesh.vertices[:, 1] += y_offset
                line_meshes.append(line_mesh)
        
        if line_meshes:
            combined = trimesh.util.concatenate(line_meshes)
            return combined
        
        return None
    
    def _create_text_mesh(self, text: str, font_size: float, depth: float) -> Optional[trimesh.Trimesh]:
        """
        Create a 3D mesh of text using the best available font engine.
        Priority: FreeType (CAD-quality) > Matplotlib > Polygon fallback
        
        Args:
            text: Text to create
            font_size: Height of each character
            depth: Extrusion depth
            
        Returns:
            Combined mesh of all characters
        """
        # Skip FreeType - use matplotlib directly for faster generation
        # FreeType with adaptive bezier is too slow for interactive use
        
        # Use matplotlib-based text path (fast and good quality)
        try:
            mesh = self._create_text_mesh_matplotlib_fast(text, font_size, depth)
            if mesh is not None:
                return mesh
        except Exception as e:
            print(f"Matplotlib fast text failed: {e}")
        
        # Fallback to polygon-based rendering
        return self._create_text_mesh_polygon(text.upper(), font_size, depth)
    
    def _create_text_mesh_freetype(self, text: str, font_size: float, depth: float) -> Optional[trimesh.Trimesh]:
        """
        Create 3D text mesh using FreeType for CAD-quality font outlines.
        FreeType provides proper glyph outlines with correct winding and watertight geometry.
        
        Args:
            text: Text to create
            font_size: Character height in mm
            depth: Extrusion depth in mm
            
        Returns:
            Extruded text mesh or None
        """
        try:
            import freetype
        except ImportError:
            return None
        
        from shapely.geometry import Polygon, MultiPolygon
        from shapely.ops import unary_union
        from shapely.validation import make_valid
        
        if not text.strip():
            return None
        
        # Find a suitable font file
        font_path = self._find_system_font()
        if font_path is None:
            return None
        
        try:
            face = freetype.Face(font_path)
        except Exception as e:
            print(f"Failed to load font: {e}")
            return None
        
        # Set font size - FreeType uses 1/64th of a point
        # We want font_size in mm, so we scale appropriately
        # Use 64 * font_size * 64 = font_size * 4096 for high resolution
        face.set_char_size(int(font_size * 64 * 64))
        
        # Adaptive tolerance for Bezier subdivision
        # Use larger tolerance for faster generation (0.1-0.2mm is fine for 3D printing)
        tolerance = max(0.1, font_size * 0.03)
        
        all_polygons = []
        pen_x = 0.0  # Current x position (advance)
        
        for char in text:
            if char == ' ':
                # Advance for space
                face.load_char(char, freetype.FT_LOAD_NO_BITMAP)
                pen_x += face.glyph.advance.x / 64.0 / 64.0  # Convert from 26.6 fixed point
                continue
            
            try:
                face.load_char(char, freetype.FT_LOAD_NO_BITMAP)
            except:
                continue
            
            outline = face.glyph.outline
            
            # Scale factor: FreeType units to mm
            scale = 1.0 / 64.0 / 64.0  # Convert from 26.6 fixed point * 64
            
            # Extract contours from outline
            char_polygons = self._freetype_outline_to_polygons(outline, tolerance, scale, pen_x)
            all_polygons.extend(char_polygons)
            
            # Advance pen position
            pen_x += face.glyph.advance.x / 64.0 / 64.0
        
        if not all_polygons:
            return None
        
        # Clean and merge polygons
        cleaned = []
        for poly in all_polygons:
            try:
                poly = poly.buffer(0)
                if not poly.is_valid:
                    poly = make_valid(poly)
                if not poly.is_empty and poly.area > 0.001:
                    if isinstance(poly, MultiPolygon):
                        cleaned.extend(p for p in poly.geoms if p.area > 0.001)
                    else:
                        cleaned.append(poly)
            except:
                continue
        
        if not cleaned:
            return None
        
        # Merge all character polygons
        try:
            merged = unary_union(cleaned)
            merged = merged.buffer(0)
            if not merged.is_valid:
                merged = make_valid(merged)
        except:
            return None
        
        # Light simplification
        try:
            merged = merged.simplify(font_size * 0.005, preserve_topology=True)
        except:
            pass
        
        # Extrude to 3D
        return self._extrude_text_polygon(merged, depth, font_size)
    
    def _find_system_font(self) -> Optional[str]:
        """Find a suitable system font for text rendering."""
        import os
        import platform
        
        font_names = ['arial.ttf', 'Arial.ttf', 'DejaVuSans.ttf', 'Helvetica.ttf', 
                      'Liberation Sans-Regular.ttf', 'FreeSans.ttf']
        
        if platform.system() == 'Windows':
            font_dirs = [
                os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts'),
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Windows', 'Fonts')
            ]
        elif platform.system() == 'Darwin':
            font_dirs = ['/Library/Fonts', '/System/Library/Fonts', os.path.expanduser('~/Library/Fonts')]
        else:
            font_dirs = ['/usr/share/fonts/truetype', '/usr/share/fonts', os.path.expanduser('~/.fonts')]
        
        for font_dir in font_dirs:
            if os.path.exists(font_dir):
                for font in font_names:
                    font_path = os.path.join(font_dir, font)
                    if os.path.exists(font_path):
                        return font_path
                # Search subdirectories
                for root, dirs, files in os.walk(font_dir):
                    for font in font_names:
                        if font.lower() in [f.lower() for f in files]:
                            for f in files:
                                if f.lower() == font.lower():
                                    return os.path.join(root, f)
        
        return None
    
    def _freetype_outline_to_polygons(self, outline, tolerance: float, scale: float, offset_x: float) -> list:
        """
        Convert FreeType outline to Shapely polygons with adaptive Bezier subdivision.
        
        Args:
            outline: FreeType outline object
            tolerance: Bezier subdivision tolerance
            scale: Scale factor from FreeType units to mm
            offset_x: X offset for character positioning
            
        Returns:
            List of Shapely Polygon objects
        """
        from shapely.geometry import Polygon
        
        polygons = []
        points = outline.points
        tags = outline.tags
        contours = outline.contours  # End indices of each contour
        
        start = 0
        for end in contours:
            contour_points = []
            i = start
            
            while i <= end:
                # Get point and tag
                pt = points[i]
                tag = tags[i]
                
                # Scale and offset
                x = pt[0] * scale + offset_x
                y = pt[1] * scale
                
                if tag & 1:  # On-curve point
                    contour_points.append((x, y))
                    i += 1
                else:
                    # Off-curve point (control point for quadratic Bezier)
                    # Need to find the on-curve points before and after
                    
                    # Previous on-curve point
                    if contour_points:
                        p0 = contour_points[-1]
                    else:
                        # Handle case where contour starts with off-curve
                        prev_idx = end if i == start else i - 1
                        prev_pt = points[prev_idx]
                        p0 = (prev_pt[0] * scale + offset_x, prev_pt[1] * scale)
                    
                    p1 = (x, y)  # Control point
                    
                    # Next point
                    next_i = i + 1 if i < end else start
                    next_pt = points[next_i]
                    next_tag = tags[next_i]
                    next_x = next_pt[0] * scale + offset_x
                    next_y = next_pt[1] * scale
                    
                    if next_tag & 1:
                        # Next is on-curve
                        p2 = (next_x, next_y)
                        i += 1
                    else:
                        # Next is also off-curve, create implicit on-curve midpoint
                        p2 = ((x + next_x) / 2, (y + next_y) / 2)
                    
                    # Adaptive subdivision of quadratic Bezier
                    curve_pts = self._adaptive_bezier_quadratic(p0, p1, p2, tolerance)
                    contour_points.extend(curve_pts)
                    
                    if next_tag & 1:
                        i += 1
                    # If next was off-curve, don't increment (we'll process it next)
            
            # Create polygon from contour
            if len(contour_points) >= 3:
                try:
                    poly = Polygon(contour_points)
                    if poly.is_valid and poly.area > 0.001:
                        polygons.append(poly)
                except:
                    pass
            
            start = end + 1
        
        return polygons
    
    def _extrude_text_polygon(self, merged, depth: float, font_size: float) -> Optional[trimesh.Trimesh]:
        """
        Extrude a merged text polygon to 3D with optional subdivision.
        
        Args:
            merged: Shapely polygon or multipolygon
            depth: Extrusion depth
            font_size: Font size for centering
            
        Returns:
            Extruded mesh
        """
        from shapely.geometry import Polygon, MultiPolygon
        
        meshes = []
        
        def extrude_polygon(poly):
            try:
                if poly.is_valid and poly.area > 0.01:
                    poly = poly.buffer(0)
                    if not poly.is_valid or poly.is_empty:
                        return None
                    mesh = trimesh.creation.extrude_polygon(poly, height=depth, engine='earcut')
                    return mesh
            except Exception as e:
                print(f"Extrusion failed: {e}")
            return None
        
        if isinstance(merged, MultiPolygon):
            for poly in merged.geoms:
                mesh = extrude_polygon(poly)
                if mesh is not None:
                    meshes.append(mesh)
        elif hasattr(merged, 'geoms'):
            for geom in merged.geoms:
                if isinstance(geom, (Polygon, MultiPolygon)):
                    if isinstance(geom, MultiPolygon):
                        for poly in geom.geoms:
                            mesh = extrude_polygon(poly)
                            if mesh is not None:
                                meshes.append(mesh)
                    else:
                        mesh = extrude_polygon(geom)
                        if mesh is not None:
                            meshes.append(mesh)
        else:
            mesh = extrude_polygon(merged)
            if mesh is not None:
                meshes.append(mesh)
        
        if meshes:
            combined = trimesh.util.concatenate(meshes)
            
            # Skip subdivision - adaptive bezier already provides smooth curves
            # Subdivision doubles face count and is slow
            
            # Center the text
            bounds = combined.bounds
            center_x = (bounds[0][0] + bounds[1][0]) / 2
            combined.vertices[:, 0] -= center_x
            return combined
        
        return None
    
    def _adaptive_bezier_quadratic(self, p0: tuple, p1: tuple, p2: tuple, tolerance: float = 0.1, depth: int = 0, max_depth: int = 5) -> list:
        """
        Adaptively subdivide a quadratic Bezier curve based on chord-distance tolerance.
        Recursively splits until the curve deviates less than tolerance from the chord.
        
        Args:
            p0, p1, p2: Control points (start, control, end)
            tolerance: Maximum allowed distance from curve to chord (mm)
            depth: Current recursion depth
            max_depth: Maximum recursion depth (5 = max 32 segments per curve)
            
        Returns:
            List of points approximating the curve (excluding p0)
        """
        # Stop if max depth reached
        if depth >= max_depth:
            return [p2]
        
        # Calculate midpoint on curve at t=0.5
        mid_t = 0.5
        mid_x = (1-mid_t)**2 * p0[0] + 2*(1-mid_t)*mid_t * p1[0] + mid_t**2 * p2[0]
        mid_y = (1-mid_t)**2 * p0[1] + 2*(1-mid_t)*mid_t * p1[1] + mid_t**2 * p2[1]
        mid_curve = (mid_x, mid_y)
        
        # Calculate midpoint on chord (straight line from p0 to p2)
        mid_chord = ((p0[0] + p2[0]) / 2, (p0[1] + p2[1]) / 2)
        
        # Distance from curve midpoint to chord midpoint
        dist = np.sqrt((mid_curve[0] - mid_chord[0])**2 + (mid_curve[1] - mid_chord[1])**2)
        
        if dist <= tolerance:
            # Curve is flat enough, return endpoint
            return [p2]
        else:
            # Subdivide: use de Casteljau's algorithm
            # Left half control points
            p01 = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
            p12 = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
            p012 = ((p01[0] + p12[0]) / 2, (p01[1] + p12[1]) / 2)
            
            # Recursively subdivide both halves
            left = self._adaptive_bezier_quadratic(p0, p01, p012, tolerance, depth + 1, max_depth)
            right = self._adaptive_bezier_quadratic(p012, p12, p2, tolerance, depth + 1, max_depth)
            
            return left + right
    
    def _adaptive_bezier_cubic(self, p0: tuple, p1: tuple, p2: tuple, p3: tuple, tolerance: float = 0.1, depth: int = 0, max_depth: int = 5) -> list:
        """
        Adaptively subdivide a cubic Bezier curve based on chord-distance tolerance.
        Recursively splits until the curve deviates less than tolerance from the chord.
        
        Args:
            p0, p1, p2, p3: Control points
            tolerance: Maximum allowed distance from curve to chord (mm)
            depth: Current recursion depth
            max_depth: Maximum recursion depth (5 = max 32 segments per curve)
            
        Returns:
            List of points approximating the curve (excluding p0)
        """
        # Stop if max depth reached
        if depth >= max_depth:
            return [p3]
        
        # Calculate point on curve at t=0.5
        mid_t = 0.5
        mid_x = (1-mid_t)**3 * p0[0] + 3*(1-mid_t)**2*mid_t * p1[0] + 3*(1-mid_t)*mid_t**2 * p2[0] + mid_t**3 * p3[0]
        mid_y = (1-mid_t)**3 * p0[1] + 3*(1-mid_t)**2*mid_t * p1[1] + 3*(1-mid_t)*mid_t**2 * p2[1] + mid_t**3 * p3[1]
        mid_curve = (mid_x, mid_y)
        
        # Calculate midpoint on chord (straight line from p0 to p3)
        mid_chord = ((p0[0] + p3[0]) / 2, (p0[1] + p3[1]) / 2)
        
        # Also check distance of control points to chord
        # This catches S-curves that might pass through the chord midpoint
        def point_to_line_dist(point, line_start, line_end):
            """Distance from point to line segment"""
            dx = line_end[0] - line_start[0]
            dy = line_end[1] - line_start[1]
            length_sq = dx*dx + dy*dy
            if length_sq < 1e-10:
                return np.sqrt((point[0] - line_start[0])**2 + (point[1] - line_start[1])**2)
            t = max(0, min(1, ((point[0] - line_start[0]) * dx + (point[1] - line_start[1]) * dy) / length_sq))
            proj_x = line_start[0] + t * dx
            proj_y = line_start[1] + t * dy
            return np.sqrt((point[0] - proj_x)**2 + (point[1] - proj_y)**2)
        
        dist_mid = np.sqrt((mid_curve[0] - mid_chord[0])**2 + (mid_curve[1] - mid_chord[1])**2)
        dist_p1 = point_to_line_dist(p1, p0, p3)
        dist_p2 = point_to_line_dist(p2, p0, p3)
        
        max_dist = max(dist_mid, dist_p1, dist_p2)
        
        if max_dist <= tolerance:
            # Curve is flat enough, return endpoint
            return [p3]
        else:
            # Subdivide using de Casteljau's algorithm
            p01 = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
            p12 = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
            p23 = ((p2[0] + p3[0]) / 2, (p2[1] + p3[1]) / 2)
            
            p012 = ((p01[0] + p12[0]) / 2, (p01[1] + p12[1]) / 2)
            p123 = ((p12[0] + p23[0]) / 2, (p12[1] + p23[1]) / 2)
            
            p0123 = ((p012[0] + p123[0]) / 2, (p012[1] + p123[1]) / 2)
            
            # Recursively subdivide both halves
            left = self._adaptive_bezier_cubic(p0, p01, p012, p0123, tolerance, depth + 1, max_depth)
            right = self._adaptive_bezier_cubic(p0123, p123, p23, p3, tolerance, depth + 1, max_depth)
            
            return left + right
    
    def _create_text_mesh_matplotlib_fast(self, text: str, font_size: float, depth: float) -> Optional[trimesh.Trimesh]:
        """
        Create 3D text mesh using matplotlib's TextPath with improved sampling.
        Optimized for both quality and speed (~200-400ms).
        
        Improvements:
        - 12 samples for quadratic, 16 for cubic (smoother curves)
        - polygon.buffer(0) to fix self-intersections
        - Light mesh subdivision for better edges
        """
        from matplotlib.textpath import TextPath
        from matplotlib.font_manager import FontProperties
        from shapely.geometry import Polygon, MultiPolygon
        from shapely.ops import unary_union
        
        if not text.strip():
            return None
        
        font_props = FontProperties(family='sans-serif', weight='bold')
        text_path = TextPath((0, 0), text, size=font_size, prop=font_props)
        
        # matplotlib path codes
        MOVETO, LINETO, CURVE3, CURVE4, CLOSEPOLY = 1, 2, 3, 4, 79
        
        polygons = []
        current_polygon = []
        vertices = text_path.vertices
        codes = text_path.codes
        
        # Increased samples for smoother curves (still fast: <400ms)
        # Using numpy linspace for even distribution
        t_samples_quad = np.linspace(0, 1, 12)[1:]  # 11 samples (skip 0)
        t_samples_cubic = np.linspace(0, 1, 16)[1:]  # 15 samples (skip 0)
        
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
                # Quadratic bezier with improved sampling
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
                # Cubic bezier with improved sampling
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
        
        # Handle remaining polygon
        if len(current_polygon) >= 3:
            try:
                poly = Polygon(current_polygon)
                if poly.is_valid and poly.area > 0.001:
                    polygons.append(poly)
            except:
                pass
        
        if not polygons:
            return None
        
        # Convert contours to valid polygons
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
        
        # Extrude to 3D with better watertight mesh
        meshes = []
        
        def extrude_poly(p):
            try:
                if p.is_valid and p.area > 0.01:
                    # Try triangle engine first (more reliable for watertight)
                    # Fall back to earcut if triangle not available
                    try:
                        mesh = trimesh.creation.extrude_polygon(p, height=depth, engine='triangle')
                    except:
                        mesh = trimesh.creation.extrude_polygon(p, height=depth, engine='earcut')
                    return mesh
            except:
                pass
            return None
        
        for poly in final_polygons:
            if isinstance(poly, MultiPolygon):
                for p in poly.geoms:
                    m = extrude_poly(p)
                    if m:
                        meshes.append(m)
            else:
                m = extrude_poly(poly)
                if m:
                    meshes.append(m)
        
        if meshes:
            combined = trimesh.util.concatenate(meshes)
            
            # Light mesh subdivision for smoother edges (1 level only)
            try:
                if len(combined.faces) < 20000:  # Only if mesh is reasonably small
                    combined = combined.subdivide()
            except:
                pass  # Skip subdivision if it fails
            
            # Center text
            bounds = combined.bounds
            center_x = (bounds[0][0] + bounds[1][0]) / 2
            combined.vertices[:, 0] -= center_x
            return combined
        
        return None
    
    def _create_text_mesh_matplotlib(self, text: str, font_size: float, depth: float) -> Optional[trimesh.Trimesh]:
        """
        Create 3D text mesh using matplotlib's TextPath with adaptive Bezier subdivision.
        Uses polygon cleanup and mesh subdivision for CAD-quality output.
        """
        from matplotlib.textpath import TextPath
        from matplotlib.font_manager import FontProperties
        from shapely.geometry import Polygon, MultiPolygon
        from shapely.ops import unary_union
        from shapely.validation import make_valid
        
        if not text.strip():
            return None
        
        # Use a clear, readable font
        font_props = FontProperties(family='sans-serif', weight='bold')
        
        # Create text path - font_size in points
        text_path = TextPath((0, 0), text, size=font_size, prop=font_props)
        
        # Adaptive subdivision tolerance: larger = faster, 0.1mm is good for 3D printing
        tolerance = max(0.1, font_size * 0.03)
        
        # Convert path to polygons with adaptive Bezier subdivision
        polygons = []
        current_polygon = []
        
        # Iterate through path vertices and codes
        vertices = text_path.vertices
        codes = text_path.codes
        
        # matplotlib path codes: MOVETO=1, LINETO=2, CURVE3=3, CURVE4=4, CLOSEPOLY=79
        MOVETO, LINETO, CURVE3, CURVE4, CLOSEPOLY = 1, 2, 3, 4, 79
        
        i = 0
        while i < len(codes):
            code = codes[i]
            
            if code == MOVETO:
                # Start new polygon
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
                # Quadratic bezier with adaptive subdivision
                if len(current_polygon) > 0:
                    p0 = current_polygon[-1]
                    p1 = tuple(vertices[i])
                    p2 = tuple(vertices[i + 1])
                    # Adaptive subdivision based on curvature
                    curve_points = self._adaptive_bezier_quadratic(p0, p1, p2, tolerance)
                    current_polygon.extend(curve_points)
                i += 2
                
            elif code == CURVE4:
                # Cubic bezier with adaptive subdivision
                if len(current_polygon) > 0:
                    p0 = current_polygon[-1]
                    p1 = tuple(vertices[i])
                    p2 = tuple(vertices[i + 1])
                    p3 = tuple(vertices[i + 2])
                    # Adaptive subdivision based on curvature
                    curve_points = self._adaptive_bezier_cubic(p0, p1, p2, p3, tolerance)
                    current_polygon.extend(curve_points)
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
        
        # Handle any remaining polygon
        if len(current_polygon) >= 3:
            try:
                poly = Polygon(current_polygon)
                if poly.is_valid and poly.area > 0.001:
                    polygons.append(poly)
            except:
                pass
        
        if not polygons:
            return None
        
        # ===== FIX 3: Polygon cleanup before merging =====
        cleaned_polygons = []
        for poly in polygons:
            try:
                # Fix self-intersections with buffer(0)
                poly = poly.buffer(0)
                if poly.is_empty:
                    continue
                # Make valid if still invalid
                if not poly.is_valid:
                    poly = make_valid(poly)
                if isinstance(poly, MultiPolygon):
                    for p in poly.geoms:
                        if p.is_valid and p.area > 0.001:
                            cleaned_polygons.append(p)
                elif poly.is_valid and poly.area > 0.001:
                    cleaned_polygons.append(poly)
            except:
                cleaned_polygons.append(poly)
        
        if not cleaned_polygons:
            return None
        
        polygons = cleaned_polygons
        
        # Merge overlapping polygons and handle holes
        try:
            merged = unary_union(polygons)
            # Clean the merged result
            merged = merged.buffer(0)
            if not merged.is_valid:
                merged = make_valid(merged)
        except:
            merged = polygons[0]
            for p in polygons[1:]:
                try:
                    merged = merged.union(p)
                except:
                    pass
        
        # Very light simplification to remove microscopic vertices without losing shape
        # Use tolerance of 0.5% of font size
        simplify_tolerance = font_size * 0.005
        try:
            merged = merged.simplify(simplify_tolerance, preserve_topology=True)
        except:
            pass
        
        # Extrude the result
        meshes = []
        
        def extrude_polygon(poly):
            try:
                if poly.is_valid and poly.area > 0.01:
                    # Final cleanup before extrusion
                    poly = poly.buffer(0)
                    if not poly.is_valid or poly.is_empty:
                        return None
                    mesh = trimesh.creation.extrude_polygon(poly, height=depth, engine='earcut')
                    return mesh
            except Exception as e:
                print(f"Extrusion failed for polygon: {e}")
            return None
        
        if isinstance(merged, MultiPolygon):
            for poly in merged.geoms:
                mesh = extrude_polygon(poly)
                if mesh is not None:
                    meshes.append(mesh)
        elif hasattr(merged, 'geoms'):
            # Handle GeometryCollection
            for geom in merged.geoms:
                if isinstance(geom, (Polygon, MultiPolygon)):
                    if isinstance(geom, MultiPolygon):
                        for poly in geom.geoms:
                            mesh = extrude_polygon(poly)
                            if mesh is not None:
                                meshes.append(mesh)
                    else:
                        mesh = extrude_polygon(geom)
                        if mesh is not None:
                            meshes.append(mesh)
        else:
            mesh = extrude_polygon(merged)
            if mesh is not None:
                meshes.append(mesh)
        
        if meshes:
            combined = trimesh.util.concatenate(meshes)
            
            # ===== FIX 4: Subdivide mesh for smoother edges =====
            # Subdivide faces to improve mesh quality, especially side faces
            try:
                # Only subdivide if mesh has reasonable face count
                if len(combined.faces) < 50000:
                    # Use trimesh's built-in subdivision
                    combined = combined.subdivide()
            except Exception as e:
                print(f"Subdivision warning: {e}")
            
            # Center the text
            bounds = combined.bounds
            center_x = (bounds[0][0] + bounds[1][0]) / 2
            combined.vertices[:, 0] -= center_x
            return combined
        
        return None
    
    def _create_text_mesh_polygon(self, text: str, font_size: float, depth: float) -> Optional[trimesh.Trimesh]:
        """
        Fallback: Create a 3D mesh of text using predefined polygon paths.
        
        Args:
            text: Text to create (should be uppercase)
            font_size: Height of each character
            depth: Extrusion depth
            
        Returns:
            Combined mesh of all characters
        """
        meshes = []
        char_width = font_size * 0.7  # Width of each character cell
        spacing = font_size * 0.15    # Space between characters
        x_offset = 0
        
        for char in text:
            if char == ' ':
                x_offset += char_width * 0.5
                continue
            
            # Get character path or use a simple box for unknown characters
            if char in LETTER_PATHS:
                paths = LETTER_PATHS[char]
            else:
                # Fallback: simple box for unknown characters
                paths = [[(0.1, 0.1), (0.1, 0.9), (0.9, 0.9), (0.9, 0.1), (0.1, 0.1)]]
            
            if not paths:
                x_offset += char_width * 0.5
                continue
            
            try:
                char_mesh = self._extrude_character(paths, font_size, depth)
                
                if char_mesh is not None:
                    # Position character
                    char_mesh.vertices[:, 0] += x_offset
                    meshes.append(char_mesh)
                
            except Exception as e:
                print(f"Warning: Could not create character '{char}': {e}")
            
            x_offset += char_width + spacing
        
        if meshes:
            combined = trimesh.util.concatenate(meshes)
            # Center the text
            bounds = combined.bounds
            center_x = (bounds[0][0] + bounds[1][0]) / 2
            combined.vertices[:, 0] -= center_x
            return combined
        
        return None
    
    def _extrude_character(self, paths: List[List[Tuple[float, float]]], 
                           font_size: float, depth: float) -> Optional[trimesh.Trimesh]:
        """
        Extrude a character from its 2D path definition.
        
        Args:
            paths: List of polygon paths (first is outer, rest are holes)
            font_size: Character height
            depth: Extrusion depth
            
        Returns:
            Extruded 3D mesh
        """
        from shapely.geometry import Polygon
        
        if not paths or not paths[0]:
            return None
        
        try:
            # Create outer polygon scaled to font_size
            outer_path = [(x * font_size, y * font_size) for x, y in paths[0]]
            polygon = Polygon(outer_path)
            
            # Add holes if any
            if len(paths) > 1:
                holes = []
                for hole_path in paths[1:]:
                    if hole_path:
                        hole = [(x * font_size, y * font_size) for x, y in hole_path]
                        holes.append(hole)
                if holes:
                    polygon = Polygon(outer_path, holes)
            
            if not polygon.is_valid:
                polygon = polygon.buffer(0)  # Fix invalid polygons
            
            if polygon.is_empty or polygon.area < 0.01:
                return None
            
            # Extrude the polygon using mapbox-earcut engine
            mesh = trimesh.creation.extrude_polygon(polygon, height=depth, engine='earcut')
            
            return mesh
            
        except Exception as e:
            print(f"Extrusion error: {e}")
            return None
    
    def save_stl(self, filepath: str, mesh: Optional[trimesh.Trimesh] = None) -> str:
        """Save mesh to STL file."""
        if mesh is None:
            mesh = self.insole_mesh
        
        if mesh is None:
            raise ValueError("No mesh to save")
        
        if not filepath.lower().endswith('.stl'):
            filepath += '.stl'
        
        dir_path = os.path.dirname(filepath)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        mesh.export(filepath, file_type='stl')
        
        return filepath
    
    def generate_filename(self, name: str, side: str, date: str, 
                         base_path: str = "") -> str:
        """Generate automatic filename for export."""
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        safe_side = side.upper() if side else 'X'
        safe_date = date.replace('/', '-').replace('\\', '-')
        
        filename = f"insole_{safe_name}_{safe_side}_{safe_date}.stl"
        
        if base_path:
            return os.path.join(base_path, filename)
        return filename
    
    def get_mesh_info(self, mesh: Optional[trimesh.Trimesh] = None) -> dict:
        """Get information about a mesh."""
        if mesh is None:
            mesh = self.insole_mesh
        
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
    
    def has_label(self) -> bool:
        """Check if insole currently has a label applied."""
        return self._current_label is not None
    
    def get_current_label(self) -> Optional[str]:
        """Get the currently applied label text."""
        return self._current_label
    
    def remove_label(self) -> trimesh.Trimesh:
        """Remove the current label from the insole."""
        if self._insole_before_label is not None:
            self.insole_mesh = self._insole_before_label.copy()
            self._current_label = None
        return self.insole_mesh
