import ezdxf
import math
import sys

def analyze_blueprint(file_path):
    """
    Analyzes a DXF file to extract geometric data and estimate complexity.
    Returns a dictionary of metrics.
    """
    try:
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()
        
        # Entity counts
        counts = {
            "LINE": 0,
            "CIRCLE": 0, 
            "ARC": 0,
            "LWPOLYLINE": 0,
            "TEXT": 0,
            "MTEXT": 0
        }
        
        # Bounding Box tracking
        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = float('-inf'), float('-inf')
        
        entity_count = 0
        
        for e in msp:
            dxftype = e.dxftype()
            if dxftype in counts:
                counts[dxftype] += 1
            entity_count += 1
            
            # Simple bounding box estimation (only for basic entities to avoid complex math deps)
            if dxftype == "LINE":
                min_x = min(min_x, e.dxf.start[0], e.dxf.end[0])
                max_x = max(max_x, e.dxf.start[0], e.dxf.end[0])
                min_y = min(min_y, e.dxf.start[1], e.dxf.end[1])
                max_y = max(max_y, e.dxf.start[1], e.dxf.end[1])
        
        # Calculate Dimensions
        width = 0
        height = 0
        area = 0
        
        if min_x != float('inf'):
            width = max_x - min_x
            height = max_y - min_y
            area = width * height
            
        # Complexity Score (Heuristic)
        # More entities per area = higher complexity
        complexity_score = 1
        if area > 0:
            density = entity_count / area
            if density > 0.1: complexity_score = 3
            elif density > 0.01: complexity_score = 2
        
        if entity_count > 1000: complexity_score += 1
        
        # Normalize score 1-10
        final_complexity = min(10, complexity_score * 2)

        return {
            "success": True,
            "entity_counts": counts,
            "total_entities": entity_count,
            "estimated_width_m": round(width, 2),
            "estimated_height_m": round(height, 2),
            "estimated_area_m2": round(area, 2),
            "complexity_score": final_complexity,
            "message": "DXF Analysis Successful"
        }

    except IOError:
        return {"success": False, "message": "Not a valid DXF file or file not found."}
    except ezdxf.DXFStructureError:
        return {"success": False, "message": "Invalid or Corrupt DXF file."}
    except Exception as e:
        return {"success": False, "message": str(e)}

if __name__ == "__main__":
    # Test
    print("Blueprint Utils Loaded.")
