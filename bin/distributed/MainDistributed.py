# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 11:14:02 2013

@author: Lucio

A script which uses MPI (mpi4py) to overlook several community simulations. The
script detects the number of nodes assigned and distributes the work among a 
primary node and worker nodes.

"""

from mpi4py import MPI
import simpactpurple.distributed.CommunityDistributed as CommunityDistributed
import simpactpurple.GraphsAndData as gad
import sys

#MPI variables
name = MPI.Get_processor_name()
comm = MPI.COMM_WORLD
rank = comm.Get_rank()

#simulation variables
num_communities = comm.Get_size()/16
communities = range(0, num_communities)

#split based on rank
if rank in communities:
    others = range(num_communities)
    others.remove(rank)
    s = CommunityDistributed.CommunityDistributed(comm, 0, others)
    s.INITIAL_POPULATION = int(sys.argv[1])
    s.NUMBER_OF_YEARS = float(sys.argv[2])
    s.run()
        
    #print out stuff
    gad.prevalence_graph(s, filename='prevalence{0}.png'.format(rank))
    gad.demographics_graph(s, box_size=5, filename='demographics_graph{0}.png'.format(rank))
    gad.formed_relations_graph(s, filename='formed_relations_graph{0}.png'.format(rank))
else:
    master = rank%num_communities
    CommunityDistributed.ServeQueue(master, comm)