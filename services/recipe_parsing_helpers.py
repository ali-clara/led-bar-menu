# testing recipe formatting and inputs
import yaml
import copy
import pandas as pd
import os
import jellyfish as jf
import glob
import numpy as np
import csv

dir_path = os.path.join(os.path.dirname( __file__ ), os.pardir)
similarity_threshold = 0.75

def format_as_inventory(input_str:str):
    return input_str.replace(" ", "_").lower().strip()

def format_as_recipe(input_str:str):
    return input_str.replace("_", " ").title().strip()

# -------------------- LOADING & READING -------------------- #
def read_main_menu():
    recipes_dict = {}
    tags_dict = {}
    recipe_path = os.path.join(dir_path, "config")
    try:
        for file in glob.glob(recipe_path+"/recipes*.yml"):
            with open(file) as stream:
                    recipes_dict.update(yaml.safe_load(stream))
    except TypeError as e:
        print(f"Failed in reading {file}: {e}")
    except FileNotFoundError as e:
        print(e)
        recipes_dict = {}

    try:
        for file in glob.glob(recipe_path+"/tags*.yml"):
            with open(file) as stream:
                tags_dict.update(yaml.safe_load(stream))
    except TypeError as e:
            print(f"Failed in reading {file}: {e}")
    except FileNotFoundError as e:
        print(e)
        tags_dict = {}

    try:
        file = dir_path+"/config/aliases.yml"
        with open(file) as stream:
            alias_dict = yaml.safe_load(stream)
    except TypeError as e:
                    print(f"Failed in reading {file}: {e}")
    except FileNotFoundError as e:
        print(e)
        alias_dict = {}
    else:
        alias_dict_restructured = {}
        for key in alias_dict:
            aliases = list(alias_dict[key]["ingredients"].keys())

            aliases = [format_as_inventory(alias) for alias in aliases]
            key = format_as_inventory(key)

            alias_dict_restructured.update({key:aliases})

    return recipes_dict, tags_dict, alias_dict_restructured

def load_recipe_names(menu_dict):
    return list(menu_dict.keys())

def load_tags(tags_dict):
    return list(tags_dict.keys())

def load_cabinet_locs() -> dict:
    """Loads all the cabinet locations and their corresponding led pixel indices. See the ReadMe for more details on the location
    setup - briefly, rows are letters (A-N) and 'columns' are numbers (1-7)(I think).

    Returns:
        dict: Location: [[start pix 1, stop pix 1], ... [start pix n, stop pix n]]
    """
    try:
        file = dir_path+"/config/led_locs_final.yml"
        with open(file) as stream:
            all_locations_dict = yaml.safe_load(stream)
    except FileNotFoundError as e:
        print(e)
        all_locations_dict = {}

    return all_locations_dict

def load_collection_names(menu_dict):
    collections = []
    for cocktail in menu_dict:
        # Grab what collection it belongs to, correcting for capitalization just in case.
        try:
            collection = menu_dict[cocktail]['collection'].title()
        except KeyError as e:
                print(f"Loading collections raised key error -- {cocktail} does not have {e} field.")
        # Check if its in our list of collections. If it's not, add it.
        else:
            if collection not in collections:
                collections.append(collection)
    return collections

def sort_collections(menu_dict, collections):
    collection_dict = {collection_name:[] for collection_name in collections}
    for collection in collection_dict:
        for cocktail in menu_dict:
            try:
                if menu_dict[cocktail]["collection"].title() == collection:
                    collection_dict[collection].append(cocktail)
            except KeyError as e:
                pass
                # print(f"Sorting collections raised key error {e} -- {cocktail} does not have 'collection' field.")
    
    return collection_dict

def load_used_ingredients(menu_dict):
    ingredient_list = []
    for cocktail in menu_dict:
        temp_ingredients = list(menu_dict[cocktail]["ingredients"].keys())
        for ingredient in temp_ingredients:
            if ingredient not in ingredient_list:
                ingredient_list.append(ingredient)

    return ingredient_list

def load_all_ingredients():
    """_summary_

    Returns:
        list, dict: list of text-formatted ingredients, dictionary of ingredient:location
    """
    all_ingredients = pd.read_csv(os.path.join(dir_path, "config/ingredients.csv"), names=["ingredients", "locations"])
    all_ingredients_list =  list(all_ingredients["ingredients"])
    # all_ingredients_formatted = [ingredient.replace("_", " ").title() for ingredient in all_ingredients_list]
    locations = list(all_ingredients["locations"])
    location_dict = {ingredient:location for ingredient, location in zip(all_ingredients_list, locations)}

    # print(location_dict)

    return all_ingredients_list, location_dict

