# -*- coding: utf-8 -*-
"""
Created on Tue Mar 11 11:11:03 2014

@author: Lucio

"""

import numpy as np
import random

def calc_gravity(pop, dist, pop_power, dist_power):
    """
    One example of a gravity function based on population 
    and distance between communities.
    """
    num = np.power(np.transpose(pop)*pop, pop_power)
    den = np.power(dist,dist_power)
     
    gravity = num/den
    probabilities = gravity / np.sum(gravity, axis=0)
    transition = np.cumsum(probabilities, axis=0)
     
    return gravity, probabilities, transition

class MigrationOperator:
    """
    The class that oversees migration operation.
    """
    def __init__(self, comm, primaries, gravity, timing):
        #model parameters
        self.NUMBER_OF_YEARS = 30
        
        #distributed parameters
        self.comm = comm
        self.primaries = primaries
        self.gravity = gravity
        self.timing = timing
        self.rank = self.comm.Get_rank()  # should be zero
        self.non_migrating_sex = 1
        
        #neon constants
        self.slots_per_node = 16  # number on neon
        self.max_age = 40  # based on number of slots available

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
        if self.comm.Get_size()/self.slots_per_node != self.primaries[-1]:
            raise ValueError, "Not enough slots/MPIprocesses for {0} communities".format(self.primaries[-1])
            
        #check that number of primary communities is equal to gravity
        if len(self.primaries) != len(self.gravity):
            raise ValueError, "Number of primaries doesn't match distance matrix. Primaries="\
                +str(len(self.primaries))+" gravity length="+str(len(self.gravity[0]))
                
        #transform gravity matrix into probability and transition matrix
        self.gravity = np.matrix(self.gravity)
        probabilities = self.gravity / np.sum(self.gravity, axis=0)
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
            #print "  removals:",[len(self.removals[t][s]) for s in range(3)]
            #print "  additions:",[len(self.additions[t][d]) for d in range(3)]
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
        if agent.sex == self.non_migrating_sex:
            agent.migrant = home
        else: # male agents
            #choose a migration destination from transition matrix
            away = [int(v) for v in np.random.random() < self.transition[:,home]].index(1)
            if home == away:
                return

            #create travel schedule for the agents migration
            agent.migrant = self.primaries[away]
            time_away = int(max(self.timing[home,home],1.0))
            time_home = int(max(self.timing[away,home],1.0))
            max_weeks = self.max_age*52
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
            if last_away >= last_home:
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
