import numpy.random as random
import numpy as np
import Community
#import Operators
import OperatorsDistributed
import time as Time

class CommunityDistributed(Community.Community):

    def __init__(self, comm):
        Community.Community.__init__(self)
        #Distributed parameters
        self.comm = comm
        self.rank = comm.Get_rank()
        self.primary = self.rank == 0
        self.size = self.comm.Get_size()
        self.others = range(self.size)
        self.others.remove(self.rank)
        self.partition = lambda agent: int(agent.attributes["LOC"][0][0] * self.size)
 
        #MODEL PARAMETERS
        self.NUMBER_OF_YEARS = 30
        
        #MODEL OPERATORS
        #hazard
        self.preferred_age_difference = -0.1
        self.probability_multiplier = -0.1
        self.preferred_age_difference_growth = 0.1
        
        #relationship operator
        self.SEXES = 2
        self.MIN_AGE = 15
        self.MAX_AGE = 65
        self.BIN_SIZE = 5
        self.MAIN_QUEUE_MAX = 0.3  # proportion of initial population
        self.DURATIONS = lambda a1, a2: 52*random.exponential(0.9)
        
        #infection operator
        self.INFECTIVITY = 0.01
        self.INTIIAL_PREVALENCE = 0  # while there's not infection operator...
        self.SEED_TIME = 0  # in years        

        #time operator
        self.time = 0
                
        #MODEL POPULATION
        self.INITIAL_POPULATION = 300
        self.AGENT_ATTRIBUTES = {}
        self.BORN = lambda: -52*random.uniform(self.MIN_AGE, self.MAX_AGE)
        self.SEX = lambda: random.randint(self.SEXES)
        self.DNP = lambda: random.power(0.2)*(4)
        
    def broadcast(self, message):
        """
        A function which sends message to all nodes. This is necessary b/c
        comm.bcast has buggy performance.
        """
        for other in self.others:
            self.comm.send(message, dest = other)
    
    def make_population(self, size):
        """
        Same as original, except non-primary communities listen for added
        agents instead of making agents themselves.
        """
        if self.primary:
            Community.Community.make_population(self, size)
            if self.time <=0:
                self.broadcast(('done','making population'))                
        else:
            self.listen('initial population')

    def add_to_simulation(self, agent):
        """
        Save the agent's name for future reference, add to network, assign
        a location, and add to grid queue.
        """
        self.agents[agent.attributes["NAME"]] = agent
        self.network.add_node(agent)
        
        #location
        agent.attributes["LOC"] = np.random.rand(1,2) # should be generic to dimensions
        agent.partition = self.partition(agent)
        if agent.partition is not self.rank:
            self.comm.send(('add_to_simulation',agent), dest = agent.partition)
        self.add_to_grid_queue(agent)
        
    def add_to_grid_queue(self, agent):
        """
        Find the appropriate grid queue for agent. Called by 
           1. Time Operator - when agent graduates to the next grid queue
           1.5 Time Operator - when relationship with removed is dissolved
           2. Relationship Operator - a relationship is dissolved
           3. Community - in make_population in the mainloop
        """
        grid_queue = [gq for gq in self.grid_queues.values() if gq.accepts(agent)][agent.sex]
        agent.grid_queue = grid_queue.my_index

        #check that agent in community boundaries
        if agent.partition is not self.rank:
            self.comm.send(('add_to_grid_queue',agent.attributes["NAME"]), dest = agent.partition)  # send to other community
            return
        
        self.pipes[agent.grid_queue].send("add")
        self.pipes[agent.grid_queue].send(agent)
        
    def listen(self, for_what, from_whom = 0):
        """
        Method for receiving messages from other communities and responding
        accordingly.
        """
        #print "v=== listen for",for_what,"| STARTED ON",self.rank,"|time",self.time,"===v"
        req = self.comm.irecv(dest = from_whom)  # data depends on msg
        while True:
            #continually check that a message was received
            flag, message = req.test()
            if not flag: continue
            msg, data = message
    	    #print "  > listening on",self.rank,"| msg:",msg,"data:",data
            if msg == 'done':
                break
            req = self.comm.irecv(dest = from_whom)  # listen for next message

            #parse message and act            
            if msg == 'add_to_simulation':
                agent = data  # data is agent object here
                self.agents[agent.attributes["NAME"]] = agent
            elif msg == 'add_to_grid_queue':
                agent = self.agents[data]  # data is agent name here
                self.add_to_grid_queue(agent)
            elif msg == 'remove':
                agent_name = data  # data is agent name here
               	agent = self.agents[agent_name]
                agent_pipe = self.pipes[agent.grid_queue]
                agent_pipe.send("remove")
                agent_pipe.send(agent_name)
            elif msg == 'add_relationship':
                relationship = data  # data is relationship tuple here
                agent1 = self.agents[relationship[0]]  # look up name
                agent2 = self.agents[relationship[1]]
                self.relationship_operator.form_relationship(agent1, agent2)
            elif msg == 'push':
                agent = data  # data is agent object here
                self.main_queue.push(agent.grid_queue, agent)
                    
        #print "^=== listen for",for_what,"| END on",self.rank,"|time",self.time,"======^" 
	#print

    def step(self):
        """
        Take a single time step (one week) in the simulation. 
        """
	    #1. Time progresses
        self.time_operator.step()
        
        #2. Form and dissolve relationships
        self.relationship_operator.step()
        
        #3. HIV transmission
        self.infection_operator.step()

    def make_operators(self):
        self.relationship_operator = OperatorsDistributed.RelationshipOperator(self)
        self.infection_operator = OperatorsDistributed.InfectionOperator(self)
        self.time_operator = OperatorsDistributed.TimeOperator(self)
            



