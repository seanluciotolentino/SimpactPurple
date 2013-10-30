# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 11:13:09 2013

@author: Lucio

A Community object (inherits from Community) that has the additional ability to
communicate via MPI with a MainSimulator.

"""
import Community

class CommunityMPI(Community.Community):
    
    def __init__(self, comm, Global):
        Community.Community.__init__(self)
        self.comm = comm
        self.Global = Global
        self.num_relationships = 0  # for indexing during updates
        
        #MODEL PARAMETERS
        self.NUMBER_OF_YEARS = Global.NUMBER_OF_YEARS

        #MODEL POPULATION
        self.INITIAL_POPULATION = 0  # Global will add
        self.AGENT_ATTRIBUTES = {}
        
        #MODEL OPERATORS
        #relationship operator
        self.GENDERS = Global.GENDERS
        self.MIN_AGE = Global.MIN_AGE
        self.MAX_AGE = Global.MAX_AGE
        self.BIN_SIZE = Global.BIN_SIZE
        self.MAIN_QUEUE_MAX = Global.MAIN_QUEUE_MAX  # proportion of initial population

        #infection operator
        self.INFECTIVITY = Global.INFECTIVITY
        self.INTIIAL_PREVALENCE = 0  # global does initial seeding
        self.SEED_TIME = 0  
                
    def start(self):
        """
        In addition to setting up simulation structures, the community needs
        to listen for agent adds from comm.
        """
        #initialize data structures
        Community.Community.start(self)
            
    def run(self):
        self.start()    
        self.time = 0
        while True:
            #print rank,"in loop, time is",time
            self.update()
            self.step()
            self.reply()
            if self.time >= (int(self.NUMBER_OF_YEARS*52)-1):  # need a more sophisticated breaking system methinks
                break
            
            #print rank,"time updated to",time
        self.cleanup()
        
    def step(self):
        print "====Community",self.comm.Get_rank(),"time",self.time,"===="
        self.debug()
        self.assertions()
        Community.Community.step(self)
        
    def add(self,agent):
        #if self.time > 1:
        #    print "    adding",agent, "age",self.age(agent)
        Community.Community.add(self,agent)
        
    def update(self):
        msg = self.comm.recv(source = 0)
        if msg != "update_start":
                raise Exception, "Didn't receive update_start from Global. Received: " + str(msg)
                
        #print self.comm.Get_rank(),"updating..."
        #1. New agents (from deaths)
        agent = self.comm.recv(source = 0)
        #print "  1. adding agents..."
        while agent != 'start':
            self.add(agent)
            agent= self.comm.recv(source = 0)
        
        #2. Rejected Relationships
        rejected_relationships = self.comm.recv(source = 0)  # list of bad rela
        #print "  2. rejected relations:",[(a1.attributes["NAME"], a2.attributes["NAME"]) for a1,a2,start,stop in rejected_relationships]
        for r in rejected_relationships:
            a1, a2, start, stop = r
            agent1 = self.agents[a1.attributes["NAME"]]
            agent2 = self.agents[a2.attributes["NAME"]]
            self.relationship_operator.dissolve_relationship(agent1, agent2)
            self.relationships.remove((agent1,agent2,start,stop))
            
            #print "  ",a1.attributes["NAME"],a2.attributes["NAME"],"rejected",\
            #    "| new relationships:",[(r[0].attributes["NAME"],r[1].attributes["NAME"]) for r in self.relationships]
        self.num_relationships = len(self.relationships)
        
        #3. New infections
        new_infections = self.comm.recv(source = 0)  # list of bad rela
        #print "  3. new_infections:",[a.attributes["NAME"] for a in new_infections]
        for a in new_infections:
            agent = self.agents[a.attributes["NAME"]]
            agent.time_of_infection=self.time
            
        #4. Get new time
        self.time = int(self.comm.recv(source = 0))
        
        msg = self.comm.recv(source = 0)
        if msg != "update_end":
                raise Exception, "Didn't receive update_end from Global. Received: " + str(msg)
        
    def reply(self):
        self.comm.send("reply_start", dest = 0)
        #print self.comm.Get_rank(),"reply... (time =",self.time,")"
        
        #1. Send agent death
        agent_deaths = [a for a in self.agents.values() if a.attributes["TIME_REMOVED"]==self.time]  # 1st pass solution
        #print "  1. agent deaths:",[a.attributes["NAME"] for a in agent_deaths]
        self.comm.send(agent_deaths, dest = 0)
        
        #2. Send new relationships
        new_relationships = self.relationships[self.num_relationships:]
        #print "  2. new_relationships:",[(a1.attributes["NAME"], a2.attributes["NAME"]) for a1,a2,start,stop in new_relationships]
        self.comm.send(new_relationships, dest = 0)
        
        #3. Send agent deaths
        new_infections = [a for a in self.agents.values() if a.time_of_infection==self.time]  # 1st pass solution
        #print "  3. new_infections:",[a.attributes["NAME"] for a in new_infections]
        self.comm.send(new_infections, dest = 0)
        
        self.comm.send("reply_end", dest = 0)
        
    def make_population(self,size, born=None, gender=None, dnp=None):
        """
        Overwrite Community *make_population* method so nothings happens at
		initialization.  This is desirable because the Global object is making
		the population. If size == 1 then the time operator is trying to
		replace an agent. 
        """
        #listen for new agents
        pass
        

    
        
        
