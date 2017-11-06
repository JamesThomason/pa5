import json
from collections import namedtuple, defaultdict, OrderedDict
from timeit import default_timer as time
from heapq import heappop, heappush

Recipe = namedtuple('Recipe', ['name', 'check', 'effect', 'cost'])
Rules = []
resources=['wood', 'cobble', 'coal', 'ore']
materials=['plank', 'ingot', 'stick', 'cart', 'rail']
tools = ["bench", "wooden_axe", "wooden_pickaxe", "stone_axe", "stone_pickaxe", "furnace", "iron_axe", "iron_pickaxe"]
ShoppingList = {}

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
    
    def heuristic(state):
        # Implement your heuristic here!
        if is_goal(state):
            return -100
        return 0
    
    return heuristic

def sub_heuristic(state, subgoal):
    #assume the goal will be met
    b = True
    #determine the conditions for a goal state
    items = subgoal.keys()
    #check each condition
    for item in items:
    #if a condition is broken, stop checking and return 0
        if state[item] < subgoal[item]:
            b = False
            break
    if b:
        return -100
    return 0
        

def search(graph, state, is_goal, limit, heuristic):

    start_time = time()

    # Implement your search here! Use your heuristic here!
    # When you find a path to the goal return a list of tuples [(state, action)]
    # representing the path. Each element (tuple) of the list represents a state
    # in the path and the action that took you to this state
    in_game_time=0
    queue = []
    parentState = {}        #binds a state to its parent state and action required to reach that state
    tools = ["bench", "furnace", "iron_axe", "iron_pickaxe", "stone_axe", "stone_pickaxe", "wooden_axe", "wooden_pickaxe"]
    parentState[state]=None
    queue.append((0, state, 0, 0))
    while time() - start_time < limit:
        if not queue:
            print("Queue Empty!")
            break
        else:
            dist, currentState, turn, game_time = heappop(queue)
            in_game_time+=game_time
            print(currentState)
            print("turn:",turn)
            queue=[]
            if is_goal(currentState):
                #print('found')
                #print (dist)
                print ("Compute Time: " + str(time()))
                print ("Game Time: {cost = " + str(in_game_time) + "} {len = " + str(turn) + "}")
                path = []
                path.append(( currentState, "End of Path") )
                while parentState[currentState] != None:
                    path.insert(0,parentState[currentState])
                    currentState = parentState[currentState][0]
                return path
            #get adjacent states
            for i in graph(currentState):
                move=True
                name, nextState, cost = i
                if not name:
                    break
                for material in nextState.keys():
                    if nextState[material]>8:
                        move=False
                    for tool in tools:
                        if tool in nextState.keys() and nextState[tool]>1:
                            move=False
                if move:
                    #heappush(queue, (cost+dist,nextState,turn+1))
                    parentState[nextState] = (currentState, name)
                    for j in graph(nextState):
                        nextName, nnextState, nextCost=j
                        if heuristic(nnextState)!=0:
                            print("trigger")
                            heappush(queue, (cost+dist+heuristic(nnextState)-50, nextState, turn+1, cost))
                    heappush(queue, (cost+dist+heuristic(nextState), nextState, turn+1, cost))
                    print ("Possible action: " + name)
                    print ("effect on inventory")
                    print (nextState)
            print ("")


    # Failed to find a path
    print(time() - start_time, 'seconds.')
    print("Failed to find a path from", state, 'within time limit.')
    return None

if __name__ == '__main__':
    with open('Crafting.json') as f:
        Crafting = json.load(f)

    #initialize shopping list
    order = tools.copy()
    order.extend(resources)
    order.extend(materials)

    ShoppingList = {key: 0 for key in order}
    print (ShoppingList)

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
    for name, rule in Crafting['Recipes'].items():
        Rules.append(rule)
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

    shopping_cart={}

    
    
    # Search for a solution
    resulting_plan = search(graph, state, is_goal, 30, heuristic)

    if resulting_plan:
        # Print resulting plan
        for state, action in resulting_plan:
            print('\t',state)
            print(action)
