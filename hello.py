from flask import Flask,render_template,request,redirect,url_for

app = Flask(__name__, template_folder='templates')

# @app.route("/")
# def hello_world():
#     # print(url_for('dranks'))
#     # return "<p>Index page!</p>"
#     return redirect(url_for('dranks'))

# @app.route("/hello")
# def hello():
#     return "Hello, World!"

# The main page (i.e what's shown at "127.0.0.1:5000")
@app.route('/')
def hello_world():
    return "Hello world!"

# Another page (i.e at 127.0.0.1:5000/hello or 127.0.0.1:5000/hello/Ali)
@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name=None):
    return render_template('hello.html', person=name)

@app.route("/dranks", methods=["GET", "POST"])
def dranks():
    chosen_ingredients = []

    if request.method == "POST":
        # print("Posted!!!")
        selected_option = request.form['dropdown']

        # print(selected_option)
        if selected_option == "Moscow Mule":
            chosen_ingredients = ["Vodka", "Ginger Beer", "Lime Juice"]
        elif selected_option == "Manhattan":
            chosen_ingredients = ["Rye Whiskey", "Angostura Bitters", "Vermouth"]
        elif selected_option == "White Russian":
            chosen_ingredients = ["Vodka", "Kahlua", "Cream"]
    

    # print(chosen_ingredients)
    options = ["Moscow Mule", "Manhattan", "White Russian"]
    ingredients = ["Vodka",
                   "Rye Whiskey",
                   "Vermouth",
                   "Kahlua",
                   "Ginger Beer",
                   "Angostura Bitters",
                   "Cream",
                   "Lime Juice"]

    return render_template('drink_menu.html', options=options,ingredients=ingredients, chosen_ingredients=chosen_ingredients)
