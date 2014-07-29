# -*- coding: utf-8 -*-
"""
Created on Thu Jul 24 10:32:59 2014

@author: emmajacobs
"""

import numpy as np
import matplotlib.pyplot as plt

data = np.loadtxt('/Users/emmajacobs/Desktop/SimpactPurple/MainMigrationNeon1.out', delimiter=" ")
label = ['pop_power','dist_power','when','prev0','prev1','prev2','num_rela0','num_rela1','num_rela2']
nrows = len(data[:,1])

def calc_gravity(pop, dist, pop_power, dist_power):
    """The function used for calculating the gravity
    between communities in model. Copied here for 
    figure generation"""
    num = np.power(np.transpose(pop)*pop, pop_power)
    den = np.power(dist,dist_power)
     
    gravity = num/den
    probabilities = gravity / np.sum(gravity, axis=0)
    transition = np.cumsum(probabilities, axis=0)
     
    return gravity, probabilities, transition

#%% inputs predicting prevalence
for i in range(3):
    plt.figure()
    for j in range(3,6):
        plt.subplot(1,3,j-2)
        plt.scatter(data[:,i],data[:,j],c=data[:,0], linewidth=0)
        plt.xlabel(label[i])
        plt.ylabel(label[j])

#%% number of relationships predicting prevalence
plt.figure()
for i in range(6,9):
    plt.subplot(1,3,i-5,)
    plt.scatter(data[:,i],data[:,i-3])
    plt.xlabel(label[i])
    plt.ylabel(label[i-3])
    
#%% inputs predicting number of relationships
for i in range(3):
    plt.figure()
    for j in range(6,9):
        plt.subplot(1,3,j-5)
        plt.scatter(data[:,i],data[:,j],linewidth=0)
        plt.xlabel(label[i])
        plt.ylabel(label[j])
        
#%% visualize gravity as a function of power multipliers
dist = np.matrix([[1,3,5],[3,1,4],[5,4,1]])
pop = np.matrix([5, 3, 1])*500
plt.figure()
the_range = np.arange(-6,8,0.1)
for i in range(3):
    plt.subplot(1,3,i+1)
    #first is pop, second is dist
    plt.suptitle('Different Population Powers')
    #plt.suptitle('Different Distance Powers')
    plt.plot(the_range, np.matrix(map(lambda x: np.array(np.transpose(calc_gravity(pop, dist, x, 0.0)[1][:,i]))[0], the_range)))
    #plt.plot(the_range, np.matrix(map(lambda x: np.array(np.transpose(calc_gravity(pop, dist, 0.0, x)[1][:,i]))[0], the_range)))
    plt.yticks(np.arange(0.0,1.0,0.1))    
    plt.grid()    
    plt.legend(('...0','...1','...2'),'center right')
    plt.title('Probability of migrating from {0} to...'.format(i))
    plt.xlabel('Multiplier')
    plt.ylabel('Probability')