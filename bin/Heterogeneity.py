# -*- coding: utf-8 -*-
"""
Created on Sun Aug 31 12:29:02 2014

@author: Lucio

This is a script to investigate the variation in prevalence (and other
model outputs) due to different levels of heterogeneity.

"""

import os
import matplotlib
import numpy as np
if os.popen("echo $DISPLAY").read().strip() == '':  # display not set
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
import time
import simpactpurple
import simpactpurple.GraphsAndData as gad

colors = ['r','g','b']
parameters = [(0.0, 0.0), (-0.5, 0.0), (-0.5, -0.5)]
populations = [100, 1000, 10000]
runs = 10

if __name__ == '__main__':
    fig = plt.figure()
    fig.set_size_inches(15, 12)
    for i, para in enumerate(parameters):
        for j, pop in enumerate(populations):
            #set options for this graph
            plt.subplot(3,3,(i*3)+(j+1))
            plt.title("Population {0}, Scenario {1}".format(pop, i))
            if j==0:
                plt.ylabel('Prevalence (%)')
            if i==2:
                plt.xlabel('Time (years)')
                
            prev = []  # for creating average
            for k in range(runs):
                print i, j, k,
                #run it
                start = time.time()
                s = simpactpurple.Community()
                s.AGE_PROBABILITY_MULTIPLIER = para[0]
                s.SB_PROBABILITY_MULTIPLIER = para[1]
                s.INITIAL_POPULATION = pop
                s.INFECTIVITY = 0.1
                s.NUMBER_OF_YEARS = 30
                s.run()
                print round(time.time()-start,2),
                
                #graph it
                prev.append(gad.prevalence_data(s)*100)
                print prev[-1]
                plt.plot(np.arange(0,s.time)/52.0, prev[-1], c = colors[i])
                plt.ylim(0,100)
            plt.plot(np.arange(0,s.time)/52.0,np.average(prev, axis=0), c= 'k')
    plt.savefig('heterogeneity_plots.png', dpi = 150)