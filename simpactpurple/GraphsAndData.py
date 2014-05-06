"""
A module for creating descriptive graphs and extracting relavent data
from a Simpact object.
"""

import numpy as np
import networkx as nx
import matplotlib
import os
if os.popen("echo $DISPLAY").read().strip() == '':  # display not set
    matplotlib.use('Agg')
import matplotlib.pyplot as plt


def age_mixing_data(s):
    """
    Generates a scatter plot of male and female ages for each relationship
    formed. If *filename* is provided (string), the graph is saved to the
    file instead of displayed on the screen.
    """
    males = []
    females = []
    for r in s.relationships:
        #eventually need an if statement to not include homosexual relations
        if r[0].sex:
            male = r[1]
            female = r[0]
        else:
            female = r[1]
            male = r[0]

        time_since_relationship = s.time - r[2]
        males.append(((s.age(male)*52.0) - time_since_relationship)/52.0)
        females.append(((s.age(female)*52.0) - time_since_relationship)/52.0)

    return np.array([males, females])

def age_mixing_graph(s, filename=None):
    """
    Generates a scatter plot of male and female ages for each relationship
    formed. If *filename* is provided (string), the graph is saved to the
    file instead of displayed on the screen.
    """
    males, females = age_mixing_data(s)

    plt.ioff()
    fig = plt.figure()
    plt.scatter(males, females)
    plt.xlim(15, 65)
    plt.ylim(15, 65)
    plt.title("Age Mixing Scatter")
    plt.xlabel("Male Age")
    plt.ylabel("Female Age")
    if filename is None:
        plt.ion()
        plt.show(block=False)
    else:
        plt.savefig(filename)
        plt.close(fig)

def age_mixing_heat_graph(s, grid = 10, filename = None):
    """
    Generates a heat map of male and female ages for each relationship
    formed. Finer or coarser grain grid can be made by changing *grid*.
    If *filename* is provided (string), the graph is saved to the
    file instead of displayed on the screen.
    """
    boxes = np.zeros((grid, grid))
    maximum = s.MAX_AGE + 1
    minimum = s.MIN_AGE

    #Go through relationships and add 1.0 to the appropriate box
    for r in s.relationships:
        #eventually need an if statement to not include homosexual relations
        if r[0].sex:
            male = r[1]
            female = r[0]
        else:
            female = r[1]
            male = r[0]

        time_since_relationship = s.time - r[2]

        male_age_at_formation = (((s.age(male) * 52.0) - time_since_relationship) / 52.0)
        male_index = np.floor(((male_age_at_formation - minimum)/(maximum - minimum)) * grid)
        female_age_at_formation = (((s.age(female) * 52.0) - time_since_relationship) / 52.0)
        female_index = np.floor(((female_age_at_formation-minimum) / (maximum - minimum)) * grid)
        boxes[female_index][male_index] += 1.0

    boxes_max = max([max(row) for row in boxes])
    boxes = np.array([[value / boxes_max for value in row] for row in boxes])

    plt.ioff()
    fig = plt.figure()
    plt.pcolormesh(boxes)
    plt.colorbar()
    plt.title("Age Mixing HeatMap")
    plt.xlabel("Male Age Bins")
    plt.ylabel("Female Age Bins")
    if filename is None:
        plt.ion()
        plt.show(block=False)
    else:
        plt.savefig(filename)
        plt.close(fig)

def formation_hazard(a,b,c):
    """
    Generates an age mixing scatter for many relationships with random
    ages for partners colored by the hazard of formation.
    """
    #some graph parameters
    pop = 2000
    min_age = 15
    max_age = 65
    range_age = max_age - min_age

    #calculate some random age differences
    male_ages = (np.random.rand(pop)*range_age)+min_age
    female_ages = (np.random.rand(pop)*range_age)+min_age
    mean_age = ((male_ages+female_ages)/2) -15
    age_difference = female_ages-male_ages

    #hazard parameters (note: for factors lower -> narrower)
    #1)
#    baseline = 1
#    age_difference_factor = -0.2
#    mean_age_factor = -0.01
#    h = baseline*np.exp(age_difference_factor*age_difference + mean_age_factor*mean_age)

    #2) since age_difference = female_age - male_age, this is from male perspective
    preferred_age_difference = a#-0.1
    probability_multiplier = b#-0.1
    preferred_age_difference_growth = c#2

    top = abs(age_difference - (preferred_age_difference*preferred_age_difference_growth*mean_age) )
    h = np.exp(probability_multiplier * top)

    #3) (same as two)
