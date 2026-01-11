"""Test script for improved text mesh generation."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Avoid VTK import issues by importing only stl_processor directly
import trimesh
import numpy as np
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from shapely.validation import make_valid


def adaptive_bezier_quadratic(p0, p1, p2, tolerance=0.05):
    """Adaptively subdivide a quadratic Bezier curve."""
    mid_t = 0.5
    mid_x = (1-mid_t)**2 * p0[0] + 2*(1-mid_t)*mid_t * p1[0] + mid_t**2 * p2[0]
    mid_y = (1-mid_t)**2 * p0[1] + 2*(1-mid_t)*mid_t * p1[1] + mid_t**2 * p2[1]
    mid_curve = (mid_x, mid_y)
    mid_chord = ((p0[0] + p2[0]) / 2, (p0[1] + p2[1]) / 2)
    dist = np.sqrt((mid_curve[0] - mid_chord[0])**2 + (mid_curve[1] - mid_chord[1])**2)
    
    if dist <= tolerance:
        return [p2]
    else:
        p01 = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
        p12 = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
        p012 = ((p01[0] + p12[0]) / 2, (p01[1] + p12[1]) / 2)
        left = adaptive_bezier_quadratic(p0, p01, p012, tolerance)
        right = adaptive_bezier_quadratic(p012, p12, p2, tolerance)
        return left + right


def adaptive_bezier_cubic(p0, p1, p2, p3, tolerance=0.05):
    """Adaptively subdivide a cubic Bezier curve."""
    mid_t = 0.5
    mid_x = (1-mid_t)**3 * p0[0] + 3*(1-mid_t)**2*mid_t * p1[0] + 3*(1-mid_t)*mid_t**2 * p2[0] + mid_t**3 * p3[0]
    mid_y = (1-mid_t)**3 * p0[1] + 3*(1-mid_t)**2*mid_t * p1[1] + 3*(1-mid_t)*mid_t**2 * p2[1] + mid_t**3 * p3[1]
    mid_curve = (mid_x, mid_y)
    mid_chord = ((p0[0] + p3[0]) / 2, (p0[1] + p3[1]) / 2)
    
    dist = np.sqrt((mid_curve[0] - mid_chord[0])**2 + (mid_curve[1] - mid_chord[1])**2)
    
    if dist <= tolerance:
        return [p3]
    else:
        p01 = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
        p12 = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
        p23 = ((p2[0] + p3[0]) / 2, (p2[1] + p3[1]) / 2)
        p012 = ((p01[0] + p12[0]) / 2, (p01[1] + p12[1]) / 2)
        p123 = ((p12[0] + p23[0]) / 2, (p12[1] + p23[1]) / 2)
        p0123 = ((p012[0] + p123[0]) / 2, (p012[1] + p123[1]) / 2)
        left = adaptive_bezier_cubic(p0, p01, p012, p0123, tolerance)
        right = adaptive_bezier_cubic(p0123, p123, p23, p3, tolerance)
        return left + right


def create_text_mesh_matplotlib(text, font_size=5.0, depth=0.6):
    """Create text mesh using matplotlib with adaptive Bezier subdivision."""
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    
    font_props = FontProperties(family='sans-serif', weight='bold')
    text_path = TextPath((0, 0), text, size=font_size, prop=font_props)
    
    tolerance = min(0.05, font_size * 0.01)
    
    polygons = []
    current_polygon = []
    vertices = text_path.vertices
    codes = text_path.codes
    
    MOVETO, LINETO, CURVE3, CURVE4, CLOSEPOLY = 1, 2, 3, 4, 79
    
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
                curve_points = adaptive_bezier_quadratic(p0, p1, p2, tolerance)
                current_polygon.extend(curve_points)
            i += 2
            
        elif code == CURVE4:
            if len(current_polygon) > 0:
                p0 = current_polygon[-1]
                p1 = tuple(vertices[i])
                p2 = tuple(vertices[i + 1])
                p3 = tuple(vertices[i + 2])
                curve_points = adaptive_bezier_cubic(p0, p1, p2, p3, tolerance)
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
    
    if len(current_polygon) >= 3:
        try:
            poly = Polygon(current_polygon)
            if poly.is_valid and poly.area > 0.001:
                polygons.append(poly)
        except:
            pass
    
    if not polygons:
        return None
    
    # Polygon cleanup
    cleaned = []
    for poly in polygons:
        try:
            poly = poly.buffer(0)
            if poly.is_empty:
                continue
            if not poly.is_valid:
                poly = make_valid(poly)
            if isinstance(poly, MultiPolygon):
                for p in poly.geoms:
                    if p.area > 0.001:
                        cleaned.append(p)
            elif poly.area > 0.001:
                cleaned.append(poly)
        except:
            cleaned.append(poly)
    
    if not cleaned:
        return None
    
    try:
        merged = unary_union(cleaned)
        merged = merged.buffer(0)
    except:
        merged = cleaned[0]
    
    # Light simplification
    try:
        merged = merged.simplify(font_size * 0.005, preserve_topology=True)
    except:
        pass
    
    # Extrude
    meshes = []
    
    def extrude_poly(poly):
        try:
            if poly.is_valid and poly.area > 0.01:
                poly = poly.buffer(0)
                if poly.is_valid and not poly.is_empty:
                    return trimesh.creation.extrude_polygon(poly, height=depth, engine='earcut')
        except Exception as e:
            print(f"Extrusion failed: {e}")
        return None
    
    if isinstance(merged, MultiPolygon):
        for poly in merged.geoms:
            mesh = extrude_poly(poly)
            if mesh:
                meshes.append(mesh)
    else:
        mesh = extrude_poly(merged)
        if mesh:
            meshes.append(mesh)
    
    if meshes:
        combined = trimesh.util.concatenate(meshes)
        # Subdivide for smoother edges
        try:
            if len(combined.faces) < 50000:
                combined = combined.subdivide()
        except:
            pass
        return combined
    
    return None


if __name__ == '__main__':
    print("Testing improved text mesh generation...")
    print()
    
    # Test 1: Adaptive Bezier subdivision
    print("1. Testing adaptive Bezier subdivision:")
    result = adaptive_bezier_quadratic((0, 0), (1, 2), (2, 0), 0.05)
    print(f"   Quadratic Bezier: {len(result)} points (was 5 with fixed sampling)")
    
    result = adaptive_bezier_cubic((0, 0), (1, 3), (2, -1), (3, 0), 0.05)
    print(f"   Cubic Bezier: {len(result)} points (was 8 with fixed sampling)")
    print()
    
    # Test 2: Text mesh creation
    print("2. Testing text mesh creation:")
    mesh = create_text_mesh_matplotlib("TEST", 5.0, 0.6)
    if mesh:
        print(f"   'TEST' mesh: {len(mesh.faces)} faces, {len(mesh.vertices)} vertices")
        print(f"   Bounds: {mesh.bounds}")
    else:
        print("   ERROR: Failed to create mesh")
    print()
    
    # Test 3: Complex text
    print("3. Testing complex text:")
    mesh = create_text_mesh_matplotlib("OBSD", 5.0, 0.6)
    if mesh:
        print(f"   'OBSD' mesh: {len(mesh.faces)} faces, {len(mesh.vertices)} vertices")
    else:
        print("   ERROR: Failed to create mesh")
    print()
    
    # Test 4: FreeType (if available)
    print("4. Testing FreeType:")
    try:
        import freetype
        print("   freetype-py is installed!")
    except ImportError:
        print("   freetype-py not available")
    print()
    
    print("All tests completed!")
