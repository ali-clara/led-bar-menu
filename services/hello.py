# The imports
from flask import Flask, render_template, request, redirect, url_for

# Create a Flask object
app = Flask(__name__, template_folder='templates')

# Redirect the main page (i.e what's shown at "127.0.0.1:5000") to the menu
@app.route("/")
def main_page():
    return redirect(url_for('main-menu'))

# Another page (i.e at 127.0.0.1:5000/hello or 127.0.0.1:5000/hello/Ali)
@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name=None):
    return render_template('hello.html', person=name)

# Set up the main drink menu page
@app.route("/main-menu", methods=["GET", "POST"])
def dranks():
    chosen_ingredients = []

    # If we've gotten a change of state on the server (in this case, due to user entry),
    #   take a look at it. 
    if request.method == "POST":
        selected_option = request.form['dropdown']
        if selected_option == "Moscow Mule":
            chosen_ingredients = ["Vodka", "Ginger Beer", "Lime Juice"]
        elif selected_option == "Manhattan":
            chosen_ingredients = ["Rye Whiskey", "Angostura Bitters", "Vermouth"]
        elif selected_option == "White Russian":
            chosen_ingredients = ["Vodka", "Kahlua", "Cream"]
    
    options = ["Moscow Mule", "Manhattan", "White Russian"]
    ingredients = ["Vodka",
                   "Rye Whiskey",
                   "Vermouth",
                   "Kahlua",
                   "Ginger Beer",
                   "Angostura Bitters",
                   "Cream",
                   "Lime Juice"]

    return render_template('drink_menu.html', options=options, ingredients=ingredients, chosen_ingredients=chosen_ingredients)
