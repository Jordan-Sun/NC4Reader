# Use latest python image as base image
FROM python:latest

# Update pip
RUN pip install --upgrade pip

# Basic packages
RUN pip install numpy
RUN pip install pandas

# Reading and writing data packages
RUN pip install cdsapi
RUN pip install netCDF4

# Plotting packages
RUN pip install matplotlib
RUN pip install cartopy