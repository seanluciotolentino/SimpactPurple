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
import numpy.random as random
import sys

def run():
    if rank < num_communities:
        op = [p for p in range(num_communities) if p != rank]
        s = CommunityDistributed.CommunityDistributed(comm, rank, [], 
                other_primaries = op, timing = timing, gravity = gravity)
        s.INITIAL_POPULATION = int(population[rank])
        s.INITIAL_PREVALENCE = init_prev[0][rank]
        s.NUMBER_OF_YEARS = time
        s.DURATIONS = lambda a1, a2: np.mean((s.age(a1),s.age(a2)))*random.exponential(5)
        s.run()
        
        #generate some output to be analyzed
        if rank == 0:
            prev = [comm.recv(source = r) for r in range(1, num_communities)]
            prev.insert(0,[round(p,3) for p in gad.prevalence_data(s)[::52*5]])
            #print migration_amount," ".join(map(lambda p: " ".join(map(str,p)),prev))
            print migration_amount, prev
        else:
            comm.send([round(p,3) for p in gad.prevalence_data(s)[::52*5]], dest = 0)
    else:
        master = rank%(comm.Get_size()/16)
        CommunityDistributed.ServeQueue(master, comm)

#MPI variables
name = MPI.Get_processor_name()
comm = MPI.COMM_WORLD
rank = comm.Get_rank()

#simulation setup parameters
time = 30.5
num_runs = 100
num_communities = comm.Get_size()/16
fraction = 1.0 / 1000
time_home = 3
time_away = 8
seed_community = min(6, num_communities-1)  # Gautang if there's that many communities
seed_prevalence = 0.05
initial_prevalence = 0.01
try:
    migration_amount = [0.1, 0.5, 0.75, 1.0, 2.0][int(sys.argv[1])]
except:
    migration_amount = 1.0 

#create parameters based on above parameters
migration = np.loadtxt('migration.csv', delimiter=",")  # place this in your neon home directory
population = np.array([migration[i,i] for i in range(num_communities)])*fraction
gravity = migration[:num_communities,:num_communities]
timing = np.ones(shape=(num_communities,num_communities))*time_away
for i in range(num_communities):
    timing[i,i] = time_home
init_prev = np.ones(shape=(1,num_communities))*initial_prevalence
init_prev[0][seed_community] = seed_prevalence
gravity = np.power(gravity, migration_amount)

#actually run it
for i in range(num_runs):
    run()
    
    
#%% process some of the input
import matplotlib.pyplot as plt
name = ['Western Cape', 'Eastern Cape', 'Northern Cape', 'Free State', 
        'KZN', 'NorthWest', 'Gauteng', 'Mpumalanda', 'Limpopo']
variation = 1
samples = 1000
plt.figure()
plt.suptitle('Prevalence under 0.1 migration', fontsize=14)
for i in range(3):
    for j in range(3):
        plt.subplot(3,3,(i*3)+(j+1))
        #plt.plot(range(0,31,5), prev[(i*3)+j])
        plt.hist([np.max((0,random.normal(100*prev[(i*3)+j][-1], variation))) for n in range(samples)])
        plt.title(name[(i*3)+j])
        if j == 0:
            plt.ylabel('Frequency')
        if i == 2:
            plt.xlabel('30-year Prevalence')
        #plt.ylim((0.0, 0.15))
        plt.xlim((0,20))
        
