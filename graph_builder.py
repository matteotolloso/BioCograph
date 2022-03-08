from builtins import dict
from textwrap import indent
import networkx as nx
from itertools import combinations
import matplotlib.pyplot as plt
from numpy import block
from tabulate import tabulate
import json

 
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
    container = []
    container.append((src, 0))
    container.sort(key=lambda x:x[1]) # sort on second element of tuple
    widest[src] = 10**9
    while (len(container)>0):

        current_src = (container[-1])[0]
        del container[-1]
        for vertex in graph.neighbors(current_src):

 
            # Finding the widest distance to the vertex
            # using current_source vertex's widest distance
            # and its widest distance so far
            distance = max(widest[vertex], min(widest[current_src], graph[current_src][vertex]['capacity']))
 
            # Relaxation of edge and adding into Priority Queue
            if (distance > widest[vertex]):
 
                # Updating bottle-neck distance
                widest[vertex] = distance
 
                # To keep track of parent
                parent[vertex] = current_src
 
                # Adding the relaxed edge in the priority queue
                container.append((vertex, distance))
                container.sort(key=lambda x:x[1])
    
    current = target
    path = []
    while current != src:
        path.append(current)
        current = parent[current]
    path.append(src)

    return path
 


def build_cooccurrences_graph(  articles : dict, 
                                mh = True, 
                                rn = True, 
                                ot = True, 
                                bbent=True, 
                                check_tags=[], 
                                thesaurus={},
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
                if bbent_types.get(ent[1]) :
                    terms.append(ent[0])

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

def draw(graph: nx.Graph):
   
    #layout
    pos = nx.spring_layout(graph, weight='capacity', seed=1)
    #pos = nx.spectral_layout(graph, weight='weight')

    #edges
    edgewidth = [ (graph[u][v]['capacity'] * 0.8) for u, v in graph.edges()]
    maxi = max(edgewidth)
    edgewidth = list(map( lambda x : 50.0 * (x/float(maxi)), edgewidth))
    #nx.draw_networkx_edges(graph, pos, alpha=0.3, width=edgewidth, edge_color="m", edgelist=graph.edges(nbunch='SON'))
    nx.draw_networkx_edges(graph, pos, alpha=0.3, width=edgewidth, edge_color="m")
    
    #nodes
    nodesize = [ (graph.nodes[v]['weight']* 2) for v in graph.nodes()]
    maxi = max(nodesize)
    nodesize = list(map( lambda x : 7000.0 * x/float(maxi), nodesize))
    nx.draw_networkx_nodes(graph, pos, node_size=nodesize, node_color="b", alpha=0.9)
    label_options = {"ec": "k", "fc": "white", "alpha": 0.5}
    nx.draw_networkx_labels(graph, pos, font_size=10, bbox=label_options)


    plt.axis("off")
    plt.show()

   
def main():

    settings = {}
    articles = {}

    with open('settings.json', 'r') as f:
        cont = f.read()
        settings = json.loads(cont)

    for k, v in settings.get('dataset').items():
        if v:
            with open(k, 'r') as f:
                articles.update(json.loads(f.read()))
            
    print('Numero di articoli: ', len(articles.keys()))

    #mesh_terms : set = extract_mesh(articles)
    #print('Numero di MeSH diversi: ', len(mesh_terms))


    cooccurrences_graph = build_cooccurrences_graph(articles, 
                                                    check_tags=settings.get('check_tags'), 
                                                    rn=settings.get('RNnumber'), 
                                                    mh=settings.get('MeSH'), 
                                                    ot=settings.get('OtherTerms'), 
                                                    thesaurus=settings.get('thresaurs'),
                                                    bbent_types=settings.get('bioBERT_entity_types')
                                                    )

    print('Grafo delle co-occorrenze:\n\tNodi: ', len(cooccurrences_graph.nodes), '\n\tArchi: ', len(cooccurrences_graph.edges))

    cooccurrences_list = list(cooccurrences_graph.edges.data('capacity'))
    cooccurrences_list.sort(key = lambda x:x[2], reverse=True)
    with open('./results/cooccurrences.txt', 'w') as file:
            file.write(tabulate(cooccurrences_list,  headers=['Entity', 'Entity', 'Number of cooccurrences'],  tablefmt='orgtbl'))

    #print('Il grafo ha: ', nx.number_connected_components(cooccurrences_graph), ' componenti connesse')

    #print('Coefficiente di clustering: ', nx.average_clustering(cooccurrences_graph))

    nodes = list(cooccurrences_graph.nodes.data('weight'))
    nodes.sort(key = lambda x:x[1], reverse=True)
    with open('./results/nodes.txt', 'w') as file:
            file.write(tabulate(nodes, headers=['Entity', 'Number of occurrences'], tablefmt='orgtbl'))

    main_nodes = []
    for i in range( min(settings.get('numb_graph_nodes'), len(nodes))):
        main_nodes.append(nodes[i][0])
    
    for n in settings.get('always_present'):
        if n not in main_nodes: 
            main_nodes.append(n)

    main_graph = cooccurrences_graph.subgraph(main_nodes)

    src = "ZTTK"
    dest = "NPC"
    
    res = widest_path(cooccurrences_graph, src, dest)

    print("widest path from",src, "to", dest, ": ", res)


    draw(main_graph)


if __name__ == "__main__":
    main()
    
    
    








