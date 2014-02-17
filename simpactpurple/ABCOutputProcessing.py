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
import matplotlib.pyplot as plt
import numpy as np

def make_multiple_partners_figure(data, lowerbound, upperbound, rows, title):    
    plt.figure()
    plt.suptitle(title,fontsize=20)
    for index in range(6):
        plt.subplot(3,2,index+1)    
        #simulation distribution
        plt.hist(accepted[:,rows[index]], normed=True, bins = 20, color = col)
        #data values
        value = data[index]
        lb = lowerbound[index]
        ub = upperbound[index]
        plt.errorbar((value,), (red_marker_location,), xerr=((value-lb,),(ub-value,)),
                     color='r', fmt='o', linewidth=2, capsize=5, mec = 'r')
        #labeling    
        plt.ylim(0,ylimit)
        plt.xlim(0,40)
    #make subplots pretty
    plt.subplot(3,2,1)
    plt.title("Males")
    plt.ylabel("'02\nFrequency")
    plt.subplot(3,2,2)
    plt.title("Females")
    plt.subplot(3,2,3)
    plt.ylabel("'05\nFrequency")
    plt.subplot(3,2,5)
    plt.ylabel("'08\nFrequency")
    plt.xlabel("Percent Responding Affirmatively")
    plt.subplot(3,2,6)
    plt.xlabel("Percent Responding Affirmatively")
    
def make_intergenerational_figure(data, lowerbound, upperbound, rows, title):
    plt.figure()
    plt.suptitle(title,fontsize=20)
    for index in range(4):
        plt.subplot(2,2,index+1)    
        #simulation distribution
        plt.hist(accepted[:,rows[index]], normed=True, bins = 20, color = col)
        #data values
        value = data[index]
        lb = lowerbound[index]
        ub = upperbound[index]
        plt.errorbar((value,), (red_marker_location,), xerr=((value-lb,),(ub-value,)),
                     color='r', fmt='o', linewidth=2, capsize=5, mec = 'r')
        #labeling    
        plt.ylim(0,ylimit)
        plt.xlim(0,100)
    #make subplots pretty
    plt.subplot(2,2,1)
    plt.title("Males")
    plt.ylabel("'05\nFrequency")
    plt.subplot(2,2,2)
    plt.title("Females")
    plt.subplot(2,2,3)
    plt.ylabel("'08\nFrequency")
    plt.xlabel("Percent Responding Affirmatively")
    plt.subplot(2,2,4)
    plt.xlabel("Percent Responding Affirmatively")
    
#%% Script starts here!
np.set_printoptions(precision=2, suppress=True)
data = np.loadtxt('ABCoutput.csv', delimiter=",")
threshold = 400
accepted = data[data[:,-2]<=threshold,:]
red_marker_location = 0.25
ylimit = 0.3
col = 'g'

#%% Posterior Distributions
parameters = ["Probability Multiplier", "Preferred Age Difference",
              "Preferred Age Difference Growth", "DNP Scale", "DNP Shape",
              "Duration Scale", "Durations Shape"]
limits = [(-0.01, -0.5), (-0.01, -0.3), (0.01, 2), 
          (1, 4), (0.05, 0.9),
          (0, 5), (2, 10)]
plt.figure()
plt.suptitle("Posterior Distributions")
for i in range(7):
    plt.subplot(3,3,i+1)
    #plt.hist(data[:,i+1],color='g',normed=True)
    plt.hist(accepted[:,i+1], color = col)    
    plt.title(parameters[i])
    plt.xlim(limits[i])
    plt.ylabel("Frequency")

#%% Distribution of distances
plt.figure()
plt.hist(data[:,-2], bins = range(0,2000,100), color = col)
plt.title("Distribution of Simulation Distances")
plt.xlabel("Distance from Survey")
plt.ylabel("Frequency")

#%% Multiple Partners for 15-24 year olds
data = [23.0,8.8,27.2,6.0,30.8,6.0]
lb = [20,7.5,23,4.8,26,4.5]
ub = [27.5,11,32,7.5,35.5,7.5]
rows = [15,16,21,22,27,28]
make_multiple_partners_figure(data,lb,ub,rows,"15-24 y.o. with Multiple Partners")

#%% Multiple Partners for 25-49 year olds
data = [11.5,2.5,14.4,1.8,14.8,3.0]
lb = [9.5,2,11,1,13.5,2]
ub = [13,3,17.5,2.5,17.5,4]
rows = [17,18,23,24,29,30]
make_multiple_partners_figure(data,lb,ub,rows,"25-49 y.o. with Multiple Partners")

#%% Multiple Partners for 50+ year olds
data = [7.5,0.6,9.8,0.3,3.7,0.8]
lb = [5.5,0,6,0,2.5,0]
ub = [10.5,1,14.8,0.8,5.5,0.5]
rows = [19,20,25,26,31,32]
make_multiple_partners_figure(data,lb,ub,rows,"50+ y.o. with Multiple Partners")

#non-Intergenerational relationships
data = [98.0,81.4,98.5,72.4]
lb = [95.8,75.5,95.8,65.5]
ub = [99.0,86.1,99.4,78.3]
rows = [7,9,11,13]
make_intergenerational_figure(data, lb, ub, rows, "Non-Intergenerational Relationships")

#Non-intergenerational relationships
data = [2.0,18.5,0.7,27.6]
lb = [1.0,13.7,0.2,21.7]
ub = [4.2,24.4,2.7,34.5]
rows = [8,10,12,14]
make_intergenerational_figure(data, lb, ub, rows, "Intergenerational Relationships")