# -*- coding: utf-8 -*-
"""
Created on Tue Sep 02 13:23:24 2014

@author: Lucio

A script to investigate whether there is a substantial difference
in model output and model runtime from four scenarios:
    (1) Default simulation with resort and recycle
    (2) No resort skipping -- i.e. resort for every suitor
    (3) No recycling -- age difference and mean age are always recalculate
    (4) No resort skipping or recycling

This script runs each scenario by using modified community and
grid queue classes (defined in this script). When this script is
called to run the two values for resort and recycle must be provided
(i.e. which of the four scenarios should the script run?) along with
the function to run (output or speed).

"""

import simpactpurple
import simpactpurple.GridQueue as GridQueue
import simpactpurple.distributed.CommunityDistributed as CommunityDistributed
import numpy as np
import random
import simpactpurple.GraphsAndData as GraphsAndData
from mpi4py import MPI
import sys

class ModifiedGridQueue(GridQueue.GridQueue):
    def enquire(self, suitor):
        """
        Rewrite the enquire method so to check the scenario
        and act accordingly
        """
        #1. empty queue?
        if self.agents.empty():
            return None
        
        #2. Resort if dissimilar from previous suitor
        if self.previous is None or self.previous.grid_queue != suitor.grid_queue:
            suitor_age = self.age_of(suitor)
            ma = (suitor_age + self.age()) / 2
            ad = suitor_age - self.age()

            #flip coins for agents
            agents = list(self.agents.heap)
            self.agents.clear()
            for old_probability, agent in agents:  # old_probability is not needed
                #===START CHANGES 1/2===#
                if self.recycle:
                    probability = self.probability(agent, suitor, age_difference = ad, mean_age = ma)                
                else:
                    probability = self.probability(agent, suitor)
                #===END CHANGES=== 1/2#
                if random.random() < probability:                    
                    self.agents.push(agent.last_match,agent)
                else:
                    self.agents.push(np.inf, agent)
        #===START CHANGES 2/2===#
        if self.resort:
            self.previous = suitor
        #===END CHANGES 2/2===#

        #3. Update last_match and return an accepting agent
        accept, match = self.agents.pop()        
        if accept >= np.inf:
            self.agents.push(np.inf, match)  # push back in
            return None
        
        #3. 1 Check that suitor is not match
        match_name = match.name
        suitor_name = suitor.name
        if match_name == suitor_name:
            if self.agents.length() <= 1:  # if there is no one else
                self.agents.push(match.last_match, match)
                return None
            else:  # try to return the next in line
                new_accept, new_match = self.agents.pop()
                self.agents.push(accept, match)
                if new_accept >= np.inf:
                    self.agents.push(new_accept, new_match)
                    return None                    
                accept, match = new_accept, new_match
                match_name = match.name        
        
        #4. Finally, return match
        match.last_match = self.time
        self.agents.push(match.last_match, match)  # move from top position        
        return match_name

class ModifiedCommunity(CommunityDistributed.CommunityDistributed):
    def make_n_queues(self, n):
        """
        Change which GridQueue is used in the simulation.
        """
        #make the grid queues
        for i in range(n):
            gq = ModifiedGridQueue(self.next_top, self.next_bottom, self.grid_queue_index)
            gq.max_age = self.MAX_AGE
            gq.sex = i  # not used
            gq.PREFERRED_AGE_DIFFERENCE= self.PREFERRED_AGE_DIFFERENCE
            gq.AGE_PROBABILITY_MULTIPLIER = self.AGE_PROBABILITY_MULTIPLIER
            gq.PREFERRED_AGE_DIFFERENCE_GROWTH = self.PREFERRED_AGE_DIFFERENCE_GROWTH
            gq.SB_PROBABILITY_MULTIPLIER = self.SB_PROBABILITY_MULTIPLIER
            
            #===START CHANGES 1/1 ===#
            #add additional variables to grid queues
            gq.resort = self.resort
            gq.recycle = self.recycle
            #===END CHANGES 1/1 ===#
            
            self.grid_queues[gq.index] = gq
            self.grid_queue_index+=1
            self.spawn_process_for(gq)  # start a new process for it
        
        #increment for next grid queue
        self.next_top += self.BIN_SIZE*52
        self.next_bottom += self.BIN_SIZE*52

#%%script starts here
resort = int(sys.argv[1])
recycle = 1
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
n = 20
for i in range(n):
    if rank == 0:
        #run the modified simulation
        s = ModifiedCommunity(comm, rank, [])
        s.INITIAL_POPULATION = 10000
        s.resort = resort
        s.recycle = recycle
        s.run()
        
        #write it all to a file
        f = open("Resort{0}Recycle{1}.csv".format(resort, recycle),'a')
        f.write(str(i) + ",")
        f.write(",".join(map(lambda x: str(round(100*x,1)), GraphsAndData.intergenerational_sex_data(s, year = s.NUMBER_OF_YEARS)))+",")  # 2008
        f.write(",".join(map(lambda x: str(round(100*x,1)), GraphsAndData.number_of_partners_data(s, year = s.NUMBER_OF_YEARS)))+",")  # 2008
        f.write("\n")
        f.close()
    else:
        simpactpurple.distributed.CommunityDistributed.ServeQueue(0, comm)

#print "population\truntime"
#for pop in range(50000,300001,50000):
#    #single node version
#    start = time.time()
#    s = ModifiedCommunity()
#    s.resort = resort
#    s.recycle = recycle
#    s.INITIAL_POPULATION = pop
#    s.run()
#    elapsed_time = round(time.time() - start,2)
#    print pop,"\t",elapsed_time
