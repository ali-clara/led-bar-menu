# testing recipe formatting and inputs
import yaml
import copy
import pandas as pd
import os
import jellyfish as jf
import glob
import numpy as np
import csv

# similarity_threshold = 0.75

def format_as_inventory(input_str:str):
    return input_str.replace(" ", "_").lower().strip()

def format_as_recipe(input_str:str):
    return input_str.replace("_", " ").title().strip()

class Menu:
    def __init__(self):
        self.dir_path = os.path.join(os.path.dirname( __file__ ), os.pardir)
        self.recipe_path = os.path.join(self.dir_path, "config")
        
        # Big menu, matches the layout of the yamls
        self.menu_dict = self.load_recipes()
        # Dictionary of all tags {tag: {ingredients: [spirit_1, spirit_2, ..., spirit_n], notes: , etc}}, dictionary of organized tags {parent_tag: [tag_1, tag_2, ..., tag_n]}
        self.tags_dict_all, self.tags_dict_organized = self.load_tags()
        self.alias_dict = self.load_aliases()
        # Dictionary of {coordinate:led pixels}, list of coordinates
        self.led_dict, self.cabinet_locations = self.load_cabinet_locs()
        # Pull info from ingredients.csv: 
        # List of spirits (& other), dictionary of {spirit:location}, set of locations
        self.inventory, self.spirit_dict, self.used_locations = self.load_all_ingredients()
        # List of used locations not in the cabinet (e.g "fridge")
        self.non_cabinet_locations = self.used_locations.difference(self.cabinet_locations)
        # List of collection names
        self.hidden_collections = ["Debug"]
        self.collections = self.get_collection_names()

        self.similarity_threshold = 0.75

    
    # -------------------- LOADING & READING -------------------- #
    def load_recipes(self):
        recipes_dict = {}
        try:
            for file in glob.glob(self.recipe_path+"/recipes*.yml"):
                with open(file) as stream:
                        recipes_dict.update(yaml.safe_load(stream))
        except TypeError as e:
            print(f"Failed to read {file}: {e}")
        except FileNotFoundError as e:
            print(e)
        else:
            return recipes_dict
        
    def load_tags(self):
        tags_dict_all = {}
        tags_dict_organized = {}
        
        try:
            for file in glob.glob(self.recipe_path+"/tags*.yml"):
                with open(file) as stream:
                    # All tags (tag: {ingredients: [spirit_1, spirit_2, ..., spirit_n], notes: , etc})
                    contents = yaml.safe_load(stream)
                    tags_dict_all.update(contents)
                    # Organized tags (parent_tag: [tag_1, tag_2, ..., tag_n])
                    filename = file.split(os.path.sep)[-1]
                    tag_names = list(contents.keys())
                    tags_dict_organized.update({filename: tag_names})
        except TypeError as e:
            print(f"Failed to read {file}: {e}")
        except FileNotFoundError as e:
            print(e)
        else:
            return tags_dict_all, tags_dict_organized
        
    def load_aliases(self):
        try:
            file = os.path.join(self.recipe_path, "aliases.yml")
            with open(file) as stream:
                alias_dict = yaml.safe_load(stream)
        except TypeError as e:
            print(f"Failed to read {file}: {e}")
        except FileNotFoundError as e:
            print(e)
        else:
            alias_dict_restructured = {}
            for key in alias_dict:
                aliases = list(alias_dict[key]["ingredients"].keys())

                aliases = [format_as_inventory(alias) for alias in aliases]
                key = format_as_inventory(key)

                alias_dict_restructured.update({key:aliases})
            return alias_dict_restructured
        
    def load_cabinet_locs(self) -> dict:
        """Loads all the cabinet locations and their corresponding led pixel indices. See the ReadMe for more details on the location
        setup - briefly, rows are letters (A-N) and 'columns' are numbers (1-7)(I think).

        Returns:
            dict: Location: [[start pix 1, stop pix 1], ... [start pix n, stop pix n]]
        """
        try:
            file = os.path.join(self.recipe_path, "led_locs_final.yml")
            with open(file) as stream:
                led_locations_dict = yaml.safe_load(stream)
        except FileNotFoundError as e:
            print(e)
        else:
            cabinet_locations = list(led_locations_dict.keys())
            cabinet_locations.sort()
            return led_locations_dict, cabinet_locations
    
    def load_all_ingredients(self):
        """_summary_

        Returns:
            list, dict: list of text-formatted ingredients, dictionary of ingredient:location
        """
        all_ingredients = pd.read_csv(os.path.join(self.recipe_path, "ingredients.csv"), names=["ingredients", "locations"])
        all_ingredients_list =  list(all_ingredients["ingredients"])
        locations = [loc.strip() for loc in all_ingredients["locations"]]
        location_dict = {ingredient:location for ingredient, location in zip(all_ingredients_list, locations)}
        # Pull a list of all used locations from the values of that dictionary
        used_locations = set(location_dict.values())

        return all_ingredients_list, location_dict, used_locations
        
    def get_recipe_names(self):
        return list(self.menu_dict.keys())
    
    def get_tag_names(self):
        return list(self.tags_dict_all.keys())
    
    def get_used_ingredients(self):
        ingredient_list = set([])
        for cocktail in self.menu_dict:
            try:
                # temp_ingredients = list(self.menu_dict[cocktail]["ingredients"].keys())
                [ingredient_list.add(ing) for ing in self.menu_dict[cocktail]["ingredients"].keys()]
                # for ingredient in temp_ingredients:
                #     if ingredient not in ingredient_list:
                #         ingredient_list.append(ingredient)
            except KeyError as e:
                print(f"Parsing ingredients raised key error -- {cocktail} does not have {e} field.")

        return ingredient_list
    
    def get_collection_names(self):
        collections = []
        for cocktail in self.menu_dict:
            # Grab what collection it belongs to, correcting for capitalization just in case.
            try:
                collection = self.menu_dict[cocktail]['collection'].title()
            except KeyError as e:
                    print(f"Parsing collections raised key error -- {cocktail} does not have {e} field.")
            # Check if its in our list of collections. If it's not, add it.
            else:
                if collection not in collections and collection not in self.hidden_collections:
                    collections.append(collection)

        return collections
    
    def sort_by_collections(self):
        collection_dict = {collection_name:[] for collection_name in self.collections}
        for collection in collection_dict:
            for cocktail in self.menu_dict:
                try:
                    if self.menu_dict[cocktail]["collection"].title() == collection:
                        collection_dict[collection].append(cocktail)
                except KeyError as e:
                    print(f"Sorting collections raised key error {e} -- {cocktail} does not have 'collection' field.")
        
        return collection_dict
    
    # -------------------- TAGS & ALIASES -------------------- #
    def expand_tag(self, given_tag:str):
        """Fully expands a tag into all its children. 'Brandy (inclusive) becomes ['boulard_calvados', 'pear_williams', 
        'christian_brothers_vs', 'christian_brothers_vsop', 'placeholder_fig_brandy', 'fidelitas_kirsch']

        Args:
            given_tag (str): Tag name

        Returns:
            list: children

            OR
            
            False: input has no children
        """
        tag_names = self.get_tag_names()
        parents = [given_tag]
        children = []
        timeout = 10

        # Stops after 10 iterations as a failsafe -- If we accidentally put in circular tags, it'll spin and spin
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
                    kids = list(self.tags_dict_all[parent]["ingredients"].keys())
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

    def expand_alias(self, ingredient:str):
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
        if ingredient in self.alias_dict.keys():
            values = self.alias_dict[ingredient]
            [names_to_check.append(value) for value in values]

        # if it's a value, add its keys
        for key in self.alias_dict:
            aliases = self.alias_dict[key]
            if ingredient in aliases:
                names_to_check.append(key)

        # print(f"given {ingredient}, should check {names_to_check} against the ingredients list")

        return names_to_check

    def find_tag_parent(self, tag:str):
        """Finds the "parent" of a tag. "tags_rum.yml" is the parent of Cachaca, Planteray Light Rum, etc

        Args:
            tag (str): _description_

        Returns:
            str: Parent tag, if it exists. Otherwise returns None
        """
        for parent_tag in self.tags_dict_organized:
            if tag in self.tags_dict_organized[parent_tag]:
                return parent_tag
            
        print(f"Could not find parent tag for {tag}")

    # -------------------- CHECKING INVENTORY -------------------- #
    def is_in_stock(self, ingredient:str, recipe_name:str, verbose=False, quiet=False):
        """Checks a given ingredient against our inventory (which has the location "none" if out of stock).

        Args:
            ingredient (str): _description_
            recipe_name (str): _description_
            verbose (bool, optional): _description_. Defaults to False.

        Returns:
            _type_: _description_
        """
        loc = self.spirit_dict[ingredient].strip()
        if loc == "none":
            if not quiet:
                ingredient = "\033[1m"+ingredient+"\033[0m"
                print(f"Could not validate {recipe_name}, {ingredient} out of stock")
            return False
        else:
            if verbose:
                print(f"Found {ingredient} in inventory list, location {loc}")
            return True
    
    def validate_one_recipe(self, recipe:dict, recipe_name:str, verbose=False, quiet=False):
        # if all the ingredients of the recipe are good, recipe is good
        # otherwise, false
        if verbose:
            print(f"Checking {recipe_name}")

        tag_names = self.get_tag_names()
        recipe_ingredients = list(recipe.keys())
        ingredient_exists = False
        ingredient_in_stock = False

        for ingredient in recipe_ingredients:
            # First, check the ingredient name and any aliases it might be under
            ing_aliases = self.expand_alias(ingredient)
            if verbose:
                print(f"Checking {ingredient} (aliases {ing_aliases[1:]})")
            # For each alias: if we can find it, check if it's in stock. If not, break here
            for alias in ing_aliases:
                if alias in self.inventory:
                    ingredient_exists = True
                    if not self.is_in_stock(alias, recipe_name, verbose, quiet):
                        return False
                    else:
                        ingredient_in_stock = True
                # If we've found an ingredient that works, we can stop here
                if ingredient_in_stock:
                    break
            # Then check if it's a tag, and repeat the process for any children
            if ingredient in tag_names:
                children = self.expand_tag(ingredient)
                # Get any aliases of each child and check them against the inventory list
                for child in children:
                    tag_aliases = self.expand_alias(child)
                    if verbose:
                        print(f"Found {child} (aliases {tag_aliases[1:]}) in the {ingredient} tag")
                    for alias in tag_aliases:
                        if alias in self.inventory:
                            ingredient_exists = True
                            if not self.is_in_stock(alias, recipe_name, verbose):
                                return False
                            else:
                                ingredient_in_stock = True
                    # If we've found an ingredient that works, we can stop here
                    if ingredient_in_stock:
                        break
                        
            if not ingredient_exists:
                if not quiet:
                    print(f"Could not validate {recipe_name}, {ingredient} not found in inventory or tags")
                return False
                    
        return True

    def validate_all_recipes(self, verbose=False, quiet=False):
        # Makes sure we have the ingredients to make a recipe

        # for each recipe, validate it. If it's good, keep it.
        # Otherwise, throw out the recipe and flag it (let us know)
        validated_menu = copy.deepcopy(self.menu_dict)
        for key in self.menu_dict:
            recipe = self.menu_dict[key]["ingredients"]
            if not self.validate_one_recipe(recipe, key, verbose, quiet):
                validated_menu.pop(key)
        
        return validated_menu


