# Use latest python image as base image
FROM python:latest

# Update pip
RUN pip install --upgrade pip

# Install required packages
RUN pip install numpy
RUN pip install pandas
RUN pip install cdsapi
RUN pip install netCDF4