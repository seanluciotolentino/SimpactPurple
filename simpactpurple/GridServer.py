# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 14:50:44 2013

@author: Lucio

"""

import multiprocessing
import GridQueue
import numpy as np

class GridServer:

    """
    The Grid Server acts as the intermediary between the MPI and the grid queues
    which it organizes.  
    """
    
    def __init__(self, comm):
        self.comm = comm
        self.master = None  # set by MainAlt
        self.pipes = {}
        self.indexes = {}
    
    def add_grid_queue(self, gq):
        """
        Grid Queues are added in the MainAlt script. The master node (to
        which this grid server is a servant) sends grid queues and
        this server initiates a process and pipe to forward messages to.
        """
        pipe_top, pipe_bottom = multiprocessing.Pipe()
        p = multiprocessing.Process(target=GridQueue.listen,args=(gq, pipe_bottom))
        p.start()
        self.pipes[gq.my_index] = pipe_top  # index --> pipe
        self.indexes[pipe_top] = gq.my_index  # pipe --> index
        
        
    def run(self):
        #print "in run"
        req = self.comm.irecv(dest = self.master)  # 'dest' means 'source'... bug in mpi4py
        end_req = self.comm.irecv(dest = 0)
        end, end_message = end_req.test()
        while True:
            # 1. check for messages from comm
            flag, message = req.test()
            if flag:
                #print "Comm: ", message,"<<<",self.master
                pipe, msg = message  # unpack further
                self.pipes[pipe].send(msg)            
                req = self.comm.irecv(dest = self.master)  #update request
                continue
                
            # 2. recheck for end message from global -- this may really slow me down...            
            end, end_message = end_req.test()
            if end:
                break
            
            # 3. check for messages from pipes
            try:
                for pipe in self.pipes.values():
                    if pipe.poll():
                        msg = pipe.recv()
                        #print "Pipe: ",(self.indexes[pipe],msg), ">>>", self.master
                        self.comm.send((self.indexes[pipe],msg), dest = self.master)
            except IOError:
                #This happens when the pipes are closed during termination
                #print "IOError"
                pass
                

                    
                
