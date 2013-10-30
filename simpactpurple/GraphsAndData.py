"""
A module for creating descriptive graphs and extracting relavent data
from a Simpact object.
"""

import math
import numpy as np
import networkx as nx
import matplotlib
import os 
if os.popen("echo $DISPLAY").read().strip() == '':  # display not set
    matplotlib.use('Agg')
import matplotlib.pyplot as plt


def age_mixing_graph(s, filename = None):
    """
    Generates a scatter plot of male and female ages for each relationship
    formed. If *filename* is provided (string), the graph is saved to the 
    file instead of displayed on the screen.
    """
    males = []
    females = []
    for r in s.relationships:
        #eventually need an if statement to not include homosexual relations
        if r[0].gender:
            male = r[1]
            female = r[0]
        else:
            female = r[1]
            male = r[0]

        
        time_since_relationship = s.time - r[3]
        males.append(((s.age(male)*52.0) - time_since_relationship)/52.0)
        females.append(((s.age(female)*52.0) - time_since_relationship)/52.0)

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
        if r[0].gender:
            male = r[1]
            female = r[0]
        else:
            female = r[1]
            male = r[0]

        time_since_relationship = s.time - r[3]

        male_age_at_formation = (((s.age(male) * 52.0) - time_since_relationship) / 52.0)
        male_index = math.floor(((male_age_at_formation - minimum)/(maximum - minimum)) * grid)
        female_age_at_formation = (((s.age(female) * 52.0) - time_since_relationship) / 52.0)
        female_index = math.floor(((female_age_at_formation-minimum) / (maximum - minimum)) * grid)
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

def formation_hazard():
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
#    preferred_age_difference = -0.5
#    probability_multiplier = -0.1
#    preferred_age_difference_growth = 1
#
#    top = abs(age_difference - (preferred_age_difference*preferred_age_difference_growth*mean_age) )
#    h = np.exp(probability_multiplier * top)

    #3) (same as two)
    preferred_age_difference = -0.5
    probability_multiplier = -0.1
    preferred_age_difference_growth = 0.9
    age_difference_dispersion = -0.01
    top = abs(age_difference - (preferred_age_difference * preferred_age_difference_growth * mean_age) )
    bottom = preferred_age_difference * mean_age * age_difference_dispersion
    h = np.exp(probability_multiplier * (top/bottom)  )

    #make graph
    fig = plt.figure()
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
    num_weeks = min(s.time, int(math.ceil(52 * s.NUMBER_OF_YEARS)))
    relations = [0] * num_weeks
    for r in s.relationships:
        start = r[2]
        end = min((r[3]+1, num_weeks))
        for t in range(start, end):
            relations[t] += 1
    
    return relations

def formed_relations_graph(s, filename = None):
    """
    Generates a plot of the number of relationships over time. If *filename* 
    is provided (string), the graph is saved to the file instead of displayed
    on the screen.
    """
    num_weeks = min(s.time,int(math.ceil(52*s.NUMBER_OF_YEARS)))
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

def infection_data(s):
    """
    Returns a list with total number of infections at every timestep. 
    """
    num_weeks = min(s.time,int(math.ceil(52*s.NUMBER_OF_YEARS)))
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
    num_weeks = min(s.time,int(math.ceil(52*s.NUMBER_OF_YEARS)))
    counts = [0]*num_weeks
    agents = s.agents.values()
    for agent in agents:
        start = agent.attributes["TIME_ADDED"]
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
    num_weeks = min(s.time,int(math.ceil(52*s.NUMBER_OF_YEARS)))
    prev = prevalence_data(s)
    
    plt.ioff()
    fig = plt.figure()
    plt.plot(np.arange(0,num_weeks)/52.0,prev)
    plt.ylim(0,1)
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
    now = min(s.time,int(math.ceil(52*s.NUMBER_OF_YEARS))) #determine if we are at the end of the simulation or in the middle
    for t in range(0,now,time_granularity):
        demographic = [0]*num_boxes; #create an list with the number of slots we want

        #go through agents...
        agents = s.agents.values()
        for agent in agents:
            age = s.age(agent)*52;  #convert age to weeks
            age_at_t = age - now + t;

            if (agent.attributes["TIME_ADDED"]>= t or agent.attributes["TIME_REMOVED"] <= t):
                continue  # skip if the agent wasn't born yet or has been removed

            age_at_t /= 52  # convert back to years
            level = min(num_boxes-1,int(math.floor( age_at_t / box_size)));
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
    num_weeks = min(s.time,int(math.ceil(52*s.NUMBER_OF_YEARS)))
    demographics = demographics_data(s,time_granularity,num_boxes,box_size)
    colors = ['b','g','r','c','m','y']
    bottom = [0]*len(demographics)
    plt.ioff()
    fig = plt.figure()
    legend = []
    for l in range(num_boxes):
        legend.append(str(l*box_size) + " - " + str((l+1)*box_size))
        data = []
        for t in range(len(demographics)):
            data.append(demographics[t][l])
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
    G = nx.Graph()
    for r in s.relationships:
        if time and not (r[2] < time and time < r[3]):  # start < time < end
            continue
        g = (["M","F"][r[0].gender], ["M","F"][r[1].gender])  # grab agent genders
        G.add_edge(str(r[0].attributes["NAME"])+g[0], str(r[1].attributes["NAME"])+g[1])

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