# -------------------- FUZZY STRINGS -------------------- #
def get_closest_match(x, list_random, verbose=False):
    best_match = None
    highest_jaro = 0
    close_to = []
    for current_string in list_random:
        current_score = jf.jaro_similarity(x, current_string)
        if current_score > similarity_threshold:
            close_to.append(current_string)
        if(current_score > highest_jaro):
            highest_jaro = current_score
            best_match = current_string

    if verbose:
        if len(close_to) > 1:
                print(f"Watch out: {x} is close to {close_to}. Choosing {best_match}")

    return best_match, highest_jaro

def check_match(given_input, valid_names, match_threshold=0.875):
    # checks to see if a given tag is close to a key in tags_dict. If it is, it replaces the given tag with the key
    # tag_names = load_tags(tags_dict)
    best_match, score = get_closest_match(given_input, valid_names)
    # print(given_tag, best_match, score)
    if score > match_threshold:
        return True, best_match, score
    else:
        return False, given_input, score

def test_similarity(used_ingredients, all_ingredients):
    for used in used_ingredients:
        result, score = get_closest_match(used, all_ingredients, verbose=True)
        print(used, "|", result, "|", score)

def get_closest_match_list(x_list, list_random):
    best_match = None
    best_score = 0
    for x in x_list:
        result, score = get_closest_match(x, list_random)
        if score > best_score:
            best_match = result
            best_score = score

    # print(x_list)
    # print(best_match, best_score)
    # print("---")
    
    return best_match, best_score

# -------------------- TAGS & ALIASES -------------------- #
def expand_tag(given_tag, tags_dict):
    tag_names = load_tags(tags_dict)
    parents = [given_tag]
    children = []
    timeout = 10

    # Stops after 10 iterations as a failsafe -- . If we accidentally put in circular tags, it'll spin and spin
    i = 0
    while len(parents) > 0:
        if i > timeout:
            print(f"Error: circular tags detected: {parents}")
            return False
        
        for parent in parents:
            # Remove the expanded tag
            parents.remove(parent)

            # If our parent is a tag, expand it into kids
            tag, parent, _ = check_match(parent, tag_names)
            if tag:
                kids = list(tags_dict[parent]["ingredients"].keys())
                # For each of those kids...
                for kid in kids:
                    # If it's a tag, put it in parents
                    tag, kid, _ = check_match(kid, tag_names)
                    if tag:
                        parents.append(kid)
                    # Otherwise, put it in children
                    else:
                        children.append(kid)
            
        i += 1

    # print(f"{given_tag} expanded to {children}")

    if len(children) > 0:
        return children
    else:
        return False

def expand_alias(ingredient, alias_dict:dict):
    """Gets any aliases of the given ingredient. Does some string format control

    Args:
        ingredient (str): _description_
        alias_dict (dict): _description_

    Returns:
        list: aliases (if no aliases found, returns [ingredient])
    """
        
    ingredient = format_as_inventory(ingredient)
    names_to_check = [ingredient]

    # print(ingredient)
    # if it's a key, add its values
    if ingredient in alias_dict.keys():
        values = alias_dict[ingredient]
        [names_to_check.append(value) for value in values]

    # if it's a value, add its keys
    for key in alias_dict:
        aliases = alias_dict[key]
        if ingredient in aliases:
            names_to_check.append(key)

    # print(f"given {ingredient}, should check {names_to_check} against the ingredients list")

    return names_to_check

# -------------------- CHECKING INVENTORY -------------------- #
def is_in_stock(ingredient:str, ingredients_dict:dict, recipe_name:str, verbose=False, quiet=False):
    """Checks a given ingredient against our inventory (which has the location "none" if out of stock).

    Args:
        ingredient (str): _description_
        ingredients_dict (dict): _description_
        recipe_name (str): _description_
        verbose (bool, optional): _description_. Defaults to False.

    Returns:
        _type_: _description_
    """
    loc = ingredients_dict[ingredient].strip()
    if loc == "none":
        if not quiet:
            # print(quiet)
            ingredient = "\033[1m"+ingredient+"\033[0m"
            print(f"Could not validate {recipe_name}, {ingredient} out of stock")
        return False
    else:
        if verbose:
            print(f"Found {ingredient} in inventory list, location {loc}")
        return True

