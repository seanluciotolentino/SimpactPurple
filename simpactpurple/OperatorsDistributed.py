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


class RelationshipOperator(Operators.RelationshipOperator):
    """
    A proof-of-concept implementation of relationship operator. More
    work is necessary in order to generalize this model.
    """
    def step(self):
        """
        Take a single time step in the simulation. 
        """
	#0. Dissolve relationships
        if self.master.primary:
            # sends agents back to right grid queues
            self.update()
            self.master.comm.send(('done',None), dest = self.master.other)
        else:
            # recv agents and add to right grid queue
            self.master.listen()
        
        #1.1 Recruit
        for i in range(int(self.master.MAIN_QUEUE_MAX * len(self.master.agents))):  # *** do this better
            self.recruit()
        self.master.comm.send(('done',None), dest = self.master.other)
        #1.2 Swap
        self.master.listen()
            
        #2.1 Match
        while(not self.master.main_queue.empty()):
            self.match()
        #2.2 Sync
        if self.master.primary:
            #add relationships from other commmunity
            self.master.listen()
            self.master.comm.send(('done',None), dest = self.master.other)
        else:
            #finish sending relationships to other community
            self.master.comm.send(('done',None), dest = self.master.other)
            #listen for agents to remove
            self.master.listen()
    
    def recruit(self):
        """
        Pick a random grid queue and send a request for a recruit. Recruited
        individuals are automatically added to the self.main_queue.
        
        Differs from normal RelationshipOperator by flipping a coin as to
        whether to add recruited agent to this main queue or other main queue.
        """
        gq = self.master.grid_queues[random.randint(len(self.master.grid_queues))]
        self.master.pipes[gq.my_index].send("recruit")
        agent_name = self.master.pipes[gq.my_index].recv()
        if agent_name is not None:
            agent = self.master.agents[agent_name]
            
            #send half of agents to other
            if random.random() < 0.5:
                self.master.main_queue.push(gq.my_index, agent)
            else:
                self.master.comm.send(('push',agent), dest = self.master.other)
    
    def match(self):
        """
        Pop a suitor off the main queue and try to match him or her.
        
        Differs from normal RelationshipOperator only in step 3 -- primary
        community adds relationship as normal, non-primary sends relationship
        to primary via MPI.
        """
        #1. get next suitor and request matches for him/her from grid queues
        suitor = self.master.main_queue.pop()[1]
	
        #1.2 Parallel, send enquiries via pipe
        for pipe in self.master.pipes.values():
            pipe.send("enquire")
            pipe.send(suitor)
        names = [pipe.recv() for pipe in self.master.pipes.values()]        
        matches = [self.master.agents[n] for n in names if n is not None]

        #2. Suitor flips coins with potential matches
        if(not matches): #no matches
            return
        pq = Queue.PriorityQueue()
        while(matches):
            match = matches.pop()
            hazard = self.master.hazard(suitor, match)  # check for pre-exisiting edge?
            r = random.random()
            decision = int(r < hazard)
            pq.put((-decision, match))
        
        #3. Verify acceptance and form the relationship
        top = pq.get()
        match = top[1]
        accept = top[0]
        if accept:
            if self.master.primary:
                self.add_relationship((suitor,match))
            else:
                suitor = suitor.attributes["NAME"]
                match = match.attributes["NAME"]
                self.master.comm.send(('add_relationship',(suitor,match)), dest = self.master.other)

    def add_relationship(self, relationship):
        suitor, match = relationship
        suitor_name = suitor.attributes["NAME"]
        match_name = match.attributes["NAME"]
        self.form_relationship(suitor, match) 
        if suitor.grid_queue is None or match.grid_queue is None:
	    print '-------'
	    print 'match',match.attributes
	    print 'suitor',suitor.attributes
        if self.master.network.degree(suitor) >= suitor.dnp:
            if suitor.attributes["LOC"][0][0] > 0.5:
                self.master.comm.send(('remove',suitor_name), dest = self.master.other)
            else:
                self.master.pipes[suitor.grid_queue].send("remove")
                self.master.pipes[suitor.grid_queue].send(suitor_name)
                
        if self.master.network.degree(match) >= match.dnp:
            if match.attributes["LOC"][0][0] > 0.5:
                self.master.comm.send(('remove',match_name), dest = self.master.other)
            else:
                self.master.pipes[match.grid_queue].send("remove")
                self.master.pipes[match.grid_queue].send(suitor_name)

