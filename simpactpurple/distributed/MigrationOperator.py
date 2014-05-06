# -*- coding: utf-8 -*-
"""
Created on Tue Mar 11 11:11:03 2014

@author: Lucio
"""

import numpy as np
import numpy.random as random

class MigrationOperator:
    
    def __init__(self, comm):
        self.comm = comm
        self.agents = {}  # rank -> [list of agents on rank]
        self.all_agents = {}  # agent_name -> agent
        self.time = 0
        self.rank = self.comm.Get_rank()    

        #define primaries and communities:
        self.communities = {1:3, 4:2}  # {primary:number_}
        for primary in self.communities:
            others = range(primary,primary+self.communities[primary])
            self.agents[primary] = []
            for rank in range(primary,primary+self.communities[primary]):
                others.remove(rank)
                self.comm.send((primary, others), dest = rank)
                others.append(rank)
                print "Migration Operator sent:",primary,others,"to",rank            
       
       #define migration pattern
        """
              \  to 1   to 2
        from 1  [1->1   1->2]
        from 2  [2->1   2->2]
        
        self.migration = np.matrix([[0.9, 0.1],
                                    [0.2, 0.8]])
        """
        self.migration = {(1,4):0.1, (4,1):0.2}  # (src, dest) -> fraction
        #self.migration = {(1,4):0.0, (4,1):0.0}  # try it with no migration first
        
    def run(self):
        #initially listen for agents
        self.listen_all('initial agents')
            
        #mainloop
        for t in range(int(self.NUMBER_OF_YEARS*52)):
            self.time = t
            self.listen_all('community updates')
            moving = {}
            
            #calculate and send removals
            for edge in self.migration:
                source,destination = edge
                moving[edge] = [agent for agent in self.agents[source] if random.random() < self.migration[edge]]
                for agent in moving[edge]:
                    agent.attributes["MIGRATION"].append((self.time, source, destination))
                self.comm.send(moving[edge], dest = source)
            
            #send additions
            for edge in self.migration:
                source, destination = edge
                self.comm.send(moving[edge], dest = destination)
                
            #update agent data structures
            for edge in self.migration:
                source, destination = edge
                while moving[edge]:
                    a = moving[edge].pop()
                    self.agents[source].remove(a)
                    self.agents[destination].append(a)
            
    def listen_all(self, for_what):
        for primary in self.communities:
            self.listen(for_what, primary)
        
    def listen(self, for_what, from_whom):
        """
        Method for receiving messages from other communities and responding
        accordingly.
        """
        #print "v=== listen for",for_what,"| FROM",from_whom,"ON",self.rank,"|time",self.time,"===v"
        msg, agent = self.comm.recv(dest = from_whom)  # data depends on msg
        while True:
            #print "  > listening on",self.rank,"| msg:",msg,"agent:",agent
            if msg == 'done':
                break
            
            #parse message and act            
            if msg == 'add':
                self.agents[from_whom].append(agent)
                self.all_agents[agent.name] = agent
            elif msg == 'remove':
                agent = self.all_agents[agent]  # convert name to known agent
                agent.attributes["MIGRATION"].append((self.time, from_whom, 0))
                self.agents[from_whom].remove(agent)
            msg, agent = self.comm.recv(dest = from_whom)  # listen for next message
        
        #print "^=== listen for",for_what,"| END on",self.rank,"|time",self.time,"======^" 
        #print