#    preferred_age_difference = -0.5
#    probability_multiplier = -0.1
#    preferred_age_difference_growth = 0.9
#    age_difference_dispersion = -0.01
#    top = abs(age_difference - (preferred_age_difference * preferred_age_difference_growth * mean_age) )
#    bottom = preferred_age_difference * mean_age * age_difference_dispersion
#    h = np.exp(probability_multiplier * (top/bottom)  )

    #make graph
    plt.ion()
    plt.figure()
    plt.scatter(male_ages,female_ages,c=h)
    plt.colorbar()
    plt.xlim(15,65)
    plt.ylim(15,65)
    plt.title("Age Mixing Scatter Tester")
    plt.xlabel("Male Age")
    plt.ylabel("Female Age")

def formed_relations_data(s):
    """
    Returns a list of the number of relationships at every timestep.
    """
    num_weeks = min(s.time, int(np.ceil(52 * s.NUMBER_OF_YEARS)))
    relations = [0] * num_weeks
    for r in s.relationships:
        start = r[2]
        end = int(round(min((r[3]+1, num_weeks))))
        for t in range(start, end):
            relations[t] += 1
    
    return relations

def formed_relations_graph(s, filename = None):
    """
    Generates a plot of the number of relationships over time. If *filename* 
    is provided (string), the graph is saved to the file instead of displayed
    on the screen.
    """
    num_weeks = min(s.time,int(np.ceil(52*s.NUMBER_OF_YEARS)))
    relations = formed_relations_data(s)
    
    plt.ioff()
    fig = plt.figure()
    plt.plot(np.arange(0,num_weeks)/52.0,relations)
    plt.xlabel('Time (Years)')
    plt.ylabel('Number of relationships')
    plt.title('Formed Relations')
    if filename is None:
        plt.ion()
        plt.show(block=False)
    else:
        plt.savefig(filename)
        plt.close(fig)

def relations_graph(s, filename = None):
    """
    Makes a graph with a line for each relationship. This is an extremely
    slow graph. 
    """
    fig = plt.figure()
    
    #num_weeks = min(s.time, int(np.ceil(52 * s.NUMBER_OF_YEARS)))
    #relations = [0] * num_weeks
    for i, r in enumerate(s.relationships):
        start = r[2]
        end = r[3]
        plt.plot((i,i),(start,end))
    
    plt.xlabel('Relationship number')
    plt.ylabel('Time')
    plt.title('Formed Relations')

def infection_data(s):
    """
    Returns a list with total number of infections at every timestep. 
    """
    num_weeks = s.time
    counts = [0]*num_weeks
    agents = s.agents.values()
    for agent in agents:
        if agent.time_of_infection >= np.Inf: continue
        start = int(agent.time_of_infection)
        end = int(min(num_weeks, agent.attributes["TIME_REMOVED"]))
        for t in range(start, end):
            counts[t]+=1.0
    return counts

def population_data(s):
    """
    Returns a list with total number of individuals at every timestep.
    """
    num_weeks = s.time
    counts = [0]*num_weeks
    agents = s.agents.values()
    for agent in agents:
        start = max(0, agent.attributes["TIME_ADDED"])
        end = min(num_weeks,agent.attributes["TIME_REMOVED"])
        for t in range(start, end):
            counts[t]+=1.0
    return counts

def prevalence_data(s):
    """
    Returns a list with prevalence at every time step.
    """
    infections = np.array(infection_data(s))
    population = np.array(population_data(s))
    prevalence = infections / population
    return prevalence

def prevalence_graph(s, filename = None):
    """
    Generates a graph of prevalence over time. If *filename* is provided 
    (string), the graph is saved to the file instead of displayed on the 
    screen.
    """
    num_weeks = s.time
    prev = prevalence_data(s)
    
    plt.ioff()
    fig = plt.figure()
    plt.plot(np.arange(0,num_weeks)/52.0,prev)
    plt.ylim(0,np.max(prev)+0.1)
    plt.xlabel('Time (Years)')
    plt.ylabel('Prevalence (%)')
    plt.title('Prevalence')
    if filename is None:
        plt.ion()
        plt.show(block=False)
    else:
        plt.savefig(filename)
        plt.close(fig)

