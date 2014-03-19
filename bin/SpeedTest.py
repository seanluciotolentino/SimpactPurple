# -*- coding: utf-8 -*-
"""
Created on Wed Oct 23 14:16:27 2013

@author: Lucio

Program for timing the execution time of SimpactPurple with clusters. Specifically,
this script should be run on the vinci cluster, but it's not appropriate for
helium.

"""

import os
import time
import simpactpurple

#population_ranges = range(1000,5001,1000)
population_ranges = range(100,501,100)
#population_ranges = range(10000,30001,10000)

print "\tmultiple\tsingle"
for pop in population_ranges:
    print pop,
    start = time.time()
    num_rela = os.popen("mpiexec -n 2 -host v2,v3 python distributed/MainDistributed.py "\
            + str(pop)).read()
    elapsed_time = round(time.time() - start,2)
    print elapsed_time,

    #continue
    start = time.time()
    s = simpactpurple.Community()
    s.INITIAL_POPULATION = pop
    s.run()
    elapsed_time = round(time.time() - start,2)
    print "\t",elapsed_time
