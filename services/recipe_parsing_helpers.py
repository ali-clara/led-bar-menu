# testing recipe formatting and inputs
import yaml
import copy
import pandas as pd
import os
import jellyfish as jf
import glob
import numpy as np

dir_path = os.path.join(os.path.dirname( __file__ ), os.pardir)
similarity_threshold = 0.75
tag_threshold = 0.875

def read_main_menu():
    recipes_dict = {}
    tags_dict = {}
    recipe_path = os.path.join(dir_path, "config")
    try:
        for file in glob.glob(recipe_path+"/recipes*.yml"):
            with open(file) as stream:
                recipes_dict.update(yaml.safe_load(stream))
    except FileNotFoundError as e:
        print(e)
        recipes_dict = {}

    try:
        for file in glob.glob(recipe_path+"/tags*.yml"):
            with open(file) as stream:
                tags_dict.update(yaml.safe_load(stream))
    except FileNotFoundError as e:
        print(e)
        tags_dict = {}

    try:
        file = dir_path+"/config/aliases.yml"
        with open(file) as stream:
            alias_dict = yaml.safe_load(stream)
    except FileNotFoundError as e:
        print(e)
        alias_dict = {}
    else:
        alias_dict_restructured = {}
        for key in alias_dict:
            aliases = list(alias_dict[key]["ingredients"].keys())

            aliases = [alias.lower() for alias in aliases]
            key = key.lower()

            alias_dict_restructured.update({key:aliases})

    return recipes_dict, tags_dict, alias_dict_restructured

def load_recipe_names(menu_dict):
    return list(menu_dict.keys())

def load_tags(tags_dict):
    return list(tags_dict.keys())

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
    all_ingredients = pd.read_csv(os.path.join(dir_path, "config/ingredients.csv"), names=["ingredients", "locations"])
    all_ingredients_list =  list(all_ingredients["ingredients"])
    all_ingredients_formatted = [ingredient.replace("_", " ").title() for ingredient in all_ingredients_list]
    locations = list(all_ingredients["locations"])
    location_dict = {ingredient:location for ingredient, location in zip(all_ingredients_formatted, locations)}

    return all_ingredients_formatted, location_dict

def get_closest_match(x, list_random, threshold=similarity_threshold, verbose=False):
    best_match = None
    highest_jaro = 0
    close_to = []
    for current_string in list_random:
        current_score = jf.jaro_similarity(x, current_string)
        if current_score > threshold:
            close_to.append(current_string)
        if(current_score > highest_jaro):
            highest_jaro = current_score
            best_match = current_string

    if verbose:
        if len(close_to) > 1:
                print(f"Watch out: {x} is close to {close_to}. Choosing {best_match}")

    return best_match, highest_jaro
                
def check_alias(ingredient, alias_dict:dict):
        
    names_to_check = [ingredient]
    ingredient = ingredient.lower()

    ## should add string validation to all this

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

def check_tags(ingredient_list:list, recipe_list:list):
    not_tags = copy.deepcopy(recipe_list)
    tags = []

    for ingredient in ingredient_list:
        if ingredient in recipe_list:
            not_tags.remove(ingredient)
            tags.append(ingredient)

    return tags, not_tags

def check_tag(given_tag, tag_names):
    # checks to see if a given tag is close to a key in tags_dict. If it is, it replaces the given tag with the key
    # tag_names = load_tags(tags_dict)
    best_match, score = get_closest_match(given_tag, tag_names)
    # print(given_tag, best_match, score)
    if score > tag_threshold:
        return True, best_match, score
    else:
        return False, given_tag, score

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
            tag, parent, _ = check_tag(parent, tag_names)
            if tag:
                kids = list(tags_dict[parent]["ingredients"].keys())
                # For each of those kids...
                for kid in kids:
                    # If it's a tag, put it in parents
                    tag, kid, _ = check_tag(kid, tag_names)
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

