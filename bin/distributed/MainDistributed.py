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
import GridQueue
import sys

#print "hello from", MPI.Get_processor_name(),"rank",MPI.COMM_WORLD.Get_rank()

#MPI variables
name = MPI.Get_processor_name()
comm = MPI.COMM_WORLD
rank = comm.Get_rank()

#simulation variables
num_communities = comm.Get_size()/16
primaries = range(0, num_communities)

#split based on rank
if rank in primaries:
    others = range(num_communities)
    others.remove(rank)
    s = CommunityDistributed.CommunityDistributed(comm, 0, others)
    s.INITIAL_POPULATION = int(sys.argv[1])
    s.NUMBER_OF_YEARS = float(sys.argv[2])
    s.run()
    
    #send "done" to all grid queue ranks
    for r in range(rank, comm.Get_size(), num_communities):
        comm.send('done', dest = r)
else:
    master = rank%num_communities
    msg = comm.recv(dest = master)
    while not msg == 'done':
        gq = msg
        pipe = CommunityDistributed.MPIpe(comm, rank)
        GridQueue.listen(gq, pipe)
        msg = comm.recv(dest = master)