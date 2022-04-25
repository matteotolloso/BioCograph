from genericpath import exists
from platform import node
import networkx as nx
from itertools import combinations
import matplotlib.pyplot as plt
from queue import PriorityQueue
from tabulate import tabulate

from sqlalchemy import desc, false
from dataset_class import Dataset

class Cograph:

    def __init__(self) -> None:
        self._nxGraph = nx.Graph()
    
    
    def add_dataset(self, 
                    dataset : 'Dataset', 
                    rn=False,
                    mh=False,
                    ot=False,
                    bbent=True,
                    bbent_types = 'all',
                    alw_pres=[] # TODO remove?
                    ) -> None:
    
        papers = dataset.get_list()

        for paper in papers:
            terms = [] # list of touples (name, type)
            # extract the types of terms required
            if mh:
                terms += (paper.get('MeSH'), 'unknown')
            if rn:
                terms += (paper.get('RNnumber'), 'unknown')
            if ot:
                terms += (paper.get('OtherTerm'), 'unknown')
            if bbent:
                ents = paper.get('bioBERT_entities') #list of touples (name, type)
                for ent in ents:
                    if (bbent_types == 'all') or(ent[0] in alw_pres)  or (bbent_types.get(ent[1]) ):
                        terms.append(ent)

            terms = list(set(terms))
            
            #TODO attenzione in questo modo alcuni sinonimi vengono esclusi ?
                        
            if not terms:
                continue
            
            for a, b in list(combinations(terms, 2)):
                
                #add a node if not already in the graph, but if the node is already in the graph but with another type, 
                #add also there is a problem with the type of the node

                if (not self._nxGraph.has_node(a[0])):
                    self._nxGraph.add_node(a[0], weight=paper['weight'], type=a[1])
                else:
                    self._nxGraph.nodes[a[0]]['weight'] += paper['weight']
                    if self._nxGraph.nodes[a[0]]['type'] != a[1] :
                        print('inconsistency detected:', a[0], 'has type', self._nxGraph.nodes[a[0]]['type'], 'while', a[0], 'has type', a[1])
                
                if (not self._nxGraph.has_node(b[0])):
                    self._nxGraph.add_node(b[0], weight=paper['weight'], type=b[1])
                else:
                    self._nxGraph.nodes[b[0]]['weight'] += paper['weight']
                    if self._nxGraph.nodes[b[0]]['type'] != b[1] :
                        print('inconsistency detected:', b[0], 'has type', self._nxGraph.nodes[b[0]]['type'], 'while', b[0], 'has type', b[1])
                
                if self._nxGraph.has_edge(a[0], b[0]):
                    self._nxGraph[a[0]][b[0]]['capacity'] += paper['weight']
                else:
                    self._nxGraph.add_edge(a[0], b[0], capacity=paper['weight'])

    def draw(self, showing_nodes : 'list[str]' = [], node_colors : dict = {}) -> None:
    
        fig, ax = plt.subplots(figsize=(17, 12))

        graph_to_draw = self._nxGraph.subgraph(showing_nodes)
        
        #layout
        pos = nx.spring_layout(graph_to_draw, weight='capacity', seed=1)
        #pos = nx.shell_layout(graph,rotate=15, nlist=[[n for n in main_nodes], [n for n in hilight if n not in main_nodes], [n for n in graph.nodes if n not in main_nodes and n not in hilight]])
        #pos = nx.nx_agraph.graphviz_layout(graph)
        #pos = nx.nx_pydot.pydot_layout(graph)

        #edges
        edge_colors = ['gray' for u, v in graph_to_draw.edges()]
        
        edgewidth = [graph_to_draw[u][v]['capacity'] for u, v in graph_to_draw.edges()]
        maxi = max(edgewidth)
        edgewidth = list(map( lambda x : 50.0 * (x/float(maxi)), edgewidth))
        nx.draw_networkx_edges(graph_to_draw, pos, alpha=0.3, width=edgewidth, edge_color=edge_colors)
        
        #nodes

        nodesize = [ (graph_to_draw.nodes[v]['weight']* 2) for v in graph_to_draw.nodes()]
        maxi = max(nodesize)
        nodesize = list(map( lambda x : 7000.0 * x/float(maxi), nodesize))
        
        node_colors = [node_colors[n] for n in graph_to_draw.nodes()] # transform dict into list
        nx.draw_networkx_nodes(graph_to_draw, pos, node_size=nodesize, node_color=node_colors, alpha=0.9)
        
        label_options = {"ec": "k", "fc": "white", "alpha": 0.5}
        nx.draw_networkx_labels(graph_to_draw, pos, font_size=10, bbox=label_options)
        

        # Title/legend
        font = {"color": "k", "fontweight": "bold", "fontsize": 15}
        title : str = "title"
        ax.set_title(title, font)


        # Resize figure for label readibility
        ax.margins(0.1, 0.05)
        fig.tight_layout()
        plt.axis("off")

    def widest_path(self, src, target, bbent_types = 'all') -> 'list[str]':

        if self._nxGraph.has_node(src) and self._nxGraph.has_node(target):
            type1 = self._nxGraph.nodes[src]['type']
            type2 = self._nxGraph.nodes[target]['type']
            if ( not bbent_types.get(type1)) or (not bbent_types.get(type2)):
                print('impossible to find a path between', src, 'and', target, 'that passes only through', bbent_types,\
                'because', src, 'has type', type1, 'and', target, 'has type', type2)
                return []
                
        # To keep track of widest distance
        widest  = {}
        for key in self._nxGraph.nodes():
            widest[key] = -10**9
        
        # To get the path at the end of the algorithm
        parent = {}
    
        # Use of Minimum Priority Queue to keep track minimum
        # widest distance vertex so far in the algorithm
        pri_queue = PriorityQueue()
        pri_queue.put((0, src))
        widest[src] = 10**9
        while (not pri_queue.empty()):

            current_src = pri_queue.get()[1] # second element of the tuple

            neighbors = []
            
            try:
                neighbors = self._nxGraph.neighbors(current_src)
            except:
                print('path not found between', src, 'and', target)
                return []
            
            if bbent_types != 'all':
                # at least one neighbor must have the type wanted, otherwise a path does not exist for me
                exists = False
                for neighbor in neighbors:
                    if  bbent_types.get( self._nxGraph.nodes[neighbor]['type'] ) : # if node type is in the wanted types
                        exists = True
                        break
                if not exists:
                    print('path not found between', src, 'and', target, 'through only', bbent_types)
                    return []

            for vertex in neighbors:

                if(not bbent_types.get( self._nxGraph.nodes[vertex]['type'] ) ): # if node type is not in the wanted types
                    continue # skip this neighbor


                # Finding the widest distance to the vertex
                # using current_source vertex's widest distance
                # and its widest distance so far
                width = max(widest[vertex], min(widest[current_src], self._nxGraph[current_src][vertex]['capacity']))
    
                # Relaxation of edge and adding into Priority Queue
                if (width > widest[vertex]):
    
                    # Updating bottle-neck distance
                    widest[vertex] = width
    
                    # To keep track of parent
                    parent[vertex] = current_src
    
                    # Adding the relaxed edge in the priority queue
                    # greater width -> greater priority -> lower value
                    pri_queue.put((width * -1, vertex))

        current = target
        path = []
        while current != src:
            path.append(current)
            try:
                current = parent[current]
            except:
                print('path not found between', src, 'and', target)
                return []

        path.append(src)
        path.reverse()

        return path 
    
    def widest_set(self, endpoints : 'list[str]', bbent_types = 'all' ) -> 'list[str]':
        if len(endpoints) == 1:
            
            if (bbent_types != 'all') and (not bbent_types.get(self._nxGraph.nodes[endpoints[0]]['type'])):
                print(endpoints[0], 'has type', self._nxGraph.nodes[endpoints[0]]['type'], 'and is not in the wanted types', bbent_types)
                return []
            
            return endpoints
        
        
        if len(endpoints) <= 0:
            return []

        widest_set = []
        for u, v in combinations(endpoints, 2):
            widest_set += self.widest_path(u, v, bbent_types=bbent_types)
        widest_set = list(set(widest_set))
        return widest_set
    
    def get_neighbors(self, nodes_from : 'list[str]', max : int, bbent_types = 'all') -> 'list[str]':
        if max <= 0:
            return []

        neighbors = []
        for node in nodes_from: # for all nodes
            curr_neighbors = self._nxGraph.neighbors(node) # get all neighbors
            for n in curr_neighbors:
                if bbent_types == 'all' or bbent_types.get( self._nxGraph.nodes[n]['type'] ): # add to list if type is in wanted types
                    neighbors.append(n)

        neighbors = list(set(neighbors))
       
        if len(neighbors) > max:
            node_importance = [(n, self._nxGraph.nodes[n]['weight']) for n in neighbors]
            node_importance.sort(key=lambda tup: tup[1], reverse = True) # sort by importance
            neighbors = [tup[0] for tup in node_importance[:max]] # take only the first max nodes

        return neighbors
    
    def get_nodes(self):
        return list(self._nxGraph.nodes())
    
    def get_main_nodes(self, max : int) -> 'list[str]':
        if max <= 0:
            return []
        nodes = list(self._nxGraph.nodes.data('weight'))
        nodes.sort(key = lambda x:x[1], reverse=True)
        return [node[0] for node in nodes[:max]]

    def save_nodes_to_path(self, path : str):
        nodes = list(self._nxGraph.nodes.data('weight'))
        nodes.sort(key = lambda x:x[1], reverse=True)
        with open(path, 'w') as file:
            file.write(tabulate(nodes, headers=['Entity', 'Number of occurrences'], tablefmt='orgtbl'))