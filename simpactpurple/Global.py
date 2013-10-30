# -*- coding: utf-8 -*-
"""
Created on Thu Oct 17 11:14:39 2013

@author: Lucio
"""

import Agent
import numpy as np
import random

class UpdateReplyStruct:
    
    def __init__(self, Global):
        self.Global = Global
        self.clear()
        
    def clear(self):
        self.agent_deaths = {c:[] for c in self.Global.communities}
        #self.new_agents = {c:[] for c in self.Global.communities}  # not used
        self.new_relationships = {}    
        self.rejected_relationships = {c:[] for c in self.Global.communities}
        self.new_infections = {}
        self.infected_agents = {c:[] for c in self.Global.communities} 

class Global:
    
    def __init__(self, comm, population):
        #global specific 
        self.comm = comm
        self.communities = range(1,comm.Get_size())
        self.number_agents = 0  # needed for replacement
        
        #MODEL PARAMETERS
        self.NUMBER_OF_YEARS = 30

        #MODEL POPULATION
        self.INITIAL_POPULATION = population
        self.AGENT_ATTRIBUTES = {}
        self.born = lambda: -52*random.uniform(self.MIN_AGE, self.MAX_AGE)
        self.gender = lambda: random.randint(0, self.GENDERS - 1)
        self.dnp = lambda: random.randint(1, 3)
        
        #MODEL OPERATORS
        #relationship operator
        self.GENDERS = 2
        self.MIN_AGE = 15
        self.MAX_AGE = 65
        self.BIN_SIZE = 5
        self.MAIN_QUEUE_MAX = 0.1  # proportion of initial population
        
        #infection operator
        self.INFECTIVITY = 0.01
        self.INTIIAL_PREVALENCE = 0.01
        self.SEED_TIME = 0 # in years        
        
        #time operator
        self.TIME = 0
        
    def make_population(self, size, born=None, gender=None, dnp=None):
        """
        Creates *size* agents with age, gender, and desired number of partners
        (DNP) dictated by *born*, *gender*, and *dnp* (functions). If these 
        these are omitted, default distributions will be used.

        After an agent receives a name, age, gender, and DNP, he or she is added
        to the network graph and added to a grid queue.
        """
        AGENT_ATTRIBUTES = {}
        AGENT_ATTRIBUTES["TIME_ADDED"] = self.TIME
        AGENT_ATTRIBUTES["TIME_REMOVED"] = np.Inf
        
        #actually make the agents and send to communities
        for i in range(size):
            #make agent and add some attributes
            a = Agent.Agent(AGENT_ATTRIBUTES.copy())
            a.attributes["NAME"] = self.number_agents
            self.number_agents+=1
            a.born = self.born()
            a.gender = self.gender()
            a.dnp = self.dnp()
            
            #flip coin for initial infected
            if size>1 and random.random() < self.INTIIAL_PREVALENCE:
                #print "agent",a,"initial infected at",self.SEED_TIME*52
                a.time_of_infection = self.SEED_TIME*52
            
            #location
            a.attributes["LOC"] = np.random.rand(1,2)*10
            for c in self.communities_for(a):
                #if size<10:  # only get the updating adds
                #    print "SENDING ",a,"to community",c,"time",self.TIME
                self.comm.send(a, dest = c)
            
    def run(self):       
        #Initialize structure for updates and replies
        UpdateReply = UpdateReplyStruct(self)
        UpdateReply.agent_deaths[1] = [0] * self.INITIAL_POPULATION  # make initial population
        self.send_update(UpdateReply)
        self.receive_replies(UpdateReply)
        self.process_replies(UpdateReply)
        self.perform_migration(UpdateReply)
        self.born = lambda: self.TIME - (52*15.02)  # new born function
    
        #mainloop:
        for t in range(int(self.NUMBER_OF_YEARS*52)):
            #0. Housekeeping
            print "===================",t,"======================"
            self.TIME = t
            random.shuffle(self.communities)  # don't give preferences            
            
            #1. Send "updates" to communities
            self.send_update(UpdateReply)
                
            #2. Wait for "reply" from communities
            self.receive_replies(UpdateReply)
                
            #3. Process replies
            self.process_replies(UpdateReply)
            
            #4. Do migration procedures
            self.perform_migration(UpdateReply)

    def send_update(self, UpdateReply):
        for c in self.communities:
            self.comm.send("update_start", dest = c)
            
        for c in self.communities:
            self.make_population(len(UpdateReply.agent_deaths[c]))
            
        for c in self.communities:
            self.comm.send("start", dest = c)            
            self.comm.send(UpdateReply.rejected_relationships[c], dest = c)
            self.comm.send(UpdateReply.infected_agents[c], dest = c)
            self.comm.send(self.TIME, dest = c)            
            self.comm.send("update_end", dest = c)            
        UpdateReply.clear()
            
    def receive_replies(self, UpdateReply):
        for c in self.communities:
            if self.comm.recv(source = c) != "reply_start":
                raise Exception,"Community "+str(c)+" not replying correctly"

            UpdateReply.agent_deaths[c] = self.comm.recv(source = c)
            UpdateReply.new_relationships[c] = self.comm.recv(source = c)
            UpdateReply.new_infections[c] = self.comm.recv(source = c)
            
            if self.comm.recv(source = c) != "reply_end":
                raise Exception,"Community "+str(c)+" not replying correctly"
            
    def process_replies(self, UpdateReply):
        successful = []            
        for c in self.communities:
            #1. Agent death
            pass  # update calls make population, no calculation needed here
        
            #2. New Relationss
            UpdateReply.rejected_relationships[c] = []
            this_successful = []  # don't check against sucessful from this community
            for r in UpdateReply.new_relationships[c]:
                agent1 = r[0].attributes["NAME"]
                agent2 = r[1].attributes["NAME"]
                if agent1 in successful or agent2 in successful:
                    UpdateReply.rejected_relationships[c].append(r)
                else:
                    this_successful.append(agent1)
                    this_successful.append(agent2)
            successful+=this_successful
            
            #3. New Infections
            for agent in UpdateReply.new_infections[c]:
                agent_communities = self.communities_for(agent)
                #print "agent",agent,"location",agent.attributes["LOC"],"communities",agent_communities, "c", c
                agent_communities.remove(c)
                for a_c in agent_communities:
                    UpdateReply.infected_agents[c].append(agent)
                    
    def perform_migration(self, UpdateReply):
        pass  # not yet implemented

    def communities_for(self, agent):
        """
        An ad-hoc, first pass at community assignment
        """
        x = agent.attributes["LOC"][0][0]
        y = agent.attributes["LOC"][0][1]
        
        communities = []    
        if y < 4:
            communities += [3]
        elif y < 6:
            communities += [1,3]
        else:
            communities += [1]
            
        #shift communities if to the right
        if x > 5:
            communities = [c+1 for c in communities]
        return communities
