"""
Module for all of the default operators.
"""

import Queue
import numpy.random as random

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
                                        
    def step(self):
        """
        Take a single time step in the simulation. 
        """
        #0. Dissolve relationships
        self.update()
        
        #1. Recruit
        for i in range(int(self.master.MAIN_QUEUE_MAX * len(self.master.agents))):  # *** do this better
            self.recruit()
        
        #2. Match
        while not self.master.main_queue.empty():
            self.match()

    def update(self):
        """
        Decrement duration of relationships by 1 week,
        remove relationships that have expired.
        """
        network = self.master.network
        relationships = network.edges() 
        for r in relationships:
            network.get_edge_data(r[0], r[1])["duration"] -= 1
            if(network.get_edge_data(r[0], r[1])["duration"] < 0):
                self.dissolve_relationship(r[0], r[1])

    def recruit(self):
        """
        Pick a random grid queue and send a request for a recruit. Recruited
        individuals are then added to the main_queue (self.master.main_queue).
        """
        gq = self.master.grid_queues[random.randint(len(self.master.grid_queues))]
        self.master.pipes[gq.my_index].send("recruit")
        agent_name = self.master.pipes[gq.my_index].recv()
        
        if agent_name is not None:
            agent = self.master.agents[agent_name]
            self.master.main_queue.push(gq.my_index, agent)
            
    def match(self):
        """
        Pop a suitor off the main queue and try to match him or her. 
        """
        #1. get next suitor and request matches for him/her from grid queues
        suitor = self.master.main_queue.pop()[1]
        #1.1 Return if matched
        if self.master.network.degree(suitor) >= suitor.dnp:
            return
        #1.6 in parallel, send enquiries via pipe
        for pipe in self.master.pipes.values():
            pipe.send("enquire")
            pipe.send(suitor)
        names = [pipe.recv() for pipe in self.master.pipes.values()]        
        matches = [self.master.agents[n] for n in names if n is not None]

        #2. Suitor flips coins with potential matches
        if not matches:  # no matches
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
            self.form_relationship(suitor, match) 
            if self.master.network.degree(suitor) >= suitor.dnp:
                self.master.pipes[suitor.grid_queue].send("remove")
                self.master.pipes[suitor.grid_queue].send(suitor.attributes["NAME"])
            if self.master.network.degree(match) >= match.dnp:
                self.master.pipes[match.grid_queue].send("remove")
                self.master.pipes[match.grid_queue].send(match.attributes["NAME"])
            
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
        self.master.network.remove_edge(agent1, agent2)

        #add agents into appropriate grid queues
        self.master.add_to_grid_queue(agent1)
        self.master.add_to_grid_queue(agent2)

    def duration(self, agent1, agent2):
        """
        Returns a duration given two agents.

        Can test some qualities of the agents to assess what
        kind of relationship they would form (i.e., transitory, casual,
        marriage). 
        """
        return self.master.DURATIONS(agent1, agent2)  # initial naive duration calculation

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
        #0. Update the clock of the GridQueues (processes AND originals)
        pipes = self.master.pipes.values()
        for pipe in pipes:
            pipe.send("time")
            pipe.send(self.master.time)
        for gq in self.master.grid_queues.values():  # kinda hacky
            gq.time = self.master.time
        
        #1. Increment ages of agents, move their queue if necessary
        agents = self.master.network.nodes()
        for agent in agents:
            agent_name = agent.attributes["NAME"]
            agent_pipe = self.master.pipes[agent.grid_queue]

            #if too old
            if self.master.age(agent) >= self.master.MAX_AGE:
                self.remove(agent)
                continue  # go to the next agent
                
            #if (assigned to wrong gq) and (needs to be in gq)
            gq = self.master.grid_queues[agent.grid_queue]
            if not gq.accepts(agent) and self.master.network.degree(agent) <= agent.dnp:
                #1. remove from current gq
                agent_pipe.send("remove")
                agent_pipe.send(agent_name) 
                
                #2. add to new grid queue
                self.master.add_to_grid_queue(agent)
                
    def remove(self, agent):
        """
        Function for removing agents from the simulation.
        """
        agent_name = agent.attributes["NAME"]
        agent_pipe = self.master.pipes[agent.grid_queue]
        
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
        agent_pipe.send("remove")  # send remove irregardless
        agent_pipe.send(agent_name) 
        agent.grid_queue = None
        self.master.network.remove_node(agent)
        agent.attributes["TIME_REMOVED"] = self.master.time
        
        #replace
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
