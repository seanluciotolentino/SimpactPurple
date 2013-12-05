"""
Module for all of the default operators.
"""

import Queue
import numpy.random as random
import GridQueue
import multiprocessing
import PriorityQueue
import sys

class RelationshipOperator():
    """
    Controls the formation and dissolution of relationships between agents. At
    initialization, the relationship operator creates the grid queues it will
    need to hold agent, and starts their functioning in seperate processes. Each
    time step, the relationship operator does three things:

       1. Dissolve relationships that have exceeded their duration
       2. Recruit from the grid queues into the main queue
       3. Iterate through main queue, attempting to match each suitor   `
          at the top of the queue.    
    """

    def __init__(self, master):
        self.master = master
        self.main_queue = PriorityQueue.PriorityQueue()
        self.grid_queues = []
        
        #make Grid Queues:
        self.pipes = {}
        for age in range(master.MIN_AGE, master.MAX_AGE, master.BIN_SIZE):
            bottom = age
            top = age+master.BIN_SIZE
            for sex in range(master.SEXES):
                #make the grid queue
                gq = GridQueue.GridQueue(top, bottom, sex, len(self.grid_queues))
                self.grid_queues.append(gq)
                                        
                #start a new process for it
                pipe_top, pipe_bottom = multiprocessing.Pipe()
                p = multiprocessing.Process(target=GridQueue.listen,args=(gq, pipe_bottom))#, semaphore))
                p.start()
                self.pipes[gq.my_index] = pipe_top                       
                                    
        master.NUMBER_OF_GRID_QUEUES = len(self.grid_queues)
                        
    def step(self):
        """
        Take a single time step in the simulation. 
        """
        #0. Dissolve relationships
        network = self.master.network
        relationships = network.edges() 
        for r in relationships:
            network.get_edge_data(r[0], r[1])["duration"] -= 1
            if(network.get_edge_data(r[0], r[1])["duration"] < 0):
                self.dissolve_relationship(r[0], r[1])
        
        #1. Recruit
        for i in range(int(self.master.MAIN_QUEUE_MAX * len(self.master.agents))):  # *** do this better
            self.recruit()
            
        #2. Match
        while(not self.main_queue.empty()):
            self.match()

    def recruit(self):
        """
        Pick a random grid queue and send a request for a recruit. Recruited
        individuals are automatically added to the self.main_queue.
        """
        gq = self.grid_queues[random.randint(len(self.grid_queues))]
        self.pipes[gq.my_index].send("recruit")
        agent_name = self.pipes[gq.my_index].recv()
        #print "recruited",agent_name
        if agent_name is not None:
            agent = self.master.agents[agent_name]
            self.main_queue.push(gq.my_index, agent)
            
    def match(self):
        """
        Pop a suitor off the main queue and try to match him or her. 
        """
        #1. get next suitor and request matches for him/her from grid queues
        suitor = self.main_queue.pop()[1]

        #print "======"
        #print "suitor:", suitor        

        #1.1 Return if matched
        if self.master.network.degree(suitor) >= suitor.dnp:
            #print "  -suitor is no longer looking"
            return

        #1.6 Parallel, send enquiries via pipe
        for pipe in self.pipes.values():
            pipe.send("enquire")
            pipe.send(suitor)
        names = [pipe.recv() for pipe in self.pipes.values()]        
        matches = [self.master.agents[n] for n in names if n is not None]

        
        #2. Suitor flips coins with potential matches
        #print "matches:",[m.attributes["NAME"] for m in matches]
        if(not matches): #no matches
            #print "   -Suitor had not matches"
            return
            
        pq = Queue.PriorityQueue()
        while(matches):
            match = matches.pop()
            #calc hazard (checking for pre-exisiting edge)
            hazard = int(not self.master.network.has_edge(suitor, match))\
                    *self.master.hazard(suitor, match)
            r = random.random()
            decision = int(r < hazard)
            pq.put((-decision, match))
        
        #3. Verify acceptance and form the relationship
        top = pq.get()
        match = top[1]
        accept = top[0]
        if accept:
            #print "   -Suitor choose",match
            self.form_relationship(suitor, match) 
            if self.master.network.degree(suitor) >= suitor.dnp:
                self.pipes[suitor.grid_queue].send("remove")
                self.pipes[suitor.grid_queue].send(suitor.attributes["NAME"])
            if self.master.network.degree(match) >= match.dnp:
                self.pipes[match.grid_queue].send("remove")
                self.pipes[match.grid_queue].send(match.attributes["NAME"])
        else:
            #print "   -Suitor had no luck flipping coins"
            pass
            
    def form_relationship(self, agent1, agent2):
        """
        Forms a relationship between agent1 and agent2.
        """
        d = self.duration(agent1, agent2)
        agent1.last_match = self.master.time
        agent2.last_match = self.master.time
        self.master.relationships.append([agent1, agent2, self.master.time, self.master.time + d])
        self.master.network.add_edge(agent1, agent2, {"duration": d})

    def dissolve_relationship(self, agent1, agent2):
        """
        Dissolves a relationship between agent1 and agent2.
        """
        #print "relationship dissolved:",agent1.attributes["NAME"],agent2.attributes["NAME"]
        self.master.network.remove_edge(agent1, agent2)
        
        #add agents into appropriate grid queues
        self.update_grid_queue_for(agent1)
        self.update_grid_queue_for(agent2)

    def duration(self, agent1, agent2):
        """
        Returns a duration given two agents.

        Can test some qualities of the agents to assess what
        kind of relationship they would form (i.e., transitory, casual,
        marriage). 
        """
        return self.master.DURATIONS()  # initial naive duration calculation

    def update_grid_queue_for(self, agent):
        """
        Find the appropriate grid queue for agent. Called by 
           1. Time Operator - when agent graduates to the next grid queue
           1.5 Time Operator - when relationship with removed is dissolved
           2. Relationship Operator - a relationship is dissolved
           3. Community - in make_population in the mainloop
        """
        grid_queue = [gq for gq in self.grid_queues if gq.accepts(agent)][agent.sex]
        agent.grid_queue = grid_queue.my_index
        if self.master.network.degree(agent) < agent.dnp:
            self.pipes[agent.grid_queue].send("add")
            self.pipes[agent.grid_queue].send(agent)


