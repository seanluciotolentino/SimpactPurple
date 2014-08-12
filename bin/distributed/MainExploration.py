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
import simpactpurple.distributed.MigrationOperator as MigrationOperator
import simpactpurple.GraphsAndData as gad
import numpy as np
import random
import sys

def run(parameter):
    #assign roles via ranks
    if rank == 0: #Migration Operator
        mo = MigrationOperator.MigrationOperator(comm, primaries, gravity, timing)
        mo.NUMBER_OF_YEARS = time
        mo.run()
        
        #grab messages from communities
        prev = [comm.recv(source = r) for r in primaries]
        print parameter," ".join(map(lambda p: " ".join(map(str,p)),prev))
    elif rank in primaries:
        s = CommunityDistributed.CommunityDistributed(comm, rank, [], migration = True)
        s.INITIAL_POPULATION = int(population[rank-1])
        s.INITIAL_PREVALENCE = initial_prevalence[rank-1]
        s.SEED_TIME = 0
        s.NUMBER_OF_YEARS = time
        s.PROBABILITY_MULTIPLIER = 0
        s.run()
        
        #generate some output to be analyzed
        if s.is_primary:
            comm.send(gad.prevalence_data(s)[::52*5], dest = 0)
    else:
        master = rank%(comm.Get_size()/16)
        master = [3,master][master>0]
        CommunityDistributed.ServeQueue(master, comm)

#MPI variables
name = MPI.Get_processor_name()
comm = MPI.COMM_WORLD
rank = comm.Get_rank()

#simulation setup parameters
time = 30.5
num_runs = 100
num_communities = 3
fraction = 1.0 / 1000
primaries = [1, 2, 3]
migration = np.loadtxt('migration.csv', delimiter=",")  # place this in your neon home directory
population = np.array([migration[i,i] for i in range(num_communities)])*fraction
gravity = migration[:num_communities,:num_communities]
timing = np.matrix([[1,5,5],[5,1,5],[5,5,1]])
prevalence_scenarios = [[51, 0, 0], [0, 51, 0], [0, 0, 51], [17, 17, 17]]  # these are set based on fraction = 1/1000

#set parameter ranges
migration_choices = [0.1, 0.5, 1.0, 2.0]
timing_choices = range(1,8,2)
prevalence_choices = range(len(prevalence_scenarios))

#set the defaults
gravity = np.power(gravity, migration_choices[0])
timing = timing*timing_choices[0]
initial_prevalence = prevalence_scenarios[prevalence_choices[0]] / population

#run it
effect = int(sys.argv[1])
for i in range(num_runs):            
    if effect == 1:
        #random migration power
        parameter = random.choice(migration_choices)
        gravity = np.power(gravity, parameter)
    elif effect == 2:
        #random timing
        parameter = random.choice(timing_choices)
        timing = timing*parameter
    elif effect == 3:
        #random initial prevalence
        parameter = random.choice(prevalence_choices)
        initial_prevalence = prevalence_scenarios[prevalence_choices[parameter]] / population
    else:
        #random choice for each
        parameter1 = random.choice(migration_choices)
        gravity = np.power(gravity, parameter1)
        
        parameter2 = random.choice(timing_choices)
        timing = timing*parameter2
        
        parameter3 = random.choice(prevalence_choices)
        initial_prevalence = prevalence_scenarios[prevalence_choices[parameter3]] / population        
        
        parameter = " ".join(map(str, [parameter1, parameter2, parameter3]))
    
    #finally, run the model
    run(parameter)