# testing recipe formatting and inputs
import yaml
import copy
import pandas as pd
import os
import jellyfish as jf
import glob

dir_path = os.path.join(os.path.dirname( __file__ ), os.pardir)
similarity_threshold = 0.75

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

    return recipes_dict, tags_dict

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
    all_ingredients = pd.read_csv(os.path.join(dir_path, "config/ingredients.csv"), header=None)
    all_ingredients_list =  list(all_ingredients[0])
    all_ingredients_formatted = [ingredient.replace("_", " ").title() for ingredient in all_ingredients_list]

    return all_ingredients_formatted
                
def check_tags(ingredient_list:list, recipe_list:list):
    not_tags = copy.deepcopy(recipe_list)
    tags = []

    for ingredient in ingredient_list:
        if ingredient in recipe_list:
            not_tags.remove(ingredient)
            tags.append(ingredient)

    return tags, not_tags

def expand_tag(given_tag, tags_dict):
    tag_names = load_tags(tags_dict)
    parents = [given_tag]
    children = []

    while len(parents) > 0:
        for parent in parents:
            if parent in tag_names:
                kids = list(tags_dict[parent]["ingredients"].keys())
                for kid in kids:
                    if kid in tag_names:
                        parents.append(kid)
                    else:
                        children.append(kid)
            parents.remove(parent)

    print(f"{given_tag} expanded to {children}")


def get_closest_match(x, list_random):
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

    if len(close_to) > 1:
            print(f"Warning: {x} is close to {close_to}. Choosing {best_match}")
    return best_match, highest_jaro

def test_similarity(used_ingredients, all_ingredients):
    for used in used_ingredients:
        result, score = get_closest_match(used, all_ingredients)
        print(used, "|", result, "|", score)

def validate_ingredient(ingredient:str, all_ingredients, recipe_name):
    # if score is over threshold, ingredient is good. Replace with name in 'ingredients.csv' master doc
    # otherwise, false
    result, score = get_closest_match(ingredient, all_ingredients)
    if score > similarity_threshold:
        return result
    else:
        print(f"Warning: Could not validate {recipe_name}, {ingredient} is below the similarity threshold.")
        return False

def validate_one_recipe(recipe:dict, all_ingredients:list, recipe_name:str):
    # if all the ingredients of the recipe are good, recipe is good
    # otherwise, false
    recipe_ingredients = list(recipe.keys())
    for ingredient in recipe_ingredients:
        validated = validate_ingredient(ingredient, all_ingredients, recipe_name)
        if not validated:
            return False
        else:
            recipe[validated] = recipe.pop(ingredient)

    return recipe

def validate_all_recipes(menu_dict:dict, all_ingredients):
    # for each recipe, validate it. If it's good, keep it.
    # Otherwise, throw out the recipe and flag it (let us know)
    validated_menu = copy.deepcopy(menu_dict)
    for key in menu_dict:
        recipe = menu_dict[key]["ingredients"]
        validated = validate_one_recipe(recipe, all_ingredients, key)
        if not validated:
            validated_menu.pop(key)
        else:
            validated_menu[key].update({"ingredients": validated})
    
    return validated_menu

if __name__ == "__main__":
    menu_dict, tags_dict = read_main_menu()
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

        
    for i, ingredient in enumerate(used_ingredients):
        expand_tag(ingredient, tags_dict)

    

    # print(used_ingredients)


    # all_ingredients = load_all_ingredients()

    # test_similarity(used_ingredients, all_ingredients)

    # validate_all_recipes(menu_dict, all_ingredients)