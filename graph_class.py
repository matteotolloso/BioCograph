import networkx as nx
from itertools import combinations
import matplotlib.pyplot as plt


class Cograph:

    def __init__(self) -> None:
        self._nxGraph = nx.Graph()
    
    
    def add_dataset(self, papers : 'list[dict]', settings : dict) -> None:
    
        check_tags : list = settings.get('check_tags')
        rn : bool = settings.get('RNnumber')
        mh : bool = settings.get('MeSH')
        ot : bool = settings.get('OtherTerms')
        bbent : bool = settings.get('bioBERT')
        thesaurus : dict = settings.get("thresaurs")
        alw_pres : list = settings.get('always_present')
        main_nodes : list = settings.get('main_nodes')
        bbent_types : dict = settings.get('bioBERT_entity_types')

        for art in papers:
            terms = []
            # extract the types of terms required
            if mh:
                terms += art.get('MeSH')
            if rn:
                terms += art.get('RNnumber')
            if ot:
                terms += art.get('OtherTerm')
            if bbent:
                ents = art.get('bioBERT_entities') #list of touples (name, type)
                for ent in ents:
                    if (ent[0] in alw_pres) or (ent[0] in main_nodes) or (bbent_types.get(ent[1]) ):
                        terms.append(ent[0])

            terms = list(set(terms))

            #remove check tags
            terms = list(filter(lambda x: x not in check_tags, terms))
            
            #TODO attenzione in questo modo alcuni sinonimi vengono esclusi 
            
            # merge synonyms
            for key in thesaurus.keys(): # for all key in thesaurus 
                for pos, term in enumerate(terms): # for all terms in this article
                    for syn in thesaurus[key]:  # for all synonyms
                        if syn in term: #if the target is contained in the term
                            terms[pos] = key  #replace the term with the synonymous
                            break
            
            terms = list(set(terms))
            
            if not terms:
                continue
            
            for a, b in list(combinations(terms, 2)):
                if not self._nxGraph.has_node(a):
                    self._nxGraph.add_node(a, weight=1)
                else:
                    self._nxGraph.nodes[a]['weight'] += 1
                
                if not self._nxGraph.has_node(b):
                    self._nxGraph.add_node(b, weight=1)
                else:
                    self._nxGraph.nodes[b]['weight'] += 1
                
                if self._nxGraph.has_edge(a, b):
                    self._nxGraph[a][b]['capacity'] += 1
                else:
                    self._nxGraph.add_edge(a, b, capacity=1)
    

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