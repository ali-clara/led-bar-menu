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

for filename in os.listdir():
    if filename[-4:] == '.yml':
        input(filename[:-4]+"\n")
        with open(filename, 'r') as file:
            eval(filename[:-4] + " = " + "%s"%yaml.safe_load(file))
            file.close()
        input("Read succesful...\n")
        print(eval(filename[:-4]))
        input("And the write too!\n")
#print(tags_brandy)

