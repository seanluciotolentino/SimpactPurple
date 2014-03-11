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
        
        #define primaries and communities:
        self.communities = {1:3, 5:2}
        for primary in self.communities:
            others = range(primary,primary+self.communities[primary])
            for rank in others:
                others.remove(rank)
                self.comm.send((primary, others), dest = rank)
                others.append(rank)
            
        #define migration pattern
        """
              \  to 1   to 2
        from 1  [1->1   1->2]
        from 2  [2->1   2->2]
        
        self.migration = np.matrix([[0.9, 0.1],
                                    [0.2, 0.8]])
        """
        self.migration = {(1,5):0.1, (5,1):0.2}  # (src, dest) -> fraction
            
    def run(self):
        #initially listen for agents
        self.listen_all('initial agents')
            
        #mainloop
        for t in range(int(self.NUMBER_OF_YEARS*52)):
            self.listen_all('community updates')
            
            #calculate and send removals
            moving = {}
            for edge in self.migration:
                source,destination = edge
                moving[source] = [agent for agent in self.agents[source] if random.random() < self.migration[edge]]
                self.comm.send(moving[source], dest = source)
            
            #send additions
            for edge in self.migration:
                source, destination = edge
                self.comm.send(moving[source], dest = destination)
                
            
    def listen_all(self, for_what):
        for primary in self.communities:
            self.listen(for_what, primary)
        
    def listen(self, for_what, from_whom):
        """
        Method for receiving messages from other communities and responding
        accordingly.
        """
        #print "v=== listen for",for_what,"| STARTED ON",self.rank,"|time",self.time,"===v"
        req = self.comm.irecv(dest = from_whom)  # data depends on msg
        while True:
            #continually check that a message was received
            flag, message = req.test()
            if not flag: continue
            msg, agent_name = message
    	    #print "  > listening on",self.rank,"| msg:",msg,"data:",data
            if msg == 'done':
                break
            req = self.comm.irecv(dest = from_whom)  # listen for next message

            #parse message and act            
            if msg == 'add':
                self.agents[from_whom].append(agent_name)
            elif msg == 'remove':
                self.agents[from_whom].remove(agent_name)

                    
        #print "^=== listen for",for_what,"| END on",self.rank,"|time",self.time,"======^" 
	#print