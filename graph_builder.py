from builtins import dict
from platform import win32_edition
import matplotlib.pyplot as plt
import json
from dataset_class import Dataset
from cograph_class import Cograph
import settings_class

 
    
def load_settings():
    settings = {}
    with open('settings.json', 'r') as f:
        cont = f.read()
        settings = json.loads(cont)
    return settings

def get_inverse_thresaurs(thresaurs : dict):
    inverse_thresaurus = {}
    for (k, v) in thresaurs.items():
        for i in v:
            inverse_thresaurus[i] = k
    return inverse_thresaurus


def main():

    settings = load_settings() # loaded ad a dict, TODO: use settingsclass
    inverse_thresaurus = get_inverse_thresaurs(settings.get('thresaurs'))
    dataset = Dataset() 

    for k, v in settings.get('dataset').items():
        if v:
            dataset.add_from_path(k)
    
    dataset.normalize(inverse_thresaurus)

    work_graph = Cograph()
    
    work_graph.add_dataset(dataset, bbent_types = settings.get('bioBERT_entity_types')) 

    work_graph.save_nodes_to_path("./results/nodes.txt")
    work_graph.save_edges_to_path("./results/edges.txt")

    widest_set = work_graph.widest_set(settings.get('widest_set'), bbent_types = settings.get('bioBERT_entity_types_widest_set') )# widest set with only selected types of entities
    
    neighbors = work_graph.get_neighbors(widest_set, bbent_types = settings.get('bioBERT_entity_types_second_layer'), max_for_node = settings.get('max_neighbors_for_node')) # seocnd layer with only selected types of entities
    
    showing_nodes = widest_set + neighbors

    showing_nodes += work_graph.get_main_nodes(max=settings.get('num_other_relevant_nodes'))

    nodes_layer = {}
    for n in showing_nodes:
        if n in widest_set:
            nodes_layer[n] = 'first'
        elif n in neighbors:
           nodes_layer[n] = 'second'
        else:
            nodes_layer[n] = 'third'
            
    
    work_graph.draw( showing_nodes=showing_nodes, layout=settings.get('layout'), nodes_layer=nodes_layer)

    work_graph.export_cytoscape_data("./results/cytoskape_format.json")
    
    plt.show()  


if __name__ == "__main__":
    main()
    
    
    








