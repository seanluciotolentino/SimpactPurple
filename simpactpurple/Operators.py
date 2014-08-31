"""
Module for all of the default operators.
"""

import Queue
import numpy as np
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
        self.max_weeks = (master.MAX_AGE*52)+1  # for efficiently knowing setting the end time of relationships
                                        
    def step(self):
        """
        Take a single time step in the simulation. 
        """        
        #1. Recruit
        for i in range(self.master.recruit):
            self.recruit()
            
        #2. Match
        while not self.master.main_queue.empty():
            self.match()


    def recruit(self):
        """
        Pick a random grid queue and send a request for a recruit. Recruited
        individuals are then added to the main_queue (self.master.main_queue).
        """
        gq = self.master.grid_queues.keys()[random.randint(len(self.master.grid_queues))]
        #gq = random.choice(self.master.grid_queues.keys())
        self.master.pipes[gq].send("recruit")
        agent_name = self.master.pipes[gq].recv()  
        if agent_name is not None:
            agent = self.master.agents[agent_name]
            self.master.main_queue.push(gq, agent)
            
    def match(self):
        """
        Pop a suitor off the main queue and try to match him or her. 
        """
        #1. Send enquiry
        suitor = self.match_enquire()
        if not suitor: 
            return
        
        #2. Receive replies
        matches = self.match_recv()
        
        #3. Process matches
        self.match_process(suitor, matches)
        
    def match_enquire(self):
        """
        1. Get next suitor in the main_queue and send request for matches for 
        him/her from grid queues.  Note that if a suitor was already matched
        the method will return None and not send an enquiry message.
        """
        #1.1 Get next suitor
        suitor = self.master.main_queue.pop()[1]
        
        #1.2 Return if matched
        if self.master.network.degree(suitor) >= suitor.dnp:
            return

        #1.3 In parallel, send enquiries via pipe
        for pipe in self.master.pipes.values():
            pipe.send("enquire")
            pipe.send(suitor)
        
        return suitor
            
    def match_recv(self):
        """
        2. Receive match messages from pipes and process them into agents.
        """
        names = [pipe.recv() for pipe in self.master.pipes.values()]        
        matches = [self.master.agents[n] for n in names if n is not None]
        return matches

    def match_process(self, suitor, matches):
        """
        3. After receiving matches allow suitor to choose.
        """
        #3.1 Suitor flips coins with potential matches
        if not matches:  # no matches
            return            
        pq = Queue.PriorityQueue()
        while(matches):
            match = matches.pop()
            #calc probability (checking for pre-exisiting edge)
            probability = int(not self.master.network.has_edge(suitor, match))\
                    *self.master.probability(suitor, match)
            r = random.random()
            decision = int(r < probability)
            pq.put((-decision, match))
            
        #3.2 Verify acceptance and form the relationship
        accept, match = pq.get()
        if accept:
            self.form_relationship(suitor, match) 
            if self.master.network.degree(suitor) >= suitor.dnp:
                self.master.pipes[suitor.grid_queue].send("remove")
                self.master.pipes[suitor.grid_queue].send(suitor.name)
            if self.master.network.degree(match) >= match.dnp:
                self.master.pipes[match.grid_queue].send("remove")
                self.master.pipes[match.grid_queue].send(match.name)
            
    def form_relationship(self, agent1, agent2):
        """
        Forms a relationship between agent1 and agent2.
        """
        d = np.max((1, self.master.DURATIONS(agent1, agent2))) # relationships must be at least 1 week

        #cache the ending time for easier access
        end_time = int(np.min((self.master.time + d, self.master.NUMBER_OF_YEARS*52, 
                               self.max_weeks+agent1.born, self.max_weeks+agent2.born)))
        self.master.relationships_ending_at[end_time].append((agent1,agent2))

        #add the relationship to data structures
        self.master.relationships.append((agent1, agent2, self.master.time, end_time))
        self.master.network.add_edge(agent1, agent2, {"start":self.master.time, "end": end_time,})
        #print " ++ ",self.master.rank, "forming relationship:", agent1.name, "and", 
        #print agent2.name,"|",self.master.time + d, self.master.NUMBER_OF_YEARS*52, 
        #print self.max_weeks+agent1.born, self.max_weeks+agent2.born,"| time", self.master.time

    def dissolve_relationship(self, agent1, agent2):
        """
        Dissolves a relationship between agent1 and agent2.
        """
        self.master.network.remove_edge(agent1, agent2)

        #add agents into appropriate grid queues
        self.master.add_to_grid_queue(agent1)
        self.master.add_to_grid_queue(agent2)