def validate_one_recipe(recipe:dict, all_ingredients:list, ingredients_dict:dict, recipe_name:str, tags_dict, alias_dict, verbose=False, quiet=False):
    # if all the ingredients of the recipe are good, recipe is good
    # otherwise, false
    if verbose:
        print(f"Checking {recipe_name}")

    tag_names = load_tags(tags_dict)
    recipe_ingredients = list(recipe.keys())
    ingredient_exists = False
    ingredient_in_stock = False

    for ingredient in recipe_ingredients:
        # First, check the ingredient name and any aliases it might be under
        ing_aliases = expand_alias(ingredient, alias_dict)
        if verbose:
            print(f"Checking {ingredient} (aliases {ing_aliases[1:]})")
        # For each alias: if we can find it, check if it's in stock. If not, break here
        for alias in ing_aliases:
            if alias in all_ingredients:
                ingredient_exists = True
                if not is_in_stock(alias, ingredients_dict, recipe_name, verbose, quiet):
                    return False
                else:
                    ingredient_in_stock = True
            # If we've found an ingredient that works, we can stop here
            if ingredient_in_stock:
                break
        # Then check if it's a tag, and repeat the process for any children
        if ingredient in tag_names:
            children = expand_tag(ingredient, tags_dict)
            # Get any aliases of each child and check them against the inventory list
            for child in children:
                tag_aliases = expand_alias(child, alias_dict)
                if verbose:
                    print(f"Found {child} (aliases {tag_aliases[1:]}) in the {ingredient} tag")
                for alias in tag_aliases:
                    if alias in all_ingredients:
                        ingredient_exists = True
                        if not is_in_stock(alias, ingredients_dict, recipe_name, verbose):
                            return False
                # If we've found an ingredient that works, we can stop here
                if ingredient_in_stock:
                    break
                    
        if not ingredient_exists:
            if not quiet:
                print(f"Could not validate {recipe_name}, {ingredient} not found in inventory or tags")
            return False
                
    return True

def validate_all_recipes(menu_dict:dict, all_ingredients_list, all_ingredients_dict, tags_dict, alias_dict, verbose=False, quiet=False):
    # should: make sure we have the ingredients to make a recipe
    # currently: makes too many of its own decisions

    # for each recipe, validate it. If it's good, keep it.
    # Otherwise, throw out the recipe and flag it (let us know)
    validated_menu = copy.deepcopy(menu_dict)
    for key in menu_dict:
        recipe = menu_dict[key]["ingredients"]
        if not validate_one_recipe(recipe, all_ingredients_list, all_ingredients_dict, key, tags_dict, alias_dict, verbose, quiet):
            validated_menu.pop(key)
    
    return validated_menu

# -------------------- ADDING THINGS VIA WEBSITE -------------------- #
def format_new_recipe_yaml(recipe_name:str, collection:str, notes:str, ingredients:list, amounts:list, units:list):
    # First build the ingredients dictionary. Loop through the list of strings and append accordingly
    ingredients_dict = {}
    for ingredient, amount, unit in zip(ingredients, amounts, units):
        ingredient = ingredient.replace("_", " ").title().strip()
        if ingredient == "":
            continue
        ingredients_dict.update({ingredient: {'amount': amount, 'units': unit}})
    # Then use the ingredients dict along with the other recipe info to build out the rest of the yaml
    new_recipe = {recipe_name: {'collection': collection, 'ingredients': ingredients_dict, 'notes': notes}}
    # Yay
    return new_recipe

def update_recipe_yaml(recipe_name:str, collection:str, notes:str, ingredients:list, amounts:list, units:list):
    recipe_path = os.path.join(dir_path, "config")

    # If we weren't given a collection, deal with that
    if collection.strip() == "":
        collection = "uncategorized"
    
    # Look for any recipe file that has the collection name. Should only be one file
    num_files = 0
    for file in glob.glob(f"{recipe_path}/recipes_*{collection.lower()}*.yml"):
        print(file)
        num_files += 1
    # If we haven't found any files, make a new one
    if num_files == 0:
        print(f"No file found for the {collection} collection. Making one")
        file = f"{recipe_path}/recipes_{collection.lower()}.yml"
        print(file)
        with open(file, 'x'):
            pass
    
    # If we've found too many, throw an error
    if num_files > 1:
        print(f"Found more than one recipe yaml with '{collection}' in the name. Is that intentional?")
    # Otherwise, open and update
    else:
        try:
            with open(file) as stream:
                menu_dict = yaml.safe_load(stream)
        except FileNotFoundError as e:
            print(e)
        else:
            new_recipe = format_new_recipe_yaml(recipe_name, collection, notes, ingredients, amounts, units)
            if type(menu_dict) == dict:
                menu_dict.update(new_recipe)
            else:
                menu_dict = new_recipe
                print("Expected dictionary, did not find one. Replacing file contents with new recipe")
            with open(file, 'w') as outfile:
                yaml.dump(menu_dict, outfile, default_flow_style=False)

