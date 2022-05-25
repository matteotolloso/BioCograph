import math
from pprint import pprint
from re import A
import re
import networkx as nx
from itertools import combinations
import matplotlib.pyplot as plt
from queue import PriorityQueue
from tabulate import tabulate
import json
from colorsys import hsv_to_rgb
from sqlalchemy import desc, false
from dataset_class import Dataset


class Cograph:

    def __init__(self, cograph = None) -> None:
        if type(cograph) == Cograph:
            self._nxGraph = nx.Graph(cograph.get_nxGraph())
        elif type(cograph) == nx.Graph:
            self._nxGraph = nx.Graph(cograph)
        else:
            self._nxGraph = nx.Graph()
         
    def get_nxGraph(self):
        return self._nxGraph
    
    
    def add_dataset(self, 
                    dataset : 'Dataset', 
                    rn=False,
                    mh=False,
                    ot=False,
                    bbent=True,
                    bbent_types = {},
                    alw_pres=[], # TODO remove?
                    normalize = True
                    ) -> None:
    
        papers = dataset.get_list()

        for paper in papers:
            terms = [] # list of touples (name, type)
            # extract the types of terms required
            if mh:
                for t in paper.get('MeSH'):
                    terms.append((t, 'unknown'))
            if rn:
                for t in paper.get('RNnumber'):
                    terms.append((t, 'unknown'))
            if ot:
                for t in paper.get('OtherTerm'):
                    terms.append((t, 'unknown'))
            if bbent:
                ents = paper.get('bioBERT_entities') #list of touples (name, type)
                for ent in ents:
                    if (bbent_types.get(ent[1])) or (ent[0] in alw_pres) :
                        terms.append(ent)

            # the same term that occurs more than once in the same paper is only added once
            terms = list(set(terms))

                        
            if not terms or len(terms) == 1:
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
        
        # new capacity is the old capacity divided by the sum of the weights of the nodes
        # it is a value between 0 and 1, it is 1 if the nodes occours always together
        #TODO problem: nodes that appear few time in the same papers has an high capacity
        if normalize: 
            for (a, b) in self._nxGraph.edges:
                self._nxGraph[a][b]['capacity'] = 2 * self._nxGraph[a][b]['capacity'] / (self._nxGraph.nodes[a]['weight'] + self._nxGraph.nodes[b]['weight'])

    def disease_rank(self, source, path_to_save) -> list:
        if not self._nxGraph.has_node(source):
            print(source, 'not in graph')
            return []

        #shortest path considering the capacity of the edges as a distance
        #in this case a greater capacity means more correlation, so a shorter path
        #to enable this we use 1-capacity as the distance (capacity is a value between 0 and 1) 
        
        def _weight(a, b, attr):
            return 1 - attr['capacity']

        rank = []
        for n in self._nxGraph.nodes:
            if self._nxGraph.nodes[n]['type'] == 'disease':
                path = []
                try:
                    path = nx.shortest_path(self._nxGraph, source=source, target=n, weight=_weight)
                except nx.exception.NetworkXNoPath:
                    continue
                
                path_weight = 0
                for i in range(len(path)-1):    
                    path_weight += self._nxGraph[path[i]][path[i+1]]['capacity']
                rank.append((n, path_weight))
        
        rank.sort(key = lambda x:x[1], reverse=True)
        with open(path_to_save, 'w') as file:
            file.write('Disease rank from ' + source + '\n')
            file.write(tabulate(rank,  headers=['Entity', 'Path weight'],  tablefmt='orgtbl'))

        return rank


    def draw(self, showing_nodes : 'list[str]' = [], nodes_layer : dict = {}, layout: str = 'spring', percentage = 0.1) -> None:
    
        if len(showing_nodes) <= 0:
            print("no nodes to show")
            return
        
        fig, ax = plt.subplots(figsize=(17, 12))

        graph_to_draw = self._nxGraph.subgraph(showing_nodes)
        graph_to_draw = nx.Graph(graph_to_draw)
        
        #layout
        pos = []
        
        if layout == 'spring':
            pos = nx.spring_layout(graph_to_draw, weight='capacity', seed=1)
        
        elif layout == 'shell':
            # position based on the node layer
            first_list = [n if nodes_layer[n] == 'first' else None for n in graph_to_draw.nodes]
            second_list = [n if nodes_layer[n] == 'second' else None for n in graph_to_draw.nodes]
            third_list = [n if nodes_layer[n] == 'third' else None for n in graph_to_draw.nodes]
            pos = nx.shell_layout(graph_to_draw, nlist=[first_list, second_list, third_list])

        #edges
        edges : list = list(graph_to_draw.edges.data('capacity'))
        edges.sort(key = lambda x: x[2])
        index_for_split = int( round(len(edges)*(1- percentage)))
        edges_to_remove = edges[ 0 : index_for_split]
        edges = edges[index_for_split : len(edges)] # take only the most capacity edges 

        for a, b, _ in edges_to_remove:
            graph_to_draw.remove_edge(a, b)

        max_cap_edge : float = edges[len(edges)-1][2]
        min_cap_edge : float = edges[0][2]

        edge_colors = []
        for u, v in graph_to_draw.edges():
            edge_colors.append(self.pseudocolor(graph_to_draw[u][v]['capacity'], min_cap_edge, max_cap_edge ))


        edgewidth = [3 for u, v in graph_to_draw.edges()]
        nx.draw_networkx_edges(graph_to_draw, pos, alpha=0.3, width=edgewidth, edge_color=edge_colors)
        
        #nodes
        # TODO nodesize not used
        nodesize = [ (graph_to_draw.nodes[v]['weight']* 2) for v in graph_to_draw.nodes()]
        maxi = max(nodesize)
        nodesize = list(map( lambda x : 7000.0 * x/float(maxi), nodesize))
        
        #color based on the node layer
        # transform dict of layer into list of colors
        node_color = [] 
        for n in graph_to_draw.nodes():
            if nodes_layer[n] == 'first':
                node_color.append('red')
            elif nodes_layer[n] == 'second':
                node_color.append('yellow')
            else:
                node_color.append('green')

        nx.draw_networkx_nodes(graph_to_draw, pos, node_color=node_color, alpha=0.9)
        
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
        return Cograph(graph_to_draw)

    def widest_path(self, s, t, bbent_types = {}) -> list:
        """
        find the widest path from s to t
        assunig 0 == -infinity and 1 == infinity
        """

        if s not in self._nxGraph.nodes or t not in self._nxGraph.nodes:
            print('node not in graph')
            return []

        p = {}  #parent
        b = {}  #bandwidth
        f = []  #frontier

        for n in self._nxGraph.nodes:
            p[n] = None
            b[n] = 0 #assuming all edges have capacity greater than 0 ([0, 1])

        b[s] = 1    

        neighbors = self._nxGraph.neighbors(s)
        neighbors = list(filter(lambda x: bbent_types.get(self._nxGraph.nodes[x]['type']) or x == t, neighbors))

        for w in neighbors:
            p[w] = s  #s is the parent of w
            b[w] = self._nxGraph[s][w]['capacity'] #capacity is the bandwidth to w (because is a neighbor of s)
            # append w to the frontier 
            f.append(w)
        
        while True:
            u = max(f, key = lambda x: b[x]) # node with the maximum bandwidth
            f.remove(u)

            neighbors = self._nxGraph.neighbors(u)
            neighbors = list(filter(lambda x: bbent_types.get(self._nxGraph.nodes[x]['type']) or x == t, neighbors))
            
            for w in neighbors:
                if b[w] == 0:
                    p[w] = u
                    b[w] = min(b[u], self._nxGraph[u][w]['capacity'])
                    # append w to the frontier 
                    f.append(w)
                elif (w in f) and (b[w] < min(b[u], self._nxGraph[u][w]['capacity'])):
                    p[w] = u
                    b[w] = min(b[u], self._nxGraph[u][w]['capacity'])
            
            
            if (b[t] > 0) and (t not in f):
                #arrived to the target with the maximum bandwidth
                break

            if f == []:
                # there is no path from s to t
                return []   
                
        # build the path
        path = [t]
        while t != s:
            t = p[t]
            path.append(t)
        path.reverse()
        return path

    def widest_set(self, endpoints : 'list[str]', bbent_types = {}) -> 'list[str]':
        if len(endpoints) == 1:
            return endpoints
        
        if len(endpoints) <= 0:
            return []

        widest_set = []
        
        for u, v in combinations(endpoints, 2):
            wp =self.widest_path(u, v, bbent_types=bbent_types)
            widest_set += wp
            print("wildest path from",u,"to", v, wp)

        for n in endpoints: # add the endpoints
            if n in self._nxGraph.nodes:
                widest_set.append(n)

        widest_set = list(set(widest_set))
        return widest_set
    
    def get_neighbors(self, nodes_from : 'list[str]', max_for_node : int, bbent_types = {}) -> 'list[str]':
        # for each node in nodes_from, get the first max_neighbors based on the edge capacity
        
        if max_for_node <= 0:
            return []
        
        result = []

        for n in nodes_from: # for each node in nodes_from
            neighbors = list(self._nxGraph.neighbors(n)) # get the neighbors of n
            neighbors = list(filter(lambda x: bbent_types.get(self._nxGraph.nodes[x]['type']), neighbors)) # filter the neighbors by the types wanted
            neighbors.sort(key=lambda x: self._nxGraph[n][x]['capacity'], reverse=True) # sort the neighbors by capacity from source
            neighbors = neighbors[:max_for_node] # get the first max_neighbors
            result+=neighbors
        
        result = list(set(result))

        return result
    
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

    def save_edges_to_path(self, path : str):
        cooccurrences_list = list(self._nxGraph.edges.data('capacity'))
        cooccurrences_list.sort(key = lambda x:x[2], reverse=True)
        with open(path, 'w') as file:
                file.write(tabulate(cooccurrences_list,  headers=['Entity', 'Entity', 'Number of cooccurrences'],  tablefmt='orgtbl'))

    def export_cytoscape_data(self, path : str) -> None:
        res = nx.cytoscape_data(self._nxGraph)
        with open(path, 'w') as f:
            f.write(json.dumps(res))
    
    
    def pseudocolor(self, val, minval, maxval):
        """ Convert val in range minval..maxval to the range 0..120 degrees which
        correspond to the colors Red and Green in the HSV colorspace.
        """
        avg = (minval + maxval) / 2.0
        val = (val-avg)*(-1) + avg

        #TODO possible divide by zero exception
        h = (float(val-minval) / float(maxval-minval)) * 120

        # Convert hsv color (h,1,1) to its rgb equivalent.
        # Note: hsv_to_rgb() function expects h to be in the range 0..1 not 0..360
        r, g, b = hsv_to_rgb(h/360, 1., 1.)
        return r, g, b
        
    
    