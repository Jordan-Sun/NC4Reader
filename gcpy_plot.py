import os
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import gcpy

# Relative path to the dataset
type = "c24_p144"
file = "GEOSChem.KppDiags.20190701_0000z.nc4"
# Read the dataset
ds = xr.open_dataset(f"gchp/{type}/{file}")
os.makedirs(f"figures/{type}", exist_ok=True)

# Plotting with gcpy
gcpy.plot.single_panel(
    ds["KppTotSteps"].isel(lev=0),
    title=f"{type} KPP Steps at interval 0",
    gridtype="cs",
)
plt.savefig(f"figures/{type}/gcpy_{file}.png", dpi=300, bbox_inches="tight")


# Plotting with Cartopy
plt.figure()
ax = plt.axes(projection=ccrs.EqualEarth())
ax.coastlines()
ax.set_global()

for face in range(6):
    x = ds.corner_lons.isel(nf=face)
    y = ds.corner_lats.isel(nf=face)
    v = ds.KppTotSteps.isel(time=0, lev=0, nf=face)
    ax.pcolormesh(x, y, v, transform=ccrs.PlateCarree())
plt.savefig(f"figures/{type}/cartopy_{file}.png", dpi=300, bbox_inches='tight')