def add_spirit(spirit:str, coord:str):
    """Updates or adds the given (spirit, coord) pair to ingredients.csv

    Args:
        spirit (str): _description_
        coord (str): _description_
    """
    # Check if the given coordinate is valid. If so...
    all_cabinet_locs = load_cabinet_locs()
    if coord in all_cabinet_locs.keys():
        # Format a new entry with the given location
        spirit = format_as_inventory(spirit)
        new_row = [spirit, coord]
        spirit_exists = False
        # Grab the old rows of the csv
        with open(os.path.join(dir_path, "config/ingredients.csv"), 'r') as orig:
            orig_rows = [row for row in csv.reader(orig)]

        # We want to avoid duplicate entries here, so first look through all existing rows of the csv.
        # If we find a match, update its position
        with open(os.path.join(dir_path, "config/ingredients.csv"), 'w', newline='') as file:
            writer = csv.writer(file)
            for row in orig_rows:
                # Try-except block in case we've done anything funny with the csv
                try:
                    # Jack likes having spaces in the csv for organization, so preserve that here
                    if len(row) == 0:
                        writer.writerow([])
                    # Write all other rows as they were
                    elif row[0] != spirit:
                        writer.writerow(row)
                    # Replace the one to "remove" with the new row: spirit_name, "none"
                    else:
                        writer.writerow(new_row)
                        spirit_exists = True
                except Exception as e:
                    print(e)

        # If we don't find a match, add the new spirit to the end
        if not spirit_exists:
            with open(os.path.join(dir_path, "config/ingredients.csv"), 'a') as csvfile:
                writer = csv.writer(csvfile, delimiter=',', lineterminator='\n\r')
                writer.writerow(new_row)
    else:
        print(f"Invalid coordinate {coord}")

def remove_spirit(spirit:str):
    """Removes the given spirit from ingredients.csv.

    Args:
        spirit (str): _description_
    """
    # Update the spirit inventory in preparation for csv writing
    new_row = [spirit, "none"]
    # Grab the old rows of the csv
    with open(os.path.join(dir_path, "config/ingredients.csv"), 'r') as orig:
        orig_rows = [row for row in csv.reader(orig)]
    # Make a new one with this one row changed
    with open(os.path.join(dir_path, "config/ingredients.csv"), 'w', newline='') as file:
        writer = csv.writer(file)
        for row in orig_rows:
            # Try-except block in case we've done anything funny with the csv
            try:
                # Jack likes having spaces in the csv for organization, so preserve that here
                if len(row) == 0:
                    writer.writerow([])
                # Write all other rows as they were
                elif row[0] != spirit:
                    writer.writerow(row)
                # Replace the one to "remove" with the new row: spirit_name, "none"
                else:
                    writer.writerow(new_row)
            except Exception as e:
                print(e)

# -------------------- FLAGGING OUR MISTAKES -------------------- #
def get_all_used_ingredients(menu_dict, tags_dict, verbose=False):
    """_summary_

    Args:
        menu_dict (dict): big menu dictionary, created by read_main_menu()
        tags_dict (dict): big tags dictionary, created by read_main_menu()
        verbose (bool, optional): Set True to print during the loop. Defaults to False.

    Returns:
        list: names of all ingredients used in recipes
    """
    # Load all the tag names
    tag_names = load_tags(tags_dict)
    # Initialize lists for the loops
    all_ingredience_once = set([])
    printed_tags = []
    # Now loop --
    # Pull out the ingredient from each recipe, avoiding duplicates
    for key in menu_dict:
        # Pull out the recipe and its ingredients
        recipe = menu_dict[key]["ingredients"]
        recipe_ingredients = list(recipe.keys())
        for ingredient in recipe_ingredients:
            # If we've found a tag, add all its children
            if ingredient in tag_names:
                children = expand_tag(ingredient, tags_dict)
                [all_ingredience_once.add(child) for child in children]
                # Optional printout of every tag identified (only once per tag)
                if verbose:
                    if ingredient not in printed_tags:
                        printed_tags.append(ingredient)
                        print(f"Tag identified: {ingredient}. \n Children: {children}")
            # Otherwise, just add the ingredient
            else:
                all_ingredience_once.add(ingredient)

    if verbose:
        print("\n All ingredients identified:")
        print(all_ingredience_once)

    return all_ingredience_once

