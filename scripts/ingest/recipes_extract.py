import json

with open("../../recipes_full.txt", "r") as f:
    recipes = json.load(f)
i = 0
for recipe in recipes.values():
    if recipe["views"] > 1000:
        i += 1
        print(recipe["name"])

print(i)