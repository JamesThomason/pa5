import json
from collections import namedtuple, defaultdict, OrderedDict
from timeit import default_timer as time
from heapq import heappop, heappush

Recipe = namedtuple('Recipe', ['name', 'check', 'effect', 'cost'])
resources=['wood', 'cobble', 'coal', 'ore']
materials=['plank', 'ingot', 'stick', 'cart', 'rail']
tools = ["bench", "wooden_axe", "wooden_pickaxe", "stone_axe", "stone_pickaxe", "furnace", "iron_axe", "iron_pickaxe"]

#fills out the priority list, which is used to push the search towards items that will reach will the goal
def make_priority_list(item, priority):
    #find the rule that produces the given item
    for rule in rules:
        if item in rule["Produces"]:
            #loop through its ingredients
            if "Consumes" in rule:
                for consumed in rule["Consumes"]:
                    #add it to the list. Items closer in the recipe tree to the goal get a higher priority
                    #if a material is found twice, put it at its loweset possible priority
                    if consumed not in priority_list or priority_list[consumed] < rule["Consumes"][consumed]:
                        priority_list[consumed] = priority + 1
                    #if its not a natural resource, recursively call this function to get the next level of ingredients
                    if consumed not in  resources:
                        make_priority_list(consumed, priority + 1)
            #also take note of tools required to make materials. These are given a much higher priority in the heuristic
            if "Requires" in rule:
                for tool in rule["Requires"]:
                    if tool not in priority_list:
                        priority_list[tool] = True
                        if tool == "furnace":
                            # Fringe case: Make a stone_pickaxe when making a furnace
                            priority_list["stone_pickaxe"] = True
            break
    pass

class State(OrderedDict):
    """ This class is a thin wrapper around an OrderedDict, which is simply a dictionary which keeps the order in
        which elements are added (for consistent key-value pair comparisons). Here, we have provided functionality
        for hashing, should you need to use a state as a key in another dictionary, e.g. distance[state] = 5. By
        default, dictionaries are not hashable. Additionally, when the state is converted to a string, it removes
        all items with quantity 0.

        Use of this state representation is optional, should you prefer another.
    """

    def __key(self):
        return tuple(self.items())

    def __hash__(self):
        return hash(self.__key())

    def __lt__(self, other):
        return self.__key() < other.__key()

    def copy(self):
        new_state = State()
        new_state.update(self)
        return new_state

    def __str__(self):
        return str(dict(item for item in self.items() if item[1] > 0))

def make_checker(rule):
    # Implement a function that returns a function to determine whether a state meets a
    # rule's requirements. This code runs once, when the rules are constructed before
    # the search is attempted.

    def check(state):
        b = True
        # This code is called by graph(state) and runs millions of times.
        # Tip: Do something with rule['Consumes'] and rule['Requires'].
        #if the state has the required materials for consumes and the required tools in requires
        if "Consumes" in rule:
            materials = rule["Consumes"].keys()
            for material in materials:
                if state[material] < rule["Consumes"][material]:
                    b = False
                    break
        if "Requires" in rule:
            tools = rule["Requires"].keys()
            if b:
                for tool in tools:
                    if state[tool] <= 0:
                        b = False
                        break
        return b

    return check


def make_effector(rule):
    # Implement a function that returns a function which transitions from state to
    # new_state given the rule. This code runs once, when the rules are constructed
    # before the search is attempted.

    #figure out limits for any given item
    if "Consumes" in rule:
        for limit in rule["Consumes"]:
            if limit != "wood":
                if limit not in consume_limit or consume_limit[limit] < rule["Consumes"][limit]:
                    consume_limit[limit] = rule["Consumes"][limit]

    def effect(state):
        # This code is called by graph(state) and runs millions of times
        # Tip: Do something with rule['Produces'] and rule['Consumes'].
        next_state = state.copy()
        #put the key-value pairs of Produces and Consumes in a single dict
        products = rule["Produces"].copy()
        #get updated values for each item in Produces
        for product in products:
            products[product] += state[product]
        #update next_state to reflect those changes
        next_state.update(products)
        #repeat for Consumes
        if "Consumes" in rule:
            costs = rule["Consumes"].copy()
            for cost in costs:
                costs[cost] = state[cost]-costs[cost]
            next_state.update(costs)
        return next_state

    return effect


def make_goal_checker(goal):
    # Implement a function that returns a function which checks if the state has
    # met the goal criteria. This code runs once, before the search is attempted.

    #Fringe case: force make an iron_pickaxe when making more than 16 rails
    if "rail" in goal.keys():
        if goal["rail"] > 16:
            priority_list["iron_pickaxe"] = True
    #Fringe case: Add stone_pickaxe to the priority list if the goal itself is a furnace
    if "furnace" in goal.keys():
        priority_list["stone_pickaxe"] = True

    def is_goal(state):
        #assume the goal will be met
        b = True
        #determine the conditions for a goal state
        items = goal.keys()
        #check each condition
        for item in items:
            #if a condition is broken, stop checking and return false
            if state[item] < goal[item]:
                b = False
                break
        return b

    return is_goal


def graph(state):
    # Iterates through all recipes/rules, checking which are valid in the given state.
    # If a rule is valid, it returns the rule's name, the resulting state after application
    # to the given state, and the cost for the rule.
    for r in all_recipes:
        if r.check(state):
            yield (r.name, r.effect(state), r.cost)

