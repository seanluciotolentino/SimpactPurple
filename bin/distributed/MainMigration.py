# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 11:14:02 2013

@author: Lucio

A script which uses MPI (mpi4py) to overlook several community simulations.  This
is the initial test script for proof of concept.

"""

from mpi4py import MPI
import simpactpurple.distributed.CommunityDistributed as CommunityDistributed
import simpactpurple.distributed.MigrationOperator as MigrationOperator
import sys
import simpactpurple.GraphsAndData as gad
import numpy as np
import numpy.random
import random

def calc_gravity(pop, dist, pop_power, dist_power):
     num = np.power(np.transpose(pop)*pop, pop_power)
     den = np.power(dist,dist_power)
     
     gravity = num/den
     probabilities = gravity / np.sum(gravity, axis=0)
     transition = np.cumsum(probabilities, axis=0)
     
     return gravity, probabilities, transition

def run(pop_power, dist_power, when):
    #use parameters in the model:
    dist = np.matrix([[1,3,5],[3,1,4],[5,4,1]])
    pop = np.matrix(population[1:])
    gravity, probabilities, transition = calc_gravity(pop, dist, pop_power, dist_power)
    timing = when*probabilities
    
    #assign roles via ranks
    if rank == 0: #Migration Operator
        mo = MigrationOperator.MigrationOperator(comm, primaries, gravity, timing)
        mo.NUMBER_OF_YEARS = time
        mo.run()
        
        #grab messages from communities
        prev = []
        num_rela = []
        for r in [1,2,3]:
            prev.append(round(comm.recv(source = r),3))
            num_rela.append(round(comm.recv(source = r),3))
        print pop_power,dist_power,when," ".join(map(str,prev)), " ".join(map(str,num_rela))
        
    elif rank in primaries:
        s = CommunityDistributed.CommunityDistributed(comm, rank, [], migration = True)
        s.INITIAL_POPULATION = population[rank]
        s.INITIAL_PREVALENCE = initial_prevalence[rank]
        s.SEED_TIME = 0
        s.NUMBER_OF_YEARS = time
                
        #change some parameters
        #s.DURATIONS = lambda a1, a2: 10
        s.INFECTIVITY = 0.01
        
        #run the model
        s.run()
        
        #generate some output to be analyzed
        if s.is_primary:
            comm.send(gad.prevalence_data(s)[-1], dest = 0)
            comm.send(len(s.relationships), dest = 0)
    
    else:
        master = rank%(comm.Get_size()/16)
        master = [3,master][master>0]
        s = CommunityDistributed.QueueServer(master, comm)
        s.run()

#MPI variables
name = MPI.Get_processor_name()
comm = MPI.COMM_WORLD
rank = comm.Get_rank()

#simulation parameters
time = 30
pop = 100
runs = 500

#cluster set up
population = np.array([0, 5, 3, 1])*pop #note that population size for non-primary doesn't matter
initial_prevalence = [0, 0.01, 0.01, 0]
primaries = [1, 2, 3]

if len(sys.argv)<4:
    #do the runs
    for i in range(runs):
        #generate random parameters and share
        who = round(numpy.random.rand(), 2)
        where =  round(numpy.random.rand(), 2) #0.5 #
        when = random.choice(range(20,60,5)) #25 # 
            
        run(who, where, when)
else:
    run(float(sys.argv[1]),float(sys.argv[2]),int(sys.argv[3]))