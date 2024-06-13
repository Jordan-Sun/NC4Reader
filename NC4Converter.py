#!/usr/bin/python3

import os
import sys
import numpy as np
import pandas as pd
import netCDF4 as nc

# Input argument enumeration
class InputArg:
    PROGRAM_NAME = 0
    PATH = 1
    LENGTH = 2

# Error code enumeration
class ErrorCode:
    SUCCESS = 0
    INVALID_ARGUMENTS = 1
    FILE_NOT_FOUND = 2
    KEY_NOT_FOUND = 3
    ASSERTION_FAILED = -1

# Check if a file is a KPP diagnostics file
def isKppDiagsFile(file: str) -> bool:
    return file.startswith('GEOSChem.KppDiags.') and file.endswith('.nc4')

# Convert the directory named 'GEOSChem.KppDiags.*.nc4' to the timestamp
# @note: assumes that the file name is in the format 'GEOSChem.KppDiags.*.nc4'
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
        if isKppDiagsFile(filename):
            files[convertKppDiagsFileToTimestamp(filename)] = os.path.join(directory, filename)
    # sort files by timestamp
    files = dict(sorted(files.items()))
    return files

# Read keys from the netCDF4 file
def readKeys(file: str) -> list[str]:
    with nc.Dataset(file, 'r') as f:
        # keys of the variables to be read
        keys = f.variables.keys()
    return keys

# Read variables from the netCDF4 file by key
def readVariables(file: str, keys: list[str]) -> dict[str, np.ndarray]:
    variables = {} 
    with nc.Dataset(file, 'r') as f:
        # read each variable
        for key in keys:
            # read the variable
            var = f.variables[key][:]
            # check if the variable is a masked array
            if hasattr(var, 'mask'):
                # convert the masked array to a ndarray
                var = var.filled()
            # store the variable in the dictionary
            variables[key] = var
    return variables

