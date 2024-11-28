# The imports
from flask import Flask, render_template, redirect, url_for
from flask_classful import FlaskView, method, route, request
import yaml


app = Flask(__name__, template_folder="templates")

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

        self.cocktail_names = list(self.menu_dict.keys())
        self.collections = [self.menu_dict[key]['collection'] for key in list(self.menu_dict.keys())]

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
    # http://localhost:5000/
        return redirect(url_for('TestView:menu'))

    @method("POST")
    @method("GET")
    def menu(self):
        """http://localhost:5000/menu"""

        print(f"available cocktails: {self.cocktail_names}")
        print(f"collections: {self.collections}")

        # If we've gotten a change of state on the server (in this case, due to user entry),
        #   take a look at it. 
        if request.method == "POST":
            # When "post" is triggered, take a look at what happened in the HTML form. "request.form" is
            # a dictionary with key-value pairs "element-name" "element-entry". We don't really care about the name,
            # but we can use it to grab the dict value
            element_name = list(request.form.keys())[0]
            cocktail_entry = request.form.get(element_name)

            # Once we know the name of the cocktail, we can grab its ingredients. Do a quick data validation first
            # This will be more robust in the future - should check for differences in caps/misspellings
            if cocktail_entry in self.cocktail_names:
                chosen_ingredients = list(self.menu_dict[cocktail_entry]['liquors'].keys())
            else:
                chosen_ingredients = []

        else:
            chosen_ingredients = []
        
        options = self.cocktail_names
        ingredients = self.all_liquors

        return render_template('drink_menu.html', options=options, ingredients=ingredients, chosen_ingredients=chosen_ingredients, collections=self.collections)
    
    def dummy(self):
        return "<h1>This is a dummy page</h1>"
    
    def thirdpage(self, name):
    # dynamic route
    # http://localhost:5000/thirdpage/sometext
        print(f"name: {name}")

        return "<h1>This is my third page <br> welcome "+name+"</h1>"


if __name__ == "__main__":
    TestView.register(app, route_base = '/')
    app.run(host='0.0.0.0', port=5000, debug=True)
