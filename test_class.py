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

        print(f"available cocktails: {self.cocktail_names}")
        print(f"collections: {self.collections}")
    # http://localhost:5000/menu
        chosen_ingredients = []

        # If we've gotten a change of state on the server (in this case, due to user entry),
        #   take a look at it. 
        if request.method == "POST":
            selected_option = request.form['dropdown']
            chosen_ingredients = list(self.menu_dict[selected_option]['liquors'].keys())

            # if selected_option == "Moscow Mule":
            #     chosen_ingredients = ["Vodka", "Ginger Beer", "Lime Juice"]
            # elif selected_option == "Manhattan":
            #     chosen_ingredients = ["Rye Whiskey", "Angostura Bitters", "Vermouth"]
            # elif selected_option == "White Russian":
            #     chosen_ingredients = ["Vodka", "Kahlua", "Cream"]
        
        options = self.cocktail_names
        ingredients = self.all_liquors

        return render_template('drink_menu.html', options=options, ingredients=ingredients, chosen_ingredients=chosen_ingredients)
    
    def thirdpage(self, name):
    # dynamic route
    # http://localhost:5000/thirdpage/sometext
        print(f"name: {name}")

        return "<h1>This is my third page <br> welcome "+name+"</h1>"

TestView.register(app, route_base = '/')
