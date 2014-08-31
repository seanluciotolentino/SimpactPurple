# -*- coding: utf-8 -*-
"""
Created on Sun Aug 31 12:29:02 2014

@author: Lucio

This is a script to investigate the variation in prevalence (and other
model outputs) due to different levels of heterogeneity.

"""

import simpactpurple
import simpactpurple.GraphsAndData as gad
import os
import matplotlib
if os.popen("echo $DISPLAY").read().strip() == '':  # display not set
    matplotlib.use('Agg')
import matplotlib.pyplot as plt

colors = ['r','g','b']
parameters = [(0.0, 0.0), (-0.5, 0.0), (-0.5, -0.5)]
populations = [100, 1000, 10000]

if __name__ == '__main__':
    for i, para in enumerate(parameters):
        for j, pop in enumerate(populations):
            if i==0:
                plt.ylabel('Prevalence (%)')
            if j==2:
                plt.ylabel('Prevalence (%)')
            plt.subplot(3,3,(j*3)+(i+1))
            plt.title("Population {0}, Age Mult {1}, SB Mult {2}".format(pop, para[0], para[1]))
            for k in range(10):
                print i, j, k
                #run it
                s = simpactpurple.Community()
                s.AGE_PROBABILITY_MULTIPLIER = para[0]
                s.SB_PROBABILITY_MULTIPLIER = para[1]
                s.INITIAL_POPULATION = pop
                s.INFECTIVITY = 0.1
                s.NUMBER_OF_YEARS = 30
                s.run()
                
                #graph it
                plt.plot(gad.prevalence_data(s), c = colors[i])
    plt.savefig('heterogeneity_plots.png')