#!/usr/bin/python3

import os
import sys
import numpy as np
import pandas as pd
import netCDF4 as nc
import matplotlib.pyplot as plt
import cartopy.crs as ccrs


# Convert the directory named 'GEOSChem.KppDiags.*.nc4' to the timestamp
def convertKppDiagsFileToTimestamp(file: str) -> str:
    # split the file name into parts
    parts = os.path.basename(file).split('.')
    # extract the timestamp from the parts
    timestamp = parts[2]
    return timestamp

# Find all files in directory named 'GEOSChem.KppDiags.*.nc4'
def findKppDiagsFiles(directory) -> dict[str, str]:
    # dictionary to store the files by timestamp
    files = {}
    for filename in os.listdir(directory):
        if filename.startswith('GEOSChem.KppDiags.') and filename.endswith('.nc4'):
            files[convertKppDiagsFileToTimestamp(filename)] = os.path.join(directory, filename)
    # sort files by timestamp
    files = dict(sorted(files.items()))
    return files


# Main function
def main():
    if len(sys.argv) != 2:
        print('Usage: {} <directory>'.format(sys.argv[0]))
        sys.exit(1)
    
    files = findKppDiagsFiles(sys.argv[1])

    for file in files:
        os.makedirs(file, exist_ok=True)
        data = nc.Dataset(files[file], 'r')
        lons = data.variables['lons'][:]
        lats = data.variables['lats'][:]
        keys = ['KppTotSteps', 'KppRank', 'KppIndexOnRank']

        for key in keys:
            var = data.variables[key][0,:,:]

            # Source: https://disc.gsfc.nasa.gov/information/howto?title=How%20to%20read%20and%20plot%20NetCDF%20MERRA-2%20data%20in%20Python
            # Set the figure size, projection, and extent
            fig = plt.figure(figsize=(8,4))
            ax = plt.axes(projection=ccrs.Robinson())
            ax.set_global()
            ax.coastlines(resolution="110m",linewidth=1)
            ax.gridlines(linestyle='--',color='black')

            # Set contour levels, then draw the plot and a colorbar
            clevs = np.arange(230,311,5)
            plt.contourf(lons, lats, var, clevs, transform=ccrs.PlateCarree(),cmap=plt.cm.jet)
            plt.title('{}'.format(key),size=14)
            cb = plt.colorbar(ax=ax, orientation="vertical", pad=0.02, aspect=16, shrink=0.8)
            cb.ax.tick_params(labelsize=10)

# Run the main function
if __name__ == '__main__':
    main()
    