def make_heuristic(goal):
    # Makes the heuristic function to prioritize the goal if it's the next move
    def heuristic(currState, nextState):
        value = 0
        # Implement your heuristic here!
        #search through the priority list
        for item in priority_list:
            #if the proposed action results in the creation of a priority item, bump it up in the queue relative to how
            #close it is to the goal
            if item in materials or item in resources:
                if nextState[item] > currState[item] and nextState[item]:
                    value -= (30/priority_list[item])
            #Favor actions that result in a required tool, and favor all the sub_actions
            else:
                if nextState[item] == 1 or currState[item] == 1:
                    value -= 1000
        #Fringe case: The algorithm like to collect a cobble after making a furnace instead of coal. We tell it to knock
        #that off
        if currState["furnace"] == 1 and currState["stone_pickaxe"] == 1 and nextState["cobble"] > currState["cobble"]:
            value += 100
        #if the proposed action results in fulfilling part of the goal, favor that and all its children's actions
        for g in goal.keys():
            if nextState[g] > currState[g] or currState[g] > 0:
                value -= 1000

        return value
    
    return heuristic

def search(graph, state, is_goal, limit, heuristic, goals):

    start_time = time()

    #Figure out which items will be relevant for the goal
    for goal in goals:
        make_priority_list(goal, 0)

    # Implement your search here! Use your heuristic here!
    # When you find a path to the goal return a list of tuples [(state, action)]
    # representing the path. Each element (tuple) of the list represents a state
    # in the path and the action that took you to this state
    in_game_time=0
    state_count = 0         #tracks how many states we traversed in the search
    distances = {}          #tracks the cost so far of a path for each node
    queue = []              #minheap priority queue
    parentState = {}        #binds a state to its parent state and action required to reach that state
    parentState[state]=None #tracks parent nodes for path building
    distances[state] = 0
    queue.append((0, state, 0, 0))
    while time() - start_time < limit:
        state_count += 1
        #Dequeue
        priority, currentState, turn, game_time = heappop(queue)
        #update cost
        in_game_time += game_time
        curr_dist = distances[currentState]
        #if we're at the goal, stop and print time data, then return the path
        if is_goal(currentState):
            print ("Compute Time: " + str(time()))
            print ("Game Time: {cost = " + str(distances[currentState]) + "} {len = " + str(turn) + "}")
            print ("States Visited: " + str(state_count))
            path = []
            path.append(( currentState, "End of Path") )
            while parentState[currentState] != None:
                path.insert(0,parentState[currentState])
                currentState = parentState[currentState][0]
            return path
        #get adjacent states
        for i in graph(currentState):
            #assume we want to go down this path
            move = True
            name, nextState, cost = i
            if not name:
                break
            #check the properties of the resulting state
            for material in nextState.keys():
                #if we end up making more of any item than we'll ever need, ignore this path
                if material in consume_limit:
                    if currentState[material] >= consume_limit[material] and nextState[material] > currentState[material]:
                        move = False
                        break
                #if we end up making more than an arbitrary amount of wood, ignore this path
                elif nextState[material] > 8 and material not in goals:
                    move = False
                    break
                #if we end up making more than one of any tool, ignore this path
                for tool in tools:
                    if tool in nextState.keys() and nextState[tool] > 1:
                        move = False
                        break
                #if we end up making more of a goal item than we need, ignore this path
                if material in goals:
                    if nextState[material] > currentState[material] and currentState[material] >= goals[material]:
                        move = False
                        break
            #if this is a path worth considering, add it to the queue
            if move:
                pathcost = curr_dist + cost
                if nextState not in distances or pathcost < distances[nextState]:
                    distances[nextState] = pathcost
                    parentState[nextState] = (currentState, name)
                    adjusted_cost = pathcost + heuristic(currentState, nextState)
                    heappush(queue, (adjusted_cost, nextState, turn + 1, cost))
        print ("")


    # Failed to find a path
    print(time() - start_time, 'seconds.')
    print("Failed to find a path from", state, 'within time limit.')
    return None

if __name__ == '__main__':
    with open('Crafting.json') as f:
        Crafting = json.load(f)

    # # List of items that can be in your inventory:
    # print('All items:', Crafting['Items'])
    #
    # # List of items in your initial inventory with amounts:
    # print('Initial inventory:', Crafting['Initial'])
    #
    # # List of items needed to be in your inventory at the end of the plan:
    # print('Goal:',Crafting['Goal'])
    #
    # # Dict of crafting recipes (each is a dict):
    # print('Example recipe:','craft stone_pickaxe at bench ->',Crafting['Recipes']['craft stone_pickaxe at bench'])

    # Build rules
    all_recipes = []
    consume_limit = {}          #tracks the maximum amount of any item other than wood needed for any recipe
    priority_list = {}          #determines which items we'll want to make to reach the goal
    rules = []                  #gathers the rules for making the priority list
    for name, rule in Crafting['Recipes'].items():
        rules.append(rule)
        checker = make_checker(rule)
        effector = make_effector(rule)
        recipe = Recipe(name, checker, effector, rule['Time'])
        all_recipes.append(recipe)

    # Create a function which checks for the goal
    is_goal = make_goal_checker(Crafting['Goal'])

    # Initialize first state from initial inventory
    state = State({key: 0 for key in Crafting['Items']})

    state.update(Crafting['Initial'])

    # Makes heuristic
    heuristic = make_heuristic(Crafting['Goal'])

    # Search for a solution
    resulting_plan = search(graph, state, is_goal, 30, heuristic, Crafting['Goal'])

    if resulting_plan:
        # Print resulting plan
        for state, action in resulting_plan:
            print('\t',state)
            print(action)
