# -*- coding: utf-8 -*-
"""
Created on Tue Mar 11 11:11:03 2014

@author: Lucio
"""

import numpy as np
import numpy.random as random

class MigrationOperator:
    
    def __init__(self, comm):
        #model parameters
        self.NUMBER_OF_YEARS = 30
        
        #data structures
        self.comm = comm
        self.agents = {}  # rank -> [list of agents on rank]
        self.all_agents = {}  # agent_name -> agent
        self.time = 0
        self.rank = self.comm.Get_rank()  # should be zero
        self.removals = {t:{1:[],4:[]} for t in range(1+int(self.NUMBER_OF_YEARS*52))}
        self.additions = {t:{1:[],4:[]} for t in range(1+int(self.NUMBER_OF_YEARS*52))}
        
        #Migration operator parameters
        self.migration = {1:{'num_communities':3,'proportion':0.2,'time_away':25},
                          4:{'num_communities':3,'proportion':0.1,'time_away':5}}
        self.time_home = 2
        self.max_weeks = (65*52)+1  # for efficiently knowing the end of an agents life
        
    def send_roles(self):
        """
        Define primary and secondary communities. Send roles to nodes
        on other ranks.
        """
        for primary in self.migration:
            num_communities = self.migration[primary]['num_communities']
            others = range(primary,primary+num_communities)
            self.agents[primary] = []
            for rank in range(primary,primary+num_communities):
                others.remove(rank)
                self.comm.send((primary, others), dest = rank)
                others.append(rank)
                #print "Migration Operator sent:",primary,others,"to",rank            
        
    def run(self):
        #send roles:
        self.send_roles()
    
        #initially listen for agents
        self.listen_all('initial agents')
        
        #mainloop
        for t in range(int(self.NUMBER_OF_YEARS*52)):
            #basic simulation
            #print "**MO time",t
            self.time = t
            self.listen_all('community updates')

            #perform migration steps
            for source in self.migration:
                #print "  removed from",source,[a.name for a in self.removals[t][source]]
                self.comm.send(self.removals[t][source], dest = source)
            for destination in self.migration:
                #print "  added to",destination,[a.name for a in self.additions[t][destination]]
                self.comm.send(self.additions[t][destination], dest = destination)
            #print 
            #bookkeeping
            for source, destination in [(1,4),(4,1)]:  # generalize...?
                while self.removals[t][source]:
                    a = self.removals[t][source].pop()
                    #print "  updating: agent",a,"moved",source,"->",destination
                    self.agents[source].remove(a)
                    self.agents[destination].append(a)
            #print "**"
                                
    def add(self, agent, home):
        if random.random() < self.migration[home]['proportion']:
            agent.migrant = True
            away = [1,4][home==1]  # needs generalization
            time_away = self.migration[home]['time_away']
            time_home = self.time_home
            
            #create travel schedule
            start_time = self.time + random.randint(time_away)
            end_time = int(np.min((self.NUMBER_OF_YEARS*52, self.max_weeks+agent.born)))
            #schedule travel away
            for time in range(start_time, end_time, time_away+time_home):
                self.removals[time][home].append(agent)
                self.additions[time][away].append(agent)
                agent.attributes["MIGRATION"].append((self.time, home, away))
            #schedule return home
            for time in range(start_time+time_away, end_time, time_away+time_home):
                self.removals[time][away].append(agent)
                self.additions[time][home].append(agent)
                agent.attributes["MIGRATION"].append((self.time, away, home))
        else:
            agent.migrant = False
            
    def listen_all(self, for_what):
        for primary in self.migration:
            self.listen(for_what, primary)
        
    def listen(self, for_what, from_whom):
        """
        Method for receiving messages from other communities and responding
        accordingly.
        """
        #print "v=== listen for",for_what,"| FROM",from_whom,"ON",self.rank,"|time",self.time,"===v"
        msg, agent = self.comm.recv(source = from_whom)  # data depends on msg
        while True:
            #print "  > listening on",self.rank,"| msg:",msg,"agent:",agent
            if msg == 'done':
                break
            
            #parse message and act            
            if msg == 'add':
                self.agents[from_whom].append(agent)
                self.all_agents[agent.name] = agent
                self.add(agent, from_whom)
            elif msg == 'remove':
                agent = self.all_agents[agent]  # convert name to known agent
                agent.attributes["MIGRATION"].append((self.time, from_whom, 0))
                self.agents[from_whom].remove(agent)                
            msg, agent = self.comm.recv(source = from_whom)  # listen for next message
        
        #print "^=== listen for",for_what,"| END on",self.rank,"|time",self.time,"======^" 
        #print
