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
	#-1. Update times of grid queue 
	# Supposed to be time operator's job but it's disabled right now
	for gq in self.master.relationship_operator.grid_queues:
	    gq.time = self.master.time
	pipes = self.master.relationship_operator.pipes.values()
	for pipe in pipes:
	    pipe.send("time")
	    pipe.send(self.master.time)

        #0. Dissolve relationships
        if self.master.primary:
            # sends agents back to right grid queues
            self.update()
            self.master.comm.send('done', dest = self.master.other)
        else:
            # recv agents and add to right grid queue
            agent = self.master.comm.recv(source = self.master.other)
            while agent != 'done':
                self.update_grid_queue_for(agent)
                agent = self.master.comm.recv(source = self.master.other)
        
        #1. Recruit AND SWAP
        for i in range(int(self.master.MAIN_QUEUE_MAX * len(self.master.agents))):  # *** do this better
            self.recruit()
        self.master.comm.send('done', dest = self.master.other)
        agent = self.master.comm.recv(source = self.master.other)
        while agent != 'done':
            self.main_queue.push(agent.grid_queue, agent)
            agent = self.master.comm.recv(source = self.master.other)
            
        #2. Match
	#print 'main queue:',self.main_queue.length()
        while(not self.main_queue.empty()):
            self.match()
        #2.1 communicate
        if self.master.primary:
            #add relationships from other commmunity
            relationship = self.master.comm.recv(source = self.master.other)
            while relationship != 'done':
                agent0 = self.master.agents[relationship[0]]  # look up name
                agent1 = self.master.agents[relationship[1]]
                self.add_relationship((agent0, agent1))
                relationship = self.master.comm.recv(source = self.master.other)
            self.master.comm.send('done', dest = self.master.other)
        else:
            #finish sending relationships to other community
            self.master.comm.send('done', dest = self.master.other)
            #listen for agents to remove
            agent = self.master.comm.recv(source = self.master.other)
            while agent != 'done':
                agent = self.master.agents[agent.attributes["NAME"]]
                self.pipes[agent.grid_queue].send("remove")
                self.pipes[agent.grid_queue].send(agent.attributes["NAME"])
                agent = self.master.comm.recv(source = self.master.other)
    
    def recruit(self):
        """
        Pick a random grid queue and send a request for a recruit. Recruited
        individuals are automatically added to the self.main_queue.
        
        Differs from normal RelationshipOperator by flipping a coin as to
        whether to add recruited agent to this main queue or other main queue.
        """
        gq = self.grid_queues[random.randint(len(self.grid_queues))]
        self.pipes[gq.my_index].send("recruit")
        agent_name = self.pipes[gq.my_index].recv()
        #print "recruited",agent_name
        if agent_name is not None:
	    #print gq.my_index,'returned',agent_name
            agent = self.master.agents[agent_name]
            if random.random() < 0.5:
                self.main_queue.push(gq.my_index, agent)
            else:
                self.master.comm.send(agent, dest = self.master.other)
	else:
	    #print '*** None received in recruit from',gq.my_index
            pass
    
    def match(self):
        """
        Pop a suitor off the main queue and try to match him or her.
        
        Differs from normal RelationshipOperator only in step 3 -- primary
        community adds relationship as normal, non-primary sends relationship
        to primary via MPI.
        """
        #1. get next suitor and request matches for him/her from grid queues
        suitor = self.main_queue.pop()[1]
	
        #1.2 Parallel, send enquiries via pipe
        for pipe in self.pipes.values():
            pipe.send("enquire")
            pipe.send(suitor)
        names = [pipe.recv() for pipe in self.pipes.values()]        
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
                self.master.comm.send((suitor,match), dest = self.master.other)

    def add_relationship(self, relationship):
        suitor, match = relationship
        self.form_relationship(suitor, match) 
        if self.master.network.degree(suitor) >= suitor.dnp:
            if suitor.attributes["LOC"][0][0] > 0.5:
                self.master.comm.send(suitor, dest = self.master.other)
            else:
                self.pipes[suitor.grid_queue].send("remove")
                self.pipes[suitor.grid_queue].send(suitor.attributes["NAME"])
        if self.master.network.degree(match) >= match.dnp:
            if match.attributes["LOC"][0][0] > 0.5:
                self.master.comm.send(match, dest = self.master.other)
            else:
                self.pipes[match.grid_queue].send("remove")
                self.pipes[match.grid_queue].send(suitor.attributes["NAME"])
    def form_relationship(self, agent1, agent2):
	#print "forming relationship", agent1.attributes["NAME"], agent2.attributes["NAME"]
	Operators.RelationshipOperator.form_relationship(self, agent1, agent2)

    def dissolve_relationship(self, agent1, agent2):
	#print "dissolving relationship", agent1.attributes["NAME"], agent2.attributes["NAME"]
	Operators.RelationshipOperator.dissolve_relationship(self, agent1, agent2)
    def update_grid_queue_for(self, agent):
        """
        Find the appropriate grid queue for agent. Called by 
           1. Time Operator - when agent graduates to the next grid queue
           1.5 Time Operator - when relationship with removed is dissolved
           2. Relationship Operator - a relationship is dissolved
           3. Community - in make_population in the mainloop
           
        Alternative implementation also necessitates grid queue selection based
        on location.
        """
        loc = agent.attributes["LOC"][0][0]
        if self.master.primary and loc > 0.5:
            self.master.comm.send(agent, dest = self.master.other)  # send to other community
            return

        #add to new grid queue
	if agent.grid_queue is None:
	    print 'agent',agent.attributes["NAME"],'time:',self.master.time,'gq:',agent.grid_queue,'age:',self.master.age(agent)
            grid_queue = [gq for gq in self.grid_queues if gq.accepts(agent)][agent.sex]
            agent.grid_queue = grid_queue.my_index
	    
        self.pipes[agent.grid_queue].send("add")
        self.pipes[agent.grid_queue].send(agent)
