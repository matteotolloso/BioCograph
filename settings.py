import json
import os

class Settings:
    def __init__(self):
        self.checked = False
        self._settings = {}
        self._keys = ['dataset', 'MeSH', 'RNnumber', 'OtherTerms',\
                    'bioBERT', 'bioBERT_entity_types', 'numb_graph_nodes',\
                    'always_present', 'main_nodes', 'check_tags', 'thresaurs']
        
    def load(self, path : str):
        if os.path.exists(path):
            with open(path, 'r') as f:
                self._settings = json.load(f)
            print('Settings loaded')
            self.checked = False
            return self.check_settings()
        else:
            print('This path does not exist, creating new settings file')
            self.generate_settings_file(path)
            return False

    def check_settings(self):
        for k in self._keys:
            if k not in self._settings:
                print('Missing key: ' + k)
                return False
        print('Settings check ok')
        self.checked = True
        return True
        
    
    def generate_settings_file(self, path):
        with open(path, 'w+') as f:
            json.dump(self._settings, f)
        print('Settings file created at: ' + path)

