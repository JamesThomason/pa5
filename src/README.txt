README:
James Thomason
Simon

Search Approach:
The search uses a slightly modified A* that prunes the following actions and their paths:
	-redundant tools
	-item excess
	-goal item excess

Heursitic:
	The core heuristic for this program is the use of a priority list, which takes the goal and breaks them down into their components parts
down to the natural resources that make up all craftable items. Items that are further removed from the goal are given a lower priority, so the search
will prioritize making higher-order items when it can. It also takes note of tools that are required in the relevant recipes, and greatly favors paths that 
result in making those tools. 

Other Information:
	For completion, the search and heuristic handle some fringe cases to ensure efficiency