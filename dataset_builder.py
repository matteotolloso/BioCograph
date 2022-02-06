from dataclasses import replace
from hashlib import new
from unittest import skip
from pymed import PubMed
import sys
import re

def pubmed_to_json(results : list):
    pubmed = PubMed(tool="SON_dataset", email="m.tolloso@studenti.unipi.it")

    query = '(SON[Title/Abstract] AND ("DNA-Binding Proteins"[Mesh] OR "RNA-Binding Proteins"[Mesh]) AND "SON protein, human"[nm]) OR "SON gene"[All Fields] OR "SON protein"[All Fields]\
        OR NREBP[Title/Abstract]\
        OR ("DBP-5"[Title/Abstract] AND "DNA-Binding Proteins"[MeSH])\
        OR "NRE-Binding Protein"[Title/Abstract]\
        OR KIAA1019[Title/Abstract]\
        OR C21orf50[Title/Abstract]\
        OR (SON3[Title/Abstract] AND "DNA-Binding Proteins"[MeSH])\
        OR DBP5[Title/Abstract]'

    results = list(pubmed.query(query, max_results = 500))

    print("articoli trovati: ")
    print(len(results))
    
    file = open("SON_dataset.json", "w")

    for artcile in results:
        file.write(artcile.toJSON())


class Article():
    def __init__(self):
        self.attributes : list[tuple[str, str]] = []
    
    def addAttribute(self, attr):
        self.attributes.append(attr)
        

def main():

    articles : list[str] = []
    
    with open(sys.argv[1]) as file:
        articles = list(map(lambda x: x.replace('\n      ', ' '), file.read().split("\n\n")))

    dict = {}
    for art in articles:

        match = re.search('^PMID- (.*)$', art, re.MULTILINE)
        if match is None:
            continue
        pmid = match.group(1)

        match = re.search('^TI  - (.*)$', art, re.MULTILINE)
        if match is None:
            continue
        ti = match.group(1)

        match = re.search('^AB  - (.*)$', art, re.MULTILINE)
        if match is None:
            continue
        ab = match.group(1)

        mh = re.findall('^MH  - (.*)$', art, re.MULTILINE)

        dict[pmid] = {'Title' : ti, 'Abstract' : ab, ' MeSH' : mh}
    
    print(len(dict.keys()))

        



if __name__ == "__main__":
    main()
    
    
    








