import netCDF4 as nc
import numpy as np
from prompt_toolkit import prompt
from prompt_toolkit.completion import PathCompleter

def compare_nc_files(file1, file2, threshold=1e-6):
    # Open both NetCDF files
    nc1 = nc.Dataset(file1, 'r')
    nc2 = nc.Dataset(file2, 'r')
    
    # Get the list of variables from both files
    vars1 = nc1.variables.keys()
    vars2 = nc2.variables.keys()

    # Check if both files have the same variables
    if set(vars1) != set(vars2):
        print("The files have different variables.")
        print(f"Variables in {file1}: {vars1}")
        print(f"Variables in {file2}: {vars2}")
        return False

    all_match = True

    # Loop through each variable and compare the data
    for var in vars1:
        data1 = nc1.variables[var][:]
        data2 = nc2.variables[var][:]
        
        # Check if the shapes of the data are the same
        if data1.shape != data2.shape:
            print(f"Shape mismatch in variable {var}: {data1.shape} vs {data2.shape}.")
            all_match = False
            continue

        # Compare the two datasets with the given threshold
        difference = np.abs(data1 - data2)
        max_diff = np.max(difference)

        if np.all(difference <= threshold):
            print(f"Variable {var} matches within the threshold of {threshold}.")
        else:
            print(f"Variable {var} differs. Max difference: {max_diff}.")
            all_match = False

    return all_match

# set up path completer
path_completer = PathCompleter(only_directories=False)
# prompt user for file names
file1 = prompt("Enter the path to the first NetCDF file: ", completer=path_completer)
file2 = prompt("Enter the path to the second NetCDF file: ", completer=path_completer)

# Compare the two NetCDF files
comparison_result = compare_nc_files(file1, file2)

if comparison_result:
    print("All variables match within the given threshold.")
else:
    print("Some variables differ.")
