def edge_color(self, hilight):
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

def main():
    settings = load_settings()
    articles = load_articles(settings)
    normalize_articles(articles, settings.get('thresaurs'))
    # Attenzione: le entità vengono normalizzate prima che il grafo venga creato
    # quindi nel caso delle entità di bioBERT, la normalizzazione non tiene conto
    # del tipo di entità (es. "gene" e "disease")

    cooccurrences_graph : nx.Graph = build_cooccurrences_graph(articles, settings)

    print('Grafo delle co-occorrenze:\n\tNodi: ', len(cooccurrences_graph.nodes), '\n\tArchi: ', len(cooccurrences_graph.edges))

    #calcoli sul grafo
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

    
    view_nodes = [] # nodi che devono essere effettivamente visualizzati

    # in view_nodes ci saranno i nodi che devono essere visualizzati
    # cioè i nodi più pesanti, quelli in always_present e quelli nel path
    for i in range( min(settings.get('numb_graph_nodes'), len(cooccurrences_graph.nodes()))):
        view_nodes.append(nodes[i][0])
    for n in settings.get('always_present'):
        view_nodes.append(n)

    main_nodes = settings.get('main_nodes') # nodi da cui partono le ricerche
    hilight_nodes = [] # nodi che saranno colorati diversamente

    # non posso lavorare su nodi che non sono nel grafo
    main_nodes = list(filter(lambda x: x in cooccurrences_graph.nodes(), main_nodes))

    if len(main_nodes) == 2: # cerco un path
        path = widest_path(cooccurrences_graph,  main_nodes[0],  main_nodes[1])
        print("Widest path from", main_nodes[0], "to",  main_nodes[1], ": ", path)
        hilight_nodes += path
    elif len(main_nodes) > 2:  # cerco tutte le coppie di path
        #set dei nodi che appartengono al path tra due dei nodi in main_nodes
        set_nodes = widest_set(cooccurrences_graph, main_nodes)
        print("Widest set from ", ', '.join(main_nodes), ':', set_nodes)
        hilight_nodes += list(set_nodes)
    else:
        print('hilight è vuoto')

    view_nodes += hilight_nodes # gli hilight_nodes vengono aggiunti alla lista dei nodi da visualizzare
    view_nodes = list(set(view_nodes))

    # sottografo che deve essere visualizzato, indotto dai nodi che devono essere visualizzati
    view_graph = cooccurrences_graph.subgraph(view_nodes)

    my_draw(view_graph, main_nodes, hilight_nodes)

    #draw_gene_functional_association(view_graph)

    for t in my_threads:
        t.join()

    plt.show()

# Function to return the maximum weight
# in the widest path of the given graph
def widest_path(graph : nx.Graph, src, target) -> list:
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
        try:
            current = parent[current]
        except:
            print('path not found between', src, 'and', target)
            return []

    path.append(src)
    path.reverse()

    return path 

def widest_set(graph : nx.Graph, endpoints : list ) -> set:
    widest_set = []
    for u, v in combinations(endpoints, 2):
        widest_set += widest_path(graph, u, v)
    widest_set = set(widest_set)
    return widest_set

def build_cooccurrences_graph(articles : dict, settings : dict) -> nx.Graph:
    
    check_tags : list = settings.get('check_tags')
    rn : bool = settings.get('RNnumber')
    mh : bool = settings.get('MeSH')
    ot : bool = settings.get('OtherTerms')
    bbent : bool = settings.get('bioBERT')
    thesaurus : dict = settings.get("thresaurs")
    alw_pres : list = settings.get('always_present')
    main_nodes : list = settings.get('main_nodes')
    bbent_types : dict = settings.get('bioBERT_entity_types')


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

    fig, ax = plt.subplots(figsize=(20, 15))

    # compute centrality
    centrality = nx.betweenness_centrality(graph, k=10, endpoints=True)

    # compute community structure
    lpc = nx.community.label_propagation_communities(graph)
    community_index = {n: i for i, com in enumerate(lpc) for n in com}

    #### draw graph ####
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
    ax.set_title("Gene functional association network", font)
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
    plt.draw()

