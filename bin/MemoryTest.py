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
import sys
import Community
from memory_profiler import profile

@profile
def run_single(pop):
    s = Community.Community()
    s.INITIAL_POPULATION = pop
    
    #Simulate a run of the simulation
    s.start()   # initialize data structures
    
    #a few timesteps
    for i in range(int(s.NUMBER_OF_YEARS*52)):
        s.time = i
        s.time_operator.step()  # 1. Time progresses
        s.relationship_operator.step()  # 2. Form and dissolve relationships
        s.infection_operator.step()  # 3. HIV transmission
    
    #cleanup
    s.cleanup()
    

if __name__ == '__main__':
    run_single(int(sys.argv[1]))
