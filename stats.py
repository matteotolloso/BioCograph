import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors
from matplotlib.ticker import PercentFormatter
import json


def load_settings():
    settings = {}
    with open('settings.json', 'r') as f:
        cont = f.read()
        settings = json.loads(cont)
    return settings


def add_dataset(path, all_papaers):
    # read the file
    with open(path, 'r') as f:
            all_papaers.update(json.loads(f.read()))

    

def main():
    #numero di entità di biobert per ogni abstract
    settings = load_settings()

    counter = {}

    all_papaers = {}
    e_dic = {}
    total_ent = 0

    num_list = []

    for ds_name , eneble in settings.get('dataset').items():
        add_dataset(ds_name, all_papaers)
    
    for pmid, info in all_papaers.items(): # k:pubmedId, v:dict of informations
        num_ent = len(info.get('bioBERT_entities'))
        for e in info.get('bioBERT_entities'):
            e_dic[e[0]]  = True
        total_ent += num_ent
        num_list.append(num_ent)
        if num_ent in counter:
            counter[num_ent] += 1
        else:
            counter[num_ent] = 1
        print(ds_name)
    print('     total entities: ', total_ent)
    print('     total papers: ', len(all_papaers))
    print('     total different entities in the dataset: ', len(e_dic))

    draw(num_list)

    return
    print('number of papers: ', len(all_papaers))
    total_ent = 0
    for k, v in all_papaers.items(): # k:pubmedId, v:dict of informations
        num_ent = len(v.get('bioBERT_entities'))
        total_ent += num_ent
        num_list.append(num_ent)
        if num_ent in counter:
            counter[num_ent] += 1
        else:
            counter[num_ent] = 1

    print('total entities: ', total_ent)
    count_lits = [(k, v) for k, v in counter.items()]

    count_lits.sort(key=lambda x: x[0], reverse=False)

    #print(count_lits)

    return
    

def draw(num_list):
    
    #draw
    
    fig, axs = plt.subplots(1, 2, tight_layout=True)
    # N is the count in each bin, bins is the lower-limit of the bin
    plt.tick_params(axis='x', labelsize = 30)
    N, bins, patches = axs[0].hist(num_list, bins=np.linspace(0, 100, 100))
    # We'll color code by height, but you could use any scalar
    fracs = N / N.max()
    # we need to normalize the data to 0..1 for the full range of the colormap
    norm = colors.Normalize(fracs.min(), fracs.max())
    # Now, we'll loop through our objects and set the color of each accordingly
    for thisfrac, thispatch in zip(fracs, patches):
        color = plt.cm.viridis(norm(thisfrac))
        thispatch.set_facecolor(color)
        plt.tick_params(axis='x', labelsize = 30)
    # We can also normalize our inputs by the total number of counts
    axs[1].hist(num_list, bins=np.linspace(0, 100, 100), density=True)
    # Now we format the y-axis to display percentage
    axs[1].yaxis.set_major_formatter(PercentFormatter(xmax=1))
    
    plt.show()




if __name__ == "__main__":
    main()
    