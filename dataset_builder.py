from pymed import PubMed

def to_JSON_file(results : list):
    file = open("SON_dataset.json", "w")

    for artcile in results:
        file.write(artcile.toJSON())
    
    
    
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

to_JSON_file(results)








