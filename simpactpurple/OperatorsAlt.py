"""
Module for operators used in simulation in which communities are paritioned
based on location.
"""

import Queue
import numpy.random as random
import numpy as np
import GridQueue
import multiprocessing
import PriorityQueue
import Operators
import sys

class MajorPipe:
    """
    An object which is the liason between minor pipes and the grid queues to
    which they are supposed to connect. Object uses MPI to communicate with
    other nodes.
    """
    def __init__(self, comm):
        self.rank = {}  # rank[pipe] --> rank where grid queue is
        self.backlog = {}  # backlog[pipe] --> msgs that have been recieved for pipe
        self.comm = comm
    
    def connect(self, pipe, rank):
        self.rank[pipe] = rank
        self.backlog[pipe] = ""  # EMPTY STRING MEANS NO MESSAGE
        
    def send(self, pipe, msg):
        #print "MAJOR PIPE: sending",msg,"for",pipe,"rank",self.rank[pipe]
        self.comm.send((pipe, msg), dest = self.rank[pipe])
        
    def recv(self, pipe):
        #print "MAJOR PIPE: receiving for",pipe,"rank",self.rank[pipe]
        while self.backlog[pipe] is "":
            msg = self.comm.recv(source = self.rank[pipe])
            self.backlog[msg[0]] = msg[1]
        reply = self.backlog[pipe]
        self.backlog[pipe] = ""
        #print "    reply --> ", reply
        return reply

class MinorPipe:
    """
    An object which mimics the multiprocessing pipe, but talks with a major 
    pipe which communicates with Grid Queues on other nodes via MPI.
    """
    def __init__(self, gq, major_pipe):
        self.major_pipe = major_pipe
        self.major_pipe.connect(gq.my_index, gq.rank)
        self.index = gq.my_index
        
    def send(self, msg):
        self.major_pipe.send(self.index, msg)
        
    def recv(self):
        return self.major_pipe.recv(self.index)

class RelationshipOperatorAlt(Operators.RelationshipOperator):
    """
    Controls the formation and dissolution of relationships between agents. At
    initialization, the relationship operator creates the grid queues it will
    need to hold agent, and starts their functioning in seperate processes. Each
    time step, the relationship operator does three things:

       1. Dissolve relationships that have exceeded their duration
       2. Recruit from the grid queues into the main queue
       3. Iterate through main queue, attempting to match each suitor   `
          at the top of the queue.    
    """

    def __init__(self, master):
        self.master = master
        self.main_queue = PriorityQueue.PriorityQueue()
        self.grid_queues = []
        
        #make Grid Queues:
        hazard = self.master.hazard
        for age in range(self.master.MIN_AGE, self.master.MAX_AGE, self.master.BIN_SIZE):
            bottom = age
            top = age + self.master.BIN_SIZE
            for servant in self.master.servants:  # make an identical gq for each servant
                for sex in range(self.master.SEXES):
                    gq = GridQueue.GridQueue(top, bottom, sex, len(self.grid_queues))#, hazard)
                    gq.rank = servant
                    self.grid_queues.append(gq)              
                
        master.NUMBER_OF_GRID_QUEUES = len(self.grid_queues)

        #start the GridQueues
        this_rank = self.master.comm.Get_rank()
        self.pipes = {}
        major_pipe = MajorPipe(self.master.comm)
        for gq in self.grid_queues:
            if gq.rank == this_rank:  # i.e. is on this node
                pipe_top, pipe_bottom = multiprocessing.Pipe()
                p = multiprocessing.Process(target=GridQueue.listen,args=(gq, pipe_bottom))
                p.start()
            else:
                pipe_top = MinorPipe(gq, major_pipe)
                self.master.comm.send(gq, dest = gq.rank)  # start process on other node
            self.pipes[gq.my_index] = pipe_top
        
        #start Grid Servers
        for servant in self.master.servants:
            if servant == this_rank:
                continue
            self.master.comm.send("run", dest = servant)
    
    def update_grid_queue_for(self, agent):
        """
        Find the appropriate grid queue for agent. Called by 
           1. Time Operator - when agent graduates to the next grid queue
           1.5 Time Operator - when relationship with removed is dissolved
           2. Relationship Operator - a relationship is dissolved
           3. Community - in make_population in the mainloop
           
        Alternative implementation also necessitates grid queue selection based
        on location.
        """
        grid_queues = [gq for gq in self.grid_queues if gq.accepts(agent)]  # accepting grid queues
        possible_indices = range(0,2*len(self.master.servants),2)  # possible indexes into above list
        loc_index = int(np.floor(agent.attributes["LOC"][0][0]*len(self.master.servants)))  # actual index based on location
        grid_queue = grid_queues[possible_indices[loc_index]  + int(agent.sex)]  # actual index based on loc and sex
        
        agent.grid_queue = grid_queue.my_index
        self.pipes[agent.grid_queue].send("add")
        self.pipes[agent.grid_queue].send(agent)
