# -*- coding: utf-8 -*-
"""
Created on Tue Mar 11 11:11:03 2014

@author: Lucio

"""

import numpy as np
import random

class MigrationOperator:
    
    def __init__(self, comm, primaries, gravity, timing):
        #model parameters
        self.NUMBER_OF_YEARS = 30
        
        #data structures
        self.comm = comm
        self.primaries = primaries
        self.gravity = gravity
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
   
        #check that rank is 0
        if self.rank != 0:
            raise ValueError, "Migration Operator not set as rank 0"
            
        #check that enough slots were allocated
        if self.comm.Get_size()/16 != self.primaries[-1]:
            raise ValueError, "Not enough slots/MPIprocesses for {0} communities".format(self.primaries[-1])
            
        #build migration transition matrix
        if len(self.primaries) != len(self.gravity):
            raise ValueError, "Number of primaries doesn't match distance matrix. Primaries="\
                +str(len(set(self.primaries))-1)+" Distance columns="+str(len(self.gravity[0]))
        self.gravity = np.matrix(self.gravity)
        probabilities = self.gravity / np.transpose(np.sum(self.gravity, axis=1))
        self.transition = np.cumsum(probabilities, axis=0)
        
    def run(self):
        self.start()
    
        #initially listen for agents
        self.listen_all('initial agents')
        
        #mainloop
        for t in range(int(self.NUMBER_OF_YEARS*52)):
            #basic simulation
            #if t%52 == 0:
            #print "**MO time",t
            self.time = t
            self.listen_all('community updates')

            #perform migration steps
            for source in range(len(self.primaries)):
                #print "  removed from",self.primaries[source],[a.name for a in self.removals[t][source]]
                self.comm.send(self.removals[t][source], dest = self.primaries[source])
                for a in self.removals[t][source]:  # bookkeeping
                    self.agents[self.primaries[source]].remove(a)

            for destination in range(len(self.primaries)):
                #print "  added to",self.primaries[destination],[a.name for a in self.additions[t][destination]]
                self.comm.send(self.additions[t][destination], dest = self.primaries[destination])
                for a in self.additions[t][destination]:  # bookkeeping
                    self.agents[self.primaries[destination]].append(a)
                                
    def add(self, agent, home):
        agent.migrant = home
        if agent.sex:
            agent.migrant = home
        else: #agent.sex == 0:
            away = [int(v) for v in np.random.random() < self.transition[:,home]].index(1)
            
            if home == away:
                return
            
            agent.migrant = self.primaries[away]
            time_away = int(max(self.timing[away,home],1.0))
            time_home = int(max(self.timing[home,away],1.0))
            #print "agent",agent.name,"added. home",home,"away",away,"time home", time_home, "time_away", time_away
                        
            #create travel schedule
            max_weeks = 40*52  # *was* +1
            start_time = self.time + random.randint(0, time_away)
            end_time = int(np.min(((self.NUMBER_OF_YEARS*52)-1, max_weeks+agent.born)))
            if end_time <= start_time:
                return
                
            #schedule travel away
            for time in range(start_time, end_time, time_away+time_home):
                self.removals[time][home].append(agent)
                self.additions[time][away].append(agent)
                agent.attributes["MIGRATION"].append((self.time, home, away))
            last_away = time
            
            #schedule return home
            for time in range(start_time+time_away, end_time, time_away+time_home):
                self.removals[time][away].append(agent)
                self.additions[time][home].append(agent)
                agent.attributes["MIGRATION"].append((self.time, away, home))
            last_home = time
            
            #send home at end of simulation for counting purposes
            if last_away > last_home:
                self.removals[end_time][away].append(agent)
                self.additions[end_time][home].append(agent)
            
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
        while msg != 'done':
            #print "  > listening on",self.rank,"| msg:",msg,"agent:",agent
            
            #parse message and act            
            if msg == 'add':
                self.agents[from_whom].append(agent)
                self.all_agents[agent.name] = agent
                self.add(agent, self.primaries.index(from_whom))
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