# Main function
def main():
    # check if the user provided a directory
    if len(sys.argv) < InputArg.LENGTH:
        print('Usage: {} <directory>'.format(sys.argv[InputArg.PROGRAM_NAME]))
        sys.exit(ErrorCode.INVALID_ARGUMENTS)

    # optionally check for flags
    flags = sys.argv[InputArg.LENGTH:]
    # force flag: '-f' or '--force'
    force = '-f' in flags or '--force' in flags
    if force:
        print('Force: enabled.')
    # debug flag: '-D' or '--debug'
    debug = '-D' in flags or '--debug' in flags
    if debug:
        print('Debug: enabled.')

    # get the path from the command line
    path = sys.argv[InputArg.PATH]

    # check if the input is a directory or a file
    if os.path.isdir(path):
        # set the directory to be the path
        directory = path

        # find all KPP diagnostics files in the directory
        files = findKppDiagsFiles(directory)

        # check if any files were found
        if len(files) == 0:
            print('Error: No KPP diagnostics files found in \'{}\'.'.format(directory))
            sys.exit(ErrorCode.FILE_NOT_FOUND)
    elif os.path.isfile(path):
        # set the directory to be the parent directory of the file
        directory = os.path.dirname(path)
        
        # check if the file is a KPP diagnostics file
        if not isKppDiagsFile(path):
            print('Error: \'{}\' is not a KPP diagnostics file.'.format(path))
            sys.exit(ErrorCode.FILE_NOT_FOUND)
        # set the file to be the only file
        files = {convertKppDiagsFileToTimestamp(path): path}
    else:
        print('Error: Invalid path \'{}\'.'.format(path))
        sys.exit(ErrorCode.FILE_NOT_FOUND)

    # @todo: read data frame from files if they exist and only update the new data as needed unless forced
    if not force:
        pass
    
    # read the keys from the first file
    file = next(iter(files.values()))
    keys = readKeys(file)

    # verify that we have the keys needed
    requiredKeys = ['KppTotSteps', 'KppRank', 'KppIndexOnRank']
    missingKeys = [key for key in requiredKeys if key not in keys]
    if len(missingKeys) > 0:
        print('Error: Missing keys {}'.format(missingKeys))
        sys.exit(ErrorCode.KEY_NOT_FOUND)

    # read the variables from the first file
    variables = readVariables(file, requiredKeys)
    # size of the data array
    size = 59 * 6 * 24 * 24

    # debug: verify the variables
    if debug:
        for key in requiredKeys:
            # verify the shape is (1, 72, 6, 24, 24)
            if variables[key].shape != (1, 72, 6, 24, 24):
                print('Error: {} shape is not (1, 72, 6, 24, 24).'.format(key))
                exit(ErrorCode.ASSERTION_FAILED)
            # # find zero layers in the variable
            # zero_layers = []
            # for i in range(72):
            #     if not variables[key][0][i].any():
            #         zero_layers.append(i)
            # print('Zero layers in {}: {}'.format(key, zero_layers))
            # verify that layers 59-72 are all zeros
            if variables[key][0][59:72].any():
                print('Error: {}[0][59:72] is not all zeros.'.format(key))
                exit(ErrorCode.ASSERTION_FAILED)
            # verify that the length of the variable after applying the mask is equal to size
            if variables[key][0][0:59].flatten().shape[0] != size:
                print('Error: {}[0][0:59] does not have a length of {}.'.format(key, size))
                exit(ErrorCode.ASSERTION_FAILED)

    # create a DataFrame of size to store the rank and index on rank
    rankDf = pd.DataFrame(index=range(size))
    # flatten and store the ranks and indices on ranks for layers 1-59
    rankDf['KppRank'] = variables['KppRank'][0][0:59].flatten().astype(int)
    rankDf['KppIndexOnRank'] = variables['KppIndexOnRank'][0][0:59].flatten().astype(int)
    rankDf.to_csv('{}/RankIndex.csv'.format(directory), index=True)

    # @todo: update our simulation model so that it can read the assignment as a 1d array or 4d array (59, 6, 24, 24) so we don't have to reshape it here
    # write the DataFrame to a CSV file
    # reshape the rank to a 8496 by 24 array
    assignment = rankDf['KppRank'].values.reshape(8496, 24)
    # write the reshaped assignment to an assignment file for our simulation model, separated by commas
    np.savetxt('{}/original.assignment'.format(directory), assignment, fmt='%d', delimiter=',')

    # create a DataFrame of size to store the total steps
    costDf = pd.DataFrame(index=range(size))
    # read the variables from all the files
    for timestamp, file in files.items():
        # read the keys from the file
        keys = readKeys(file)
        # verify that we have the keys needed
        if debug:
            requiredKeys = ['KppTotSteps', 'KppRank', 'KppIndexOnRank']
        else:
            requiredKeys = ['KppTotSteps']
        missingKeys = [key for key in requiredKeys if key not in keys]
        if len(missingKeys) > 0:
            print('Missing keys: {}'.format(missingKeys))
            sys.exit(ErrorCode.KEY_NOT_FOUND)

        # read the variables from the file
        variables = readVariables(file, requiredKeys)

        # debug: verify the rank and index on rank match the first file
        if debug:
            for key in ['KppRank', 'KppIndexOnRank']:
                if not np.array_equal(variables[key][0][0:59].flatten().astype(int), rankDf[key]):
                    print('Error: {} does not match the first file.'.format(key))
                    exit(ErrorCode.ASSERTION_FAILED)
        
        # flatten and store the total steps for the file
        costDf = pd.concat([costDf, pd.Series(variables['KppTotSteps'][0][0:59].flatten(), name=timestamp)], axis=1)

    # write the DataFrame to a CSV file
    costDf.to_csv('{}/TotalSteps.csv'.format(directory), index=True)

# Run the main function
if __name__ == '__main__':
    main()
    
