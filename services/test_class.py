# The imports
from flask import Flask, render_template, redirect, url_for
from flask_classful import FlaskView, method, route, request
try:
    from led import LED
except ImportError:
    from services.led import LED

import yaml
import concurrent.futures
import os
import threading

try: # run from this script
    import recipe_parsing_helpers as recipe
    from randomizer import Randomizer as rands
except ImportError: # run from the main script
    from services import recipe_parsing_helpers as recipe
    from services.randomizer import Randomizer as rands


def format_for_web(string:str):
    return string.replace("_", " ").title()

dir_path = os.path.join(os.path.dirname( __file__ ), os.pardir)
# app = Flask(__name__, template_folder=dir_path+"/templates")

class TestView(FlaskView):

    def __init__(self) -> None:

        self.main_menu = recipe.Menu()

        print("init")
        super().__init__()
        self.lights = LED()
        self.lit_up_ingredients = []
        self.random_ten = []
        # self.multiprocess = multiprocessing.Process()


        # self.input_spirit = ""
        # self.input_coord = ""
        # self.input_tags = []

    def _quick_update(self):
        self.lights._forbid_flashing()
        self.main_menu.update()
        self.lights.update()
        
    
    def _full_update(self):
        pass
    
    def index(self):
        """The main page. Redirects to the menu
        This lives at http://localhost:5000/ or http://10.0.0.120:5000
        """
        return redirect(url_for('TestView:menu'), code=301)

    def not_found(self):
        return render_template("error404.html")

    @method("POST")
    @method("GET")
    def menu(self):
        """http://localhost:5000/menu"""

        self._quick_update()

        # print(f"available cocktails: {self.cocktail_names}")
        # print(f"collections: {self.collection_names}")

        # These may become class vars eventually
        chosen_ingredients = [] # proxy for led lights
        chosen_collection = None

        # If we've gotten a change of state on the server (in this case, due to user entry),
        #   take a look at it.
        if request.method == "POST":
            # Clear the LEDS, if they're on
            self.lights.all_off()
            self.lit_up_ingredients = []

            # When "post" is triggered, take a look at what happened in the HTML form. The value "request.form" is
            # a dictionary with key-value pairs "element-name" "element-entry". We use "element-name" to determine which
            # button was selected, and "element-entry" to determine the input info
            element_name = list(request.form.keys())[0]
            form_entry = request.form.get(element_name)

            # If the form has returned a cocktail, process that
            if element_name == "cocktail input":

                is_recipe, recipe_match, recipe_score = recipe.check_match(form_entry, self.main_menu.get_recipe_names(), match_threshold=0.705)
                print(is_recipe, recipe_match, recipe_score)
                is_ingredient, ingredient_match, ingredient_score = recipe.check_match(form_entry, self.main_menu.get_inventory(), match_threshold=0.75)
                print(is_ingredient, ingredient_match, ingredient_score)
                is_tag, tag_match, tag_score = recipe.check_match(form_entry, self.main_menu.get_tag_names(), match_threshold=0.75)
                print(is_tag, tag_match, tag_score)

                if is_recipe and recipe_score > ingredient_score:
                    # Once we know the name of the cocktail, we can grab its ingredients
                    # self.resippy(recipe_match)
                    return redirect(url_for('TestView:resippy', arg=recipe_match), code=308)

                elif is_tag:
                    children = self.main_menu.expand_tag(tag_match)
                    [self.lit_up_ingredients.append(child) for child in children]
                    print(f"lighting up tag: {tag_match}")
                    self.lights.illuminate_spirit(self.lit_up_ingredients)

                elif is_ingredient:
                    print(f"lighting up single ingredient: {ingredient_match}")
                    self.lights.illuminate_spirit([ingredient_match])

            # Otherwise, if the form has returned a collection, process ~that~
            elif element_name == "collection dropdown":
                if form_entry in self.main_menu.get_collection_names():
                    # This line isn't strictly necessary, but I think title case with spaces looks dumb in a URL, so I
                    #   do some string formatting
                    chosen_collection = form_entry.replace(" ", "_").lower()
                    # Redirect us to the "collections" page with the given collection
                    return redirect(url_for('TestView:collection', arg=chosen_collection), code=308)

            # The else will eventually be deleted, but it's here while there's the LED proxy on the website
            # else:
            #     chosen_ingredients = []

        return render_template('main_menu.html', options=self.main_menu.get_recipe_names(), ingredients=self.main_menu.get_inventory(), collections=self.main_menu.get_collection_names())        

    @method("GET")
    @method("POST")
    def resippy(self, arg:str):
        """http://localhost:5000/recipe/arg"""

        self.lights.all_off()
        self.lit_up_ingredients = []

        # chosen_ingredients = list(self.main_menu.menu_dict[arg]['ingredients'].keys())
        chosen_ingredients = self.main_menu.get_ingredients(arg)

        # Part 1 - the LEDS. Expand any children and call the LED class
        for ingredient in chosen_ingredients:
            children = self.main_menu.expand_tag(ingredient)
            if children:
                [self.lit_up_ingredients.append(recipe.format_as_inventory(child)) for child in children]
            else:
                self.lit_up_ingredients.append(recipe.format_as_inventory(ingredient))

        self.lights.illuminate_spirit(self.lit_up_ingredients)

        # Part 2 - the website. For each ingredient
        rendered_ingredients = []
        units = []
        amounts = []
        for ing in chosen_ingredients:
            # Format the ingredients nicely
            rendered_ingredients.append(format_for_web(ing))
            units.append(self.main_menu.menu_dict[arg]['ingredients'][ing]["units"])
            amounts.append(self.main_menu.menu_dict[arg]['ingredients'][ing]["amount"])
        notes = self.main_menu.menu_dict[arg]["notes"]
        # Then render the html page
        return render_template('recipe.html', header=arg.title(), cocktail=arg, ingredients=rendered_ingredients, units=units, amounts=amounts, notes=notes)

    @method("POST")
    @method("GET")
    def collection(self, arg:str):
        """http://localhost:5000/collection/arg"""
        # Do some string processing to match our collection title formatting -
        #   replace any underscores or hyphens with spaces, and make it title case
        if "_" in arg:
            title = format_for_web(arg)
        elif "-" in arg:
            title = arg.replace("-", " ").title()
        else:
            title = arg.title()

        # Check if it's a valid collection name. If not, stop here and let us know
        if title not in self.main_menu.get_collection_names():
            return "<p> not a valid cocktail menu collection :3 </p>"

        # If we're good, then load the available cocktails as dropdowns
        collections_dict = self.main_menu.sort_by_collections()
        cocktails_in_collection = collections_dict[title]
        ingredients_list = [list(self.main_menu.menu_dict[cocktail]["ingredients"].keys()) for cocktail in cocktails_in_collection]
        notes_list = [self.main_menu.menu_dict[cocktail]["notes"] for cocktail in cocktails_in_collection]

        return render_template('collection.html', header=title.title()+" Collection",
                               cocktails=cocktails_in_collection,
                               ingredients=ingredients_list,
                               notes=notes_list)

    def collections_main_page(self):
        self._quick_update()
        collection_names = self.main_menu.get_collection_names()
        collection_names.sort()

        collection_descriptions = ["The creations of Jack and Dane from their time in the 2201 N 106th st apartment",
                                   "Cocktails from our undergrad days at Ali's uncle's house",
                                   "Classic drinks! You could order these in public and people will probably know what you mean",
                                    "Drinks inspired by Steely Dan songs and albums. Ask for a physical menu for extra ~zing~",
                                    "Miscellaneous!",
                                    "Plagiarized from our favorite cocktail bar, The Zig Zag Cafe in Pike Place",
                                    ]
        return render_template('collections_main.html', collections=self.main_menu.get_collection_names(), notes=collection_descriptions)

    @method("POST")
    @method("GET")
    def random_cocktail_generator(self):
        self._quick_update()
        random_recipe_options = rands.get_random_recipe_options()

        # What we want displayed on the website
        numrows = 2
        numcols = 5
        button_color = [None]*numrows*numcols

        if request.method == "POST":

            self.lights.all_off()
            # When "post" is triggered, take a look at what happened in the HTML form. The value "request.form" is
            # a dictionary with key-value pairs "element-name" "element-entry". We don't really care about the name,
            # but we can use it to grab the dict value
            element_name = list(request.form.keys())[0]
            # form_entry = request.form.get(element_name)

            # If we've hit one of the broader "Random X" buttons, we want to generate 10 random cocktails of that
            # formula. E.g Random Negroni, Random Last Word, Random Random
            if element_name in random_recipe_options or element_name == "Random Random":
                self.random_ten = []

                for row in range(numrows): # rows
                    self.random_ten.append([])
                    for _ in range(numcols): # columns
                        random_dict = rands.resolve_random_recipe(element_name)
                        ingredients = []
                        quantity = []

                        # Dane's monster string, currently getting killed by html
                        amounts = "\n".join("%s\n\t%s" % (
                            i, random_dict[i]['amount'] + ' ' + random_dict[i]['units']
                        ) for i in ingredients) + "\n\n"

                        for i in random_dict:
                            ingredient = format_for_web(i)
                            amount = random_dict[i]["amount"]
                            unit = random_dict[i]["units"]
                            if amount.lower() == "taste":
                                quantity.append("To taste (%s)" % unit)
                            else:
                                quantity.append(amount + " " + unit)
                            ingredients.append(ingredient)

                        self.random_ten[row].append([ingredients, quantity])
            # If we've selected one of the random recipes
            elif element_name.isnumeric():
                try:
                    index = int(element_name)
                    flattened_ten = []
                    for i in range(numrows):
                        [flattened_ten.append(rand) for rand in self.random_ten[i]]
                
                    ingredients, quantity = flattened_ten[index]
                except ValueError as e:
                    print(f"Could not convert {element_name} to integer: {e}")
                except IndexError as e:
                    print(f"Could not index cocktails: '{e}' not found in {self.random_ten}")
                else:
                    button_color[index] = "#cf6275"
                    self.lights.illuminate_spirit(ingredients)
            # If we've hit the "I'm feeling lucky" button
            elif element_name == "random existing":
                random_cocktail = rands.select_random_recipe()
                return redirect(url_for('TestView:resippy', arg=random_cocktail))


        return render_template('randomizer.html', rand_options=random_recipe_options, cocktails=self.random_ten, 
                               rows=numrows, cols=numcols, button_color=button_color)

    def credits(self):
        mytext = "test credits"
        return render_template('empty_template.html', text=mytext)

    @method("GET")
    @method("POST")
    def put_away_ingredient(self):
        self._quick_update()

        ingredient_selected = ""
        location_selected = ""

        if request.method == "POST":
            # Clear the LEDS, if they're on
            self.lights.all_off()
            self.lit_up_ingredients = []

            ingredient_input = request.form["ingredient_input"]

            # Check to see if the input matches an ingredient or tag in our database
            is_ingredient, ingredient_match, ingredient_score = recipe.check_match(ingredient_input, self.main_menu.get_inventory(), match_threshold=0.75)
            # print(is_ingredient, ingredient_match, ingredient_score)
            is_tag, tag_match, tag_score = recipe.check_match(ingredient_input, self.main_menu.get_tag_names(), match_threshold=0.75)
            # print(is_tag, tag_match, tag_score)

            if is_ingredient and ingredient_score > tag_score:
                self.lit_up_ingredients.append(ingredient_match)
                print("from put_away:")
                self.lights.illuminate_spirit(self.lit_up_ingredients)

                # Update the website display
                ingredient_selected = ingredient_match
                # location_selected = self.main_menu.spirit_dict[ingredient_match].title()
                location_selected = self.main_menu.get_spirit_location(ingredient_match)

                # self.lights.illuminate_location(location_selected)

            # elif is_tag and tag_score > ingredient_score or tag_score == ingredient_score:
            #     if tag_score != 0:
            #         # If it's a tag, we need to get all the spirits it describes
            #         children = recipe.expand_tag(tag_match, self.tags_dict)
            #         # Turn on those LEDs
            #         [self.lit_up_ingredients.append(child) for child in children]
            #         self.lights.illuminate_spirit(self.lit_up_ingredients)
            #         # Get and format the cabinet locations of each child spirit
            #         locations = ""
            #         ingredients = ""
            #         print(self.location_dict)
            #         for child in children:
            #             print(child)
            #             try:
            #                 locations = locations + format_for_web(self.location_dict[format_for_web(child)]) + ", "
            #                 ingredients = ingredients + format_for_web(child) + ", "
            #             except KeyError as e:
            #                 print(f"Could not find {e} in the dictionary of cabinet locations.")

            #         # Update the website display
            #         location_selected = locations[0:-2] # Trim off the last two characters (comma and space)
            #         ingredient_selected = ingredients[0:-2]

        return render_template('put_away_ingredient.html', ingredients=self.main_menu.inventory,
                               ingredientSelected=ingredient_selected, locationSelected=location_selected)
      
 
    @method("GET")
    @method("POST")
    def test_dropdown(self):
        fruits = ["Apple", "Orange", "Grapes", "Berry", "Mango", "Banana"]
        return render_template("test_dropdown.html", testList=fruits)
    
    
    @method("GET")
    @method("POST")
    def modify_spirits(self):
        """Developer mode babey"""
        self._quick_update()

        # Set some initial parameters. These get passed to the HTML as result strings for the user
        # (e.g "Successfully added Roku Gin at coordinate A7" or "Failed to remove St Germain")
        recipe_result = ""
        remove_result = ""
        add_result = ""
        input_spirit = ""
        input_coord = ""
        input_tags = []

        if request.method == "POST":
            # Clear the LEDS, if they're on
            self.lights.all_off()
            # Cancel adding recipe
            if "btn_cancel_recipe" in request.form.keys():
                pass
            # Add recipe
            elif "btn_add_recipe" in request.form.keys():
                print("add recipe mode")
                print(request.form.keys())
                # Pull out the name, collection, and notes directly with their keys.
                recipe_name = request.form["input_recipe_name"]
                recipe_collection = request.form["input_recipe_collection"]
                recipe_notes = request.form["input_recipe_notes"]
                # Since we can have an arbitrary number of ingredients, extracting them is slightly different.
                # The cocktail ingredients, amounts, and units - respectively - start after "input_recipe_notes"
                # To get them organized nicely, we start at the appropriate index and grab every third dictionary value.
                cocktail_makeup = list(request.form.values())[3:]
                ingredients = cocktail_makeup[0::3]
                amounts = cocktail_makeup[1::3]
                units = cocktail_makeup[2::3]
                # Update the external yaml file with our new info
                result, updated_name = self.main_menu.update_recipe_yaml(recipe_name, recipe_collection, recipe_notes,
                                          ingredients, amounts, units)
                if result:
                    recipe_result = f"Successfully added {updated_name}!"
                else:
                    recipe_result = f"Failed to add {updated_name}. Sure would be great if we had logs published to the website"
            # Cancel adding or previewing spirit
            elif "btn_cancel_spirit" in request.form.keys():
                print("cancel input spirit")
                input_spirit = ""
                input_coord = ""
                input_tags = []
            # Add or preview spirit
            elif "input_add_spirit" in request.form.keys():
                print(request.form.keys())
                # Get the values of the html input elements
                input_spirit = request.form["input_add_spirit"]
                input_coord = request.form["input_add_coord"].upper()
                # Tags come through as dictionary keys, for some goddamn reason. Tried to make it be any different and could not.
                # Find tags through the intersection of the dict keys with our list of tag names
                tags = set(request.form.keys()).intersection(self.main_menu.get_tag_names())
                input_tags = list(tags)
                # Preview mode
                if "btn_preview_spirit" in request.form.keys():
                    print("preview spirit mode")
                    if input_coord in self.main_menu.cabinet_locations:
                        # Spin up a thread to flash the LEDs in that location
                        self.lights._allow_flashing()
                        t = threading.Thread(target=self.lights.illuminate_location, args=(input_coord, True, False))
                        t.start()
                        # self.lights.illuminate_location(self.input_coord, flash=True)
                        add_result = f'Lighting up coordinate {input_coord}'
                    else:
                        add_result = f'Warning - {input_coord} is not a cabinet coordinate. If that was intentional, carry on.'
                # Add mode
                elif "btn_add_spirit" in request.form.keys():
                    print("add spirit mode")
                    # Try to update the CSV and return the result.
                    result = self.main_menu.add_spirit(input_spirit, input_coord, input_tags)
                    if result:
                        add_result = f"Successfully added {input_spirit} to inventory"
                    else:
                        add_result = f"Failed to add {input_spirit}. Hmm."
                    # Update the html display
                    input_spirit = ""
                    input_coord = ""
                    input_tags = []
            # Remove spirit
            elif "btn_remove_spirit" in request.form.keys():
                print("remove spirit mode")
                spirit_to_remove = request.form["input_remove_spirit"]
                # Have a popup window here that asks if you're sure. While the window is up, have the 
                # spirit leds flash
                spirit_to_remove = spirit_to_remove.replace(" ", "_").lower()
                result = self.main_menu.remove_spirit(spirit_to_remove)
                if result:
                    remove_result = f"Successfully removed {spirit_to_remove} from inventory"
                else:
                    remove_result = f"Failed to remove {spirit_to_remove}. Does that spirit exist?"

        return render_template('modify_spirits.html', 
                               # These are constants
                               collections=self.main_menu.get_collection_names(),
                               spiritList=self.main_menu.inventory_user_facing,
                               tagList=self.main_menu.get_tag_names(), 
                               # These change as a result of user input
                               inputSpirit=input_spirit, 
                               inputCoord=input_coord,
                               inputTags=input_tags, 
                               recipeResultString=recipe_result, 
                               removeResultString=remove_result, 
                               addResultString=add_result)


# TestView.register(app, route_base = '/')

if __name__ == "__main__":
#     TestView.register(app, route_base = '/')
#     app.register_error_handler(404, TestView.not_found)
#     app.run(host='0.0.0.0', port=5000, debug=True)

    test = TestView()

