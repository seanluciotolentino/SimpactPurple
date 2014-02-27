# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 11:14:02 2013

@author: Lucio

A script which uses MPI (mpi4py) to overlook several community simulations.  This
is the initial test script for proof of concept.

"""

from mpi4py import MPI
import CommunityDistributed


#MPI variables
comm = MPI.COMM_WORLD
c = CommunityDistributed.Community(comm)
c.run()
