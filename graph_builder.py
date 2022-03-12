from builtins import dict
import networkx as nx
from itertools import combinations, starmap
import matplotlib.pyplot as plt
from tabulate import tabulate
import json
from queue import PriorityQueue
import time
import threading

 
# Function to return the maximum weight
# in the widest path of the given graph
def widest_path(graph : nx.Graph, src, target):
    # To keep track of widest distance
    widest  = {}
    for key in graph.nodes():
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

        for vertex in graph.neighbors(current_src):

            # Finding the widest distance to the vertex
            # using current_source vertex's widest distance
            # and its widest distance so far
            width = max(widest[vertex], min(widest[current_src], graph[current_src][vertex]['capacity']))
 
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
        current = parent[current]
    path.append(src)
    path.reverse()

    return path
 

def build_cooccurrences_graph(  articles : dict, 
                                mh = True, 
                                rn = True, 
                                ot = True, 
                                bbent=True, 
                                check_tags=[], 
                                thesaurus={},
                                alw_pres=[],
                                bbent_types = {}) -> nx.Graph:
    
    graph = nx.Graph()

    for art in articles.values():
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
                ent[0] = ent[0].lower()
                if ent[0] in alw_pres:
                    terms.append(ent[0])
                elif bbent_types.get(ent[1]) :
                    terms.append(ent[0])

        terms = list(map(lambda x : x.lower(), terms))
        #remove check tags
        terms = list(filter(lambda x: x not in check_tags, terms))
        
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
            if not graph.has_node(a):
                graph.add_node(a, weight=1)
            else:
                graph.nodes[a]['weight'] += 1
            
            if not graph.has_node(b):
                graph.add_node(b, weight=1)
            else:
                graph.nodes[b]['weight'] += 1
            
            if graph.has_edge(a, b):
                graph[a][b]['capacity'] += 1
            else:
                graph.add_edge(a, b, capacity=1)
    
    return graph

def draw_gene_functional_association(graph : nx.Graph):

    # compute centrality
    centrality = nx.betweenness_centrality(graph, k=10, endpoints=True)

    # compute community structure
    lpc = nx.community.label_propagation_communities(graph)
    community_index = {n: i for i, com in enumerate(lpc) for n in com}

    #### draw graph ####
    fig, ax = plt.subplots(figsize=(20, 15))
    pos = nx.spring_layout(graph, k=0.15, seed=4572321, weight='capacity')
    node_color = [community_index[n] for n in graph]
    node_size = [v * 20000 for v in centrality.values()]
    nx.draw_networkx(
        graph,
        pos=pos,
        with_labels=False,
        node_color=node_color,
        node_size=node_size,
        edge_color="gainsboro",
        alpha=0.4,
    )
    
    label_options = {"ec": "k", "fc": "white", "alpha": 0.5}
    nx.draw_networkx_labels(graph, pos, font_size=10, bbox=label_options)

    # Title/legend
    font = {"color": "k", "fontweight": "bold", "fontsize": 20}
    ax.set_title("Gene functional association network (C. elegans)", font)
    # Change font color for legend
    font["color"] = "r"

    ax.text(
        0.80,
        0.10,
        "node color = community structure",
        horizontalalignment="center",
        transform=ax.transAxes,
        fontdict=font,
    )
    ax.text(
        0.80,
        0.06,
        "node size = betweeness centrality",
        horizontalalignment="center",
        transform=ax.transAxes,
        fontdict=font,
    )

    # Resize figure for label readibility
    ax.margins(0.1, 0.05)
    fig.tight_layout()
    plt.axis("off")
    plt.show()

