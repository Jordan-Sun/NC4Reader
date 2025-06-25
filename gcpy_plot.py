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

# # Plotting with gcpy (summed over levels)
# plt.figure(figsize=(10, 9))
# gcpy.plot.single_panel(
#     kpp_sum,
#     title=f"C{resolution} Global Column Total KPP Steps",
#     gridtype="cs",
# )
# plt.savefig(f"figures/{plot_type}/gcpy_column_{diag_file}.pdf", bbox_inches="tight")

# Compute sum over levels for each column
column_workload = kpp_sum.values.flatten()  # shape: (total_columns,)

# Compute total workload per processor
processor_totals = np.zeros(processors)
for proc in range(processors):
    mask = processor_map == proc
    if np.any(mask):
        processor_totals[proc] = column_workload[mask].sum()
    else:
        processor_totals[proc] = np.nan  # or 0

# Assign each column the total workload of its processor
column_proc_total = processor_totals[processor_map]
column_proc_total_reshaped = column_proc_total.reshape((faces, resolution, resolution))

# Create a DataArray for plotting
proc_total_da = xr.DataArray(
    column_proc_total_reshaped,
    dims=("nf", "Ydim", "Xdim"),
    coords={
        "nf": ds.nf,
        "Ydim": ds.Ydim,
        "Xdim": ds.Xdim,
    },
    name="ProcessorTotalKppSteps",
)

# Plot using gcpy
plt.figure(figsize=(10, 9))
gcpy.plot.single_panel(
    proc_total_da,
    title=f"C{resolution} Processor Total KPP Steps",
    gridtype="cs",
)

plt.savefig(f"figures/{plot_type}/gcpy_proctotal_{diag_file}.pdf", bbox_inches="tight")

# Overlay convex hull polygons for each processor
ax = plt.gca()
ax.set_global()

# Assign a visually distinct color to each host (avoid blue, red, green, yellow)
# Use a custom list of distinct colors (black, magenta, cyan, purple, brown, gray, white)
distinct_colors = [
    "black", "magenta", "cyan", "purple", "brown", "gray", "white",
    "orange", "lime", "deepskyblue", "orchid", "gold", "navy", "darkorange",
]
n_hosts = processors // 36
# Repeat colors if not enough for all hosts
host_colors = [distinct_colors[i % len(distinct_colors)] for i in range(n_hosts)]

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

        # Build a boolean mask for this processor's region
        proc_mask = np.zeros((resolution, resolution), dtype=bool)
        for i, j in indices:
            proc_mask[i, j] = True

        # Find halo (boundary) cells: cells in proc_mask with at least one neighbor not in proc_mask
        halo_indices = []
        for i, j in indices:
            for di, dj in [(-1,0), (0,1), (1,0), (0,-1)]:
                ni, nj = i + di, j + dj
                if ni < 0 or ni >= resolution or nj < 0 or nj >= resolution or not proc_mask[ni, nj]:
                    halo_indices.append((i, j))
                    break

        # Use ConvexHull to get the boundary of the region, handling dateline crossing
        if len(points) >= 3:
            lons = points[:, 0]
            lats = points[:, 1]
            lon_range = lons.max() - lons.min()
            if lon_range < 180:
                hull = ConvexHull(points)
                hull_points = points[hull.vertices]
            else:
                lons_wrapped = np.where(lons < 180, lons + 360, lons)
                points_wrapped = np.column_stack((lons_wrapped, lats))
                hull = ConvexHull(points_wrapped)
                hull_points = points_wrapped[hull.vertices]
                hull_points[:, 0] = np.where(
                    hull_points[:, 0] > 180, hull_points[:, 0] - 360, hull_points[:, 0]
                )

            # Assign color by host
            host_id = proc_id // 36
            color = host_colors[host_id]

            # polygon = patches.Polygon(
            #     hull_points.tolist(),
            #     closed=True,
            #     facecolor="none",
            #     edgecolor=color,
            #     linewidth=1.2,  # Make outline thicker for visibility
            #     transform=cartopy.crs.PlateCarree(),
            #     zorder=5,
            # )
            # ax.add_patch(polygon)

            # Label the processor at the center of the polygon
            centroid_lon = np.mean(hull_points[:, 0])
            centroid_lat = np.mean(hull_points[:, 1])
            ax.text(
                centroid_lon,
                centroid_lat,
                str(proc_id),
                fontsize=6,
                ha="center",
                va="center",
                color="black",
                transform=cartopy.crs.PlateCarree(),
                zorder=6,
            )

            # --- Plot only the halo edges for this processor ---
            for i, j in halo_indices:
                for c, (di, dj) in enumerate([(-1,0), (0,1), (1,0), (0,-1)]):
                    ni, nj = i + di, j + dj
                    plot_edge = False
                    if ni < 0 or ni >= resolution or nj < 0 or nj >= resolution:
                        plot_edge = True  # At face boundary
                    elif not proc_mask[ni, nj]:
                        neighbor_proc = face_assignments[ni, nj]
                        neighbor_host = neighbor_proc // 36
                        if neighbor_host != host_id:
                            plot_edge = True
                    if plot_edge:
                        corners = [
                            (face_lons[i, j], face_lats[i, j]),
                            (face_lons[i+1, j], face_lats[i+1, j]),
                            (face_lons[i+1, j+1], face_lats[i+1, j+1]),
                            (face_lons[i, j+1], face_lats[i, j+1]),
                        ]
                        c1 = corners[c]
                        c2 = corners[(c+1)%4]
                        if abs(c1[0] - c2[0]) > 180:
                            # Handle longitude wraparound
                            if c1[0] < c2[0]:
                                c1 = (c1[0] + 360, c1[1])
                            else:
                                c2 = (c2[0] + 360, c2[1])
                        ax.plot([c1[0], c2[0]], [c1[1], c2[1]], color=color, linewidth=1.5, zorder=8, transform=cartopy.crs.PlateCarree())

plt.savefig(
    f"figures/{plot_type}/overlay_processors_{diag_file}.pdf", bbox_inches="tight"
)
