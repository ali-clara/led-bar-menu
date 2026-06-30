import yaml

overstock = []

with open("ingredients.csv", 'r') as file:
    for i in file.read().split("\n"):
        if ',' not in i:
            continue
        if i.split(',')[1] == 'overflow':
                overstock.append(i.split(',')[0])
existing_clearance = []
contents = {}

with open("tags_meta.yml") as stream:
    contents = yaml.safe_load(stream)

contents['Clearance']['ingredients'] += overstock
contents['Clearance']['ingredients'] = list(set(contents['Clearance']['ingredients']))

with open("tags_meta.yml", 'w') as stream:
    yaml.dump(contents, stream, sort_keys=False)