def draw(graph: nx.Graph, path=[]):
   
    #layout
    pos = nx.spring_layout(graph, weight='capacity', seed=1)
    #pos = nx.spectral_layout(graph, weight='weight')

    #edges
    edgewidth = [ (graph[u][v]['capacity'] * 0.8) for u, v in graph.edges()]
    edge_colors = []
    if len(path) <= 2:
        edge_colors = ["r" if u in path and v in path else "m" for u, v in graph.edges()]
    else:
        edge_colors = ["r" if u in path and v in path and ((u, v) != (path[0], path[-1]) and (v, u) != (path[0], path[-1])) else "m" for u, v in graph.edges() ]

    maxi = max(edgewidth)
    edgewidth = list(map( lambda x : 50.0 * (x/float(maxi)), edgewidth))
    #edgecolor = list(map(lambda x: "m" if x not in))
    nx.draw_networkx_edges(graph, pos, alpha=0.3, width=edgewidth, edge_color=edge_colors)
    
    #nodes
    nodesize = [ (graph.nodes[v]['weight']* 2) for v in graph.nodes()]
    maxi = max(nodesize)
    nodesize = list(map( lambda x : 7000.0 * x/float(maxi), nodesize))
    node_colors = ["r" if u in path else "b" for u in graph.nodes()]
    nx.draw_networkx_nodes(graph, pos, node_size=nodesize, node_color=node_colors, alpha=0.9)
    label_options = {"ec": "k", "fc": "white", "alpha": 0.5}
    nx.draw_networkx_labels(graph, pos, font_size=10, bbox=label_options)


    plt.axis("off")
    plt.show()

def connected_components(graph : nx.Graph):
    con_comp = nx.number_connected_components(graph)
    print('Il grafo ha: ',con_comp , ' componenti connesse')

def clusetring(graph : nx.Graph):
    clust = nx.average_clustering(graph)
    print('Coefficiente di clustering: ', clust)

def save_cooccurences(graph : nx.Graph):
    cooccurrences_list = list(graph.edges.data('capacity'))
    cooccurrences_list.sort(key = lambda x:x[2], reverse=True)
    with open('./results/cooccurrences.txt', 'w') as file:
            file.write(tabulate(cooccurrences_list,  headers=['Entity', 'Entity', 'Number of cooccurrences'],  tablefmt='orgtbl'))

def main():

    settings = {}
    articles = {}

    #load setting
    with open('settings.json', 'r') as f:
        cont = f.read()
        settings = json.loads(cont)
   
    #load dataset
    print("Loading dataset...")
    for k, v in settings.get('dataset').items():
        if v:
            with open(k, 'r') as f:
                articles.update(json.loads(f.read()))
    print("Dataset OK")

    print('Numero di articoli: ', len(articles.keys()))
    
    settings.get('always_present').append(settings.get('hilight_path').get('source'))
    settings.get('always_present').append(settings.get('hilight_path').get('destination'))

    print("Building graph")
    cooccurrences_graph = build_cooccurrences_graph(articles, 
                                                    check_tags=settings.get('check_tags'), 
                                                    rn=settings.get('RNnumber'), 
                                                    mh=settings.get('MeSH'), 
                                                    ot=settings.get('OtherTerms'), 
                                                    thesaurus=settings.get('thresaurs'),
                                                    alw_pres=settings.get('always_present'),
                                                    bbent_types=settings.get('bioBERT_entity_types')
                                                    )
    print("Graph OK")
    print('Grafo delle co-occorrenze:\n\tNodi: ', len(cooccurrences_graph.nodes), '\n\tArchi: ', len(cooccurrences_graph.edges))

    
    my_threads = []
    my_threads.append(threading.Thread(target=connected_components, args=(cooccurrences_graph,)))
    my_threads.append(threading.Thread(target=clusetring, args=(cooccurrences_graph,)))
    my_threads.append(threading.Thread(target=save_cooccurences, args=(cooccurrences_graph,)))
    for t in my_threads:
        t.start()

 
    nodes = list(cooccurrences_graph.nodes.data('weight'))
    nodes.sort(key = lambda x:x[1], reverse=True)
    with open('./results/nodes.txt', 'w') as file:
            file.write(tabulate(nodes, headers=['Entity', 'Number of occurrences'], tablefmt='orgtbl'))

    main_nodes = []
    for i in range( min(settings.get('numb_graph_nodes'), len(cooccurrences_graph.nodes()))):
        main_nodes.append(nodes[i][0])
    
    for n in settings.get('always_present'):
        if n not in main_nodes: 
            main_nodes.append(n)

    main_graph = cooccurrences_graph.subgraph(main_nodes)

    start = time.time()
    res = widest_path(cooccurrences_graph,  settings.get('hilight_path').get('source'),  settings.get('hilight_path').get('destination'))
    print("widest path from", settings.get('hilight_path').get('source'), "to",  settings.get('hilight_path').get('destination'), ": ", res)
    print("time: ", time.time() - start)

    #draw(main_graph, res)
    draw_gene_functional_association(main_graph)

    for t in my_threads:
        t.join()


if __name__ == "__main__":
    main()
    
    
    








