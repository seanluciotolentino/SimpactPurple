# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 11:14:02 2013

@author: Lucio

A script for running a distributed simulation with communities uniformly
on a unit circle. Probability of forming a relationship between communities
is based on the distance with a minimum distance based on *min_*. 

"""

from mpi4py import MPI
import simpactpurple.distributed.CommunityDistributed as CommunityDistributed
import simpactpurple.GraphsAndData as GraphsAndData
import numpy as np
import numpy.random as random
import sys
import json
import networkx as nx

#print "hello from", MPI.Get_processor_name(),"rank",MPI.COMM_WORLD.Get_rank()
def make_transition_matrix(n, seed, multiplier):
    """
    Creates and returns attenuation, probability, and transition matrix based
	on the number of communities *n*, a *seed*, and probability *multiplier*.
    """
    distance = np.zeros((n,n))
    dist = lambda p1,p2: np.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
        
    #assign a geographic location to each partition
    random.seed(seed)
    x = np.random.rand(1,n)
    y = np.random.rand(1,n)          
    for i in range(int(n)):
        for j in range(int(n)):
            distance[i][j] = dist((x[0][i],y[0][i]),(x[0][j],y[0][j]))
    
    #transform distances                           
    attenuation = np.e**(multiplier*distance)
    probabilities = attenuation / np.transpose(np.sum(attenuation, axis=0))
    transition = np.cumsum(probabilities, axis=0)

    return attenuation, probabilities, transition

def non_diagonal_average(m):
	"""
	Calculate the non-diagonal average for matrix m.
	"""
    n = np.shape(m)[0]
    if np.size(m) == 1:
        return 1
    else:
        return ( np.sum(m) - n) / ( n**2 - n)
		
def inter_community_probability(pm, cn):
	"""
	Calculate the probability of an inter-community relationship from
	the probability matrix *pm* for community number *cn*
	"""
	return np.sum(pm[:,cn]) - pm[cn,cn]
    
#MPI variables
comm = MPI.COMM_WORLD
others = range(comm.Get_size())
others.remove(comm.Get_rank())
s = CommunityDistributed.CommunityDistributed(comm, 0, others)
s.INITIAL_POPULATION = int(sys.argv[1])#*comm.Get_size()  # each community should have about 1k (or however many)
s.NUMBER_OF_YEARS = float(sys.argv[2])

#initialize community locations
if comm.Get_rank() == 0:
    seed = np.random.randint(100000000)
    for other in others:
        comm.send(seed, dest = other)
else:
    seed = comm.recv(source = 0)
new_seed = np.random.randint(100000000)
attenuation, probabilities, transition = set_distance_function(comm.Get_size(), seed, float(sys.argv[3]))
np.random.seed(new_seed)
s.transition_probabilities = probabilities
s.run()

if comm.Get_rank() == 0:
    #post process output
    on_node_relations = len([e for e in s.network.edges() if e[0].partition == 0 and e[1].partition == 0])
    off_node_relations = len([e for e in s.network.edges() if e[0].partition > 0 and e[1].partition > 0])
    one_infected = len([a for a in s.infection_operator.infected_agents if a.partition == 0])
    all_infected = len(s.infection_operator.infected_agents)
    print json.dumps( {"on_node_relationships":on_node_relations,
                       "off_node_relationships":off_node_relations,
                       "inter_node_relationships":len(s.network.edges())-on_node_relations-off_node_relations,
                       "total_relationships":len(s.network.edges()),
                       
                       "one_infected":one_infected,
                       "all_infected":all_infected,
                       
                       "average_attenuation":non_diagonal_average(attenuation),
                       "total_attenuation":np.sum(attenuation) - s.size,
                       "inter_community_probability":inter_community_probability(probabilities, 0)
                        })
