# -*- coding: utf-8 -*-
"""
Created on Wed Oct 23 14:16:27 2013

@author: Lucio

Program for timing the execution time of SimpactPurple with clusters. 
Specifically the script is for running a simulation distributed across v2 & v3
on the vinci cluster.

"""
import time
import simpactpurple

population_ranges = range(10000,150001,10000)
#population_ranges = range(100,501,100)
#population_ranges = range(10000,30001,5000)

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
