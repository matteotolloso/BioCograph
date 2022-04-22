import networkx as nx
from itertools import combinations
import matplotlib.pyplot as plt
from queue import PriorityQueue

from sqlalchemy import false
from dataset_class import Dataset

class Cograph:

    def __init__(self) -> None:
        self._nxGraph = nx.Graph()
    
    
    def add_dataset(self, 
                    dataset : 'Dataset', 
                    check_tags=[],
                    rn=False,
                    mh=False,
                    ot=False,
                    bbent=False,
                    alw_pres=[],
                    bbent_types=[]) -> None:
    
        papers = dataset.papers_list

        for art in papers:
            terms = [] # list of touples (name, type)
            # extract the types of terms required
            if mh:
                terms += (art.get('MeSH'), 'unknown')
            if rn:
                terms += (art.get('RNnumber'), 'unknown')
            if ot:
                terms += (art.get('OtherTerm'), 'unknown')
            if bbent:
                ents = art.get('bioBERT_entities') #list of touples (name, type)
                for ent in ents:
                    if (ent[0] in alw_pres)  or (bbent_types.get(ent[1]) ):
                        terms.append(ent)

            terms = list(set(terms))

            #remove check tags
            terms = list(filter(lambda x: x not in check_tags, terms))
            
            #TODO attenzione in questo modo alcuni sinonimi vengono esclusi 
            
            terms = list(set(terms))
            
            if not terms:
                continue
            
            for a, b in list(combinations(terms, 2)):
                if not self._nxGraph.has_node(a[0]):
                    self._nxGraph.add_node(a[0], weight=1, type=a[1])
                else:
                    self._nxGraph.nodes[a[0]]['weight'] += 1
                
                if not self._nxGraph.has_node(b[0]):
                    self._nxGraph.add_node(b[0], weight=1)
                else:
                    self._nxGraph.nodes[b[0]]['weight'] += 1
                
                if self._nxGraph.has_edge(a[0], b[0]):
                    self._nxGraph[a[0]][b[0]]['capacity'] += 1
                else:
                    self._nxGraph.add_edge(a[0], b[0], capacity=1)


    def draw(self, main_nodes : 'list[str]' = [], hilight : 'list[str]' =[]) -> None:
    
        fig, ax = plt.subplots(figsize=(17, 12))
        
        #layout
        pos = nx.spring_layout(self._nxGraph, weight='capacity', seed=1)
        #pos = nx.shell_layout(graph,rotate=15, nlist=[[n for n in main_nodes], [n for n in hilight if n not in main_nodes], [n for n in graph.nodes if n not in main_nodes and n not in hilight]])
        #pos = nx.nx_agraph.graphviz_layout(graph)
        #pos = nx.nx_pydot.pydot_layout(graph)

        #edges
        edgewidth = [ (self._nxGraph[u][v]['capacity'] * 0.8) for u, v in self._nxGraph.edges()]
        edge_colors = []
        if len(hilight) == 2:
            for u, v in self._nxGraph.edges():
                index_u : int
                index_v : int
                try:
                    index_u = hilight.index(u)
                    index_v = hilight.index(v)
                except:
                    edge_colors.append("g")
                    continue
                
                if abs(index_v - index_u) == 1:
                    edge_colors.append("r")
                else:
                    edge_colors.append("g") 
        elif len(hilight) > 2:
            for u, v in self._nxGraph.edges():
                if u in hilight and v in hilight:
                    edge_colors.append("r")
                else:
                    edge_colors.append("g")
        else:
            edge_colors = ["g" for u, v in self._nxGraph.edges()]
        
        maxi = max(edgewidth)
        edgewidth = list(map( lambda x : 50.0 * (x/float(maxi)), edgewidth))
        nx.draw_networkx_edges(self._nxGraph, pos, alpha=0.3, width=edgewidth, edge_color=edge_colors)
        
        #nodes
        nodesize = [ (self._nxGraph.nodes[v]['weight']* 2) for v in self._nxGraph.nodes()]
        maxi = max(nodesize)
        nodesize = list(map( lambda x : 7000.0 * x/float(maxi), nodesize))
        node_colors = ["r" if u in hilight else "b" for u in self._nxGraph.nodes()]
        nx.draw_networkx_nodes(self._nxGraph, pos, node_size=nodesize, node_color=node_colors, alpha=0.9)
        label_options = {"ec": "k", "fc": "white", "alpha": 0.5}
        nx.draw_networkx_labels(self._nxGraph, pos, font_size=10, bbox=label_options)
        
        label_options = {"ec": "k", "fc": "white", "alpha": 0.5}
        nx.draw_networkx_labels(self._nxGraph, pos, font_size=10, bbox=label_options)

        # Title/legend
        font = {"color": "k", "fontweight": "bold", "fontsize": 15}
        title : str = ""
        if len(hilight) == 2:
            title += "The widest path between \""+main_nodes[0]+ "\" and \""+ main_nodes[1] + "\" is: ["+ ', '.join(hilight) +"]\n"
        elif len(hilight) > 2:
            title+= "The widest set between {" + ', '.join(main_nodes) + "} is {" + ', '.join(hilight) + "}\n"   
        title += "Nodes position calculated using Fruchterman-Reingold force-directed algorithm."
        ax.set_title(title, font)
        # Change font color for legend
        font["color"] = "r"

        # Resize figure for label readibility
        ax.margins(0.1, 0.05)
        fig.tight_layout()
        plt.axis("off")

    def widest_path(self, src, target) -> list:
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

            for vertex in self._nxGraph.neighbors(current_src):

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
    
    
    def widest_set(self, endpoints : 'list[str]' ) -> 'set[str]':
        widest_set = []
        for u, v in combinations(endpoints, 2):
            widest_set += self.widest_path(u, v)
        widest_set = set(widest_set)
        return widest_set
    
    def get_neighbors(self, nodes : 'list[str]' ) -> 'list[str]':
        neighbors = []
        for node in nodes:
            neighbors += self._nxGraph.neighbors(node)
        return list(set(neighbors))