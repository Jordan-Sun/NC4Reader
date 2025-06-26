import os
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import cartopy
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

plot_type = f"c{resolution}_p{processors}"
diag_file = "GEOSChem.KppDiags.20190701_0000z.nc4"
assign_file = "RankIndex.csv"

# Load dataset
ds = xr.open_dataset(f"gchp/{plot_type}/{diag_file}")
os.makedirs(f"figures/{plot_type}", exist_ok=True)

# Load assignment
assignment_df = pd.read_csv(f"gchp/{plot_type}/{assign_file}", index_col=0)
processor_map = assignment_df["KppRank"].to_numpy()

# Compute node assignments
node_map = processor_map // 36

# Sum over all levels
kpp_sum = ds["KppTotSteps"].sum(dim="lev")

# Plotting with gcpy (summed over levels)
plt.figure(figsize=(10, 9))
gcpy.plot.single_panel(
    kpp_sum,
    title=f"C{resolution} Global Column Total KPP Steps",
    gridtype="cs",
)
plt.savefig(f"figures/{plot_type}/gcpy_column_{diag_file}.pdf", bbox_inches="tight")

# # Compute sum over levels for each column
# column_workload = kpp_sum.values.flatten()  # shape: (total_columns,)

# # Compute total workload per processor
# processor_totals = np.zeros(processors)
# for proc in range(processors):
#     mask = processor_map == proc
#     if np.any(mask):
#         processor_totals[proc] = column_workload[mask].sum()
#     else:
#         processor_totals[proc] = np.nan  # or 0

# # Assign each column the total workload of its processor
# column_proc_total = processor_totals[processor_map]
# column_proc_total_reshaped = column_proc_total.reshape((faces, resolution, resolution))

# # Create a DataArray for plotting
# proc_total_da = xr.DataArray(
#     column_proc_total_reshaped,
#     dims=("nf", "Ydim", "Xdim"),
#     coords={
#         "nf": ds.nf,
#         "Ydim": ds.Ydim,
#         "Xdim": ds.Xdim,
#     },
#     name="ProcessorTotalKppSteps",
# )

# # Plot using gcpy
# plt.figure(figsize=(10, 9))
# gcpy.plot.single_panel(
#     proc_total_da,
#     title=f"C{resolution} Processor Total KPP Steps",
#     gridtype="cs",
# )

# plt.savefig(f"figures/{plot_type}/gcpy_proctotal_{diag_file}.pdf", bbox_inches="tight")

# Overlay convex hull polygons for each processor
ax = plt.gca()
ax.set_global()

# Get corner coordinates
corner_lons = ds.corner_lons.values  # shape (6, 181, 181)
corner_lats = ds.corner_lats.values

for face in range(faces):
    face_lons = corner_lons[face]
    face_lats = corner_lats[face]

    # Get processor assignments for this face's columns
    start_idx = face * cells_per_face
    end_idx = start_idx + cells_per_face
    face_assignments = processor_map[start_idx:end_idx].reshape(resolution, resolution)

    for proc_id in np.unique(face_assignments):
        indices = np.argwhere(face_assignments == proc_id)
        if indices.size == 0:
            continue

        # Collect all corner points for this processor
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

        # Use ConvexHull to get the boundary of the region, handling dateline crossing
        if len(points) >= 3:
            lons = points[:, 0]
            lats = points[:, 1]
            # We know wrapped around 0 if both near 0 and 360 degress longitudes are in the points
            lon_range = lons.max() - lons.min()
            if lon_range < 180:
                # No dateline crossing, use original points
                hull = ConvexHull(points)
                hull_points = points[hull.vertices]
            else:
                # Add 360 to any that are less than 180 degrees to handle dateline crossing
                lons_wrapped = np.where(lons < 180, lons + 360, lons)
                # Create points with wrapped longitudes
                points_wrapped = np.column_stack((lons_wrapped, lats))
                hull = ConvexHull(points_wrapped)
                hull_points = points_wrapped[hull.vertices]
                # Shift back for plotting in [-180, 180]
                hull_points[:, 0] = np.where(
                    hull_points[:, 0] > 180, hull_points[:, 0] - 360, hull_points[:, 0]
                )

            polygon = patches.Polygon(
                hull_points.tolist(),
                closed=True,
                facecolor="none",
                edgecolor="black",
                linewidth=plot_linewidth,
                transform=cartopy.crs.PlateCarree(),
                zorder=5,
            )
            ax.add_patch(polygon)

            # # Label the processor at the center of the polygon
            # centroid_lon = np.mean(hull_points[:, 0])
            # centroid_lat = np.mean(hull_points[:, 1])
            # ax.text(
            #     centroid_lon,
            #     centroid_lat,
            #     str(proc_id),
            #     fontsize=6,
            #     ha="center",
            #     va="center",
            #     color="black",
            #     transform=cartopy.crs.PlateCarree(),
            #     zorder=6,
            # )

plt.savefig(
    f"figures/{plot_type}/overlay_processors_{diag_file}.pdf", bbox_inches="tight"
)