class TimeOperator():
    """
    Controls the progression of time in the simulation. In particular,
    the time operator updates the clocks of the queues, dissolves relationships
    that are past their duration, and removes agents that are beyond the 
    maximum age.
    """
    def __init__(self, master):
        self.master = master
        self.oldest_queues = self.master.grid_queues.keys()[:2]  # needs to be generalized...
        
    def step(self):
        """
        Take a single step in the simulation.
        """
        #1.1 Update the clocks of the GridQueues (processes AND originals)
        pipes = self.master.pipes.values()
        for pipe in pipes:
            pipe.send("time")
            pipe.send(self.master.time)        
        for gq in self.master.grid_queues.values():  # kinda hacky
            gq.time = self.master.time
            
        #1.2 Update relationships
        for r in self.master.relationships_ending_at[self.master.time]:
            self.master.relationship_operator.dissolve_relationship(r[0], r[1])
            
        #2.1 Make a new grid queue if necessary
        if self.master.time%(self.master.BIN_SIZE*52)==0:
            self.master.make_n_queues(self.master.SEXES)
            
        #2.2 Grab oldest agents from oldest grid queues
        for queue in self.oldest_queues:
            self.master.pipes[queue].send("oldest")
        for queue in self.oldest_queues:
            msg = self.master.pipes[queue].recv()
            while msg != 'done':
                agent = self.master.agents[msg]
                self.remove(agent)
                self.replace(agent)
                msg = self.master.pipes[queue].recv()
                
        #2.3 Terminate old grid queue if necessary
        if self.master.time%(self.master.BIN_SIZE*52)==0:
            for queue in self.oldest_queues:
                self.master.pipes[queue].send("terminate")
                del self.master.grid_queues[queue]
                del self.master.pipes[queue]
            self.oldest_queues = self.master.grid_queues.keys()[:2]
                
    def remove(self, agent):
        """
        Function for removing agents from the simulation.
        """
        agent.grid_queue = None
        self.master.network.remove_node(agent)
        agent.attributes["TIME_REMOVED"] = self.master.time
        if agent.time_of_infection < np.inf:
            self.master.infection_operator.infected_agents.remove(agent)
            
    def replace(self, agent):
        """
        Function to replace *agent*.
        """
        self.master.make_population(1)

class InfectionOperator():
    """
    Controls the progression of the sexually transmitted disease. 
    """
    def __init__(self, master):
        self.master = master
        self.infected_agents = []

    def step(self):
        """
        Take a single step in the simulation: Go through relationships, if
        relationship is serodiscordant, infect the uninfected partner with
        probablity this is relative to infectivity.
        """
        #Go through edges and flip coin for infections
        now = self.master.time
        for agent in self.infected_agents:
            relationships = self.master.network.edges(agent)
            
            for r in relationships:
                if(r[0].time_of_infection < now and r[1].time_of_infection > now and random.random() < self.master.INFECTIVITY):
                    r[1].time_of_infection = now
                    self.infected_agents.append(r[1])
                    continue
                if(r[1].time_of_infection < now and r[0].time_of_infection > now and random.random() < self.master.INFECTIVITY):
                    r[0].time_of_infection = now
                    self.infected_agents.append(r[0])

    def perform_initial_infections(self, initial_prevalence, seed_time):
        """
        Seeds the population with *initial_prevalence* at *seed_time*.
        """
        infections = int(initial_prevalence*self.master.INITIAL_POPULATION)
        agent = self.master.agents[random.randint(0, len(self.master.agents) - 1)]
        for i in range(infections):
            while agent in self.infected_agents:
                agent = self.master.agents[random.randint(0, len(self.master.agents) - 1)]
                #agent = random.choice(self.master.agents.values())
            agent.time_of_infection = seed_time
            self.infected_agents.append(agent)
        
