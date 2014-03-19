# -*- coding: utf-8 -*-
"""
Created on Mon Feb 17 17:14:48 2014

@author: Lucio

mpi script for distributed computation of the ABC parameter inference. The 
job file in the helium home directory makes a call to this short script. This
script runs the ABCparameterInference scripts and saves the output to a file
that contains the name of the machine it is run on. 

"""

from mpi4py import MPI
import os

name = MPI.Get_processor_name()
os.popen("python ABCParameterInference.py 1000 ABCout"+name+".csv")