myMenu = Menu()
dir_path = myMenu.dir_path
load_tag_names = myMenu.get_tag_names
similarity_threshold = myMenu.similarity_threshold

# -------------------- FUZZY STRINGS -------------------- #
def get_closest_match(x, to_check_against, verbose=False):
    best_match = None
    highest_jaro = 0
    close_to = []
    for current_string in to_check_against:
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
    best_match, score = get_closest_match(given_input, valid_names)
    # print(given_tag, best_match, score)
    if score > match_threshold:
        return True, best_match, score
    else:
        return False, given_input, score

def test_similarity(list_to_match:list, to_check_against:list):
    for used in list_to_match:
        result, score = get_closest_match(used, to_check_against, verbose=True)
        print(used, "|", result, "|", score)


# -------------------- ADDING THINGS VIA WEBSITE -------------------- #
def format_new_recipe_yaml(recipe_name:str, collection:str, notes:str, ingredients:list, amounts:list, units:list):
    # First build the ingredients dictionary. Loop through the list of strings and append accordingly
    ingredients_dict = {}
    for ingredient, amount, unit in zip(ingredients, amounts, units):
        ingredient = format_as_recipe(ingredient)
        if ingredient == "":
            continue
        ingredients_dict.update({ingredient: {'amount': amount, 'units': unit}})
    # Then use the ingredients dict along with the other recipe info to build out the rest of the yaml
    recipe_name = recipe_name.title()
    new_recipe = {recipe_name: {'collection': collection, 'ingredients': ingredients_dict, 'notes': notes}}
    # Yay
    return new_recipe, recipe_name

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
            new_recipe, recipe_name = format_new_recipe_yaml(recipe_name, collection, notes, ingredients, amounts, units)
            if type(menu_dict) == dict:
                menu_dict.update(new_recipe)
            else:
                menu_dict = new_recipe
                print("Expected dictionary, did not find one. Replacing file contents with new recipe")
            with open(file, 'w') as outfile:
                yaml.dump(menu_dict, outfile, sort_keys=False)
            return True, recipe_name
        
    return False, recipe_name