def demographics_data(s,time_granularity = 4,num_boxes = 7,box_size = 10):
    """
    Returns a list of lists, with the first dimension being time, the second
    dimension being age groups. User is able to specify *time_granularity*, 
    i.e. how often to sample,
    *box_size*, the size of age boxes, *num_boxes*, the number of age boxes to
    use.
    """
    data = []
    now = min(s.time,int(np.ceil(52*s.NUMBER_OF_YEARS))) #determine if we are at the end of the simulation or in the middle
    for t in range(0,now,time_granularity):
        demographic = [0]*num_boxes; #create an list with the number of slots we want

        #go through agents...
        agents = s.agents.values()
        for agent in agents:
            age = s.age(agent)*52;  #convert age to weeks
            age_at_t = age - now + t;

            if agent.attributes["TIME_ADDED"]>= t or agent.attributes["TIME_REMOVED"] <= t:
                continue  # skip if the agent wasn't born yet or has been removed
                
            if hasattr(s,'migration') and s.migration:
                #find nearest migration timestamp
                before_time = -np.inf
                before = None           
                for timestamp in agent.attributes["MIGRATION"]:
                    if timestamp[0] > before_time and timestamp[0] <= t:
                        before_time = timestamp[0]
                        before = timestamp

                #if didn't migrate here in most previous timestep
                if before[2] is not s.rank:
                    #print "time",t,"before",before,"migration",agent.attributes["MIGRATION"]
                    continue
                
                    

            age_at_t /= 52  # convert back to years
            level = min(num_boxes-1,int(np.floor( age_at_t / box_size)));
            demographic[level] += 1;  # ...and add them to their delineations level

        #add the delineations to the data
        data.append(demographic)
    return data

def demographics_graph(s,time_granularity = 4,num_boxes = 7,box_size = 10, filename = None):
    """
    Generates a graph of the demographic make-up of the population over time. 
    User is able to specify *time_granularity*, i.e. how often to sample,
    *box_size*, the size of age boxes, *num_boxes*, the number of age boxes to
    use. If *filename* is provided (string), the graph is saved to the 
    file instead of displayed on the screen.
    """
    num_weeks = min(s.time,int(np.ceil(52*s.NUMBER_OF_YEARS)))
    demographics = demographics_data(s,time_granularity,num_boxes,box_size)
    colors = ['b','g','r','c','m','y']
    bottom = [0]*len(demographics)
    plt.ioff()
    fig = plt.figure()
    legend = []
    for l in range(num_boxes):  # l -> level
        legend.append(str(l*box_size) + " - " + str((l+1)*box_size))
        data = [demographics[t][l] for t in range(len(demographics))]
        plt.bar(left = range(0, num_weeks ,time_granularity), height = data,
                bottom=bottom, width=time_granularity,
                color=colors[l%len(colors)], linewidth=0.0, zorder=0.0)
        bottom = [data[i] + bottom[i] for i in range(len(bottom))]

    #make the figure
    plt.xlim(0,num_weeks)
    plt.ylim(1,max(bottom))
    plt.xlabel("Time (weeks)")
    plt.legend(legend,title = 'Age Groups')
    plt.ylabel("Number (count)")
    plt.title("Demographics")
    if filename is None:
        plt.ion()
        plt.show(block=False)
    else:
        plt.savefig(filename)
        plt.close(fig)

def sexual_network_graph(s, layout = "spring", time = None, filename = None):
    """
    Generates the cumulative sexual network graph. *layout* specifies the way
    that the agents should be arranged ('spring','circular','bipartite')
    If *time* is provided, the sexual network at that time will be drawn. If
    *filename* is provided (string), the graph is saved to the file instead 
    of displayed on the screen.
    """
    #rebuild the graph for visualization
    if not time:
        time = s.NUMBER_OF_YEARS*52
    G = nx.Graph()
    for r in s.relationships:
        if time and not (r[2] < time and time < r[3]):  # start < time < end
            continue
        g = (["M","F"][r[0].sex], ["M","F"][r[1].sex])  # grab agent sexes
        G.add_edge(str(r[0].name)+g[0], str(r[1].name)+g[1])

    #get layout
    if layout == "spring":
        pos = nx.spring_layout(G)
    elif layout == "circular":
        pos = nx.circular_layout(G)
    elif layout == "bipartite":
        pos = {}
        male = 0
        female = 0
        spacing = 50
        for n in G.nodes():
            if "M" in n: 
                x = 0
                y = male
                male+=spacing
                pos[n] = (x,y)
            if "F" in n: 
                x = 10
                y = female
                female+=spacing
                pos[n] = (x,y)
    else:
        raise Exception("unknown layout:" + layout)

    colors = [['c','r'][int("M" in n)] for n in G.nodes()]
    
    plt.ioff()
    fig = plt.figure()
    nx.draw(G, pos, node_color = colors, node_size = 800)
    if filename is None:
        plt.ion()
        plt.show(block=False)
    else:
        plt.savefig(filename)
        plt.close(fig)
        
