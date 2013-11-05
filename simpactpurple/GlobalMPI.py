import Agent
import numpy as np
import random

class UpdateReplyStruct:
    """
    Structure for holding relevant information for updating and replying
    """
    
    def __init__(self, Global):
        self.Global = Global
        self.clear()
        
    def clear(self):
        #1. New Agents
        self.agent_deaths = {c:[] for c in self.Global.communities}
        self.new_agents = {c:[] for c in self.Global.communities}  # not used

        #2. Relationships
        self.formed_relationships = {}
        self.dissolved_relationships = {}
        self.rejected_relationships = {c:[] for c in self.Global.communities}        

        #3. Infections
        self.new_infections = {}
        self.infected_agents = {c:[] for c in self.Global.communities} 

class Global:
    """
    The Global class is reponsible for generating the initial population as well
    as dealing with communication and syncing between communities. Each time
    step the Global object sends updates to communities, receives replies, and
    processes the replies for the next rounds updates.
    """
    
    def __init__(self, comm, population):        
        #global specific 
        self.comm = comm
        self.communities = range(1,comm.Get_size())
        self.number_agents = 0  # needed for replacement
        
        #MODEL PARAMETERS
        self.NUMBER_OF_YEARS = 30

        #MODEL POPULATION
        self.INITIAL_POPULATION = population
        self.AGENT_ATTRIBUTES = {}
        self.born = lambda: -52*random.uniform(self.MIN_AGE, self.MAX_AGE)
        self.gender = lambda: random.randint(0, self.GENDERS - 1)
        self.dnp = lambda: random.randint(1, 3)
        
        #MODEL OPERATORS
        #relationship operator
        self.GENDERS = 2
        self.MIN_AGE = 15
        self.MAX_AGE = 65
        self.BIN_SIZE = 5
        self.MAIN_QUEUE_MAX = 0.1  # proportion of initial population
        
        #infection operator
        self.INFECTIVITY = 0.01
        self.INTIIAL_PREVALENCE = 0.01
        self.SEED_TIME = 0 # in years        
        
        #time operator
        self.TIME = 0
            
    def run(self):
        """
        Initialize the population and start the mainloop.
        """
        #Initialize structure for updates and replies
        UpdateReply = UpdateReplyStruct(self)
        self.make_population(self.INITIAL_POPULATION, UpdateReply)
        self.born = lambda: self.TIME - (52*15.02)  # new born function
    
        #mainloop:
        for t in range(int(self.NUMBER_OF_YEARS*52)):
            #0. Housekeeping
            print "===================",t,"======================"
            self.TIME = t
            random.shuffle(self.communities)  # don't give preferences            
            
            #1. Send "updates" to communities
            self.updates(UpdateReply)
                
            #2. Wait for "reply" from communities
            self.replies(UpdateReply)
                
            #3. Process replies
            self.process(UpdateReply)
            
            #4. Do migration procedures
            self.perform_migration(UpdateReply)

    def updates(self, UpdateReply):
        """
        Send updates to the communities: (1) new agents to be added, (2) relationships
        that were rejected and agents which need to adjust their preferences in
        the community, (3) new infections which occured.
        """
        for c in self.communities:
            #0. Handshake
            self.comm.send("update_start", dest = c)

            #1. New Agents
            self.comm.send(UpdateReply.new_agents[c])  
            
            #2. Relationships
            self.comm.send(UpdateReply.rejected_relationships[c], dest = c)
            self.comm.send(UpdateReply.formation_agents[c], dest = c)
            self.comm.send(UpdateReply.dissolution_agents[c], dest = c)
            
            #3. Infections
            self.comm.send(UpdateReply.infected_agents[c], dest = c)

            #4. Housekeeping / handshake
            self.comm.send(self.TIME, dest = c)            
            self.comm.send("update_end", dest = c)            
        UpdateReply.clear()
            
    def replies(self, UpdateReply):
        """
        Receive new agent, relationships, and infections information from the 
        communities and store them in the UpdateReply struct.
        """
        for c in self.communities:
            #0. Handshake
            if self.comm.recv(source = c) != "reply_start":
                raise Exception,"Community "+str(c)+" not replying correctly"

            #1. Agent Deaths
            UpdateReply.agent_deaths[c] = self.comm.recv(source = c)

            #2. Relationships
            UpdateReply.formed_relationships[c] = self.comm.recv(source = c)
            UpdateReply.dissolved_relationships[c] = self.comm.recv(source = c)

            #3. Infections
            UpdateReply.new_infections[c] = self.comm.recv(source = c)

            #4. Handshake
            if self.comm.recv(source = c) != "reply_end":
                raise Exception,"Community "+str(c)+" not replying correctly"
            
    def process(self, UpdateReply):
        """
        Process the replies from the communities into updates.
        """
        successful = []    
        all_deaths = []        
        for c in self.communities:
            #1. Agent deaths
            agents = list(UpdateReply.agent_deaths[c])
            for agent in agents:
                agent_name = agent.attributes["NAME"]
                #if statement checks for agent in multiple communities
                if agent_name not in all_deaths:
                    all_deaths.append(agent_name)
                else:
                    UpdateReply.agent_deaths[c].remove(agent)
            self.make_population(len(UpdateReply.agent_deaths[c], UpdateReply))
        
            #2. New Relationss
            UpdateReply.rejected_relationships[c] = []
            this_successful = []  # don't check against sucessful from this community
            for r in UpdateReply.formed_relationships[c]:
                agent1 = r[0].attributes["NAME"]
                agent2 = r[1].attributes["NAME"]
                if agent1 in successful or agent2 in successful:
                    #2.1 Reject some relationships
                    UpdateReply.rejected_relationships[c].append(r)
                else:
                    this_successful.append(agent1)
                    this_successful.append(agent2)
                    
                    #2.2 Add agent to formation agents
                    #agent1
                    agent_communities = self.communities_for(agent1)
                    agent_communities.remove(c)
                    for a_c in agent_communities:
                        UpdateReply.formation_agents[a_c].append(agent1)
                    #agent2
                    agent_communities = self.communities_for(agent2)
                    agent_communities.remove(c)
                    for a_c in agent_communities:
                        UpdateReply.formation_agents[a_c].append(agent2)
            successful+=this_successful

            #2.3 Dissolved agents
            for r in UpdateReply.dissolved_relationships[c]:
                agent1 = r[0].attributes["NAME"]
                agent2 = r[1].attributes["NAME"]

                agent_communities = self.communities_for(agent1)
                agent_communities.remove(c)
                for a_c in agent_communities:
                    UpdateReply.dissolution_agents[a_c].append(agent)
                
                agent_communities = self.communities_for(agent2)
                agent_communities.remove(c)
                for a_c in agent_communities:
                    UpdateReply.dissolution_agents[a_c].append(agent)
            
            #3. New Infections
            for agent in UpdateReply.new_infections[c]:
                agent_communities = self.communities_for(agent)
                agent_communities.remove(c)
                for a_c in agent_communities:
                    UpdateReply.infected_agents[a_c].append(agent)
                    
    def perform_migration(self, UpdateReply):
        """
        Move agents into different communities based on some migration model.
        """
        pass  # not yet implemented

    def make_population(self, size, UpdateReply):
        """
        Creates *size* agents with age, gender, and desired number of partners
        (DNP) dictated by *born*, *gender*, and *dnp* (functions). If these 
        these are omitted, default distributions will be used.

        After an agent receives a name, age, gender, and DNP, he or she is added
        to the network graph and added to a grid queue.
        """
        AGENT_ATTRIBUTES = {}
        AGENT_ATTRIBUTES["TIME_ADDED"] = self.TIME
        AGENT_ATTRIBUTES["TIME_REMOVED"] = np.Inf
        
        #actually make the agents and send to communities
        for i in range(size):
            #make agent and add some attributes
            a = Agent.Agent(AGENT_ATTRIBUTES.copy())
            a.attributes["NAME"] = self.number_agents
            self.number_agents+=1
            a.born = self.born()
            a.gender = self.gender()
            a.dnp = self.dnp()
            
            #flip coin for initial infected
            if size>1 and random.random() < self.INTIIAL_PREVALENCE:
                #print "agent",a,"initial infected at",self.SEED_TIME*52
                a.time_of_infection = self.SEED_TIME*52
            
            #location
            a.attributes["LOC"] = np.random.rand(1,2)*10
            for c in self.communities_for(a):
                #self.comm.send(a, dest = c)
                UpdateReply.new_agents[c].append(a)
                
    def communities_for(self, agent):
        """
        An ad-hoc, first pass at community assignment
        """
        x = agent.attributes["LOC"][0][0]
        y = agent.attributes["LOC"][0][1]
        
        communities = []    
        if y < 4:
            communities += [3]
        elif y < 6:
            communities += [1,3]
        else:
            communities += [1]
            
        #shift communities if to the right
        if x > 5:
            communities = [c+1 for c in communities]
        return communities

