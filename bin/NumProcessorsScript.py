# -*- coding: utf-8 -*-
"""
Created on Thu Nov 07 11:39:12 2013

@author: Lucio

Script for determining runtime versus number of processors. Need to add 
semaphore to grid queues and s.NUM_CPUS to community. 

"""

import simpactpurple
import simpactpurple.GraphsAndData as gad
import time

if __name__ == '__main__':
    num_processors = range(1,6)
    for bin_size in [1, 5, 10]:
        print (50.0/bin_size)*2,"grid queues"
        for n in num_processors:
            start = time.time()
            s = simpactpurple.Community()
            s.INITIAL_POPULATION = 1000
            s.probability_multiplier = -0.2
            s.NUMBER_OF_YEARS = 30
            s.NUM_CPUS = n
            s.BIN_SIZE = bin_size
            s.run()
            print n, time.time()-start
        #gad.age_mixing_graph(s,filename='age-mixing{0}.png'.format(bin_size))

