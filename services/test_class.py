# The imports
from flask import Flask, render_template, redirect, url_for
from flask_classful import FlaskView, method, route, request
import yaml

# app = Flask(__name__, template_folder="templates")

class TestView(FlaskView):

    def __init__(self) -> None:
        super().__init__()
        self._load_menu()
        self._load_liquors()

    def _load_menu(self):
        try:
            with open("config/main-menu.yaml") as stream:
                self.menu_dict = yaml.safe_load(stream)
        except FileNotFoundError as e:
            print(e)
            self.menu_dict = {}
        except KeyError as e:
            print(e)
            self.menu_dict = {}

        # Create lists of the cocktail names and collection names, for easy reference later
        self.cocktail_names = list(self.menu_dict.keys())
        self.collections = []
        # For each cocktail...
        for key in self.menu_dict:
            # Grab what collection it belongs to, correcting for capitalization just in case.
            collection = self.menu_dict[key]['collection'].title()
            # Check if its in our list of collections. If it's not, add it.
            if collection not in self.collections:
                self.collections.append(collection)

        # Build a dictionary that sorts the cocktail names by collection
        #   e.g {'5057 main menu': ['Anthracite Prospector'], '2201 main menu': ['The Highland Locust'], 'lord of the rings': ['Pippin']}
        # Double for loop yay
        self.collection_dict = {collection_name:[] for collection_name in self.collections}
        for collection in self.collection_dict:
            for cocktail in self.cocktail_names:
                if self.menu_dict[cocktail]["collection"].title() == collection:
                    self.collection_dict[collection].append(cocktail)

        # print(f"Cocktail names: {self.cocktail_names}")
        # print(f"Collections: {self.collections}")
        # print(f"Sorted collection dict: {self.collection_dict}")

    def _load_liquors(self):
        try:
            with open("config/locations.yaml") as stream:
                self.locations_dict = yaml.safe_load(stream)
        except FileNotFoundError as e:
            print(e)
            self.locations_dict = {}
        except KeyError as e:
            print(e)
            self.locations_dict = {}

        self.all_liquors = list(self.locations_dict.values())

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
        # print(f"collections: {self.collections}")

        # These may become class vars eventually
        chosen_ingredients = [] # proxy for led lights
        chosen_collection = None

        # If we've gotten a change of state on the server (in this case, due to user entry),
        #   take a look at it. 
        if request.method == "POST":
            # When "post" is triggered, take a look at what happened in the HTML form. The value "request.form" is
            # a dictionary with key-value pairs "element-name" "element-entry". We don't really care about the name,
            # but we can use it to grab the dict value
            element_name = list(request.form.keys())[0]
            form_entry = request.form.get(element_name)

            # If the form has returned a cocktail, process that
            if form_entry in self.cocktail_names:
                # Once we know the name of the cocktail, we can grab its ingredients. Do a quick data validation first
                # This will be more robust in the future - should check for differences in caps/misspellings
                chosen_ingredients = list(self.menu_dict[form_entry]['liquors'].keys())
            # Otherwise, if the form has returned a collection, process ~that~
            elif form_entry in self.collections:
                # This line isn't strictly necessary, but I think title case with spaces looks dumb in a URL, so I 
                #   do some string formatting
                chosen_collection = form_entry.replace(" ", "_").lower()
                # Redirect us to the "collections" page with the given collection
                return redirect(url_for('TestView:collection', arg=chosen_collection))
            
            # The else will eventually be deleted, but it's here while there's the LED proxy on the website
            else:
                chosen_ingredients = []

        return render_template('main_menu.html', options=self.cocktail_names, ingredients=self.all_liquors, chosen_ingredients=chosen_ingredients, collections=self.collections)
    
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
        if title not in self.collections:
            return "<p> not a valid cocktail menu collection :3 </p>"
        
        # If we're good, then load the available cocktails as dropdowns
        cocktails_in_collection = self.collection_dict[title]
        ingredients_list = [list(self.menu_dict[cocktail]["liquors"].keys()) for cocktail in cocktails_in_collection]

        return render_template('collections.html', header=title.title()+" Collection", cocktails=cocktails_in_collection, ingredients=ingredients_list)
    
    @route("collections")
    def collections_main_page(self):
        mytext = "Collections page"
        return render_template('empty_template.html', text=mytext)
    
    @route("random-cocktail-generator")
    def random_cocktail_generator(self):
        mytext = "This will generate you a random cocktail once we integrate Dane's script"
        return render_template('empty_template.html', text=mytext)

# if __name__ == "__main__":
#     TestView.register(app, route_base = '/')
#     app.register_error_handler(404, TestView.not_found)
#     app.run(host='0.0.0.0', port=5000, debug=True)