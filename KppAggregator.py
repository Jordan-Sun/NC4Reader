#!/usr/bin/python3

import os
import sys
import numpy as np
import pandas as pd

# Input argument enumeration
class InputArg:
    PROGRAM_NAME = 0
    RANK_INDEX_FILE = 1
    TOTAL_STEPS_FILE = 2
    OUTPUT_FILE = 3
    ARG_LENGTH = 4

# Error code enumeration
class ErrorCode:
    SUCCESS = 0
    INVALID_ARGUMENTS = 1
    FILE_NOT_FOUND = 2
    FILE_ALREADY_EXISTS = 3

if __name__ == '__main__':
    # Check if there are enough arguments
    if len(sys.argv) < InputArg.ARG_LENGTH:
        print('Usage: {} <rank_index_file> <total_steps_file> <output_file>'.format(sys.argv[InputArg.PROGRAM_NAME]))
        sys.exit(ErrorCode.INVALID_ARGUMENTS)

    # Check if the rank index file exists
    if not os.path.exists(sys.argv[InputArg.RANK_INDEX_FILE]):
        print('Error: rank index file not found')
        sys.exit(ErrorCode.FILE_NOT_FOUND)
    
    # Check if the total steps file exists
    if not os.path.exists(sys.argv[InputArg.TOTAL_STEPS_FILE]):
        print('Error: total steps file not found')
        sys.exit(ErrorCode.FILE_NOT_FOUND)
    
    # Check if the output file already exists
    if os.path.exists(sys.argv[InputArg.OUTPUT_FILE]):
        # Ask the user if they want to overwrite the file
        print('Warning: output file already exists. Do you want to overwrite it? (y/N)', end=' ')
        response = input()
        if response.lower() != 'y':
            sys.exit(ErrorCode.FILE_ALREADY_EXISTS)

    # Read the rank index file
    rank_index = pd.read_csv(sys.argv[InputArg.RANK_INDEX_FILE], header='infer')
    num_ranks = 24
    # Read the total steps file
    total_steps = pd.read_csv(sys.argv[InputArg.TOTAL_STEPS_FILE], header='infer')
    num_cells = total_steps.shape[0]
    num_intervals = total_steps.shape[1] - 1

    # Compute the total KPP steps per rank per interval
    total_kpp_steps = np.zeros((num_ranks, num_intervals))
    
    # Compute the total KPP steps per rank per interval
    for i in range(num_cells):
        print('Aggregating KPP steps for cell {}/{}'.format(i + 1, num_cells), end='\r')
        rank = rank_index['KppRank'][i]
        for j in range(num_intervals):
            total_kpp_steps[rank, j] = max(total_kpp_steps[rank, j], total_steps.iloc[i, j + 1])
    print('Aggregated KPP steps for {} cells'.format(num_cells))
    
    # Create a DataFrame for the total KPP steps per rank per interval
    columns = ['Rank'] + [f'Interval_{j}' for j in range(num_intervals)]
    data = np.hstack((np.arange(num_ranks).reshape(-1, 1), total_kpp_steps))
    df = pd.DataFrame(data, columns=columns)
    
    # Save the DataFrame to a CSV file
    df.to_csv(sys.argv[InputArg.OUTPUT_FILE], index=False)