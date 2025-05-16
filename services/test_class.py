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
except ImportError:
    from services import recipe_parsing_helpers as recipe

# app = Flask(__name__, template_folder="templates")

class TestView(FlaskView):

    def __init__(self) -> None:
        super().__init__()
        self._load_menu()
        self.lights = LED(self.location_dict)

    def _load_menu(self):
        # Read in the main menu and validate it against our master list of ingredients
        menu_dict_raw, self.tags_dict = recipe.read_main_menu()
        all_ingredients, self.location_dict = recipe.load_all_ingredients()
        self.cabinet_liquors = list(self.location_dict.keys())
        self.menu_dict = recipe.validate_all_recipes(menu_dict_raw, all_ingredients, self.tags_dict)

        print("--")
        print(f"Validated recipes: {list(self.menu_dict.keys())}")

        # Pull out collection and cocktail names
        self.collection_names = recipe.load_collection_names(self.menu_dict)
        self.cocktail_names = recipe.load_recipe_names(self.menu_dict)
        self.used_ingredients = recipe.load_used_ingredients(self.menu_dict)

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

            # When "post" is triggered, take a look at what happened in the HTML form. The value "request.form" is
            # a dictionary with key-value pairs "element-name" "element-entry". We don't really care about the name,
            # but we can use it to grab the dict value
            element_name = list(request.form.keys())[0]
            form_entry = request.form.get(element_name)

            # If the form has returned a cocktail, process that
            if form_entry in self.cocktail_names:
                # Once we know the name of the cocktail, we can grab its ingredients. Do a quick data validation first
                # This will be more robust in the future - should check for differences in caps/misspellings
                chosen_ingredients = list(self.menu_dict[form_entry]['ingredients'].keys())
                lit_up_ingredients = []

                for ingredient in chosen_ingredients:
                    children = recipe.expand_tag(ingredient, self.tags_dict)
                    if children:
                        [lit_up_ingredients.append(child) for child in children]
                    else:
                        lit_up_ingredients.append(ingredient)

                self.lights.illuminate(lit_up_ingredients)
                print(chosen_ingredients)

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
    
    @route("random-cocktail-generator")
    def random_cocktail_generator(self):
        mytext = "This will generate you a random cocktail once we integrate Dane's script"
        return render_template('empty_template.html', text=mytext)

if __name__ == "__main__":
#     TestView.register(app, route_base = '/')
#     app.register_error_handler(404, TestView.not_found)
#     app.run(host='0.0.0.0', port=5000, debug=True)

    test = TestView()