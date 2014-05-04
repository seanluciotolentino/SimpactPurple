# -*- coding: utf-8 -*-
"""
Created on Wed Oct 23 14:16:27 2013

@author: Lucio

Program for timing the execution time of SimpactPurple with clusters. 
Specifically the script is for running a simulation distributed across v2 & v3
on the vinci cluster.

"""

import os
import time
import simpactpurple

population_ranges = range(5000,30001,5000)
#population_ranges = range(100,501,100)
#population_ranges = range(10000,30001,5000)

years = 30
print "\tmultiple\tsingle"
for pop in population_ranges:
    print pop,
    
    #distributed version
    start = time.time()
    num_rela = os.popen("mpiexec -n 2 -host v2,v3 python bin/distributed/MainDistributed.py "\
            + str(pop) + " " + str(years)).read().strip()
    elapsed_time = round(time.time() - start,2)
    print elapsed_time,

    #single node version
    start = time.time()
    s = simpactpurple.Community()
    s.INITIAL_POPULATION = pop
    s.NUMBER_OF_YEARS = years
    s.run()
    elapsed_time = round(time.time() - start,2)
    print "\t",elapsed_time
