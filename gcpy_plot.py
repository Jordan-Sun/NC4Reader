import os
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import gcpy

# Relative path to the dataset
resolution = 24
processors = 144
type = f"c{resolution}_p{processors}"
file = "GEOSChem.KppDiags.20190701_0000z.nc4"

# Read the dataset
ds = xr.open_dataset(f"gchp/{type}/{file}")
os.makedirs(f"figures/{type}", exist_ok=True)

# Sum over all levels
kpp_sum = ds["KppTotSteps"].sum(dim="lev")

# Plotting with gcpy (summed over levels)
plt.figure(figsize=(10,9))
gcpy.plot.single_panel(
    kpp_sum,
    title=f"C{resolution} Global Column Total KPP Steps",
    gridtype="cs",
)
plt.savefig(f"figures/{type}/gcpy_sum_{file}.pdf", bbox_inches="tight")

# # Plotting with Cartopy (summed over levels)
# plt.figure()
# ax = plt.axes(projection=ccrs.EqualEarth())
# ax.coastlines()
# ax.set_global()

# for face in range(6):
#     x = ds.corner_lons.isel(nf=face)
#     y = ds.corner_lats.isel(nf=face)
#     v = kpp_sum.isel(time=0, nf=face)  # summed over lev
#     ax.pcolormesh(x, y, v, transform=ccrs.PlateCarree())
# plt.savefig(f"figures/{type}/cartopy_sum_{file}.pdf", bbox_inches="tight")