#
#
#class TimeOperator():
#    """
#    Controls the progression of time in the simulation. In particular,
#    the time operator removes agents that are beyond a maximum age,
#    and moves agents between grid queues.
#    """
#    def __init__(self, master):
#        self.master = master
#
#    def step(self):
#        """
#        Take a single step in the simulation: Go through agents, remove
#        agents that are too old, and move agents to new grid queue (if
#        required.)
#        """
#        #0.1 sync grid_queue clocks
#        for gq in self.master.relationship_operator.grid_queues:  # kinda hacky
#            gq.time = self.master.time
#            
#        #0.2 Update the clock of the GridQueues (processes AND originals)
#        pipes = self.master.relationship_operator.pipes.values()
#        for pipe in pipes:
#            pipe.send("time")
#            pipe.send(self.master.time)
#
#        #1. non-primary: listen for updates
#        if not self.master.primary:  # wait for updates about agents
#            agent = self.master.comm.recv(source = self.master.other)
#            while agent != 'done':
#                self.update_grid_queue_for(agent)
#                agent = self.master.comm.recv(source = self.master.other)
#        
#        #2. primary: increment ages of agents, move their queue if necessary
#        agents = self.master.network.nodes()
#        for agent in agents:
#            agent_name = agent.attributes["NAME"]
#            agent_pipe = self.master.relationship_operator.pipes[agent.grid_queue]
#
#            #if too old
#            if self.master.age(agent) >= self.master.MAX_AGE:
#                self.remove(agent)
#                continue  # go to the next agent
#                
#            #if (in queue) and (shouldn't be)
#            gq = self.master.relationship_operator.grid_queues[agent.grid_queue]
#            if not gq.accepts(agent):  
#                self.master.relationship_operator.update_grid_queue_for(agent)
#        self.master.comm.send('done',dest = self.master.other)
#                
#    def remove(self, agent):
#        agent_name = agent.attributes["NAME"]
#        agent_pipe = self.master.relationship_operator.pipes[agent.grid_queue]
#        
#        #end ongoing relations
#        relations = self.master.network.edges(agent)
#        for r in relations:
#            other = [r[0],r[1]][r[0]==agent]
#            other_gq = self.master.relationship_operator.grid_queues[other.grid_queue]
#            self.master.network.remove_edge(r[0], r[1])
#            if self.master.age(other) >= self.master.MAX_AGE or not other_gq.accepts(other): 
#                continue  # going to be updated later
#            self.master.relationship_operator.update_grid_queue_for(other)
#            
#        #remove from grid queues
#        agent_pipe.send("remove")  # send remove irregardless
#        agent_pipe.send(agent_name) 
#        agent.grid_queue = None
#        self.master.grid_queue[agent] = None
#        self.master.network.remove_node(agent)
#        agent.attributes["TIME_REMOVED"] = self.master.time
#        
#        #replace
#        #self.master.make_population(1, born=lambda: self.master.time - (52*15))
#        self.master.make_population(1)
#
#class InfectionOperator():
#    """
#    Controls the progression of the sexually transmitted disease. 
#    """
#
#    def __init__(self, master):
#        self.master = master
#
#    def step(self):
#        """
#        Take a single step in the simulation: Go through relationships, if
#        relationship is serodiscordant, infect the uninfected partner with
#        probablity this is relative to infectivity.
#        """
#        if not self.master.primary:
#            return
#        
#        #Go through edges and flip coin for infections
#        now = self.master.time
#        relationships = self.master.network.edges()
#        for r in relationships:
#            #print "now:",now,"|",r[0].time_of_infection, r[0].time_of_infection<now, r[1].time_of_infection, r[1].time_of_infection>now
#            if(r[0].time_of_infection < now and r[1].time_of_infection > now and random.random() < self.master.INFECTIVITY):
#                r[1].time_of_infection = now
#                continue
#            if(r[1].time_of_infection < now and r[0].time_of_infection > now and random.random() < self.master.INFECTIVITY):
#                r[0].time_of_infection = now
#
#    def perform_initial_infections(self, initial_prevalence, seed_time):
#        """
#        Seeds the population with *initial_prevalence* at *seed_time*.
#        """
#        infections = int(initial_prevalence*self.master.INITIAL_POPULATION)
#        for i in range(infections):
#            agent = self.master.agents[random.randint(0, len(self.master.agents) - 1)]
#            agent.time_of_infection = seed_time * 52
#
