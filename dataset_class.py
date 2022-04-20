import os
import json

class Dataset:
    def __init__(self, path : str) -> None:
        self.name = os.path.basename(path)
        self._papers = {}
        with open(path, 'r') as f:
                self._papers.update(json.loads(f.read()))
        self.num_of_papers = len(self._papers)
        self.paper_relative_value = 1
        self.papers_list = [i for i in self._papers.values()]
    
    def normalize(self, inverse_thresaurus) -> None:
        for paper_id in self._papers:  # for each paper
            entities_list = self._papers[paper_id]['bioBERT_entities'] # list of entities
            normalized_entities_list = [] # new normalized list of entities
            for entity in entities_list: # list of touple (name, type)
                if (entity[0].lower() in inverse_thresaurus) and (entity[0].lower() not in normalized_entities_list):
                    normalized_entities_list.append( (inverse_thresaurus[entity[0].lower()], entity[1] )    )
                else:
                    normalized_entities_list.append( (entity[0].lower() , entity[1]) )
            self._papers[paper_id]['bioBERT_entities'] = normalized_entities_list
        self.papers_list = [i for i in self._papers.values()] #upgrade list
        
    def get_papers(self):
        return list(self.papers_list)

