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
    #dist = np.matrix([[1,3,5],[3,1,4],[5,4,1]])
    dist = np.matrix([[1,5,12],[5,1,5],[12,5,1]])
    pop = np.matrix(population[1:])
    gravity, probabilities, transition = calc_gravity(pop, dist, pop_power, dist_power)
    timing = np.matrix([[1,3,5],[3,1,4],[5,4,1]])*5  # make a constant
    
    #assign roles via ranks
    if rank == 0: #Migration Operator
        mo = MigrationOperator.MigrationOperator(comm, primaries, gravity, timing)
        mo.NUMBER_OF_YEARS = time
        mo.run()
        
        #grab messages from communities
        #print "timing",timing
        #print "probabilities",probabilities
        prev = []
        num_rela = []
        for r in [1,2,3]:
            #prev.append(round(comm.recv(source = r),3))
            prev.append(comm.recv(source = r))
            num_rela.append(round(comm.recv(source = r),3))
        seed_time = comm.recv(source=3)
        
            
        #print pop_power,dist_power,when," ".join(map(str,prev)), " ".join(map(str,num_rela)),
        print pop_power,dist_power,when," ".join(map(lambda p: " ".join(map(str,p)),prev)),
        print " ".join(map(str,num_rela)),
        print " ".join([str(len(mo.removals[1557][s])) for s in range(3)]),
        print " ".join([str(len(mo.additions[1557][d])) for d in range(3)]),
        print seed_time
    elif rank in primaries:
        s = CommunityDistributed.CommunityDistributed(comm, rank, [], migration = True)
        s.INITIAL_POPULATION = population[rank]
        s.INITIAL_PREVALENCE = initial_prevalence[rank]
        s.SEED_TIME = 0
        s.NUMBER_OF_YEARS = time
                
        #change some parameters
        #s.DURATIONS = lambda a1, a2: 10
        s.INFECTIVITY = 0.01
        s.PROBABILITY_MULTIPLIER=0
        
        #run the model
        s.run()
        
        #generate some output to be analyzed
        #gad.prevalence_graph(s,filename="prevalence{0}.png".format(rank))
        #gad.demographics_graph(s,box_size=5,num_boxes=8, filename='demographics{0}.png'.format(rank))
        if s.is_primary:
            comm.send(gad.prevalence_data(s)[::52*5], dest = 0)
            comm.send(len(s.relationships), dest = 0)
        if rank == 3:
            comm.send(min([a.time_of_infection for a in s.agents.values()]), dest = 0)
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
time = 31
pop = 500
runs = 500

#cluster set up
population = np.array([0, 3, 3, 1])*pop #note that population size for non-primary doesn't matter
initial_prevalence = [0, 0.05, 0.05, 0]
primaries = [1, 2, 3]

if len(sys.argv)<4:
    #do the runs
    for i in range(runs):
        #generate random parameters and share
        who = 6.0*round(numpy.random.rand(), 2)
        where =  6.0*round(numpy.random.rand(), 2) #0.5 #
        when = random.choice(range(20,60,5)) #25 # 
            
        run(who, where, when)
else:
    run(float(sys.argv[1]),float(sys.argv[2]),int(sys.argv[3]))
