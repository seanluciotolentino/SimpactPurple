# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 11:14:02 2013

@author: Lucio

A script which uses MPI (mpi4py) to overlook several community simulations.  This
is the initial test script for proof of concept.

"""

from mpi4py import MPI
import CommunityDistributed
import GraphsAndData

print "hello from", MPI.Get_processor_name()

#MPI variables
comm = MPI.COMM_WORLD
c = CommunityDistributed.CommunityDistributed(comm)
c.run()

GraphsAndData.formed_relations_graph(s,filename='formed_relations'+MPI.Get_processor_name+'.png')
GraphsAndData.sexual_network_graph(s,filename='sexual_network'+MPI.Get_processor_name+'.png')

