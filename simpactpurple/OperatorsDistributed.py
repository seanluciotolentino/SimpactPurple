"""
Module for operators used in simulation in which communities are paritioned
based on location.
"""
import Queue
import numpy.random as random
import numpy as np
import Operators

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
            self.master.broadcast(('done','updating relationships'))
        else:
            # recv agents and add to right grid queue
            self.master.listen('relationship updates')
        self.already_added = []  # reset relationships formed this round

        #1.1 Recruit
        for i in range(int(0.5 * self.master.MAIN_QUEUE_MAX * len(self.master.agents))):  # *** do this better
            self.recruit()
        self.master.broadcast(('done','recruiting'))
        #1.2 Swap
        for other in self.master.others:
            self.master.listen('new recruits', from_whom = other)

        #2.1 Match
        while(not self.master.main_queue.empty()):
            self.match()
        #2.2 Sync
        if self.master.primary:
            #add relationships from other commmunity
            for other in self.master.others:
                self.master.listen('non-primary relationship')
            self.master.broadcast(('done','adding matches'))
        else:
            #finish sending relationships to other community
            self.master.comm.send(('done','sending matches'), dest = 0)
            self.master.listen('matched agent removals')
    
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
            if random.random() < 1.0/self.master.size:
                self.master.main_queue.push(gq.my_index, agent)  # keep agent
            else:
                self.master.comm.send(('push',agent),
                                      dest=self.master.others[random.randint(len(self.master.others))])
    
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
        if not matches:  # no matches
            return
        pq = Queue.PriorityQueue()
        while matches:
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
                suitor = self.master.agents[suitor.attributes["NAME"]]  # grab the appropriate agent
                match = self.master.agents[match.attributes["NAME"]]
                self.form_relationship(suitor,match)
            else:
                suitor = suitor.attributes["NAME"]
                match = match.attributes["NAME"]
                self.master.comm.send(('add_relationship',(suitor,match)), dest = 0)

    def form_relationship(self, agent1, agent2):
        #check agents haven't already formed a relationship this round
        for agent in [agent1, agent2]:
            agent_name = agent.attributes["NAME"]
            if agent_name in self.already_added:
                return
        self.already_added+=[agent1.attributes["NAME"], agent2.attributes["NAME"]]
        
        #actually form the relationship        
        Operators.RelationshipOperator.form_relationship(self, agent1, agent2)
        
        #remove from grid queue if necessary
        for agent in [agent1, agent2]:
            agent_name = agent.attributes["NAME"]
            if self.master.network.degree(agent) >= agent.dnp:
                if agent.partition is not self.master.rank:
                    self.master.comm.send(('remove',agent_name), dest = agent.partition)
                else:
                    self.master.pipes[agent.grid_queue].send("remove")
                    self.master.pipes[agent.grid_queue].send(agent_name)

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
            self.master.listen('time operations')
            return
        
        #2. primary: check age consistency of agents
        agents = self.master.network.nodes()
        for agent in agents:
            agent_name = agent.attributes["NAME"]
	
            #2.1 remove if older than max age of simulation
            if self.master.age(agent) >= self.master.MAX_AGE:
                self.remove(agent)
                continue  # go to the next agent
            
            #2.2 move gq if older than max age of grid queue
            gq = self.master.grid_queues[agent.grid_queue]
            if not gq.accepts(agent) and self.master.network.degree(agent) <= agent.dnp:
                #2.2.1 remove from current gq
                if agent.partition is not self.rank:
                    self.master.comm.send(('remove',agent_name), dest=agent.partition)
                else:
                    agent_pipe = self.master.pipes[agent.grid_queue]
                    agent_pipe.send("remove")
                    agent_pipe.send(agent_name)

        		#2.2.2 add to new grid queue
                self.master.add_to_grid_queue(agent)
    
        #3. send done signal
    	self.master.comm.send(('done','time operations'),dest = self.master.other)
                
    def remove(self, agent):
        agent_name = agent.attributes["NAME"]
        
        #1. End current relationships
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
            
        #2. Remove from grid queues and network
        if agent.rank is not self.rank:
            self.master.comm.send(('remove',agent_name), dest = agent.rank)  # send to other community
        else:
            agent_pipe = self.master.pipes[agent.grid_queue]
            agent_pipe.send("remove")  # send remove irregardless
            agent_pipe.send(agent_name) 
        agent.grid_queue = None
        self.master.network.remove_node(agent)
        agent.attributes["TIME_REMOVED"] = self.master.time
        
        #3. Replace with new young agent
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

