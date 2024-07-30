import sys
import os
import json
import shutil
import platform
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
                             QFormLayout, QListWidget, QListWidgetItem, QCompleter, QTabWidget, QComboBox, QInputDialog)
from PyQt5.QtCore import Qt
from decimal import Decimal

def get_app_data_directory(app_name):
    """Get the path to the application's data directory."""
    if platform.system() == 'Darwin':  # macOS
        app_data_dir = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', app_name)
    elif platform.system() == 'Windows':  # Windows
        app_data_dir = os.path.join(os.getenv('APPDATA'), app_name)
    else:  # Linux and other OSes
        app_data_dir = os.path.join(os.path.expanduser('~'), f'.{app_name}')

    if not os.path.exists(app_data_dir):
        os.makedirs(app_data_dir)

    return app_data_dir

class ELiquidCalculator(QWidget):
    def __init__(self):
        super().__init__()

        self.recipes_directory = get_app_data_directory("ElixrRecipes")
        self.flavor_weights_file = os.path.join(self.recipes_directory, 'flavor_weights.json')
        self.pre_saved_recipes_directory = os.path.join(self.recipes_directory, 'pre_saved_recipes')

        self.setWindowTitle("Elixr - E-Liquid Calculator")
        self.flavorings = self.load_flavorings()
        self.copy_pre_saved_recipes()

        # Initialize tabs
        self.tabs = QTabWidget()
        self.calculator_tab = QWidget()
        self.settings_tab = QWidget()

        # Set up the tabs
        self.tabs.addTab(self.calculator_tab, "Calculator")
        self.tabs.addTab(self.settings_tab, "Settings")

        # Initialize the delete recipe button
        self.setup_delete_recipe()  # Ensure this is called before setup_calculator_tab
        self.setup_clear_flavor_list()

        # Set up the calculator tab
        self.setup_calculator_tab()

        # Set up the settings tab
        self.setup_settings_tab()

        # Layout for the main window
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def setup_calculator_tab(self):
        # Create widgets for the calculator tab
        self.amount_label = QLabel("Amount to make in ml:")
        self.strength_label = QLabel("Desired final strength in mg/ml:")
        self.pg_label = QLabel("Desired PG%:")
        self.vg_label = QLabel("Desired VG%:")
        self.flavor_label = QLabel("Flavor:")
        self.flavor_percentage_label = QLabel("Flavor Percentage (%):")

        self.amount_entry = QLineEdit()
        self.strength_entry = QLineEdit()
        self.pg_entry = QLineEdit()
        self.vg_entry = QLineEdit()
        self.flavor_name_entry = QLineEdit()
        self.flavor_percentage_entry = QLineEdit()

        # Create a completer for flavor suggestions
        self.flavor_completer = QCompleter(list(self.flavorings.keys()))
        self.flavor_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.flavor_name_entry.setCompleter(self.flavor_completer)
        self.flavor_completer.setFilterMode(Qt.MatchContains)  # Allow partial matches
        self.flavor_name_entry.setCompleter(self.flavor_completer)

        self.flavor_list = QListWidget()

        self.add_flavor_button = QPushButton("Add Flavor")
        self.add_flavor_button.clicked.connect(self.add_flavor)

        self.calculate_button = QPushButton("Calculate")
        self.calculate_button.clicked.connect(self.calculate)

        self.save_button = QPushButton("Save Recipe")
        self.save_button.clicked.connect(self.save_recipe)

        self.result_label = QLabel("Results will be displayed here")

        # Set up the recipe loader
        self.setup_recipe_loader()

        # Left side layout
        form_layout = QFormLayout()
        form_layout.addRow(self.amount_label, self.amount_entry)
        form_layout.addRow(self.strength_label, self.strength_entry)
        form_layout.addRow(self.pg_label, self.pg_entry)
        form_layout.addRow(self.vg_label, self.vg_entry)
        form_layout.addRow(self.flavor_label, self.flavor_name_entry)
        form_layout.addRow(self.flavor_percentage_label, self.flavor_percentage_entry)

        button_layout = QVBoxLayout()
        button_layout.addWidget(self.add_flavor_button)
        button_layout.addWidget(self.calculate_button)
        button_layout.addWidget(self.save_button)
        button_layout.addLayout(self.recipe_loader_layout)
        button_layout.addWidget(self.delete_recipe_button)
        button_layout.addWidget(self.clear_flavor_list_button)

        input_layout = QVBoxLayout()
        input_layout.addLayout(form_layout)
        input_layout.addLayout(button_layout)

        # Right side layout
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.flavor_list)
        right_layout.addWidget(self.result_label)

        # Main horizontal layout
        main_horizontal_layout = QHBoxLayout()
        main_horizontal_layout.addLayout(input_layout)
        main_horizontal_layout.addLayout(right_layout)

        # Add the recipe loader layout to the main horizontal layout
        main_horizontal_layout.addLayout(self.recipe_loader_layout)

        self.calculator_tab.setLayout(main_horizontal_layout)

    def setup_settings_tab(self):
        # Create widgets for the settings tab
        self.new_flavor_name_label = QLabel("Flavor Name:")
        self.new_flavor_name_entry = QLineEdit()

        self.new_flavor_weight_label = QLabel("Flavor Weight:")
        self.new_flavor_weight_entry = QLineEdit()

        self.add_new_flavor_button = QPushButton("Add New Flavor")
        self.add_new_flavor_button.clicked.connect(self.add_new_flavor)

        # Layout for the settings tab
        settings_layout = QVBoxLayout()
        settings_layout.addWidget(self.new_flavor_name_label)
        settings_layout.addWidget(self.new_flavor_name_entry)
        settings_layout.addWidget(self.new_flavor_weight_label)
        settings_layout.addWidget(self.new_flavor_weight_entry)
        settings_layout.addWidget(self.add_new_flavor_button)

        self.settings_tab.setLayout(settings_layout)

    def setup_delete_recipe(self):
        self.delete_recipe_button = QPushButton("Delete Recipe")
        self.delete_recipe_button.clicked.connect(self.delete_recipe)

    def setup_recipe_loader(self):
        # Create widgets for recipe loading
        self.recipe_dropdown = QComboBox()
        self.load_recipe_button = QPushButton("Load Recipe")
        self.load_recipe_button.clicked.connect(self.load_recipe)

        # Layout for the recipe loader
        self.recipe_loader_layout = QHBoxLayout()
        self.recipe_loader_layout.addWidget(self.recipe_dropdown)
        self.recipe_loader_layout.addWidget(self.load_recipe_button)

        self.update_recipe_list()

    def update_recipe_list(self):
        recipes_directory = self.recipes_directory
        try:
            recipe_files = [f for f in os.listdir(recipes_directory) if f.endswith('.json') and 'flavor_weights' not in f]
            print(f"Found recipes: {recipe_files}")  # Debug print
            recipe_names = [os.path.splitext(f)[0] for f in recipe_files]
            self.recipe_dropdown.clear()
            self.recipe_dropdown.addItems(recipe_names)
        except FileNotFoundError:
            print("Recipes directory not found.")  # Debug print
            self.result_label.setText("Recipes directory not found.")

    def setup_clear_flavor_list(self):
        self.clear_flavor_list_button = QPushButton("Clear Flavor List")
        self.clear_flavor_list_button.clicked.connect(self.clear_flavor_list)

    def load_flavorings(self):
        try:
            with open(self.flavor_weights_file, 'r') as file:
                flavorings_floats = json.load(file)
            return {k: Decimal(str(v)) for k, v in flavorings_floats.items()}
        except (FileNotFoundError, json.JSONDecodeError):
            # If the file doesn't exist or is invalid, use default flavorings
            return {
                "TFA Almond Amaretto": 1.0290,
                "TFA Apple": 1.0406,
                "TFA Apricot": 1.045,
                "TFA Banana Cream": 1.020,
                "TFA Bananas Foster": 1.030,
                "TFA Bavarian Cream": 1.0681,
                "TFA Belgian Waffle": 1.057,
                "TFA Berry Crunch": 1.000,
                "TFA Bitter Nut": 1.000,
                "TFA Black Honey": 1.000,
                "TFA Blueberry Extra": 1.052,
                "TFA Blueberry Wild": 1.0283,
                "TFA Brown Sugar": 1.066,
                "TFA Butter": 1.033,
                "TFA Butterscotch": 1.039,
                "TFA Caramel": 1.054,
                "TFA Cheesecake Graham Crust": 1.042,
                "TFA Cinnamon": 0.9728,
                "TFA Cinnamon Danish": 1.053,
                "TFA Circus Cotton Candy": 1.069,
                "TFA Creme De Menthe": 0.945,
                "TFA Dairy Milk": 1.029,
                "TFA Dragonfruit": 1.024,
                "TFA French Vanilla Deluxe": 1.014,
                "TFA Gingerbread Cookie": 1.051,
                "TFA Graham Cracker": 1.059,
                "TFA Grape Candy": 1.026,
                "TFA Grape Juice": 1.041,
                "TFA Green Tea": 1.034,
                "TFA Honeysuckle": 1.1562,
                "TFA Juicy Peach": 1.0349,
                "TFA Kentucky Bourbon": 1.029,
                "TFA Key Lime": 1.027,
                "TFA Koolada": 1.0519,
                "TFA Lemonade Cookie": 1.000,
                "TFA Malted Milk": 1.048,
                "TFA Maple": 0.908,
                "TFA Marshmallow": 1.042,
                "Menthol": 0.9403,
                "TFA Passionfruit": 1.053,
                "TFA Pear": 1.029,
                "TFA Pie Crust": 1.052,
                "TFA Phillipine Mango": 1.033,
                "TFA Popcorn": 1.042,
                "TFA Raspberry Sweet": 1.0399,
                "TFA Red Type": 1.033,
                "TFA Rice Crunchies": 1.000,
                "TFA Ripe Banana": 0.939,
                "TFA Smooth": 1.046,
                "TFA Spearmint": 0.960,
                "TFA Strawberries and Cream": 1.047,
                "TFA Sweet Cream": 1.040,
                "TFA Sweetener": 1.056,
                "TFA Tabanon": 1.000,
                "TFA Toasted Almond": 1.0397,
                "TFA Toasted Marshmallow": 1.0924,
                "TFA Turkish": 1.052,
                "TFA Vanilla Bean Ice Cream": 1.0623,
                "TFA Vanilla Cupcake": 1.0623,
                "TFA Vanilla Custard": 1.0484,
                "TFA Whipped Cream": 1.0441,
                "TFA Wintergreen": 1.0519,
                "CAP Blue Raspberry Cotton Candy": 1.048,
                "CAP Cool Mint": 1.045,
                "CAP Double Apple": 1.000,
                "CAP Golden Pineapple": 1.0408,
                "CAP Green Apple": 0.918,
                "CAP Grenadine": 1.000,
                "CAP Italian Lemon Sicily": 1.000,
                "CAP Jelly Candy": 1.000,
                "CAP Juicy Orange": 1.000,
                "CAP New York Cheesecake": 1.0284,
                "CAP Peppermint": 1.035,
                "CAP Raspberry": 1.033,
                "CAP Sweet Mango": 1.032,
                "CAP Sweet Strawberry": 1.0044,
                "CAP Sweet Watermelon": 1.027,
                "CAP Yellow Peach": 0.870,
                "LA Watermelon": 1.000,
                "NF Cookie Dough": 1.000,
                "FA Cookie": 1.0530,
                "FA Meringue": 1.053,
                "FA Vienna Cream": 1.0364
            }

    def save_flavorings(self):
        with open(self.flavor_weights_file, 'w') as file:
            flavorings_serializable = {k: float(v) for k, v in self.flavorings.items()}
            json.dump(flavorings_serializable, file, indent=4, sort_keys=True)

    def copy_pre_saved_recipes(self):
        # Copy pre-saved recipes from the installation directory to the user's data directory
        install_dir = os.path.dirname(os.path.realpath(__file__))
        pre_saved_recipes_src = os.path.join(install_dir, 'pre_saved_recipes')
        pre_saved_recipes_dest = self.recipes_directory

        for recipe_file in os.listdir(pre_saved_recipes_src):
            src_file = os.path.join(pre_saved_recipes_src, recipe_file)
            dest_file = os.path.join(pre_saved_recipes_dest, recipe_file)
            if not os.path.exists(dest_file):
                shutil.copy(src_file, dest_file)

    def add_flavor(self):
        flavor_name = self.flavor_name_entry.text()
        flavor_percentage = self.flavor_percentage_entry.text()

        if flavor_name and flavor_percentage:
            item = QListWidgetItem(f"{flavor_name}: {flavor_percentage}%")
            self.flavor_list.addItem(item)

            self.flavor_name_entry.clear()
            self.flavor_percentage_entry.clear()

    def calculate(self):
        try:
            amount = Decimal(self.amount_entry.text())
            strength = Decimal(self.strength_entry.text())
            pg_percentage = Decimal(self.pg_entry.text())
            vg_percentage = Decimal(self.vg_entry.text())

            nicotine_volume = (strength / Decimal('100')) * amount

            flavor_weights = self.get_flavor_weights_as_dict()
            flavor_volume, flavor_weight = self.calculate_flavor(flavor_weights, amount)

            total_vg_volume = (vg_percentage / Decimal('100')) * amount - nicotine_volume
            total_pg_volume = (pg_percentage / Decimal('100')) * amount - flavor_volume

            nicotine_weight = nicotine_volume * Decimal('1.261')
            vg_weight = total_vg_volume * Decimal('1.261')
            pg_weight = total_pg_volume * Decimal('1.036')

            result = (
                f"Nicotine: {nicotine_weight:.2f} g\n"
                f"VG: {vg_weight:.2f} g\n"
                f"PG: {pg_weight:.2f} g"
            )

            if flavor_weights:
                for flavor_name, flavor_percentage in flavor_weights.items():
                    flavor_weight = flavor_percentage * amount * Decimal(self.flavorings.get(flavor_name, 1.000))
                    result += f"\n{flavor_name}: {flavor_weight:.2f} g"

            self.result_label.setText(result)

        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            self.result_label.setText(error_message)

    def calculate_flavor(self, flavor_weights, amount):
        flavor_volume = Decimal('0.0')
        flavor_weight = Decimal('0.0')
        for flavor_name, flavor_percentage in flavor_weights.items():
            individual_flavor_weight = flavor_percentage * Decimal(amount) * Decimal(self.flavorings.get(flavor_name, '1.000'))
            flavor_weight += individual_flavor_weight
            flavor_volume += flavor_percentage * amount

        return flavor_volume, flavor_weight

    def add_new_flavor(self):
        flavor_name = self.new_flavor_name_entry.text().strip()
        flavor_weight = self.new_flavor_weight_entry.text().strip()
        if flavor_name and self.is_valid_weight(flavor_weight):
            self.flavorings[flavor_name] = Decimal(flavor_weight)
            self.new_flavor_name_entry.clear()
            self.new_flavor_weight_entry.clear()
            self.update_completer()
            self.save_flavorings()
        else:
            self.result_label.setText("Invalid flavor name or weight")

    def update_completer(self):
        model = self.flavor_completer.model()
        model.setStringList(list(self.flavorings.keys()))

    def is_valid_weight(self, weight):
        try:
            Decimal(weight)
            return True
        except:
            return False

    def save_recipe(self):
        recipe_name, ok = QInputDialog.getText(self, 'Save Recipe', 'Enter recipe name:')
        if ok and recipe_name:
            recipe_file = os.path.join(self.recipes_directory, f"{recipe_name}.json")
            recipe = {
                "amount": self.amount_entry.text(),
                "strength": self.strength_entry.text(),
                "pg_percentage": self.pg_entry.text(),
                "vg_percentage": self.vg_entry.text(),
                "flavors": self.get_flavor_weights_as_dict()
            }
            for flavor, percentage in recipe["flavors"].items():
                recipe["flavors"][flavor] = f"{percentage * 100}%"
            
            try:
                with open(recipe_file, "w") as file:
                    recipe_serializable = {k: (float(v) if isinstance(v, Decimal) else v) for k, v in recipe.items()}
                    json.dump(recipe_serializable, file, indent=4)
                print(f"Recipe '{recipe_name}' saved successfully to {recipe_file}")

                # Refresh the recipe list to include the new recipe
                self.update_recipe_list()

            except Exception as e:
                print(f"Failed to save recipe: {e}")
                self.result_label.setText(f"Failed to save recipe: {e}")
        else:
            self.result_label.setText("Invalid recipe name or cancelled operation.")

    def load_recipe(self):
        selected_recipe_name = self.recipe_dropdown.currentText()
        if selected_recipe_name:
            recipe_file = os.path.join(self.recipes_directory, f"{selected_recipe_name}.json")
            try:
                with open(recipe_file, 'r') as file:
                    recipe = json.load(file)

                self.amount_entry.setText(recipe["amount"])
                self.strength_entry.setText(recipe["strength"])
                self.pg_entry.setText(recipe["pg_percentage"])
                self.vg_entry.setText(recipe["vg_percentage"])

                self.flavor_list.clear()
                for flavor, percentage in recipe["flavors"].items():
                    item = QListWidgetItem(f"{flavor}: {percentage}")
                    self.flavor_list.addItem(item)

                self.result_label.setText(f"Recipe '{selected_recipe_name}' loaded successfully")

            except Exception as e:
                print(f"Failed to load recipe: {e}")
                self.result_label.setText(f"Failed to load recipe: {e}")

    def delete_recipe(self):
        selected_recipe_name = self.recipe_dropdown.currentText()
        if selected_recipe_name:
            recipe_file = os.path.join(self.recipes_directory, f"{selected_recipe_name}.json")
            try:
                os.remove(recipe_file)
                print(f"Recipe '{selected_recipe_name}' deleted successfully")

                # Refresh the recipe list to remove the deleted recipe
                self.update_recipe_list()

                self.result_label.setText(f"Recipe '{selected_recipe_name}' deleted successfully")

            except Exception as e:
                print(f"Failed to delete recipe: {e}")
                self.result_label.setText(f"Failed to delete recipe: {e}")

    def get_flavor_weights_as_dict(self):
        flavor_weights = {}
        for i in range(self.flavor_list.count()):
            item_text = self.flavor_list.item(i).text()
            flavor, percentage = item_text.split(':')
            flavor_weights[flavor.strip()] = Decimal(percentage.strip().replace('%', '')) / 100
        return flavor_weights

    def clear_flavor_list(self):
        self.flavor_list.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ELiquidCalculator()
    window.show()
    sys.exit(app.exec_())
