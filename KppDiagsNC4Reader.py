#!/usr/bin/python3

import os
import sys
import pandas as pd
import netCDF4 as nc

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
        # keys of the variables to be read
        keys = f.variables.keys()
        # read each variable
        for key in keys:
            # read the variable
            var = f.variables[key][:]
            # check if the variable is a masked array
            if hasattr(var, 'mask'):
                # convert the masked array to a list
                var = var.filled()
            # store the variable in the dictionary
            vars[key] = var

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
            # ask if the user wants to overwrite the directory
            overwrite = input('Do you want to overwrite the directory? (y/N): ')
            if overwrite.lower() != 'y':
                continue
        os.makedirs(outputDir, exist_ok=True)

        # read the KPP diagnostics from the file
        vars = readKppDiags(file)

        # print each variable to their own file and shape to the console
        for key in vars:
            print('{}: {}'.format(key, vars[key].shape))
            printToFile('{}/{}.txt'.format(outputDir, key), vars[key])

if __name__ == '__main__':
    main()