class TimeOperator():
    """
    Controls the progression of time in the simulation. In particular,
    the time operator removes agents that are beyond a maximum age,
    and moves agents between grid queues.
    """
    def __init__(self, master):
        self.master = master

    def step(self):
        """
        Take a single step in the simulation: Go through agents, remove
        agents that are too old, and move agents to new grid queue (if
        required.)
        """
        #sync grid_queue clocks
        for gq in self.master.relationship_operator.grid_queues:  # kinda hacky
            gq.time = self.master.time
            
        #0. Update the clock of the GridQueues (processes AND originals)
        pipes = self.master.relationship_operator.pipes.values()
        for pipe in pipes:
            pipe.send("time")
            pipe.send(self.master.time)
        
        #Increment ages of agents, move their queue if necessary
        agents = self.master.network.nodes()
        for agent in agents:
            agent_name = agent.attributes["NAME"]
            agent_pipe = self.master.relationship_operator.pipes[agent.grid_queue]

            #if too old
            if self.master.age(agent) >= self.master.MAX_AGE:
                self.remove(agent)
                continue  # go to the next agent
                
            #if (in queue) and (shouldn't be)
            gq = self.master.relationship_operator.grid_queues[agent.grid_queue]
            if not gq.accepts(agent):  
                agent_pipe.send("remove")
                agent_pipe.send(agent_name) 
                self.master.relationship_operator.update_grid_queue_for(agent)
                
    def remove(self, agent):
        agent_name = agent.attributes["NAME"]
        agent_pipe = self.master.relationship_operator.pipes[agent.grid_queue]
        
        #end ongoing relations
        relations = self.master.network.edges(agent)
        for r in relations:
            other = [r[0],r[1]][r[0]==agent]
            other_gq = self.master.relationship_operator.grid_queues[other.grid_queue]
            self.master.network.remove_edge(r[0], r[1])
            if self.master.age(other) >= self.master.MAX_AGE or not other_gq.accepts(other): 
                continue  # going to be updated later
            self.master.relationship_operator.update_grid_queue_for(other)
            
        #remove from grid queues
        agent_pipe.send("remove")  # send remove irregardless
        agent_pipe.send(agent_name) 
        agent.grid_queue = None
        self.master.grid_queue[agent] = None
        self.master.network.remove_node(agent)
        agent.attributes["TIME_REMOVED"] = self.master.time
        
        #replace
        #self.master.make_population(1, born=lambda: self.master.time - (52*15))
        self.master.make_population(1)

class InfectionOperator():
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
