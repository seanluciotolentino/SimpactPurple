import Community

class CommunityMPI(Community.Community):
    """
    This particular Community object knows how to communicate with a Global 
    object via OpenMPI and run parallel to other CommunityMPI objects
    """
    
    def __init__(self, comm, Global):
        Community.Community.__init__(self)
        self.comm = comm
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
            
    def run(self):
        """
        Initialize data structures and begin the mainloop of the modified 
        Community: Each step receive updates from global, perform a step, then
        reply to Global with new changes to the system (new agents, 
        relationships, and infections).
        """
        self.start()
        self.time = 0
        end_of_simulation = int(self.NUMBER_OF_YEARS*52)-1
        while True:
            self.update()  # updates self.time
            self.step()
            self.reply()
            if self.time >= end_of_simulation:
                break
            
        self.cleanup()
        
    def update(self):
        """
        Receive updates from the global manager and react accordingly (add new
        agents, delete rejected relationships, etc.).
        """
        #handshake
        msg = self.comm.recv(source = 0)
        if msg != "update_start":
            raise Exception, "Didn't receive update_start from Global. Received: " + str(msg)
                
        #1. New agents (from deaths)
        new_agents = self.comm.recv(source = 0)
        for agent in new_agents:
            self.add(agent)
        
        #2. Relationships
        #2.1 Rejected Relationships
        rejected_relationships = self.comm.recv(source = 0)  # list of bad rela
        for r in rejected_relationships:
            a1, a2, start, stop = r
            agent1 = self.agents[a1.attributes["NAME"]]
            agent2 = self.agents[a2.attributes["NAME"]]
            self.relationship_operator.dissolve_relationship(agent1, agent2)
            self.relationships.remove((agent1,agent2,start,stop))
        self.num_relationships = len(self.relationships)
        
        #2.2 Relations formed for shared agents
        forming_agents = self.comm.recv(source = 0)
        for name in forming_agents:
            agent = self.agents[name]
            agent.dnp -= 1

        #2.3 Relations dissolved for shared agents
        dissolving_agents = self.comm.recv(source = 0)
        for name in dissolving_agents:
            agent = self.agents[name]
            agent.dnp += 1
        
        #3. New infections
        new_infections = self.comm.recv(source = 0)  # list of bad rela
        for name in new_infections:
            agent = self.agents[name]
            agent.time_of_infection=self.time
            
        #4. Get new time
        self.time = int(self.comm.recv(source = 0))
        
        msg = self.comm.recv(source = 0)
        if msg != "update_end":
            raise Exception, "Didn't receive update_end from Global. Received: " + str(msg)
        
    def reply(self):
        """
        Send reply to Global with information about events of this past round 
        (agent deaths, new relationships, etc.).
        """
        self.comm.send("reply_start", dest = 0)
        
        #1. Send agent deaths
        agent_deaths = [a for a in self.agents.values() if a.attributes["TIME_REMOVED"]==self.time]  # 1st pass solution
        self.comm.send(agent_deaths, dest = 0)
        
        #2.1 Formed relationships
        new_relationships = self.relationships[self.num_relationships:]
        self.comm.send(new_relationships, dest = 0)
        
        #2.2 Dissolved relationships
        old_relationships = [r for r in self.relationships if r[3] == self.time]
        self.comm.send(old_relationships, dest = 0)
        
        #3. Send agent deaths
        new_infections = [a for a in self.agents.values() if a.time_of_infection==self.time]  # 1st pass solution
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
        

    
        
        