def relationship_durations(s, filename = None):
    """
    Generates a histogram of relationship durations in the simulation.
    """
    durations = [r[3]-r[2] for r in s.relationships]
    
    plt.ioff()
    fig = plt.figure()
    plt.hist(durations, normed = True)
    plt.xlabel("Relationship Duration (weeks)")
    plt.ylabel("Freqency (count)")
    plt.title("Relationship Durations")
    if filename is None:
        plt.ion()
        plt.show(block=False)
    else:
        plt.savefig(filename)
        plt.close(fig)

def gap_lengths(s, filename=None):
    """
    Generates a histogram of gap lengths (i.e. the time between relationships
    for individuals).
    
    NOTE: THIS FIRST PASS SOLUTION IS INCORRECT.  The gap length is the time
    between the most recently ended relationship and the start of the next.
    Currently it is just between the previous relationship and the start of 
    the next (the previous relationship isn't always the most recently ended)
    """
    gap_lengths = []
    for agent in s.agents.values():
        agent_relations = [(r[2],r[3]) for r in s.relationships if r[0] is agent or r[1] is agent]
        if not agent_relations:
            continue  # skip if this agent didn't have any relationships
        agent_relations.sort()
        gap_length = [agent_relations[i][0] - agent_relations[i-1][1] for i in range(1,len(agent_relations))]
        gap_lengths.append(sum(gap_length)/len(agent_relations))
        
    #plot it        
    plt.ioff()
    fig = plt.figure()
    plt.hist(gap_lengths)
    plt.xlabel("Gap Lengths (weeks)")
    plt.ylabel("Freqency (count)")
    plt.title("Gap Lengths")
    if filename is None:
        plt.ion()
        plt.show(block=False)
    else:
        plt.savefig(filename)
        plt.close(fig)
        
def partner_turnover_rate(s):
    """
    Calculates and returns the partner turnover rate of a simulation.
    """
    #1. Calc person years
    person_years = 0.0
    for agent in s.agents.values():
        removal = min(s.NUMBER_OF_YEARS*52, agent.attributes["TIME_REMOVED"])
        added = agent.attributes["TIME_ADDED"]
        person_years += max(0, (removal - added)/52.0)
        
    #2. Calculate number of relationships
    number_relationships = 2.0*len(s.relationships)
    
    #3. divide number of relationships by person years to get partners per year
    return number_relationships / person_years
    
def concurrency(s, time = None):
    """
    Calculates the point prevalence of concurrency in the sexual network. This
    is defined as the proportion of relationships in which at least one of the 
    partners is in an additional relationship. If *time* is provided, the 
    concurrency will be calculated for the sexual network for that time. The
    default time is the end of the simulation.
    """
    if not time:
        G = s.network
    else:  # rebuild the graph for the given timestep
        G = nx.Graph()
        for r in s.relationships:
            if time and not (r[2] < time and time < r[3]):  # start < time < end
                continue
            G.add_edge(r[0], r[1])
            
    #go through edges and see if it's a concurrent relationship
    concurrent = [1.0 for relationship in G.edges() \
        if G.degree(relationship[0]) > 1 or G.degree(relationship[1]) > 1]
    return sum(concurrent) / G.number_of_edges()
    
def total_lifetime_partners(s, filename = None):
    """
    Generates a heat map of male and female ages for each relationship
    formed. Finer or coarser grain grid can be made by changing *grid*.
    If *filename* is provided (string), the graph is saved to the 
    file instead of displayed on the screen.
    """
    boxes = np.zeros((20, 20))
    
    #Go through relationships and add 1 to the appropriate box
    for agent in s.agents.values():
        age = int(s.age(agent) / s.BIN_SIZE)
        partners = min(19, len([r for r in s.relationships if r[0] is agent or r[1] is agent]))
        boxes[partners][age] += 1.0

    boxes_max = max([max(row) for row in boxes])
    boxes = np.array([[value / boxes_max for value in row] for row in boxes])

    plt.ioff()
    fig = plt.figure()
    plt.pcolormesh(boxes)
    plt.colorbar()
    plt.title("Total Lifetime Partners")
    plt.xlabel("Age Bins")
    plt.ylabel("Total Partners")
    if filename is None:
        plt.ion()
        plt.show(block=False)
    else:
        plt.savefig(filename)
        plt.close(fig)
        