def add_spirit(spirit:str, coord:str, tags:list, tags_dict_organized:dict):
    """Updates or adds the given (spirit, coord) pair to ingredients.csv

    Args:
        spirit (str): _description_
        coord (str): _description_
    """
    # Check if the given coordinate is valid. If so...
    # all_cabinet_locs = load_cabinet_locs()
    # if coord in all_cabinet_locs.keys():

    # String formatting
    spirit = format_as_inventory(spirit)
    # If it's a coordinate (has a number), format as such (uppercase). Otherwise, make it lowercase
    if any(char.isnumeric() for char in coord):
        coord = coord.upper()
    else:
        coord = format_as_inventory(coord)

    # Add the spirit to the appropriate tags
    print(f"adding {spirit} to {tags}")
    result = add_spirit_to_tag_list(spirit, tags, tags_dict_organized)
    if not result:
        print(f"Failed to add {spirit} to tags. Not updating inventory.")
        return False

    # Format a new entry with the given location
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
    
    if spirit_exists:
        return True
    else:
        with open(os.path.join(dir_path, "config/ingredients.csv"), 'a') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', lineterminator='\n\r')
            writer.writerow(new_row)
            return True
    
    
    return False

def remove_spirit(spirit:str):
    """Removes the given spirit from ingredients.csv.

    Args:
        spirit (str): _description_
    """
    # Update the spirit inventory in preparation for csv writing
    spirit = format_as_inventory(spirit)
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
                    return True
            except Exception as e:
                print(e)
    return False

