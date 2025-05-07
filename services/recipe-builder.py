import yaml
import time
import os 

dir_path = os.path.join(os.path.dirname( __file__ ), os.pardir)

print("Welcome to the main menu recipe builder (terminal version). Eventually this will be replaced by the website, but Ali would " \
"rather write Python than CSS.")
main_menu = {}
while True:
    choice = input("(a) Add a recipe (b) List the recipe names you've added (c) Print a recipe (q) Save and quit \n")
    if choice == "a":
        name = input("Recipe name: ")
        collection = input("Collection: ")
        main_menu.update({name: {"ingredients": {}}})
        ingredients = []
        amounts = []
        units = []
        while True:
            ingredients.append(input("    Ingredient: "))
            amounts.append(input("        Amount: "))
            units.append(input("        Units: "))

            done_ask = input("Hit 9 to stop adding ingredients. Hit 2 to clear that last ingredient. Hit anything else to save and continue.")
            if done_ask == "9":
                break
            elif done_ask == "2":
                ingredients.pop()
                amounts.pop()
                units.pop()
        
        notes = input("Notes: ")
        
        main_menu[name].update({"notes": notes})
        main_menu[name].update({"collection": collection})
        for (ingredient, amount, unit) in zip(ingredients, amounts, units):
            main_menu[name]["ingredients"].update({ingredient: {"units": unit, "amount": amount}})
        
    elif choice == "b":
        for key in main_menu:
            print(key)
        
    elif choice == "c":
        recipe = input("What recipe do you want to display? \n")
        try:
            print(main_menu[recipe])
        except:
            print("Could not find that recipe in the saved dictionary. Recipes you've entered: ") 
            print(list(main_menu.keys()))

    elif choice == "q":
        print("-----")
        print("Final main menu: ")
        print(main_menu)
        
        suffix = time.time()
        with open(os.path.join(dir_path, f'config/recipe_{suffix}.yml'), 'w') as outfile:
            yaml.dump(main_menu, outfile, default_flow_style=False)

        break