def intergenerational_sex_data(s, year = None):
    """
    Generates percentages of men and women 15-19 who have had intergenerational
    relationships. Inspired by 2008 SA Health Survey, used for validation 
    graphs.  Note: current implementation is slow and ugly, but intuitive. 
    """
    original_time = s.time  # place holder
    if year is not None:  # allow user to specify a year              
        s.time = year*52.0
        
    male_intergenerational = {0:0}
    male_generational = {0:0}
    female_intergenerational = {0:0}
    female_generational = {0:0}
    for agent in s.agents.values():
        if (s.age(agent)<15) or (s.age(agent) >= 20):
            continue  # only query < 20 y.o.

        if agent.sex:            
            female_intergenerational[agent] = 0.0
            female_generational[agent] = 0.0
        else:
            male_intergenerational[agent] = 0.0
            male_generational[agent] = 0.0  
        
        for r in s.relationships:  
            if r[0] is not agent and r[1] is not agent:
                continue
            if r[2] > s.time:  # happened after queried time
                continue
            
            if np.abs(s.age(r[0])-s.age(r[1])) >= 5:
                if agent.sex:            
                    female_intergenerational[agent] = 1.0
                else:
                    male_intergenerational[agent] = 1.0
            else:
                if agent.sex:            
                    female_generational[agent] = 1.0
                else:
                    male_generational[agent] = 1.0
    
    #post process tallies
    s.time = original_time 
    return (sum(male_generational.values())/len(male_generational),
            sum(male_intergenerational.values())/len(male_intergenerational),
            sum(female_generational.values())/len(female_generational),
            sum(female_intergenerational.values())/len(female_intergenerational) )

def number_of_partners_data(s, year = None):
    """
    Generates percentages of men and women who have had multiple partners in 
    the past 12 months. Inspired by 2008 SA Health Survey, used for validation 
    graphs.  Note: current implementation is slow and ugly, but intuitive. 
    """
    original_time = s.time  # place holder
    if year is not None:  # allow user to specify a year         
        s.time = year*52.0
        
    now = min(s.time,int(np.ceil(52*s.NUMBER_OF_YEARS))) 
    relationships = {}
    for agent in s.agents.values():  # for each agent...
        if agent.attributes["TIME_REMOVED"] < np.inf:
            continue
        #print "investigating agent", agent
        relationships[agent] = 0
        for r in s.relationships:  # ...go through and count relationships from the past year
            if r[0] is not agent and r[1] is not agent:
                continue
            if r[3] <= now-52 or r[2]> now:  #only relationships from past 12 months
                continue   
            #print "   relationship found", r[2],r[3]
            relationships[agent]+=1
    
    #post process tallies
    total = {i:0 for i in range(6)}
    positive = {i:0 for i in range(6)}
    for agent in relationships.keys():
        if s.age(agent)<24:
            age = 0
        elif s.age(agent)<50:
            age = 1
        else:
            age = 2
        group = age + (3*agent.sex)
        #print "sex",agent.sex,"age",s.age(agent), " group --> ", group, relationships[agent], "| total[group]", total[group], "positive[group]", positive[group]
        total[group]+=1.0
        positive[group]+=[0,1][relationships[agent]>1]
        
    s.time = original_time 
    #return positive/total for each group
    return [positive[i]/total[i] for i in range(6)]
        
def test_distribution(distribution, samplesize = 100):
    data = [distribution() for i in range(samplesize)]
    
    plt.hist(data, normed=True)
    plt.title("Test Distribution")
    plt.xlabel("Bins")
    plt.ylabel("Frequency")
    plt.show(block=False)

def network_metrics(s):
    print "Concurrency", concurrency(s)
    print "Partner Turnover Rate", partner_turnover_rate(s)
    print "Average Clustering", nx.algorithms.bipartite.average_clustering(s.network)
    print "Degree Assortivity", nx.degree_assortativity_coefficient(s.network)
    print "Average node connectivity", nx.average_node_connectivity(s.network)
    
    
