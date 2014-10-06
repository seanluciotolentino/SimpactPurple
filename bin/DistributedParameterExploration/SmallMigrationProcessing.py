# -*- coding: utf-8 -*-
"""
Created on Mon Sep 15 10:38:06 2014

@author: Lucio

Script to process the output from MainMigrationScenarios run with only
three inter-migrating communities and exploring three parameters:
    (1) Amount of migration
    (2) Time spent in home/away locations
    (3) Initial seeding scenarios

"""

#%% process some of the input
import matplotlib.pyplot as plt
import numpy as np
           
plt.ion()
name = ['Community 1', 'Community 2', 'Community 3']
colors = ['g','b','r']
plt.close('all')
plt.figure()
noise = 0.0 # set a default

#which data?
scenario = 1
if scenario == 0:
    data = np.loadtxt('SmallMigration.out', delimiter=" ")
    title = "Migration"
    noise = 0.1
elif scenario == 1:
    data = np.loadtxt('SmallTiming.out', delimiter=" ")
    title = "Timing"
elif scenario == 2:
    data = np.loadtxt('SmallSeeding.out', delimiter=" ")
    title = "Seeding"
    noise = 0.2

#make plots
thirty_prevalence = data[:,9:-1:7]  # indicies of 30-year prevalence in the data
fifteen_prevalence = data[:,6:-1:7]
for i in range(3):
    plt.subplot(1,3,i+1)
    plt.suptitle('Prevalence under Different {0} Scenarios'.format(title), fontsize=14)
    plt.scatter(data[:,scenario]+np.random.uniform(-noise, noise,
                size=np.size(data[:,scenario])),
                thirty_prevalence[:,i], 
                #c = data[:,scenario],
                c = data[:,0], # color by migration
                #c = fifteen_prevalence[:,i],
                linewidth=0)
        
    plt.title('Community {0}'.format(i))
    if i == 0:
        plt.ylabel('30-year Prevalence')
    plt.xlabel('{0} Value'.format(title))
    plt.ylim((0.0, 0.3))
    