# -*- coding: utf-8 -*-
"""
Created on Tue Mar 11 11:11:03 2014

@author: Lucio
"""

import numpy as np
import random

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
        
        #Migration operator parameters
        self.migration = {1:{'num_communities':1,'proportion':0.6,'time_here':30},
                          2:{'num_communities':2,'proportion':0,'time_here':4},
                          4:{'num_communities':2,'proportion':0,'time_here':12}}
        self.time_home = 2
        self.max_weeks = (65*52)+1  # for efficiently knowing the end of an agents life
        self.sexual_behavior_association = 0.0  # percent chance that migrant has increased sexual behavior
        self.sexual_behavior_amount = 1.5 # set migrant DNP to this value...?
        
    def start(self):
        self.removals = {t:{1:[],2:[],4:[]} for t in range(1+int(self.NUMBER_OF_YEARS*52))}
        self.additions = {t:{1:[],2:[],4:[]} for t in range(1+int(self.NUMBER_OF_YEARS*52))}
        
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
        self.start()        
        
        #send roles:
        self.send_roles()
    
        #initially listen for agents
        self.listen_all('initial agents')
        
        #mainloop
        for t in range(int(self.NUMBER_OF_YEARS*52)):
            #basic simulation
            if t%100 == 0:
                print "**MO time",t
            self.time = t
            self.listen_all('community updates')

            #perform migration steps
            for source in self.migration:
                #print "  removed from",source,[a.name for a in self.removals[t][source]]
                self.comm.send(self.removals[t][source], dest = source)
                for a in self.removals[t][source]:  # bookkeeping
                    self.agents[source].remove(a)
            for destination in self.migration:
                #print "  added to",destination,[a.name for a in self.additions[t][destination]]
                self.comm.send(self.additions[t][destination], dest = destination)
                for a in self.additions[t][destination]:  # bookkeeping
                    self.agents[destination].append(a)
            #print "**"
                                
    def add(self, agent, home):
        #print "     adding agent",agent,"from",home,
        if agent.sex == 0 and random.random() < self.migration[home]['proportion']:
            #assign migration place
            away = random.choice([2,4])  # needs generalization
            agent.migrant = away
            time_away = self.migration[away]['time_here']
            time_home = self.migration[home]['time_here']
                        
            #create travel schedule
            start_time = self.time + random.randint(0, time_away)
            end_time = int(np.min(((self.NUMBER_OF_YEARS*52)-1, self.max_weeks+agent.born)))
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
                
            #set associated increase in sexual behavior
            if random.random() < self.sexual_behavior_association:
                agent.dnp = max((self.sexual_behavior_amount,agent.dnp))
        else:
            #print "--> no migration"
            agent.migrant = 1
            
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
            elif msg == 'infections':
                agents = agent
                for agent_name in agents:
                    self.all_agents[agent_name].time_of_infection = self.time
            else:
                raise ValueError,'Unknown message received:'+msg
            msg, agent = self.comm.recv(source = from_whom)  # listen for next message
        
        #print "^=== listen for",for_what,"| END on",self.rank,"|time",self.time,"======^" 
        #print
