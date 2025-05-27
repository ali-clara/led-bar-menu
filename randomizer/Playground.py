import yaml
import copy
import pandas as pd
import os
import jellyfish as jf
import glob
import numpy as np


os.chdir("..\\config")

#print(os.listdir())

#What I need to do now is load everything into the document

#This holds in the data of all of the tag files.
##It's possible that we're going to to run into problems with the aliases, so I might need to exclude that one specifically.
yamls = {}
for filename in os.listdir():
    if filename[-4:] == '.yml' and filename[:5] == "tags_":
        with open(filename, 'r') as file:
            yamls[filename[:-4]] = yaml.safe_load(file)
            file.close()

#We'd like lists of all tags and ingredients
tags = []
ingredients = []
for tagfile in yamls:
    for tag in yamls[tagfile].keys():
        tags.append(tag)
with open("Ingredients.csv", 'r') as file:
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