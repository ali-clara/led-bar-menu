# led-bar-menu
Getting lit (hah)

**highly recommend installing Code Spell Checker on VSCode, I've made a workspace dictionary that will hopefully help us avoid any yaml key errors when we edit the cocktail menu. Also it's just slick**

### Works! Notes:
- Publish the logs to the website
- shutdown pi button on website
- "did you mean" feature in lots of places (adding recipe/ingredient, searching, really anywhere there's user input)
- pi isn't automatically updating from github
- be able to add tags when you add a recipe
    - sort the tags list
- comments on recipes
- make "debug" and "uncategorized" hidden recipe files
- think about refactoring recipe_parsing_helpers into its own class, it's getting pretty complex by now and would be good to
isolate where data/dictionaries/big lists live.
- external param for "does the system need updating" (set to Yes upon init)

### Docs
- https://docs.circuitpython.org/projects/neopixel/en/latest/index.html
- https://cdn-learn.adafruit.com/downloads/pdf/neopixels-on-raspberry-pi.pdf 
- https://pinout.xyz/