def my_draw(graph: nx.Graph, main_nodes = [], hilight=[]):
    
    fig, ax = plt.subplots(figsize=(17, 12))
    
    #layout
    pos = nx.spring_layout(graph, weight='capacity', seed=1)
    #pos = nx.shell_layout(graph,rotate=15, nlist=[[n for n in main_nodes], [n for n in hilight if n not in main_nodes], [n for n in graph.nodes if n not in main_nodes and n not in hilight]])
    #pos = nx.nx_agraph.graphviz_layout(graph)
    #pos = nx.nx_pydot.pydot_layout(graph)

    #edges
    edgewidth = [ (graph[u][v]['capacity'] * 0.8) for u, v in graph.edges()]
    edge_colors = []
    if len(hilight) == 2:
        for u, v in graph.edges():
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
        for u, v in graph.edges():
            if u in hilight and v in hilight:
                edge_colors.append("r")
            else:
                edge_colors.append("g")
    else:
        edge_colors = ["g" for u, v in graph.edges()]
    
    maxi = max(edgewidth)
    edgewidth = list(map( lambda x : 50.0 * (x/float(maxi)), edgewidth))
    nx.draw_networkx_edges(graph, pos, alpha=0.3, width=edgewidth, edge_color=edge_colors)
    
    #nodes
    nodesize = [ (graph.nodes[v]['weight']* 2) for v in graph.nodes()]
    maxi = max(nodesize)
    nodesize = list(map( lambda x : 7000.0 * x/float(maxi), nodesize))
    node_colors = ["r" if u in hilight else "b" for u in graph.nodes()]
    nx.draw_networkx_nodes(graph, pos, node_size=nodesize, node_color=node_colors, alpha=0.9)
    label_options = {"ec": "k", "fc": "white", "alpha": 0.5}
    nx.draw_networkx_labels(graph, pos, font_size=10, bbox=label_options)
    
    label_options = {"ec": "k", "fc": "white", "alpha": 0.5}
    nx.draw_networkx_labels(graph, pos, font_size=10, bbox=label_options)

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


def load_articles(settings : dict):
    articles = {}
    for k, v in settings.get('dataset').items():
        if v:
            with open(k, 'r') as f:
                articles.update(json.loads(f.read()))
    return articles

def normalize_articles(articles : dict, thresaurs : dict):
    # thresaurs: associa al nome principale una lista di sinonimi
    # inverse_thresaurus: associa ad un sinonimo il nome principale

    inverse_thresaurus = {}
    for (k, v) in thresaurs.items():
        for i in v:
            inverse_thresaurus[i.lower()] = k.lower()

   

    for paper_id in articles:  # for each paper
        entities_list = articles[paper_id]['bioBERT_entities'] # list of entities
        normalized_entities_list = []
        for entity in entities_list: # list of touple (entity, type)
            if (entity[0].lower() in inverse_thresaurus) and (entity[0].lower() not in normalized_entities_list):
                normalized_entities_list.append( (inverse_thresaurus[entity[0].lower()], entity[1] )    )
            else:
                normalized_entities_list.append( (entity[0].lower() , entity[1]) )
        articles[paper_id]['bioBERT_entities'] = normalized_entities_list
       

def _old_widest_path(self, src, target, bbent_types = 'all') -> 'list[str]':
        #TODO problem: non deterministic
                
        # To keep track of widest distance
        widest  = {}
        for key in self._nxGraph.nodes():
            widest[key] = -(10**9)
        
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
                # at least one neighbor must have the type wanted or to be the target, 
                # otherwise a path does not exist for me
                exists = False
                for neighbor in neighbors:
                    if  bbent_types.get( self._nxGraph.nodes[neighbor]['type']  or neighbor == target) : # if node type is in the wanted types
                        exists = True
                        break
                if not exists:
                    print('path not found between', src, 'and', target, 'through only', bbent_types)
                    return []

            for vertex in neighbors:

                if (not bbent_types.get( self._nxGraph.nodes[vertex]['type'] )) and (not vertex == target):
                    # if the neighbor is not in the wanted types and is not the target
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
    