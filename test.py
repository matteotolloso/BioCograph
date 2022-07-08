from dataset_class import Dataset
from cograph_class import Cograph

thesaurus = {}
source_nodes = []

dataset = Dataset()
dataset.add_from_path("./annotated_dataset/zttk.json")
dataset.normalize(thesaurus)
work_graph = Cograph()

work_graph.add_dataset( dataset, 
                        norm_type=2)

work_graph.save_edges_to_path("./results/edges.txt")

work_graph.disease_rank(source="zttk", 
                        rank_type="gene", 
                        algorithm="max_flow",  
                        path_to_save="./results/disease_rank.txt")

widest_set = work_graph.widest_set( ["zttk", "son", "spg17"], 
                                    bbent_types = ["gene", "disease"] )

neighbors = work_graph.get_neighbors(   widest_set, 
                                        bbent_types = ["drug"], 
                                        max_for_node = 10)

view_nodes = widest_set + neighbors

view_graph : Cograph = work_graph.draw(  showing_nodes=view_nodes, 
                                            layout="spring", 
                                            percentage = 0.7)

view_graph.export_cytoscape_data("./results/cytoskape_format.json")