class TimeOperator(Operators.TimeOperator):
    """
    Controls the progression of time in the simulation. In particular,
    the time operator removes agents that are beyond a maximum age,
    and moves agents between grid queues.
    """
    def step(self):
        """
        Take a single step in the simulation: Go through agents, remove
        agents that are too old, and move agents to new grid queue (if
        required.)
        
        If primary community send signal with message about actions to the
        other. If not a primary wait for messages. 
        """
        #0. Update the clock of the GridQueues (processes AND originals)
        pipes = self.master.pipes.values()
        for pipe in pipes:
            pipe.send("time")
            pipe.send(self.master.time)
        for gq in self.master.grid_queues.values():  # kinda hacky
            gq.time = self.master.time

        #1. non-primary: listen for updates
        if not self.master.primary:  # wait for updates about agents
            self.master.listen()
            return
        
	#2. primary: check age consistency of agents
        agents = self.master.network.nodes()
        for agent in agents:
            #if older than max age of simulation
            if self.master.age(agent) >= self.master.MAX_AGE:
                self.remove(agent)
                continue  # go to the next agent
                
            #if older than max age of grid queue
            gq = self.master.grid_queues[agent.grid_queue]
            if not gq.accepts(agent):  
                self.master.add_to_grid_queue(agent)
                
        self.master.comm.send(('done',None),dest = self.master.other)
                
    def remove(self, agent):
        agent_name = agent.attributes["NAME"]

        #end ongoing relations
        relations = self.master.network.edges(agent)
        for r in relations:
            other = [r[0],r[1]][r[0]==agent]
            other_gq = self.master.grid_queues[other.grid_queue]
            self.master.network.remove_edge(r[0], r[1])
            if self.master.age(other) >= self.master.MAX_AGE:  # if going to be remove later
                continue
            if  not other_gq.accepts(other):  # if gq going to be updated later
                continue
            self.master.add_to_grid_queue(other)
            
        #remove from grid queues
        loc = agent.attributes["LOC"][0][0]
        if self.master.primary and loc > 0.5:
            self.master.comm.send(('remove',agent_name), dest = self.master.other)  # send to other community
        else:
            agent_pipe = self.master.pipes[agent.grid_queue]
            agent_pipe.send("remove")  # send remove irregardless
            agent_pipe.send(agent_name) 
        agent.grid_queue = None
        self.master.network.remove_node(agent)
        agent.attributes["TIME_REMOVED"] = self.master.time
        
        #replace
        self.master.make_population(1)

class InfectionOperator(Operators.InfectionOperator):
    """
    Controls the progression of the sexually transmitted disease. 
    """

    def __init__(self, master):
        self.master = master

    def step(self):
        """
        Take a single step in the simulation: Go through relationships, if
        relationship is serodiscordant, infect the uninfected partner with
        probablity this is relative to infectivity.
        """
        if not self.master.primary:
            return
        
        #Go through edges and flip coin for infections
        now = self.master.time
        relationships = self.master.network.edges()
        for r in relationships:
            #print "now:",now,"|",r[0].time_of_infection, r[0].time_of_infection<now, r[1].time_of_infection, r[1].time_of_infection>now
            if(r[0].time_of_infection < now and r[1].time_of_infection > now and random.random() < self.master.INFECTIVITY):
                r[1].time_of_infection = now
                continue
            if(r[1].time_of_infection < now and r[0].time_of_infection > now and random.random() < self.master.INFECTIVITY):
                r[0].time_of_infection = now

    def perform_initial_infections(self, initial_prevalence, seed_time):
        """
        Seeds the population with *initial_prevalence* at *seed_time*.
        """
        infections = int(initial_prevalence*self.master.INITIAL_POPULATION)
        for i in range(infections):
            agent = self.master.agents[random.randint(0, len(self.master.agents) - 1)]
            agent.time_of_infection = seed_time * 52