def add_spirit_to_tag(spirit:str, tag:str, tags_dict_organized:dict):
    recipe_path = os.path.join(dir_path, "config")
    parent = find_tag_parent(tag, tags_dict_organized)
    if parent:
        parent_file = os.path.join(recipe_path, parent)
        with open(parent_file, 'r') as stream:
            data_dict = yaml.safe_load(stream)
        try:
            # Update the "ingredients" key of the tag to include the new spirit
            data_dict[tag]["ingredients"].update({spirit: {}})
        except KeyError as e:
            print(e)
        else:
            with open(parent_file, 'w') as outfile:
                yaml.dump(data_dict, outfile, sort_keys=False)
            return True
    else:
        print(f"Unable to add {spirit} to {tag} - no parent")
        return False

def add_spirit_to_tag_list(spirit:str, tags:list, tags_dict_organized:dict):
    results = []
    for tag in tags:
        print(tag)
        result = add_spirit_to_tag(spirit, tag, tags_dict_organized)
        results.append(result)
        if not result:
            print(f"Failed to add {spirit} to {tag}")

    if all(results):
        return True
    else:
        return False

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
    tag_names = load_tag_names(tags_dict)
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


    # print(myMenu.expand_tag("Brandy (inclusive)"))
    # print(myMenu.expand_alias("Amaro 04"))
    # print(myMenu.find_tag_parent("Planteray Light Rum"))

    print(myMenu.validate_all_recipes())


    # menu_dict, tags_dict_all, tags_dict_organized, alias_dict = read_main_menu()
    # print(menu_dict)
    # print("---")
    # print(alias_dict)

    # add_spirit_to_tag("test wine", "Vermouth", tags_dict_organized)

    # ingredients_list, ingredients_dict = load_all_ingredients()
    # print(ingredients)

    # menu_val = validate_all_recipes(menu_dict, ingredients_list, ingredients_dict, tags_dict, alias_dict, verbose=False)

    # print(menu_val)

    # check_recipe_against_csv(menu_dict, ingredients, tags_dict, alias_dict, verbose=False)

    # update_recipe_yaml("test2", "blah", "notes", ["", "two"], ["", "2"], ["", "oz"])


    # recipe_names = load_recipe_names(menu_dict)
    # tag_names = load_tag_names(tags_dict)
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