import sys
import os
import json
import shutil
import platform
from decimal import Decimal
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QHBoxLayout, QFormLayout, QListWidget, QListWidgetItem, QCompleter,
    QTabWidget, QComboBox, QInputDialog, QMessageBox
)
from PyQt5.QtCore import Qt


def get_app_data_directory(app_name):
    """Return an OS-appropriate directory for storing user data."""
    if platform.system() == 'Darwin':
        app_data_dir = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', app_name)
    elif platform.system() == 'Windows':
        app_data_dir = os.path.join(os.getenv('APPDATA'), app_name)
    else:
        app_data_dir = os.path.join(os.path.expanduser('~'), f'.{app_name}')

    os.makedirs(app_data_dir, exist_ok=True)
    return app_data_dir


class ELiquidCalculator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Elixr - E-Liquid Calculator")

        # Directories & files
        self.recipes_directory = get_app_data_directory("ElixrRecipes")
        self.flavor_weights_file = os.path.join(self.recipes_directory, 'flavor_weights.json')

        # Load data
        self.flavorings = self.load_flavorings()
        self.copy_pre_saved_recipes()

        # Tabs
        self.tabs = QTabWidget()
        self.calculator_tab = QWidget()
        self.settings_tab = QWidget()
        self.tabs.addTab(self.calculator_tab, "Calculator")
        self.tabs.addTab(self.settings_tab, "Settings")

        # UI setup
        self.setup_delete_recipe()
        self.setup_clear_flavor_list()
        self.setup_calculator_tab()
        self.setup_settings_tab()

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    # ---------- Calculator Tab ----------

    def setup_calculator_tab(self):
        self.amount_entry = QLineEdit()
        self.strength_entry = QLineEdit()
        self.pg_entry = QLineEdit()
        self.vg_entry = QLineEdit()
        self.flavor_name_entry = QLineEdit()
        self.flavor_percentage_entry = QLineEdit()

        # Auto-complete for flavors
        self.flavor_completer = QCompleter(list(self.flavorings.keys()))
        self.flavor_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.flavor_completer.setFilterMode(Qt.MatchContains)
        self.flavor_name_entry.setCompleter(self.flavor_completer)

        self.flavor_list = QListWidget()

        self.add_flavor_button = QPushButton("Add Flavor")
        self.add_flavor_button.clicked.connect(self.add_flavor)

        self.calculate_button = QPushButton("Calculate")
        self.calculate_button.clicked.connect(self.calculate)

        self.save_button = QPushButton("Save Recipe")
        self.save_button.clicked.connect(self.save_recipe)

        self.result_label = QLabel("Results will appear here.")
        self.result_label.setWordWrap(True)

        self.setup_recipe_loader()

        form_layout = QFormLayout()
        form_layout.addRow("Amount (ml):", self.amount_entry)
        form_layout.addRow("Strength (mg/ml):", self.strength_entry)
        form_layout.addRow("PG%:", self.pg_entry)
        form_layout.addRow("VG%:", self.vg_entry)
        form_layout.addRow("Flavor:", self.flavor_name_entry)
        form_layout.addRow("Flavor %:", self.flavor_percentage_entry)

        button_layout = QVBoxLayout()
        for w in [self.add_flavor_button, self.calculate_button, self.save_button,
                  self.delete_recipe_button, self.clear_flavor_list_button]:
            button_layout.addWidget(w)
        button_layout.addLayout(self.recipe_loader_layout)

        left_layout = QVBoxLayout()
        left_layout.addLayout(form_layout)
        left_layout.addLayout(button_layout)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.flavor_list)
        right_layout.addWidget(self.result_label)

        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)
        self.calculator_tab.setLayout(main_layout)

    # ---------- Settings Tab ----------

    def setup_settings_tab(self):
        self.new_flavor_name_entry = QLineEdit()
        self.new_flavor_weight_entry = QLineEdit()
        add_button = QPushButton("Add New Flavor")
        add_button.clicked.connect(self.add_new_flavor)

        layout = QFormLayout()
        layout.addRow("Flavor Name:", self.new_flavor_name_entry)
        layout.addRow("Flavor Weight:", self.new_flavor_weight_entry)
        layout.addWidget(add_button)
        self.settings_tab.setLayout(layout)

    # ---------- Helper UI Setup ----------

    def setup_delete_recipe(self):
        self.delete_recipe_button = QPushButton("Delete Recipe")
        self.delete_recipe_button.clicked.connect(self.delete_recipe)

    def setup_clear_flavor_list(self):
        self.clear_flavor_list_button = QPushButton("Clear Flavor List")
        self.clear_flavor_list_button.clicked.connect(self.flavor_list.clear)

    def setup_recipe_loader(self):
        self.recipe_dropdown = QComboBox()
        self.load_recipe_button = QPushButton("Load Recipe")
        self.load_recipe_button.clicked.connect(self.load_recipe)
        self.recipe_loader_layout = QHBoxLayout()
        self.recipe_loader_layout.addWidget(self.recipe_dropdown)
        self.recipe_loader_layout.addWidget(self.load_recipe_button)
        self.update_recipe_list()

    # ---------- Data Ops ----------

    def load_flavorings(self):
        try:
            with open(self.flavor_weights_file, 'r') as f:
                return {k: Decimal(str(v)) for k, v in json.load(f).items()}
        except Exception:
            return { "TFA Almond Amaretto": 1.0290, "TFA Apple": 1.0406, "TFA Apricot": 1.045, "TFA Banana Cream": 1.020, "TFA Bananas Foster": 1.030, "TFA Bavarian Cream": 1.0681, "TFA Belgian Waffle": 1.057, "TFA Berry Crunch": 1.000, "TFA Bitter Nut": 1.000, "TFA Black Honey": 1.000, "TFA Blueberry Extra": 1.052, "TFA Blueberry Wild": 1.0283, "TFA Brown Sugar": 1.066, "TFA Butter": 1.033, "TFA Butterscotch": 1.039, "TFA Caramel": 1.054, "TFA Cheesecake Graham Crust": 1.042, "TFA Cinnamon": 0.9728, "TFA Cinnamon Danish": 1.053, "TFA Circus Cotton Candy": 1.069, "TFA Creme De Menthe": 0.945, "TFA Dairy Milk": 1.029, "TFA Dragonfruit": 1.024, "TFA French Vanilla Deluxe": 1.014, "TFA Gingerbread Cookie": 1.051, "TFA Graham Cracker": 1.059, "TFA Grape Candy": 1.026, "TFA Grape Juice": 1.041, "TFA Green Tea": 1.034, "TFA Honeysuckle": 1.1562, "TFA Juicy Peach": 1.0349, "TFA Kentucky Bourbon": 1.029, "TFA Key Lime": 1.027, "TFA Koolada": 1.0519, "TFA Lemonade Cookie": 1.000, "TFA Malted Milk": 1.048, "TFA Maple": 0.908, "TFA Marshmallow": 1.042, "Menthol": 0.9403, "TFA Passionfruit": 1.053, "TFA Pear": 1.029, "TFA Pie Crust": 1.052, "TFA Phillipine Mango": 1.033, "TFA Popcorn": 1.042, "TFA Raspberry Sweet": 1.0399, "TFA Red Type": 1.033, "TFA Rice Crunchies": 1.000, "TFA Ripe Banana": 0.939, "TFA Smooth": 1.046, "TFA Spearmint": 0.960, "TFA Strawberries and Cream": 1.047, "TFA Sweet Cream": 1.040, "TFA Sweetener": 1.056, "TFA Tabanon": 1.000, "TFA Toasted Almond": 1.0397, "TFA Toasted Marshmallow": 1.0924, "TFA Turkish": 1.052, "TFA Vanilla Bean Ice Cream": 1.0623, "TFA Vanilla Cupcake": 1.0623, "TFA Vanilla Custard": 1.0484, "TFA Whipped Cream": 1.0441, "TFA Wintergreen": 1.0519, "CAP Blue Raspberry Cotton Candy": 1.048, "CAP Cool Mint": 1.045, "CAP Double Apple": 1.000, "CAP Golden Pineapple": 1.0408, "CAP Green Apple": 0.918, "CAP Grenadine": 1.000, "CAP Italian Lemon Sicily": 1.000, "CAP Jelly Candy": 1.000, "CAP Juicy Orange": 1.000, "CAP New York Cheesecake": 1.0284, "CAP Peppermint": 1.035, "CAP Raspberry": 1.033, "CAP Sweet Mango": 1.032, "CAP Sweet Strawberry": 1.0044, "CAP Sweet Watermelon": 1.027, "CAP Yellow Peach": 0.870, "LA Watermelon": 1.000, "NF Cookie Dough": 1.000, "FA Cookie": 1.0530, "FA Meringue": 1.053, "FA Vienna Cream": 1.0364 }

    def save_flavorings(self):
        with open(self.flavor_weights_file, 'w') as f:
            json.dump({k: float(v) for k, v in self.flavorings.items()}, f, indent=4)

    def copy_pre_saved_recipes(self):
        """Gracefully skip if 'pre_saved_recipes' folder is missing."""
        install_dir = os.path.dirname(os.path.realpath(__file__))
        src = os.path.join(install_dir, 'pre_saved_recipes')
        dest = self.recipes_directory
        if not os.path.exists(src):
            print("No pre_saved_recipes directory found — skipping copy.")
            return
        for file in os.listdir(src):
            src_file = os.path.join(src, file)
            dest_file = os.path.join(dest, file)
            if not os.path.exists(dest_file):
                shutil.copy(src_file, dest_file)

    # ---------- Actions ----------

    def add_flavor(self):
        name = self.flavor_name_entry.text().strip()
        pct = self.flavor_percentage_entry.text().strip()
        if not name or not pct:
            QMessageBox.warning(self, "Missing Info", "Enter flavor name and percentage.")
            return
        self.flavor_list.addItem(f"{name}: {pct}%")
        self.flavor_name_entry.clear()
        self.flavor_percentage_entry.clear()

    def get_flavor_weights(self):
        data = {}
        for i in range(self.flavor_list.count()):
            txt = self.flavor_list.item(i).text()
            if ':' in txt:
                name, pct = txt.split(':', 1)
                data[name.strip()] = Decimal(pct.strip().replace('%', '')) / 100
        return data

    def calculate(self):
        try:
            amount = Decimal(self.amount_entry.text())
            strength = Decimal(self.strength_entry.text())
            pg_pct = Decimal(self.pg_entry.text())
            vg_pct = Decimal(self.vg_entry.text())

            nic_vol = (strength / 100) * amount
            flv_dict = self.get_flavor_weights()
            flv_vol = sum(v * amount for v in flv_dict.values())

            vg_vol = (vg_pct / 100) * amount - nic_vol
            pg_vol = (pg_pct / 100) * amount - flv_vol

            result = f"Nicotine: {nic_vol:.2f} ml\nVG: {vg_vol:.2f} ml\nPG: {pg_vol:.2f} ml"
            for n, p in flv_dict.items():
                flv_wt = p * amount * self.flavorings.get(n, Decimal("1.000"))
                result += f"\n{n}: {flv_wt:.2f} g"
            self.result_label.setText(result)
        except Exception as e:
            self.result_label.setText(f"Error: {e}")

    def add_new_flavor(self):
        name = self.new_flavor_name_entry.text().strip()
        wt = self.new_flavor_weight_entry.text().strip()
        try:
            if not name or not wt:
                raise ValueError
            self.flavorings[name] = Decimal(wt)
            self.save_flavorings()
            self.flavor_completer.model().setStringList(list(self.flavorings.keys()))
            QMessageBox.information(self, "Success", f"Added flavor: {name}")
            self.new_flavor_name_entry.clear()
            self.new_flavor_weight_entry.clear()
        except Exception:
            QMessageBox.warning(self, "Error", "Invalid name or weight.")

    def save_recipe(self):
        name, ok = QInputDialog.getText(self, "Save Recipe", "Recipe name:")
        if not ok or not name:
            return
        path = os.path.join(self.recipes_directory, f"{name}.json")
        recipe = {
            "amount": self.amount_entry.text(),
            "strength": self.strength_entry.text(),
            "pg": self.pg_entry.text(),
            "vg": self.vg_entry.text(),
            "flavors": {k: float(v * 100) for k, v in self.get_flavor_weights().items()}
        }
        with open(path, 'w') as f:
            json.dump(recipe, f, indent=4)
        self.update_recipe_list()
        QMessageBox.information(self, "Saved", f"Recipe '{name}' saved!")

    def load_recipe(self):
        name = self.recipe_dropdown.currentText()
        if not name:
            return
        path = os.path.join(self.recipes_directory, f"{name}.json")
        try:
            with open(path, 'r') as f:
                r = json.load(f)
            self.amount_entry.setText(r["amount"])
            self.strength_entry.setText(r["strength"])
            self.pg_entry.setText(r["pg"])
            self.vg_entry.setText(r["vg"])
            self.flavor_list.clear()
            for k, v in r["flavors"].items():
                self.flavor_list.addItem(f"{k}: {v}%")
            self.result_label.setText(f"Loaded '{name}' successfully.")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def delete_recipe(self):
        name = self.recipe_dropdown.currentText()
        if not name:
            return
        path = os.path.join(self.recipes_directory, f"{name}.json")
        if os.path.exists(path):
            os.remove(path)
            self.update_recipe_list()
            QMessageBox.information(self, "Deleted", f"Recipe '{name}' removed.")
        else:
            QMessageBox.warning(self, "Error", "Recipe not found.")

    def update_recipe_list(self):
        try:
            files = [f[:-5] for f in os.listdir(self.recipes_directory) if f.endswith('.json')]
            self.recipe_dropdown.clear()
            self.recipe_dropdown.addItems(files)
        except FileNotFoundError:
            os.makedirs(self.recipes_directory, exist_ok=True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = ELiquidCalculator()
    w.show()
    sys.exit(app.exec_())
