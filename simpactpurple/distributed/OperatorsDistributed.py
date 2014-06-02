"""
Module for operators used in distributed simulation (communities is made up of
smaller subcommunities).
"""
import Queue
import numpy.random
import random
import numpy as np
import simpactpurple.Operators as Operators

class RelationshipOperator(Operators.RelationshipOperator):
    """
    A distributed implementation of a relationship operator.
    """
    def step(self):
        """
        Take a single time step in the simulation. 
        """
        #1.1 Recruit
        recruits = 0
        for i in range(2*self.master.recruit):
            recruits += self.recruit()
            if recruits >= self.master.recruit:
                break
        self.master.broadcast(('done','recruiting'))
        #1.2 Swap
        self.master.listen_all('new recruits')
        
        #2.1 Match
        while(not self.master.main_queue.empty()):
            self.match()
        #2.2 Sync
        if self.master.is_primary:
            #add relationships from other commmunity
            self.master.listen_all('non-primary relationship')
            self.master.broadcast(('done','adding matches'))
        else:
            #finish sending relationships to other community
            self.master.comm.send(('done','sending matches'), dest = self.master.primary)
            self.master.listen('matched agent removals', self.master.primary)
   
    def recruit(self):
        """
        Pick a random grid queue and send a request for a recruit. Recruited
        individuals are randomly selected to enter this main queue or the
        main queue of another community.
        """
        #gq = self.master.grid_queues.keys()[random.randint(len(self.master.grid_queues))]
        gq = random.choice(self.master.grid_queues.keys())
        self.master.pipes[gq].send("recruit")
        agent_name = self.master.pipes[gq].recv()
        if agent_name is not None:
            agent = self.master.agents[agent_name]
            #send fraction of agents to other community
            #if np.random.random() < 1.0/self.master.size:
            #    self.master.main_queue.push(gq, agent)  # keep agent
            #else:
            #    #other = self.master.others[random.randint(len(self.master.others))]
            #    other = random.choice(self.master.others)
            #    self.master.comm.send(('push',agent),dest=other)

            #send fraction based on transition matrix
            rand = np.random.random()
            rank = [int(v) for v in rand < self.master.transition[:,self.master.rank]].index(1)
            if rank == self.master.rank:
                self.master.main_queue.push(gq, agent)
            else:
                self.master.comm.send(('push',agent),dest=rank)
            return 1
        else:
            return 0
    
    def match_enquire(self):
        """
        1. Get next suitor in the main_queue and send request for matches for 
        him/her from grid queues.  Note that if a suitor was already matched
        the method will return None and not send an enquiry message.
        """
        #1. get next suitor and request matches for him/her from grid queues
        suitor = self.master.main_queue.pop()[1]
        
        #1.1 Return if matched (only for primary)
        if self.master.is_primary and self.master.network.degree(\
            self.master.agents[suitor.name]) >= suitor.dnp:
            return

        #1.2 In parallel, send enquires via pipe            
        for pipe in self.master.pipes.values():
            pipe.send("enquire")
            pipe.send(suitor)
            
        return suitor
        
    def match_process(self, suitor, matches):
        """
        3. After receiving matches allow suitor to choose.
        """
        #3. Suitor flips coins with potential matches
        if not matches:  # no matches
            return
        pq = Queue.PriorityQueue()
        while matches:
            match = matches.pop()
            hazard = self.master.hazard(suitor, match)
            r = np.random.random()
            decision = int(r < hazard)
            pq.put((-decision, match))
        
        #3.1 Verify acceptance and form the relationship
        accept, match = pq.get()
        if accept:
            if self.master.is_primary:
                suitor = self.master.agents[suitor.name]  # grab the appropriate agent
                match = self.master.agents[match.name]
                self.form_relationship(suitor,match)
            else:
                suitor = suitor.name
                match = match.name
                self.master.comm.send(('add_relationship',(suitor,match)), dest = self.master.primary)

    def form_relationship(self, agent1, agent2):
        """
        Forms a relationship between agent1 and agent2.
        """
        # Reject based on DNP rule
        for agent in [agent1, agent2]:
            if self.master.network.degree(agent) >= agent.dnp:
                return
                
        # Reject if relationship exists
        if self.master.network.has_edge(agent1,agent2):
            return
                
        #actually form the relationship        
        Operators.RelationshipOperator.form_relationship(self, agent1, agent2)
        
        #remove from grid queue if necessary
        for agent in [agent1, agent2]:
            if self.master.network.degree(agent) >= agent.dnp:
                if agent.partition is not self.master.rank:
                    self.master.comm.send(('remove_from_grid_queue',agent.name), dest = agent.partition)
                else:
                    self.master.pipes[agent.grid_queue].send("remove")
                    self.master.pipes[agent.grid_queue].send(agent.name)

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
        """
        #1.1 Update the clocks of the GridQueues (processes AND originals)
        pipes = self.master.pipes.values()
        for pipe in pipes:
            pipe.send("time")
            pipe.send(self.master.time)
        for gq in self.master.grid_queues.values():  # kinda hacky
            gq.time = self.master.time
                
        #1.2 Update relationships
        if self.master.is_primary:
            # sends agents back to correct grid queues
            for r in self.master.relationships_ending_at[self.master.time]:
                try:
                    self.master.relationship_operator.dissolve_relationship(r[0], r[1])
                except:
                    if r[0] in self.master.network:
                        self.master.add_to_grid_queue(r[0])
                    elif r[1] in self.master.network:
                        self.master.add_to_grid_queue(r[1])
            self.master.broadcast(('done','updating relationships'))
        else:
            # recv agents and add to right grid queue
            self.master.listen('relationship updates', self.master.primary)
            
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
                if self.master.is_primary:
                    self.remove(agent)
                    self.replace(agent)
                else:
                    self.master.comm.send(('remove_from_simulation',agent.name), dest = self.master.primary)
                msg = self.master.pipes[queue].recv()
                
        #2.3. Terminate old grid queue if necessary
        if self.master.time%(self.master.BIN_SIZE*52)==0:
            for queue in self.oldest_queues:
                self.master.pipes[queue].send("terminate")
                del self.master.grid_queues[queue]
                del self.master.pipes[queue]
            self.oldest_queues = self.master.grid_queues.keys()[:2]
            
        #3 Listen for updates from others
        if self.master.is_primary:
            self.master.listen_all('oldest removals')
        else:
            self.master.comm.send(('done','removing oldest'), dest = self.master.primary)
            
                
    def remove(self, agent):
        """
        Function for removing agents from the distributed simulation.
        """
        #Update migration variables
        if self.master.migration:
            agent.attributes["MIGRATION"].append((self.master.time, self.master.rank, 0))
            self.master.comm.send(('remove',agent.name), dest = 0)
        #essential removes            
        agent.grid_queue = None
        self.master.network.remove_node(agent)
        agent.attributes["TIME_REMOVED"] = self.master.time
        if agent.time_of_infection < np.inf:
            self.master.infection_operator.infected_agents.remove(agent)
        

        
class InfectionOperator(Operators.InfectionOperator):
    """
    Controls the progression of the sexually transmitted disease. 
    """

    def __init__(self, master):
        self.master = master
        self.infected_agents = []
        self.number_infected = []

    def step(self):
        """
        Take a single step in the simulation: Go through relationships, if
        relationship is serodiscordant, infect the uninfected partner with
        probablity this is relative to infectivity.
        """
        if not self.master.is_primary:
            return
        self.number_infected.append(len(self.infected_agents))
        #Go through edges and flip coin for infections
        now = self.master.time
        for agent in self.infected_agents:
            relationships = self.master.network.edges(agent)
            for r in relationships:
                if (r[0].time_of_infection < now and r[1].time_of_infection > now) and np.random.random() < self.master.INFECTIVITY:
                    self.infected_agents.append(r[1])
                    r[1].time_of_infection = now
                    continue
                if (r[1].time_of_infection < now and r[0].time_of_infection > now) and np.random.random() < self.master.INFECTIVITY:
                    self.infected_agents.append(r[0])
                    r[0].time_of_infection = now

    def perform_initial_infections(self, initial_prevalence, seed_time):
        """
        Seeds the population with *initial_prevalence* at *seed_time*.
        """
        if not self.master.is_primary:
            return
        infections = int(initial_prevalence*self.master.INITIAL_POPULATION)
        #agent = self.master.agents.values()[random.randint(0, len(self.master.agents) - 1)]
        agent = random.choice(self.master.agents.values())
        for i in range(infections):
            #while agent in self.infected_agents:  # avoid duplicates
            while agent in self.infected_agents or agent.partition != self.master.primary:  # avoid duplicates and seed in primary
                #agent = self.master.agents.values()[random.randint(0, len(self.master.agents) - 1)]
                agent = random.choice(self.master.agents.values())
            agent.time_of_infection = seed_time
            self.infected_agents.append(agent)

