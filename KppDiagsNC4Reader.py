#!/usr/bin/python3

import os
import sys
import pandas as pd
import netCDF4 as nc

# Read the following variables from the 'GEOSChem.KppDiags.%y4%m2%d2_%h2%n2z.nc4' file
# KppAccSteps       count
# KppIntCounts      count
# KppJacCounts      count
# KppLuDecomps      count
# KppSmDecomps      count
# KppSubsts         count
# KppRejSteps       count
# KppTotSteps       count

# Find file in directory named 'GEOSChem.KppDiags.*.nc4'
def findKppDiagsFile(directory):
    for filename in os.listdir(directory):
        if filename.startswith('GEOSChem.KppDiags.') and filename.endswith('.nc4'):
            return filename
    return None

# Read the KPP diagnostics from the netCDF4 file
def readKppDiags(file):
    with nc.Dataset(file, 'r') as f:
        KppAccSteps = f.variables['KppAccSteps'][:]
        KppIntCounts = f.variables['KppIntCounts'][:]
        KppJacCounts = f.variables['KppJacCounts'][:]
        KppLuDecomps = f.variables['KppLuDecomps'][:]
        KppSmDecomps = f.variables['KppSmDecomps'][:]
        KppSubsts = f.variables['KppSubsts'][:]
        KppRejSteps = f.variables['KppRejSteps'][:]
        KppTotSteps = f.variables['KppTotSteps'][:]
    return KppAccSteps, KppIntCounts, KppJacCounts, KppLuDecomps, KppSmDecomps, KppSubsts, KppRejSteps, KppTotSteps

# Utility function to print a nested list to a file
def printNestedListToFile(f, nestedList, indent=0):
    # check if the first item in the nested list is a list
    if isinstance(nestedList[0], list):
        # nested list, print the list with indentation
        f.write('  ' * indent + '[\n')
        for item in nestedList:
            printNestedListToFile(f, item, indent+1)
        f.write('  ' * indent + ']\n')
    else:
        # not a nested list, print the list as is
        f.write('  ' * indent + str(nestedList) + '\n')

# Print a variable to a file
def printToFile(file, variable):
    with open(file, 'w') as f:
        # convert the mased array to a list
        list = variable.tolist()
        # write the list to the file with indentations for each nested list
        printNestedListToFile(f, list)

# Main function
def main():
    # default directory to be the current directory
    dir = '.'
    # check if an argument is passed to the script
    if len(sys.argv) > 1:
        # set the directory to the argument passed
        dir = sys.argv[1]
        
    # find the KPP diagnostics file
    file = findKppDiagsFile(dir)
    if file is None:
        print('No KPP diagnostics file found in the directory:', dir)
        return
    
    # read the KPP diagnostics from the file
    KppAccSteps, KppIntCounts, KppJacCounts, KppLuDecomps, KppSmDecomps, KppSubsts, KppRejSteps, KppTotSteps = readKppDiags(file)

    # create an output directory with the name of the file
    outputDir = file.split('.')[2]
    os.makedirs(outputDir, exist_ok=True)
    os.chdir(outputDir)

    # print each variable to their own file
    printToFile('KppAccSteps.txt', KppAccSteps)
    printToFile('KppIntCounts.txt', KppIntCounts)
    printToFile('KppJacCounts.txt', KppJacCounts)
    printToFile('KppLuDecomps.txt', KppLuDecomps)
    printToFile('KppSmDecomps.txt', KppSmDecomps)
    printToFile('KppSubsts.txt', KppSubsts)
    printToFile('KppRejSteps.txt', KppRejSteps)
    printToFile('KppTotSteps.txt', KppTotSteps)

if __name__ == '__main__':
    main()