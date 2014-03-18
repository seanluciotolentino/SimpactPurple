# -*- coding: utf-8 -*-
"""
Created on Sun Mar 16 10:33:32 2014

@author: Lucio

Produce graphs for Chapter 3: The Mathematical Formulation

"""

import numpy as np
import numpy.random as random
import matplotlib.pyplot as plt

#%% Different Probability Multipliers
#h_ij = exp ( probability_multiplier * abs( age_difference(i,j) - preferred_age_difference ) )
plt.figure()
age_difference = np.arange(-20,21,0.5)
preferred_age_difference = np.repeat(0, len(age_difference))
probability_multipliers = [-0.01, -0.1, -0.5]
for probability_multiplier in probability_multipliers:
    hazard = np.exp(probability_multiplier*np.abs(age_difference - preferred_age_difference))
    plt.plot(age_difference, hazard)
plt.legend([str(pm) for pm in probability_multipliers], bbox_to_anchor = (1, 0.8))
plt.grid()
plt.yticks(np.arange(0,1.1,0.1))
plt.ylabel('Hazard of Age Difference')
plt.xlabel('Age Difference')
plt.xlim((-20,20))
plt.title('Hazards of Age Difference for Various Probability Multipliers')

#%% Hazards for different Age Combinations
#some graph parameters
pop = 10000
min_age = 15
max_age = 65
range_age = max_age - min_age
#calculate some random age differences
male_ages = (np.random.rand(pop)*range_age)+min_age
female_ages = (np.random.rand(pop)*range_age)+min_age
mean_age = ((male_ages+female_ages)/2) -15
age_difference = female_ages-male_ages

## hazard 0 (simple)
#baseline = 1
#age_difference_factor = -0.1
#mean_age_factor = -0.03
##h = baseline*np.exp(age_difference_factor*np.abs(age_difference))
#h = baseline*np.exp(age_difference_factor*np.abs(age_difference) + mean_age_factor*mean_age)

## hazard 1 parameters (note: for factors lower -> narrower)
#preferred_age_difference = -0.2
#probability_multiplier = -0.1
#preferred_age_difference_growth = 2
#top = abs(age_difference - (preferred_age_difference*mean_age) )
#h = np.exp(probability_multiplier * top)
preferred_age_difference = -0.2
probability_multiplier = -0.1
preferred_age_difference_growth = 2
age_difference_dispersion = -0.2
top = abs(age_difference - (preferred_age_difference * preferred_age_difference_growth * mean_age) )
bottom = preferred_age_difference*mean_age*age_difference_dispersion
h = np.exp(probability_multiplier * (np.transpose(top)/bottom))

#make graph
plt.figure()
plt.scatter(male_ages,female_ages,c=h,linewidths=0)
plt.plot((min_age,max_age),(min_age,max_age),linewidth=2,c='k')
plt.colorbar()
plt.xlim(15,65)
plt.ylim(15,65)
plt.title("Age Mixing Scatter")
plt.xlabel("Male Age")
plt.ylabel("Female Age")

#%% DNP Distribution
#shape = 0.1
#scale = 1.5
#DNP = lambda: random.power(shape)*scale
#values = [DNP() for i in range(1000)]
#plt.figure()
#plt.hist(values, normed=True)

