# -*- coding: utf-8 -*-
"""
Created on Wed Oct 23 14:16:27 2013

@author: Lucio

Program for assessing the memory footprint of the simulation. Needs the 
memory_profiler module (installed on the milano cluster).

"""

import os
import time
import sys
import simpactpurple
from memory_profiler import profile

@profile
def run_single(pop):
    s = simpactpurple.Community()
    s.INITIAL_POPULATION = pop
    
    #Simulate a run of the simulation
    s.start()   # initialize data structures
    
    #a few timesteps
    s.update_recruiting(s.RECRUIT_INITIAL)
    for i in range(s.RECRUIT_WARM_UP):
        s.time = i
        s.time_operator.step()  # 1. Time progresses
        s.relationship_operator.step()  # 2. Form and dissolve relationships
        s.infection_operator.step()  # 3. HIV transmission
        
    s.update_recruiting(s.RECRUIT_RATE)
    for i in range(s.RECRUIT_WARM_UP, int(s.NUMBER_OF_YEARS*52)):
        s.time = i
        s.time_operator.step()  # 1. Time progresses
        s.relationship_operator.step()  # 2. Form and dissolve relationships
        s.infection_operator.step()  # 3. HIV transmission
    
    #post-process / clean-up
    for pipe in s.pipes.values():
        pipe.send("terminate")
    
if __name__ == '__main__':
    run_single(int(sys.argv[1]))
