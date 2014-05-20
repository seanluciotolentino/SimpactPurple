# -*- coding: utf-8 -*-
"""
Created on Wed Oct 23 14:16:27 2013

@author: Lucio

Program for timing the execution time of single SimpactPurple community.

"""
import time
import simpactpurple

population_ranges = range(10000,150001,10000)
#population_ranges = range(100,501,100)
#population_ranges = range(10000,30001,5000)

if __name__ == '__main__':
    years = 30
    print "population\truntime"
    for pop in population_ranges:
        #single node version
        start = time.time()
        s = simpactpurple.Community()
        s.INITIAL_POPULATION = pop
        s.NUMBER_OF_YEARS = years
        s.run()
        elapsed_time = round(time.time() - start,2)
        print pop,"\t",elapsed_time
