# -*- coding: utf-8 -*-
"""
Created on Wed Oct 23 14:16:27 2013

@author: Lucio

Program for timing the execution time of SimpactPurple with clusters. 
Specifically the script is for running on the vinci cluster; it's not 
appropriate for helium.

"""

import os
import time
import simpactpurple
import numpy as np
import numpy.random as random
population_ranges = range(1000,5001,1000)
#population_ranges = range(100,501,100)
#population_ranges = range(10000,30001,5000)

years = 30
print "\tmultiple\tsingle"
for pop in population_ranges:
    print pop,
    start = time.time()
    num_rela = os.popen("mpiexec -n 2 -host v2,v3 python bin/distributed/MainDistributed.py "\
            + str(pop) + " " + str(years)).read().strip()
    elapsed_time = round(time.time() - start,2)
    print elapsed_time,"(",num_rela,")",

    #continue
    start = time.time()
    s = simpactpurple.Community()
    s.INITIAL_POPULATION = pop
    s.NUMBER_OF_YEARS = years
    s.DURATIONS = lambda a1, a2: (np.mean((s.age(a1),s.age(a2)))/5)*random.exponential(5)
    #s.DURATIONS = lambda a1, a2: 4*random.exponential(5)
    s.run()
    elapsed_time = round(time.time() - start,2)
    print "\t",elapsed_time,"(",len(s.network.edges()),")"
