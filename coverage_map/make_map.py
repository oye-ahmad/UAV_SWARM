from PIL import Image
import numpy as np

# Map size in meters and resolution
width_m, height_m = 40.0, 40.0
resolution = 0.2  # meters/pixel

w_px = int(width_m / resolution)
h_px = int(height_m / resolution)

# 254 = free (white), 0 = occupied (black), 205 = unknown (gray) - standard map_server convention
grid = np.full((h_px, w_px), 254, dtype=np.uint8)

# Border = obstacle, 1 pixel thick
grid[0, :] = 0
grid[-1, :] = 0
grid[:, 0] = 0
grid[:, -1] = 0

# PGM is stored top-row-first but map_server treats row 0 of the image as the TOP
# of the map (max y); that's handled by 'negate' + origin, no need to flip manually
img = Image.fromarray(grid, mode='L')
img.save('/home/claude/coverage_map/coverage_area.pgm')

yaml_content = f"""image: coverage_area.pgm
resolution: {resolution}
origin: [{-width_m/2}, {-height_m/2}, 0.0]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.196
"""
with open('/home/claude/coverage_map/coverage_area.yaml', 'w') as f:
    f.write(yaml_content)

print(f"Map: {w_px}x{h_px} px, {resolution} m/px, origin centered at home")
