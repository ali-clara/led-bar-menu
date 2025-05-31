# The imports
from flask import Flask, render_template, redirect, url_for
from flask_classful import FlaskView, method, route, request
try:
    from led import LED
except ImportError:
    from services.led import LED

import yaml

try:
    import recipe_parsing_helpers as recipe
    from randomizer import Randomizer as rands
except ImportError:
    from services import recipe_parsing_helpers as recipe
    from services.randomizer import Randomizer as rands

# app = Flask(__name__, template_folder="templates")

class TestView(FlaskView):

    def __init__(self) -> None:
        super().__init__()
        self._load_menu()
        self.lights = LED(self.location_dict)
        self.lit_up_ingredients = []
        self.random_ten = []

    def _load_menu(self):
        # Read in the main menu and validate it against our master list of ingredients
        menu_dict_raw, self.tags_dict, alias_dict = recipe.read_main_menu()
        self.all_ingredients, self.location_dict = recipe.load_all_ingredients()
        self.menu_dict = recipe.validate_all_recipes(menu_dict_raw, self.all_ingredients, self.tags_dict, alias_dict)

        print("--")
        print(f"Validated recipes: {list(self.menu_dict.keys())}")

        # Pull out collection and cocktail names
        self.collection_names = recipe.load_collection_names(self.menu_dict)
        self.cocktail_names = recipe.load_recipe_names(self.menu_dict)
        self.used_ingredients = recipe.load_used_ingredients(self.menu_dict)
        self.tags = recipe.load_tags(self.tags_dict)

        # Build a dictionary that sorts the cocktail names by collection
        #   e.g {'5057 main menu': ['Anthracite Prospector'], '2201 main menu': ['The Highland Locust'], 'lord of the rings': ['Pippin']}
        self.collection_dict = recipe.sort_collections(self.menu_dict, self.collection_names)

        # print(f"Cocktail names: {self.cocktail_names}")
        # print(f"Collections: {self.collection_names}")
        # print(f"Sorted collection dict: {self.collection_dict}")

    def index(self):
        """The main page. Redirects to the menu
        This lives at http://localhost:5000/ or http://10.0.0.120:5000
        """
        return redirect(url_for('TestView:menu'))
    
    def not_found(self):
        return render_template("error404.html")

    @method("POST")
    @method("GET")
    def menu(self):
        """http://localhost:5000/menu"""

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

            print(request.form)

            # When "post" is triggered, take a look at what happened in the HTML form. The value "request.form" is
            # a dictionary with key-value pairs "element-name" "element-entry". We don't really care about the name,
            # but we can use it to grab the dict value
            element_name = list(request.form.keys())[0]
            form_entry = request.form.get(element_name)

            print(form_entry)
            is_recipe, recipe_match, recipe_score = recipe.check_match(form_entry, self.cocktail_names, match_threshold=0.705)
            print(is_recipe, recipe_match, recipe_score)
            is_ingredient, ingredient_match, score = recipe.check_match(form_entry, self.all_ingredients, match_threshold=0.75)
            print(is_ingredient, ingredient_match, score)
            is_tag, tag_match, tag_score = recipe.check_match(form_entry, self.tags, match_threshold=0.75)
            print(is_tag, tag_match, tag_score)

            # If the form has returned a cocktail, process that
            if is_recipe:
                # Once we know the name of the cocktail, we can grab its ingredients
                # self.resippy(recipe_match)
                return redirect(url_for('TestView:resippy', arg=recipe_match))

            elif is_tag:
                children = recipe.expand_tag(tag_match, self.tags_dict)
                [self.lit_up_ingredients.append(child) for child in children]
                print(f"lighting up tag: {tag_match}")
                self.lights.illuminate(self.lit_up_ingredients)
            
            elif is_ingredient:
                print(f"lighting up single ingredient: {ingredient_match}")
                self.lights.illuminate([ingredient_match])

            # Otherwise, if the form has returned a collection, process ~that~
            elif form_entry in self.collection_names:
                # This line isn't strictly necessary, but I think title case with spaces looks dumb in a URL, so I 
                #   do some string formatting
                chosen_collection = form_entry.replace(" ", "_").lower()
                # Redirect us to the "collections" page with the given collection
                return redirect(url_for('TestView:collection', arg=chosen_collection))
            
            # The else will eventually be deleted, but it's here while there's the LED proxy on the website
            else:
                chosen_ingredients = []

        return render_template('main_menu.html', options=self.cocktail_names, ingredients=self.used_ingredients, chosen_ingredients=chosen_ingredients, collections=self.collection_names)
    
    def resippy(self, arg:str):
        """http://localhost:5000/recipe/arg"""
        
        self.lights.all_off()
        self.lit_up_ingredients = []
        
        print("lit up ingredients:")
        print(self.lit_up_ingredients)
        

        chosen_ingredients = list(self.menu_dict[arg]['ingredients'].keys())
        print("chosen ingredients:")
        print(chosen_ingredients)
        
        # Part 1 - the LEDS. Expand any children and call the LED class
        for ingredient in chosen_ingredients:
            children = recipe.expand_tag(ingredient, self.tags_dict)
            if children:
                [self.lit_up_ingredients.append(child) for child in children]
            else:
                self.lit_up_ingredients.append(ingredient)

        self.lights.illuminate(self.lit_up_ingredients)

        print("lit up ingredients:")
        print(self.lit_up_ingredients)

        # Part 2 - the website. For each ingredient
        rendered_ingredients = []
        units = []
        amounts = []
        for ing in chosen_ingredients:
            # Format the ingredients nicely
            rendered_ingredients.append(ing.replace("_", " ").title())
            units.append(self.menu_dict[arg]['ingredients'][ing]["units"])
            amounts.append(self.menu_dict[arg]['ingredients'][ing]["amount"])
        notes = self.menu_dict[arg]["notes"]
        # Then render the html page
        return render_template('recipe.html', header=arg.title(), cocktail=arg, ingredients=rendered_ingredients, units=units, amounts=amounts, notes=notes)

    
    def collection(self, arg:str):
        """http://localhost:5000/collection/arg"""
        # Do some string processing to match our collection title formatting - 
        #   replace any underscores or hyphens with spaces, and make it title case
        if "_" in arg:
            title = arg.replace("_", " ").title()
        elif "-" in arg:
            title = arg.replace("-", " ").title()
        else:
            title = arg.title()

        # Check if it's a valid collection name. If not, stop here and let us know
        if title not in self.collection_names:
            return "<p> not a valid cocktail menu collection :3 </p>"
        
        # If we're good, then load the available cocktails as dropdowns
        cocktails_in_collection = self.collection_dict[title]
        ingredients_list = [list(self.menu_dict[cocktail]["ingredients"].keys()) for cocktail in cocktails_in_collection]

        return render_template('collections.html', header=title.title()+" Collection", cocktails=cocktails_in_collection, ingredients=ingredients_list)
    
    @route("collections")
    def collections_main_page(self):
        mytext = "Collections page"
        return render_template('empty_template.html', text=mytext)
    
    
    @method("POST")
    @method("GET")
    def random_cocktail_generator(self):
        random_recipe_options = rands.get_random_recipe_options()
        mytext = "This will generate you a random cocktail once we integrate Dane's script"

        if request.method == "POST":   

            self.lights.all_off()

            # When "post" is triggered, take a look at what happened in the HTML form. The value "request.form" is
            # a dictionary with key-value pairs "element-name" "element-entry". We don't really care about the name,
            # but we can use it to grab the dict value
            element_name = list(request.form.keys())[0]
            # form_entry = request.form.get(element_name)

            print(element_name)
            numcols = 5
            
            if element_name in random_recipe_options:
                self.random_ten = []

                for row in range(2): # rows
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
                            ingredient = i.replace("_", " ").title()
                            amount = random_dict[i]["amount"]
                            unit = random_dict[i]["units"]

                            quantity.append(amount + " " + unit)
                            ingredients.append(ingredient)

                        self.random_ten[row].append([ingredients, quantity])

            elif element_name.isnumeric():
                try:
                    index = int(element_name)
                    ingredients, quantity = self.random_ten[index//numcols][index%numcols]
                except ValueError as e:
                    print(f"Could not convert {element_name} to integer: {e}")
                except IndexError as e:
                    print(f"Could not index cocktails: '{e}' not found in {self.random_ten}")
                else:
                    self.lights.illuminate(ingredients)


        return render_template('randomizer.html', rand_options=random_recipe_options, cocktails=self.random_ten)

if __name__ == "__main__":
#     TestView.register(app, route_base = '/')
#     app.register_error_handler(404, TestView.not_found)
#     app.run(host='0.0.0.0', port=5000, debug=True)

    test = TestView()
