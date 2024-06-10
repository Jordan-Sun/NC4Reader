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

# Find all files in directory named 'GEOSChem.KppDiags.*.nc4'
def findKppDiagsFiles(directory):
    files = []
    for filename in os.listdir(directory):
        if filename.startswith('GEOSChem.KppDiags.') and filename.endswith('.nc4'):
            files.append(os.path.join(directory, filename))
    return files

# Read the KPP diagnostics from the netCDF4 file
def readKppDiags(file):
    # dictionary to store the variables
    vars = {}
    with nc.Dataset(file, 'r') as f:
        Xdim = f.variables['Xdim'][:]
        Ydim = f.variables['Ydim'][:]
        nf = f.variables['nf'][:]
        ncontact = f.variables['ncontact'][:]
        contacts = f.variables['contacts'][:]
        anchor = f.variables['anchor'][:]
        lons = f.variables['lons'][:]
        lats = f.variables['lats'][:]
        corner_lons = f.variables['corner_lons'][:]
        corner_lats = f.variables['corner_lats'][:]
        lev = f.variables['lev'][:]
        time = f.variables['time'][:]
        KppAccSteps = f.variables['KppAccSteps'][:]
        KppIntCounts = f.variables['KppIntCounts'][:]
        KppJacCounts = f.variables['KppJacCounts'][:]
        KppLuDecomps = f.variables['KppLuDecomps'][:]
        KppSmDecomps = f.variables['KppSmDecomps'][:]
        KppSubsts = f.variables['KppSubsts'][:]
        KppRejSteps = f.variables['KppRejSteps'][:]
        KppTotSteps = f.variables['KppTotSteps'][:]

        # add the variables to the dictionary
        vars['Xdim'] = Xdim
        vars['Ydim'] = Ydim
        vars['nf'] = nf
        vars['ncontact'] = ncontact
        vars['contacts'] = contacts
        vars['anchor'] = anchor
        vars['lons'] = lons
        vars['lats'] = lats
        vars['corner_lons'] = corner_lons
        vars['corner_lats'] = corner_lats
        vars['lev'] = lev
        vars['time'] = time
        vars['KppAccSteps'] = KppAccSteps
        vars['KppIntCounts'] = KppIntCounts
        vars['KppJacCounts'] = KppJacCounts
        vars['KppLuDecomps'] = KppLuDecomps
        vars['KppSmDecomps'] = KppSmDecomps
        vars['KppSubsts'] = KppSubsts
        vars['KppRejSteps'] = KppRejSteps
        vars['KppTotSteps'] = KppTotSteps

    return vars
    

# Utility function to print a nested list to a file, return the number of items printed
def printNestedListToFile(f, nestedList, indent=0):
    count = 0
    # check if the first item in the nested list is a list
    if isinstance(nestedList[0], list):
        # nested list, print the list with indentation
        f.write('  ' * indent + '[\n')
        for item in nestedList:
            count += printNestedListToFile(f, item, indent+1)
        f.write('  ' * indent + ']\n')
        return count
    else:
        # not a nested list, print the list as is
        f.write('  ' * indent + str(nestedList) + '\n')
        return len(nestedList)

# Print a variable to a file
def printToFile(file, variable):
    with open(file, 'w') as f:
        # convert the mased array to a list
        list = variable.tolist()
        # write the list to the file with indentations for each nested list
        count = printNestedListToFile(f, list)
        print('Printed {} items to \'{}\'.'.format(count, file))

# Main function
def main():
    # default directory to be the current directory
    dir = 'KppDiags'
    # check if an argument is passed to the script
    if len(sys.argv) > 1:
        # set the directory to the argument passed
        dir = sys.argv[1]
    
    # check if the directory exists
    if not os.path.exists(dir):
        print('Directory \'{}\' does not exist.'.format(dir))
        # ask if the user wants to create the directory
        create = input('Do you want to create the directory? (y/N): ')
        if create.lower() == 'y':
            os.makedirs(dir)
        return
        
    # find the KPP diagnostics file
    files = findKppDiagsFiles(dir)
    # check if any files were found
    if len(files) == 0:
        print('No KPP diagnostics files found in \'{}\'.'.format(dir))
        return
    
    # for each file found
    for file in files:
        # create an output directory with the name of the file
        outputDir = file.split('.')[2]
        # skip if the directory already exists
        if os.path.exists(outputDir):
            print('Output directory \'{}\' already exists. Skipping...'.format(outputDir))
            continue
        os.makedirs(outputDir, exist_ok=True)

        # read the KPP diagnostics from the file
        vars = readKppDiags(file)

        # print each variable to their own file
        for key in vars:
            printToFile('{}/{}.txt'.format(outputDir, key), vars[key])

if __name__ == '__main__':
    main()