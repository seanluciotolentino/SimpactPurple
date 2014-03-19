import numpy.random as random
import numpy as np
import simpactpurple
import OperatorsDistributed
import time as Time

class CommunityDistributed(simpactpurple.Community):

    def __init__(self, comm, primary, others, migration = False):
        simpactpurple.Community.__init__(self)
        #Distributed parameters
        self.comm = comm
        self.rank = comm.Get_rank()
        self.primary = primary
        self.is_primary = self.rank == primary
        self.others = others
        self.size = len(self.others) 
        self.migration = migration
        #print "checking in: rank",comm.Get_rank(),"primary",primary, "others",others,"migration",self.migration
        
        #MODEL PARAMETERS
        self.NUMBER_OF_YEARS = 30
        
        #MODEL OPERATORS
        #hazard
        self.preferred_age_difference = -0.1
        self.probability_multiplier = -0.2
        self.preferred_age_difference_growth = 0.1
        
        #relationship operator
        self.SEXES = 2
        self.MIN_AGE = 15
        self.MAX_AGE = 65
        self.BIN_SIZE = 5
        self.MAIN_QUEUE_MAX = 0.3  # proportion of initial population
        self.DURATIONS = lambda a1, a2: np.mean((self.age(a1),self.age(a2)))*10*random.exponential(5)  # scale*expo(shape)
        
        #infection operator
        self.INFECTIVITY = 0.01
        self.INTIIAL_PREVALENCE = 0.01  # while there's not infection operator...
        self.SEED_TIME = 0  # in years        

        #time operator
        self.time = -1  # initialization time
                
        #MODEL POPULATION
        self.INITIAL_POPULATION = 100
        self.AGENT_ATTRIBUTES = {}
        self.BORN = lambda: -52*random.uniform(self.MIN_AGE, self.MAX_AGE)
        self.SEX = lambda: random.randint(self.SEXES)
        self.DNP = lambda: random.power(0.1)*1.5  #power(shape)*scale
        
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
        if self.is_primary:
            simpactpurple.Community.make_population(self, size)
            if self.time < 0:
                self.broadcast(('done','making population')) 
                if self.migration:
                    self.comm.send(('done','making population'), dest = 0)
        else:
            self.listen('initial population', self.primary)

    def add_to_simulation(self, agent):
        """
        Save the agent's name for future reference, add to network, assign
        a location, and add to grid queue.
        """
        if type(agent.attributes["NAME"]) == type(0):
            agent.attributes["NAME"] = str(self.primary) + "-" + str(agent.attributes["NAME"])
        
        self.agents[agent.attributes["NAME"]] = agent
        self.network.add_node(agent)
        
        #location
        partitions = list(self.others)
        partitions.append(self.primary)  # only primary calls this so same as self.rank
        agent.partition = partitions[random.randint(len(partitions))]
        if agent.partition is not self.rank:
            self.comm.send(('add_to_simulation',agent), dest = agent.partition)
        if self.migration:  # and not a update add
            agent.attributes["MIGRATION"] = [(self.time, 0, self.rank)]
            self.comm.send(('add',agent), dest = 0)
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
        
    def listen(self, for_what, from_whom):
        """
        Method for receiving messages from other communities and responding
        accordingly.
        """
        #print "v=== listen for",for_what,"| FROM",from_whom,"ON",self.rank,"|time",self.time,"===v"
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
        #1. Proceede normally
        simpactpurple.Community.step(self)
            
        #2. Migration operations
        if not self.migration:
            return

        if self.is_primary:
            self.comm.send(('done','updating'), dest = 0)
            #print '-----primary',self.rank,'migration operations-----'
            self.migration = False  # temp disable 'add' and 'remove' messages to MO
            #0.1 Remove some agents (migrate away)
            removals = self.comm.recv(source = 0)
            #print self.rank,"  received removals:",[a.attributes["NAME"] for a in removals]
            for removed in removals:
                agent = self.agents[removed.attributes["NAME"]]
                self.time_operator.remove(agent)
                
            #0.2 Add some agents (migrate in)
            additions = self.comm.recv(source = 0)
            #print self.rank,"  received additions:",[a.attributes["NAME"] for a in additions]
            #iself.migration = False  # so 'add' message not sent to MO
            for agent in additions:
                self.add_to_simulation(agent)
                #print "    -",agent.attributes["NAME"],"in network:",agent in self.network
            self.migration = True
                        
            
            #0.3 finish
            self.broadcast(('done','migration updating'))
            #print '-----end migration operations----------'
        else:
            self.listen('migration updates', self.primary)
            
    def make_operators(self):
        self.relationship_operator = OperatorsDistributed.RelationshipOperator(self)
        self.infection_operator = OperatorsDistributed.InfectionOperator(self)
        self.time_operator = OperatorsDistributed.TimeOperator(self)