def check_recipe_against_csv(menu_dict:dict, all_ingredients, tags_dict, alias_dict, verbose=False):
    """Checks each used ingredient against our master CSV, and throws a flag if it can't find a match. Used
    only for internal system checks.

    Formatting note -- We use Title Case in recipes (public facing) and snake_case in the ingredients list (internal). E.g
    Amaro Nonino in The Spanish Graft and amaro_nonino in ingredients.csv.

    Args:
        menu_dict (dict): _description_
        all_ingredients (_type_): _description_
        tags_dict (_type_): _description_
        alias_dict (_type_): _description_
    """
    # Identify all the ingredients we use throughout every recipe
    all_ingredience_once = get_all_used_ingredients(menu_dict, tags_dict, verbose)

    # Now do the flagging
    for ingredient in all_ingredience_once:
        # Check for any aliases, and reformat to match ingredients.csv
        aliases = expand_alias(ingredient, alias_dict)
        if verbose:
            print(f"Given {ingredient}, checking {aliases}")
        aliases = [format_as_inventory(alias) for alias in aliases]
        # If we couldn't find any aliases in our master ingredients list, throw a flag
        if not any((True for x in aliases if x in all_ingredients)):
            print("---")
            print(f"Could not find {ingredient} in ingredients list: looking for {aliases}")
            print()

if __name__ == "__main__":
    menu_dict, tags_dict, alias_dict = read_main_menu()
    # print(menu_dict)
    # print("---")
    # print(tags_dict)
    # print(alias_dict)

    # ingredients_list, ingredients_dict = load_all_ingredients()
    # print(ingredients)

    # menu_val = validate_all_recipes(menu_dict, ingredients_list, ingredients_dict, tags_dict, alias_dict, verbose=False)

    # print(menu_val)

    # check_recipe_against_csv(menu_dict, ingredients, tags_dict, alias_dict, verbose=False)

    update_recipe_yaml("test2", "blah", "notes", ["", "two"], ["", "2"], ["", "oz"])


    # recipe_names = load_recipe_names(menu_dict)
    # tag_names = load_tags(tags_dict)
    # collections = load_collection_names(menu_dict)

    # print(f"Full menu: {menu_dict}")
    # print("---")
    # print(f"Recipe names: {recipe_names}")
    # print("---")
    # print(f"Collections: {collections}")
    # print("---")

    # used_ingredients = load_used_ingredients(menu_dict)
    # print(f"Used ingredients: {used_ingredients}")
    # print("---")

    # tags, not_tags = check_tags(used_ingredients, recipe_names)
    # print(f"Tags: {tags}")
    # print(f"Not tags: {not_tags}")
        
    # for ingredient in used_ingredients:
    #     children = expand_tag(ingredient, tags_dict)
    #     if children:
    #         print(f"expanded {ingredient} to {children}")

    # all_ingredients, location_dict = load_all_ingredients()
    # print(location_dict)
    # print(all_ingredients)

    # # Test the similarity metric and the validation
    # test_similarity(used_ingredients, all_ingredients)
    # validate_all_recipes(menu_dict, all_ingredients, tags_dict, alias_dict, verbose=True)

    # # Test the new recipe formatting
    # corn_and_oil = format_new_recipe_yaml('Corn and Oil', 'Classics', "Ali's favorite. Stirred", 
    #                                       ['Rum', 'Falernum', 'Lime'], ['1', '1', ''], ['oz', 'oz', 'squeeze'])
    # print("---")
    # menu_dict.update(corn_and_oil)
    # print(menu_dict)

    # # Test the yaml updating
    # update_recipe_yaml('Corn and Oil', 'Classics', "Ali's favorite. Stirred, preferably with big ice cube. This was written from recipe_parsing_helpers.py", 
    #                                       ['Rum', 'Falernum', 'Lime'], ['1', '1', ''], ['oz', 'oz', 'squeeze'])

    # print(load_cabinet_locs().keys())

    # update_cabinet_locs("test", "G7")

    # remove_spirit("website_test_spirit")