def validate_ingredient(ingredient:str, all_ingredients, recipe_name, tags_dict, alias_dict, verbose):
    # if score is over threshold, ingredient is good. Replace with name in 'ingredients.csv' master doc
    # otherwise, check if it's a tag. If so, check if we have ~any~ acceptable 
    # otherwise, false
    # Check and see if there's an alias for our ingredient (e.g "meletti" and "amaro meletti")
    aliases = check_alias(ingredient, alias_dict)
    # Use string comparison to get the closest match between the ingredient we're looking at (from a recipe)
    # and our master list of ingredients
    best_match, match_score = get_closest_match_list(aliases, all_ingredients)
    # Check and see if we're dealing with a tag instead of a single ingredient
    # children = expand_tag(ingredient, tags_dict)
    tag_names = load_tags(tags_dict)
    tag, tag_name, tag_score = check_tag(ingredient, tag_names)
    # If we've identified a tag, check a match for each child
    if tag:
        children = expand_tag(tag_name, tags_dict)
        children_scores = []
        children_matches = []
        for child in children:
            child = child.replace("_", " ").title()
            match, child_score = get_closest_match(child, all_ingredients)
            children_scores.append(child_score)
            children_matches.append(match)
        # If we've found a match, return the tag
        if any(np.array(children_scores) > similarity_threshold):
            if verbose:
                print(f"tag   - {ingredient} -> {tag_name}, {tag_score}")
            return tag_name
    # Otherwise, if we've gotten a match, return it
    if match_score > similarity_threshold:
        if verbose:
            print(f"match - {ingredient} -> {best_match}, {match_score}")
        return best_match
    
    # Otherwise, no can do chief. Return False
    else:
        print(f"Warning: Could not validate {recipe_name}, {ingredient} is below the similarity threshold.")
        return False

def validate_one_recipe(recipe:dict, all_ingredients:list, recipe_name:str, tags_dict, alias_dict, verbose):
    # if all the ingredients of the recipe are good, recipe is good
    # otherwise, false
    recipe_ingredients = list(recipe.keys())
    for ingredient in recipe_ingredients:
        validated = validate_ingredient(ingredient, all_ingredients, recipe_name, tags_dict, alias_dict, verbose)
        if not validated:
            return False
        else:
            recipe[validated] = recipe.pop(ingredient)

    return recipe

def validate_all_recipes(menu_dict:dict, all_ingredients, tags_dict, alias_dict, verbose=False):
    # for each recipe, validate it. If it's good, keep it.
    # Otherwise, throw out the recipe and flag it (let us know)
    validated_menu = copy.deepcopy(menu_dict)
    for key in menu_dict:
        recipe = menu_dict[key]["ingredients"]
        validated = validate_one_recipe(recipe, all_ingredients, key, tags_dict, alias_dict, verbose)
        if not validated:
            validated_menu.pop(key)
        else:
            validated_menu[key].update({"ingredients": validated})
    
    return validated_menu

if __name__ == "__main__":
    menu_dict, tags_dict, alias_dict = read_main_menu()
    recipe_names = load_recipe_names(menu_dict)
    tag_names = load_tags(tags_dict)
    collections = load_collection_names(menu_dict)
    # print(f"Full menu: {menu_dict}")
    # print("---")
    # print(f"Recipe names: {recipe_names}")
    # print("---")
    # print(f"Collections: {collections}")
    # print("---")

    used_ingredients = load_used_ingredients(menu_dict)
    # print(f"Used ingredients: {used_ingredients}")
    # print("---")

    # tags, not_tags = check_tags(used_ingredients, recipe_names)
    # print(f"Tags: {tags}")
    # print(f"Not tags: {not_tags}")
        
    # for ingredient in used_ingredients:
    #     children = expand_tag(ingredient, tags_dict)
    #     if children:
    #         print(f"expanded {ingredient} to {children}")

    all_ingredients, location_dict = load_all_ingredients()
    # print(all_ingredients)

    # test_similarity(used_ingredients, all_ingredients)
    validate_all_recipes(menu_dict, all_ingredients, tags_dict, alias_dict, verbose=True)