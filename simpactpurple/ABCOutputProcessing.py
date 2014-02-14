# -*- coding: utf-8 -*-
"""
Created on Fri Feb 14 12:28:59 2014

@author: Lucio

A script for processing the file produces by the ABCParameterInference script.
This script reads in the file and produces 26 subplots in 5 different figures.
The figures and subplots are:
    -Multiple Partners for 15-24 y.o. (2 sex x 3 years = 6 subplots)
    -Multiple Partners for 25-49 y.o. (2 sex x 3 years = 6 subplots)
    -Multiple Partners for 50+ y.o. (2 sex x 3 years = 6 subplots)
    -Intergenerational relationships (2 sex x 2 years = 4 subplots)
    -Non-intergenerational relationships (2 sex x 2 years = 4 subplots)

"""

import numpy as np

np.set_printoptions(precision=2, suppress=True)
data = np.loadtxt('ABCoutput.csv', delimiter=",")

threshold = 400
accepted = data[data[:,-2]<=threshold,:]