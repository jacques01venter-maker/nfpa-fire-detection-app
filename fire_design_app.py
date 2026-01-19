# NFPA Fire Detection BOQ & Layout App (Windows)
# ==================================================
# This file provides:
# 1) System architecture & design notes
# 2) NFPA-driven rules engine structure (simplified, extensible)
# 3) A working MVP desktop app (PyQt5) that:
#    - Uses a generic fire detection equipment library
#    - Allows item selection via dropdown and quantity control
#    - Accepts room dimensions
#    - Generates a BOQ (CSV)
#    - Produces a simple line drawing (DXF) showing recommended detector layout
#
# IMPORTANT:
# - This is an ENGINEERING ASSIST TOOL, not a final design authority.
# - All outputs must be verified by a competent fire engineer.
# - NFPA references are encoded as RULES, not copied text.
# - Designed for South African engineering workflows (Windows-first).

# ==============================
# 1. ARCHITECTURE OVERVIEW
# ==============================
# UI Layer        : PyQt5 (Windows desktop)
# Domain Logic    : NFPA Rules Engine (Python)
# Data            : Equipment Library (JSON)
# Output          : BOQ (CSV) + Line Drawing (DXF)
# Extensible to   : PDF reports, AutoCAD DWG export, Revit, IFC

# Modules:
# - equipment_library.py   -> Generic fire detection items
# - nfpa_rules.py          -> Spacing, coverage, mounting rules
# - boq_generator.py       -> BOQ creation
# - drawing_generator.py  -> Simple line drawings (DXF)
# - app.py                 -> GUI

# ==============================
# 2. GENERIC EQUIPMENT LIBRARY
# ==============================
import json

equipment_library = [
    {
        "category": "Smoke Detection",
        "items": [
            {"name": "Point Smoke Detector", "nfpa": "NFPA 72", "default_spacing_m": 9.1},
            {"name": "Beam Smoke Detector", "nfpa": "NFPA 72", "default_spacing_m": 18.0}
        ]
    },
    {
        "category": "Heat Detection",
        "items": [
            {"name": "Fixed Temperature Heat Detector", "nfpa": "NFPA 72", "default_spacing_m": 15.2},
            {"name": "Rate-of-Rise Heat Detector", "nfpa": "NFPA 72", "default_spacing_m": 15.2}
        ]
    },
    {
        "category": "Flame Detection",
        "items": [
            {"name": "UV Flame Detector", "nfpa": "NFPA 72", "coverage_m2": 400},
            {"name": "IR Flame Detector", "nfpa": "NFPA 72", "coverage_m2": 600}
        ]
    },
    {
        "category": "Manual Devices",
        "items": [
            {"name": "Manual Call Point", "nfpa": "NFPA 72", "max_travel_distance_m": 61}
        ]
    },
    {
        "category": "Notification",
        "items": [
            {"name": "Sounder", "nfpa": "NFPA 72"},
            {"name": "Strobe", "nfpa": "NFPA 72"}
        ]
    }
]

# ==============================
# 3. NFPA RULES ENGINE (SIMPLIFIED)
# ==============================
import math

def calculate_detector_quantity(room_length, room_width, spacing):
    """
    NFPA 72 simplified spacing rule:
    - Max spacing per detector (flat ceiling, smooth)
    - Square coverage assumed
    """
    area = room_length * room_width
    coverage_per_detector = spacing * spacing
    qty = math.ceil(area / coverage_per_detector)
    return qty


def generate_detector_grid(room_length, room_width, spacing):
    """
    Generates XY positions for detectors based on spacing
    """
    x_count = math.ceil(room_length / spacing)
    y_count = math.ceil(room_width / spacing)

    positions = []
    for i in range(x_count):
        for j in range(y_count):
            x = (i + 0.5) * spacing
            y = (j + 0.5) * spacing
            if x <= room_length and y <= room_width:
                positions.append((x, y))
    return positions

# ==============================
# 4. BOQ GENERATOR
# ==============================
import csv

def generate_boq(selected_items, output_file="boq.csv"):
    with open(output_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Item", "Quantity", "NFPA Reference"])
        for item in selected_items:
            writer.writerow([item['name'], item['quantity'], item['nfpa']])

# ==============================
# 5. LINE DRAWING GENERATOR (DXF)
# ==============================
import ezdxf

def generate_dxf(room_length, room_width, detector_positions, filename="layout.dxf"):
    doc = ezdxf.new()
    msp = doc.modelspace()

    # Room outline
    msp.add_lwpolyline([
        (0, 0),
        (room_length, 0),
        (room_length, room_width),
        (0, room_width),
        (0, 0)
    ])

    # Detectors
    for x, y in detector_positions:
        msp.add_circle((x, y), radius=0.2)

    doc.saveas(filename)

# ==============================
# 6. GUI (PyQt5 MVP)
# ==============================
from PyQt5 import QtWidgets
import sys

class FireDesignApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NFPA Fire Detection BOQ & Layout Tool")
        self.resize(600, 400)

        layout = QtWidgets.QVBoxLayout()

        self.length_input = QtWidgets.QLineEdit()
        self.width_input = QtWidgets.QLineEdit()
        self.length_input.setPlaceholderText("Room Length (m)")
        self.width_input.setPlaceholderText("Room Width (m)")

        self.equipment_dropdown = QtWidgets.QComboBox()
        for category in equipment_library:
            for item in category['items']:
                self.equipment_dropdown.addItem(item['name'], item)

        self.add_button = QtWidgets.QPushButton("Add Item")
        self.generate_button = QtWidgets.QPushButton("Generate BOQ & Drawing")

        self.list_widget = QtWidgets.QListWidget()

        self.selected_items = []

        self.add_button.clicked.connect(self.add_item)
        self.generate_button.clicked.connect(self.generate_outputs)

        layout.addWidget(self.length_input)
        layout.addWidget(self.width_input)
        layout.addWidget(self.equipment_dropdown)
        layout.addWidget(self.add_button)
        layout.addWidget(self.list_widget)
        layout.addWidget(self.generate_button)

        self.setLayout(layout)

    def add_item(self):
        item = self.equipment_dropdown.currentData()
        self.selected_items.append({
            "name": item['name'],
            "quantity": 1,
            "nfpa": item['nfpa'],
            "spacing": item.get('default_spacing_m', None)
        })
        self.list_widget.addItem(item['name'])

    def generate_outputs(self):
        length = float(self.length_input.text())
        width = float(self.width_input.text())

        detectors = [i for i in self.selected_items if i['spacing']]
        detector_positions = []

        for det in detectors:
            detector_positions.extend(generate_detector_grid(length, width, det['spacing']))
            det['quantity'] = calculate_detector_quantity(length, width, det['spacing'])

        generate_boq(self.selected_items)
        generate_dxf(length, width, detector_positions)

        QtWidgets.QMessageBox.information(self, "Done", "BOQ and DXF layout generated")

# ==============================
# 7. APPLICATION ENTRY POINT
# ==============================
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = FireDesignApp()
    window.show()
    sys.exit(app.exec_())

# ==============================
# 8. NEXT STEPS (RECOMMENDED)
# ==============================
# - Add ceiling height, roof type, obstruction rules
# - Add NFPA 72 Chapter-based rule toggles
# - Add South African standards (SANS 10139, SANS 7240)
# - Export DWG, PDF, and stamped calculation reports
# - Multi-room & building-level design
# - User roles & approval workflow
