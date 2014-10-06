# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 11:14:02 2013

@author: Lucio

A script to explore the effects of migration, timing, and initial prevalence
seeding in a 3 community setting. This script is meant to be run on Neon
which has 16 cores per node.

Migration info from StatsSA:

http://www.statssa.gov.za/publications/P03014/P030142011.pdf (page 26)
matrix([[5158316,	40152,	10566,	5155,	9221,	5039,	50694,	4759,	3381],	
        [170829,	6250135,	5081,	15542,	73831,	32341,	117964,	12001,	8877],	
        [17577,	4077,	1054841,	8559,	5708,	11478,	16019,	4202,	1907],	
        [12644,	8155,	7103,	2524282,	8881,	24090,	74387,	10859,	5283],	
        [21857,	19178,	2437,	11481,	9812129,	8655,	184337,	28904,	4719],	
        [6013,	3085,	17000,	9917,	3882,	3146255,	103550,	8495,	14066],	
        [74915,	40161,	9446,	31455,	55620,	75260,	10416258,	61269,	54145],	
        [7256,	3390,	1932,	5032,	12511,	13091,	122578,	3723843,	25299],	
        [7826,	2742,	1847,	5481,	4574,	26826,	283495,	39492,	5088084]])

#some commands that might helpful:
gravity = gravity.astype(float)
probabilities = gravity / np.sum(gravity, axis=0)
np.set_printoptions(precision=3, linewidth=150)

"""

from mpi4py import MPI
import simpactpurple.distributed.CommunityDistributed as CommunityDistributed
import simpactpurple.GraphsAndData as gad
import numpy as np
import random as random
import sys
import time

def run():
    if rank < num_communities and rank<num_primaries:
        start = time.time()
        op = [p for p in range(min(9,num_communities)) if p != rank]
        others = range(rank+9, num_communities, 9)
        s = CommunityDistributed.CommunityDistributed(comm, rank, others, 
                other_primaries = op, timing = timing, gravity = gravity)
        s.INITIAL_POPULATION = int(population[rank])
        s.INITIAL_PREVALENCE = init_prev[rank]
        s.NUMBER_OF_YEARS = years
        s.DURATIONS = lambda a1, a2: np.mean((s.age(a1),s.age(a2)))*np.random.exponential(5)
        s.run()
        
        #generate some output to be analyzed
        if rank == 0:
            prev = [comm.recv(source = r) for r in range(1, num_primaries)]
            prev.insert(0,[round(p,3) for p in gad.prevalence_data(s)[::52*5]])
            print migration_amount,timing_scale, seed_scenario,
            print " ".join(map(lambda p: " ".join(map(str,p)),prev)),
            print round(time.time() - start, 3),
            print " ".join(map(lambda p: " ".join(map(str,p)),init_prev))
        else:
            comm.send([round(p,3) for p in gad.prevalence_data(s)[::52*5]], dest = 0)
    elif rank < num_communities:
        s = CommunityDistributed.CommunityDistributed(comm, rank-9, [rank-9])
        s.run()
    else:
        master = rank%num_communities
        CommunityDistributed.ServeQueue(master, comm)

#MPI variables
name = MPI.Get_processor_name()
comm = MPI.COMM_WORLD
rank = comm.Get_rank()

#simulation setup parameters
years = 30.1
num_runs = 100
num_primaries = np.min(9,comm.Get_size()/16)
num_communities = comm.Get_size()/16
fraction = 1.0 / 100
seed_prevalence = 0.01
migration = np.loadtxt('migration.csv', delimiter=",")  # place this in your neon home directory
population = np.array([migration[i,i] for i in range(num_primaries)])*fraction

#switch based provided input
migration_amount = 1.0
timing_scale = 3.0
seed_scenario = 0
try:
    scenario = int(sys.argv[1])
except IndexError:
    scenario = 0    

#actually run it
for i in range(num_runs):
    #grab random variables
    if scenario == 0:
        migration_amount = random.choice([0.1, 0.6, 1.0, 1.5, 2.0])    
    elif scenario == 1:
        timing_scale = random.choice([1.0,3.0,5.0,7.0])
    elif scenario == 2:
        seed_scenario = random.choice([0,1,2])        
    
    #create parameters based on random variables
    #migrations
    gravity = migration[:num_primaries,:num_primaries]
    gravity = np.power(gravity, migration_amount)
    #timing
    timing = np.ones(shape=(num_primaries,num_primaries))*timing_scale
    for i in range(num_primaries):
        for j in range(num_primaries):
            if i == j:
                continue
            else:
                timing[i,j] = timing[i,j]*5
    #initial seeds
    number_seeds = seed_prevalence * sum(population)
    if seed_scenario == 0: # isolated seed in community 0
        init_prev = [0] * num_primaries
        init_prev[0] = number_seeds / population[0]
    elif seed_scenario == 1: # population dispersed
        init_prev = (number_seeds/num_primaries) / population
    else:  #geographically dispersed
        init_prev = [seed_prevalence]*num_primaries
    run()
