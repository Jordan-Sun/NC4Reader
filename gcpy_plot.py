import os
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import cartopy.crs as ccrs
import gcpy
import numpy as np
from scipy.spatial import ConvexHull

# Configuration
resolution = 180
processors = 576
faces = 6
cells_per_face = resolution * resolution
corners_per_face = resolution + 1

plot_linewidth = 0.6
lon_wrap_threshold = 300  # degrees
lat_span_threshold = 150  # degrees

plot_type = f"c{resolution}_p{processors}"
diag_file = "GEOSChem.KppDiags.20190701_0000z.nc4"
assign_file = "RankIndex.csv"

# Load dataset
ds = xr.open_dataset(f"gchp/{plot_type}/{diag_file}")
os.makedirs(f"figures/{plot_type}", exist_ok=True)

# Load assignment
assignment_df = pd.read_csv(f"gchp/{plot_type}/{assign_file}", index_col=0)
processor_map = assignment_df["KppRank"].to_numpy()

# Sum over all levels
kpp_sum = ds["KppTotSteps"].sum(dim="lev")

# Plotting with gcpy (summed over levels)
plt.figure(figsize=(10, 9))
gcpy.plot.single_panel(
    kpp_sum,
    title=f"C{resolution} Global Column Total KPP Steps",
    gridtype="cs",
)
plt.savefig(f"figures/{plot_type}/gcpy_sum_{diag_file}.pdf", bbox_inches="tight")

# Plotting with Cartopy and overlay boxes
fig = plt.figure(figsize=(12, 10))
ax = plt.axes(projection=ccrs.EqualEarth())
ax.set_global()
ax.coastlines()

# Plot data
for face in range(faces):
    x = ds.corner_lons.isel(nf=face)
    y = ds.corner_lats.isel(nf=face)
    v = kpp_sum.isel(time=0, nf=face)  # summed over lev
    ax.pcolormesh(x, y, v, transform=ccrs.PlateCarree())

# Overlay processor assignment bounding polygons via ConvexHull
corner_lons = ds.corner_lons.values  # shape (6, 181, 181)
corner_lats = ds.corner_lats.values

for face in range(faces):
    face_lons = corner_lons[face]  # (181, 181)
    face_lats = corner_lats[face]

    # Get processor IDs for this face's columns
    start_idx = face * cells_per_face
    end_idx = start_idx + cells_per_face
    face_assignments = processor_map[start_idx:end_idx].reshape(resolution, resolution)

    # For each processor, collect corner points
    for proc_id in np.unique(face_assignments):
        indices = np.argwhere(face_assignments == proc_id)
        if indices.size == 0:
            continue

        points = []
        for i, j in indices:
            points.extend(
                [
                    (face_lons[i, j], face_lats[i, j]),
                    (face_lons[i + 1, j], face_lats[i + 1, j]),
                    (face_lons[i + 1, j + 1], face_lats[i + 1, j + 1]),
                    (face_lons[i, j + 1], face_lats[i, j + 1]),
                ]
            )

        points = np.array(points)
        try:
            lon_span = points[:, 0].max() - points[:, 0].min()
            lat_span = points[:, 1].max() - points[:, 1].min()
            if lon_span > lon_wrap_threshold or lat_span > lat_span_threshold:
                continue

            hull = ConvexHull(points)
            hull_points = points[hull.vertices]

            polygon = patches.Polygon(
                hull_points,
                linewidth=plot_linewidth,
                edgecolor="black",
                facecolor="none",
                transform=ccrs.PlateCarree(),
                zorder=5,
            )
            ax.add_patch(polygon)
        except Exception as e:
            print(f"Convex hull failed for processor {proc_id} on face {face}: {e}")

plt.title(f"{plot_type.upper()} Global Column Total KPP Steps with Processor Overlay")
plt.savefig(f"figures/{plot_type}/overlay_sum_{diag_file}.pdf", bbox_inches="tight")
