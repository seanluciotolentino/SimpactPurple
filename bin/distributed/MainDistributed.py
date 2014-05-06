# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 11:14:02 2013

@author: Lucio

A script which uses MPI (mpi4py) to overlook several community simulations. The
script detects the number of nodes assigned and distributed the work among a 
primary node and worker nodes.

"""

from mpi4py import MPI
import simpactpurple.distributed.CommunityDistributed as CommunityDistributed
import simpactpurple.GraphsAndData as GraphsAndData
import numpy as np
import numpy.random as random
import sys

#print "hello from", MPI.Get_processor_name(),"rank",MPI.COMM_WORLD.Get_rank()

#MPI variables
name = MPI.Get_processor_name()
comm = MPI.COMM_WORLD
others = range(comm.Get_size())
others.remove(comm.Get_rank())
c = CommunityDistributed.CommunityDistributed(comm, 0, others)
c.INITIAL_POPULATION = int(sys.argv[1])
c.NUMBER_OF_YEARS = float(sys.argv[2])
c.run()

if comm.Get_rank() == 0:
    #GraphsAndData.formed_relations_graph(c,filename='formed_relations_distributed.png')
    #GraphsAndData.sexual_network_graph(c,filename='sexual_network_distributed.png')
    #GraphsAndData.demographics_graph(c,filename='demographics_distributed.png')
    #GraphsAndData.prevalence_graph(c, filename='prevalence_distributed.png')
    #GraphsAndData.age_mixing_graph(c, filename='agemixing_distributed.png')
	#GraphsAndData.relationship_durations(c, filename='durations_distributed.png')
	#GraphsAndData.gap_lengths(c, filename='gaplengths_distributed.png')
    print len(c.network.edges())
