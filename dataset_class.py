from distutils.log import error
import os
import json
from unicodedata import name

class Dataset:
    
    def __init__(self) -> None:
        self._papers = {}
        self._names = []
        self._type_conunter = {}
            
    def add_from_path(self, path : str) -> None:
        new_papers = {}
        with open(path, 'r') as f:
                new_papers.update(json.loads(f.read()))

        for paper_id in new_papers:
            new_papers[paper_id]['weight'] = 1
        
        self._papers.update(new_papers)
        
        self._names.append(os.path.basename(path))
        

    def get_list(self) -> 'list[dict]':
        plist = [i for i in self._papers.values()]
        return plist
    
    def normalize(self, inverse_thresaurus) -> None:
        
        #normalization of entity name
        for paper_id in self._papers:  # for each paper
            entities_list = self._papers[paper_id]['bioBERT_entities'] # list of entities touple (name, type)
            normalized_entities_list = [] # new normalized list of entities
            for entity in entities_list: # list of touple (name, type)
                if (entity[0].lower() in inverse_thresaurus):
                    normalized_entities_list.append( (inverse_thresaurus[entity[0].lower()], entity[1] )    )
                else:
                    normalized_entities_list.append( (entity[0].lower() , entity[1]) )
            self._papers[paper_id]['bioBERT_entities'] = normalized_entities_list
        
        #normalization of entity type: the type of an entity is the most occurred type from bioBert, 
        #this because sometime biobert annotates the same entity with different type
        
        for paper_id in self._papers:  # for each paper
            entities_list = self._papers[paper_id]['bioBERT_entities'] # list of entities touple (name, type)
            for entity in entities_list: # list of touple (name, type)
                if not entity[0] in self._type_conunter:
                    self._type_conunter[entity[0]] = {'gene': 0, 'disease': 0, 'species': 0, 'drug': 0, 'mutation': 0 , "miRNA" : 0, "pathway" : 0 }
                try:
                    self._type_conunter[entity[0]][entity[1]] += 1
                except:
                    print('new type fonud: ' + entity[1])

        for paper_id in self._papers:  # for each paper
            entities_list = self._papers[paper_id]['bioBERT_entities'] # list of entities touple (name, type)
            new_entities_list = [] # new list of entities
            for entity in entities_list: # list of touple (name, type)
                new_entities_list.append( (entity[0], max(self._type_conunter[entity[0]].items(), key=lambda x: x[1])[0]) )
            self._papers[paper_id]['bioBERT_entities'] = new_entities_list
    
    def get_type_of(self, entity_name) -> str:
        if entity_name in self._type_conunter:
            return max(self._type_conunter[entity_name].items(), key=lambda x: x[1])[0]
        else:
            return 'unknown'