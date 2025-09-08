# Helper functions to manage 'global' website parameters that are shared across pages.

import yaml
import os
from readerwriterlock import rwlock

dir_path = os.path.join(os.path.dirname( __file__ ), os.pardir)
lock = rwlock.RWLockWriteD() # sets up a lock to prevent simultanous reading and writing

def read() -> dict:
    """Reads in the parameters from params.yml. This file holds any variables we need to change and access 
    across different pages of the website. I don't know enough about HTML to be sure this is the most elegant
    way, but the different versions(?) of this script that seemed to exist on the different pages were causing
    GHOSTS in my WIRES. And this is a little better than a sledgehammer.

    Returns:
        dict: dictionary of parameters, key:value pair of variable_name:variable_value
    """
    with lock.gen_rlock():
        try:
            with open(dir_path+"/config/params.yml") as stream:
                params_dict = yaml.safe_load(stream)
        except FileNotFoundError:
            print("Could not find params.yaml in config directory")
            params_dict = {}

    return params_dict
    
def write(new_params:dict):
    """Updates the parameter dictionary stored in params.yml. Careful with this, it overwrites things.

    Args:
        new_params (dict): new parameter dictionary, key:value pair of variable_name:variable_value
    """
    with lock.gen_wlock():
        with open(dir_path+"/config/params.yml", 'w') as outfile:
            yaml.dump(new_params, outfile, default_flow_style=False)