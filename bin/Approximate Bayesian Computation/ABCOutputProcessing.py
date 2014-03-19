# -*- coding: utf-8 -*-
"""
Created on Fri Feb 14 12:28:59 2014

@author: Lucio

A script for processing the file produced by the ABCParameterInference script.
This script reads in the file and produces 7 figures, 5 of which have
26 subplots communatively.
The figures and subplots are:
    -Posterior distributions of parameters
    -Distribution of distances
    -Multiple Partners for 15-24 y.o. (2 sex x 3 years = 6 subplots)
    -Multiple Partners for 25-49 y.o. (2 sex x 3 years = 6 subplots)
    -Multiple Partners for 50+ y.o. (2 sex x 3 years = 6 subplots)
    -Intergenerational relationships (2 sex x 2 years = 4 subplots)
    -Non-intergenerational relationships (2 sex x 2 years = 4 subplots)

"""
import matplotlib.pyplot as plt
import numpy as np
import os

def load_data():
    """
    Returns matrix of data to use: Looks for pre-built ABCoutput.csv and
    returns it if it exists. Otherwise builds data matrix from all other
    ABCoutput files (generated by the cluster).
    """
    files = os.popen('ls ABCoutput/ABCout*').read().split('\n')[:-1]
    if 'ABCoutput/ABCoutput.csv' in files:
        return np.loadtxt('ABCoutput/ABCoutput.csv', delimiter=",")
    else:
        data = np.loadtxt(open(files[0]), delimiter=",")
        
        for filename in files[1:]:
            data = np.append(data, np.loadtxt(open(filename), delimiter=","),axis=0)
        np.savetxt(fname='ABCoutput/ABCoutput.csv',X=data,delimiter=",")
        return data

def make_multiple_partners_figure(data, lowerbound, upperbound, rows, title):    
    plt.figure(figsize=(10,10))
    plt.suptitle(title,fontsize=20)
    for index in range(6):
        plt.subplot(3,2,index+1)    
        #simulation distribution
        plt.hist(accepted[:,rows[index]], normed=True, bins = range(0,100,2), color = col)
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
    plt.figure(figsize=(10,10))
    plt.suptitle(title,fontsize=20)
    for index in range(4):
        plt.subplot(2,2,index+1)    
        #simulation distribution
        plt.hist(accepted[:,rows[index]], normed=True, bins = range(0,100,5), color = col)
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

#################################################################
#%% Script starts here!
np.set_printoptions(precision=2, suppress=True)
threshold = 250
red_marker_location = 0.15  # for showing survey data
ylimit = 0.20  # upper y-lim for graphs
col = 'b'  # color of bars
save = True  # save to file?

data = load_data()
#accepted = data[data[:,-1]<=threshold,:]
accepted = data[np.random.random((len(data),1))[:,0]<=0.02,:]

#%% Posterior Distributions
parameters = ["Probability Multiplier", "Preferred Age Difference",
              "Preferred Age Difference Growth", "DNP Scale", "DNP Shape",
              "Duration Scale", "Durations Shape"]
limits = [(-0.01, -0.3), (-0.01, -0.5), (0.01, 2), 
          (1, 4), (0.05, 0.9),
          (2, 10), (0, 5)]
plt.figure(figsize=(12,12))
plt.suptitle("Posterior Distributions",fontsize=20)
for i in range(7):
    plt.subplot(3,3,i+1)
    #plt.hist(data[:,i+1],color='g',normed=True)
    plt.hist(accepted[:,i+1], color = col)    
    plt.title(parameters[i])
    plt.xlim(limits[i])
    plt.ylabel("Frequency")
if save:
    plt.savefig('ABCgraphs/posterior_'+col+'.png')

#%% Distribution of distances
plt.figure()
hist = plt.hist(data[:,-1], bins = range(0,2000,50), color = col)
plt.title("Distribution of Simulation Distances")
plt.xlabel("Distance from Survey")
plt.ylabel("Frequency")
# descriptive line and text
above = 400
space = above/4.0
plt.plot((threshold, threshold), (0,max(hist[0])+above),'r--')
plt.text(x=threshold,y=max(hist[0])+space*3,s=("  Acceptance threshold: "+str(threshold)))
acceptance_rate = str(round(len(accepted)/float(len(data)),2))
plt.text(x=threshold,y=max(hist[0])+space*2,s=("  # Accepted: "+str(len(accepted))+" of "+str(len(data))))
plt.text(x=threshold,y=max(hist[0])+space*1,s=("  % Accepted: "+acceptance_rate))
if save:
    plt.savefig('ABCgraphs/distance_distribution_'+col+'.png')

#%% Multiple Partners for 15-24 year olds
survey_data = [23.0,8.8,27.2,6.0,30.8,6.0]
lb = [20,7.5,23,4.8,26,4.5]
ub = [27.5,11,32,7.5,35.5,7.5]
rows = [16, 17, 22, 23, 28, 29]
make_multiple_partners_figure(survey_data,lb,ub,rows,"15-24 y.o. with Multiple Partners")
if save:
    plt.savefig('ABCgraphs/mp_young_'+col+'.png')

#%% Multiple Partners for 25-49 year olds
survey_data = [11.5,2.5,14.4,1.8,14.8,3.0]
lb = [9.5,2,11,1,13.5,2]
ub = [13,3,17.5,2.5,17.5,4]
rows = [18, 19, 24, 25, 30, 31]
make_multiple_partners_figure(survey_data,lb,ub,rows,"25-49 y.o. with Multiple Partners")
if save:
    plt.savefig('ABCgraphs/mp_adult_'+col+'.png')

#%% Multiple Partners for 50+ year olds
survey_data = [7.5,0.6,9.8,0.3,3.7,0.8]
lb = [5.5,0,6,0,2.5,0]
ub = [10.5,1,14.8,0.8,5.5,0.5]
rows = [20, 21, 26, 27, 32, 33]
make_multiple_partners_figure(survey_data,lb,ub,rows,"50+ y.o. with Multiple Partners")
if save:
    plt.savefig('ABCgraphs/mp_old_'+col+'.png')

#change this for generational graphs
red_marker_location = 0.10  # for showing survey data
ylimit = 0.12  # upper y-lim for graphs

#non-Intergenerational relationships
survey_data = [98.0,81.4,98.5,72.4]
lb = [95.8,75.5,95.8,65.5]
ub = [99.0,86.1,99.4,78.3]
rows = [8, 10, 12, 14]
make_intergenerational_figure(survey_data, lb, ub, rows, "Non-Intergenerational Relationships")
if save:
    plt.savefig('ABCgraphs/noninter_'+col+'.png')

#Non-intergenerational relationships
survey_data = [2.0,18.5,0.7,27.6]
lb = [1.0,13.7,0.2,21.7]
ub = [4.2,24.4,2.7,34.5]
rows = [9, 11, 13, 15]
make_intergenerational_figure(survey_data, lb, ub, rows, "Intergenerational Relationships")
if save:
    plt.savefig('ABCgraphs/inter_'+col+'.png')