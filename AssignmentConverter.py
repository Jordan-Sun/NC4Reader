#!/usr/bin/python3

import os
import sys
import re
import numpy as np
import pandas as pd

# Input argument enumeration
class InputArg:
    PROGRAM_NAME = 0
    RANK_INDEX_FILE = 1
    ASSIGNMENT_FILE = 2
    LENGTH = 3

# Error code enumeration
class ErrorCode:
    SUCCESS = 0
    INVALID_ARGUMENTS = 1
    FILE_NOT_FOUND = 2
    KEY_NOT_FOUND = 3
    ASSERTION_FAILED = -1

# Read in the assignment file and the rank index csv file, convert the assignment to a mapping to target rank for balancing for each rank.

def main():
    # Validate the input arguments
    if len(sys.argv) < InputArg.LENGTH:
        print('Usage: {} <rank_index_file> <assignment_file/directory>'.format(sys.argv[InputArg.PROGRAM_NAME]))
        sys.exit(ErrorCode.INVALID_ARGUMENTS)

    # Read in the rank index file
    rank_index_file = sys.argv[InputArg.RANK_INDEX_FILE]
    if not os.path.exists(rank_index_file):
        print('Error: Rank index file \'{}\' not found.'.format(rank_index_file))
        sys.exit(ErrorCode.FILE_NOT_FOUND)
    rank_index = pd.read_csv(rank_index_file)

    # Retrieve number of ranks and indices on rank
    num_ranks = max(rank_index['KppRank']) + 1
    num_indices = max(rank_index['KppIndexOnRank'])
    num_cells = len(rank_index)

    print('Number of ranks: {}'.format(num_ranks))
    print('Number of indices: {}'.format(num_indices))
    print('Number of cells: {}'.format(num_cells))
    
    # Read in the assignment file
    assignment_file = sys.argv[InputArg.ASSIGNMENT_FILE]
    if not os.path.exists(assignment_file):
        print('Error: Assignment file/directory \'{}\' not found.'.format(assignment_file))
        sys.exit(ErrorCode.FILE_NOT_FOUND)
    # If the assignment file is a directory, read in all the files in the directory
    files = []
    if os.path.isdir(assignment_file):
        for filename in os.listdir(assignment_file):
            files.append(os.path.join(assignment_file, filename))
    else:
        files.append(assignment_file)

    # Retrieve number of intervals
    num_intervals = len(files)
    print('Number of intervals: {}'.format(num_intervals))
    
    # Create an dictionary of interval number to mapping
    mappings = {}
    # Compile the regex pattern
    interval_pattern = re.compile(r'interval_(\d+)\.assignment')

    for file in files:
        print('Reading assignment file: {}'.format(file))
        # Extract interval number using the compiled regex
        match = interval_pattern.search(file)
        if match:
            # Extract the interval number
            interval_number = int(match.group(1))
            print('Processing interval: {}'.format(interval_number))
        else:
            # Skip the file if the interval number is not found
            print('Error: Interval number not found in assignment file name.')
            continue
        assignment = pd.read_csv(file, header=None)
        # Flatten the assignment dataframe
        assignment = assignment.values.flatten()
        # Check if the number of cells in the assignment file matches the number of cells in the rank index file
        if len(assignment) != num_cells:
            print('Error: Number of cells in assignment file does not match number of cells in rank index file.')
            sys.exit(ErrorCode.ASSERTION_FAILED)

        # Create a panda dataframe to store the mapping of assignment to target rank
        mapping = pd.DataFrame(index=range(num_ranks), columns=range(num_indices))

        # Set of reassigned ranks for each rank
        sets = [set() for _ in range(num_ranks)]

        # Iterate through the assignment file and populate the mapping
        for i in range(num_cells):
            rank = rank_index['KppRank'][i]
            index = rank_index['KppIndexOnRank'][i] - 1
            target_rank = assignment[i].astype(int)
            mapping.at[rank, index] = target_rank
            sets[rank].add(target_rank)

        # Append the mapping to the mappings dictionary
        mappings[interval_number] = mapping

        # # Print the number of unique target ranks for each rank
        # for i in range(num_ranks):
        #     print('Rank {}: {}'.format(i, len(sets[i])))

    # Create a Mappings directory if it does not exist
    mapping_dir = assignment_file.replace('Assignments', 'Mappings')
    if not os.path.exists(mapping_dir):
        os.makedirs(mapping_dir)

    # Convert the mappings dictionary to a dataframe per rank
    for rank in range(num_ranks):
        # Create a dataframe to store the mapping for the rank
        rank_mapping = pd.DataFrame(index=range(num_intervals), columns=range(num_indices))
        for interval in range(num_intervals):
            rank_mapping.at[interval, :] = mappings[interval].loc[rank, :]
        # Write the rank mapping to a csv file
        rank_mapping.to_csv(os.path.join(mapping_dir, 'rank_{}.csv'.format(rank)), header=False, index=False)

    # Make a Mappings directory if it does not exist
    if not os.path.exists('Mappings'):
        os.makedirs('Mappings')

if __name__ == '__main__':
    main()