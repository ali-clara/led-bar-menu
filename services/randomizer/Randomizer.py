import yaml
import copy
import pandas as pd
import os
import jellyfish as jf
import glob
import numpy as np


dir_path = os.path.dirname( __file__ )
serv_path = os.path.join(dir_path, "..")
config_path = os.path.join(serv_path, '..\\config')
#What I need to do now is load everything into the document

#This holds in the data of all of the tag files.
yamls = {}
for filename in os.listdir(config_path):
    if filename[-4:] == '.yml' and filename[:5] == "tags_":
        with open(config_path+"\\%s"%filename, 'r') as file:
            yamls[filename[:-4]] = yaml.safe_load(file)
            file.close()

#We'd like lists of all tags and ingredients
tags = []
ingredients = []
for tagfile in yamls:
    for tag in yamls[tagfile].keys():
        tags.append(tag)
with open(config_path+"\\Ingredients.csv", 'r') as file:
    data = file.read().split("\n")
    for i in data:
        if len(i)>1:
            ingredients.append(i.split(',')[0])


#Armed with the tags and the ingredients, we now
def get_ingredients(tag):
    ingredience = []
    #To avoid recursion
    investigated_tags = [tag]
    for tagfile in yamls:
        if tag in yamls[tagfile]:
            subsidiaries = yamls[tagfile][tag]['ingredients'].keys()
            for sub in subsidiaries:
                if sub in ingredients:
                    ingredience.append(sub)
                if sub in tags and sub not in investigated_tags:
                    ingredience = ingredience + get_ingredients(sub)
                    investigated_tags.append(sub)
    return ingredience


#Take an (extant!) random ingredient tag and resolve it to an existing ingredient
def resolve_random_ingredient(rand_ingredient):
    data = {}
    with open(dir_path+"\\random_tags.yml", 'r') as file:
        data = yaml.safe_load(file)
        file.close()
    configuration = data[rand_ingredient]['included']
    #Select a tag category from the configuration
    distribution = []
    for i in configuration:
        distribution = distribution + [i]*configuration[i]
    selected = distribution[int(np.random.rand()*len(distribution))]
    if selected in ingredients:
        return selected
    elif selected in tags:
        available_ingredients = get_ingredients(selected)
        return available_ingredients[int(np.random.rand()*len(available_ingredients))]

def load_random_recipes():
    recipes = {}
    with open(dir_path+"\\random_recipes.yml", 'r') as file:
        recipes = yaml.safe_load(file)
        file.close()
    return recipes

def get_random_recipe_options():
    recipes = load_random_recipes()
    return list(recipes.keys())

def resolve_random_recipe(rand_recipe):
    recipes = load_random_recipes()
    random_ingredients = recipes[rand_recipe]['ingredients']
    for i in list(random_ingredients.keys()):
        if i[:6] == "Random":
            resolution = resolve_random_ingredient(i)
            random_ingredients[resolution] = random_ingredients[i]
            del random_ingredients[i]
    return random_ingredients

if __name__ == "__main__":
    random_ingredients = resolve_random_recipe("Random Sour")
    print(random_ingredients)