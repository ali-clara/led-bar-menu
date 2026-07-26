import yaml
import os

dir_path = os.path.join(os.path.dirname( __file__ ), os.pardir, os.pardir)
file_path = os.path.join(dir_path, "config")

# This is Dane's doing. It's written in vim, which I think explains enough

overstock = []

with open(os.path.join(file_path,"ingredients.csv"), 'r') as file:
    for i in file.read().split("\n"):
        if ',' not in i:
            continue
        if i.split(',')[1] == 'overflow':
                overstock.append(i.split(',')[0])
existing_clearance = []
contents = {}

with open(os.path.join(file_path,"tags_meta.yml")) as stream:
    contents = yaml.safe_load(stream)

contents['Clearance']['ingredients'] += overstock
contents['Clearance']['ingredients'] = list(set(contents['Clearance']['ingredients']))

with open(os.path.join(file_path,"tags_meta.yml"), 'w') as stream:
    yaml.dump(contents, stream, sort_keys=False)

