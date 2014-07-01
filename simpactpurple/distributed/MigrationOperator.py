# -*- coding: utf-8 -*-
"""
Created on Tue Mar 11 11:11:03 2014

@author: Lucio
"""

import numpy as np
import random

class MigrationOperator:
    
    def __init__(self, comm, primaries, proportion_migrate, distance, timing):
        #model parameters
        self.NUMBER_OF_YEARS = 30
        
        #data structures
        self.comm = comm
        self.rank_primaries = primaries
        self.primaries = list(set(primaries[1:]))  # grab unique primaries
        self.proportion_migrate = proportion_migrate
        self.distance = distance
        self.timing = timing
        self.rank = self.comm.Get_rank()  # should be zero

    def start(self):
        """
        Initialize necessary data structures and do checks for
        well-formed inputs.
        """
        #basic structures
        self.agents = {r:[] for r in self.primaries}  # rank -> [list of agents on rank]
        self.all_agents = {}  # agent_name -> agent
        self.time = 0
        self.removals = {t:{p:[] for p in range(len(self.primaries))} for t in range(1+int(self.NUMBER_OF_YEARS*52))}
        self.additions = {t:{p:[] for p in range(len(self.primaries))} for t in range(1+int(self.NUMBER_OF_YEARS*52))}

        #check that primaries are well formed
        for p in self.rank_primaries:
            if self.rank_primaries[p] != p:
                raise ValueError, "Malformed primary list" 
                
        #check that rank is 0
        if self.rank != 0:
            raise ValueError, "Migration Operator not set as rank 0"
            
        #build migration transition matrix
        if len(self.primaries) != len(self.distance[0]):
            raise ValueError, "Number of primaries doesn't match distance matrix. Primaries="\
                +str(len(set(self.primaries))-1)+" Distance columns="+str(len(self.distance[0]))
        self.distance = np.matrix(self.distance)
        probabilities = self.distance / np.transpose(np.sum(self.distance, axis=1))
        self.transition = np.cumsum(probabilities, axis=0)
        
    def run(self):
        self.start()
    
        #initially listen for agents
        self.listen_all('initial agents')
        
        #mainloop
        for t in range(int(self.NUMBER_OF_YEARS*52)):
            #basic simulation
            #if t%100 == 0:
            print "**MO time",t
            self.time = t
            self.listen_all('community updates')

            #perform migration steps
            for source in range(len(self.primaries)):
                print "  removed from",self.primaries[source],[a.name for a in self.removals[t][source]]
                self.comm.send(self.removals[t][source], dest = self.primaries[source])
                for a in self.removals[t][source]:  # bookkeeping
                    self.agents[self.primaries[source]].remove(a)
                    
            for destination in range(len(self.primaries)):
                print "  added to",self.primaries[destination],[a.name for a in self.additions[t][destination]]
                self.comm.send(self.additions[t][destination], dest = self.primaries[destination])
                for a in self.additions[t][destination]:  # bookkeeping
                    self.agents[self.primaries[destination]].append(a)
                                
    def add(self, agent, rank):
        print "     adding agent",agent,"from",rank,
        home = self.primaries.index(self.rank_primaries[rank]) # respective column in the transition matrix for rank
        if agent.sex == 0 and random.random() < self.proportion_migrate[rank]:
            #find home and away
            away = [int(v) for v in np.random.random() < self.transition[:,home]].index(1)
            agent.migrant = self.primaries[away]
            time_away = self.timing[away][home]
            time_home = self.timing[home][away]
            print " --> migrates to", away
                        
            #create travel schedule
            max_weeks = (65*52)+1
            start_time = self.time + random.randint(0, time_away)
            end_time = int(np.min(((self.NUMBER_OF_YEARS*52)-1, max_weeks+agent.born)))
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
            #if random.random() < self.sexual_behavior_association:
            #    agent.dnp = max((self.sexual_behavior_amount,agent.dnp))
        else:
            print "--> no migration"
            agent.migrant = home
            
    def listen_all(self, for_what):
        """
        Listen to primaries in turn.
        """
        for primary in self.primaries:
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
