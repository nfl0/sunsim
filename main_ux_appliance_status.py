import sys
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QListWidget, QMessageBox, 
                             QComboBox, QTimeEdit, QFileDialog, QTabWidget, QGridLayout)
from PyQt5.QtCore import Qt, QTime
from PyQt5.QtGui import QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class SolarComponent:
    def __init__(self, name, capacity):
        self.name = name
        self.capacity = capacity

    def to_dict(self):
        return {"name": self.name, "capacity": self.capacity}

    @classmethod
    def from_dict(cls, data):
        return cls(data["name"], data["capacity"])

class Appliance:
    def __init__(self, name, power, priority, start_time, end_time, min_runtime):
        self.name = name
        self.power = power
        self.priority = priority
        self.start_time = start_time
        self.end_time = end_time
        self.min_runtime = min_runtime
        self.daily_runtime = {}  # Track runtime for each day

    def reset_daily_runtime(self, day):
        self.daily_runtime[day] = 0

    def add_runtime(self, day, hours):
        if day not in self.daily_runtime:
            self.daily_runtime[day] = 0
        self.daily_runtime[day] += hours

    def get_daily_runtime(self, day):
        return self.daily_runtime.get(day, 0)

    def to_dict(self):
        return {
            "name": self.name,
            "power": self.power,
            "priority": self.priority,
            "start_time": self.start_time.toString("HH:mm"),
            "end_time": self.end_time.toString("HH:mm"),
            "min_runtime": self.min_runtime
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["name"],
            data["power"],
            data["priority"],
            QTime.fromString(data["start_time"], "HH:mm"),
            QTime.fromString(data["end_time"], "HH:mm"),
            data["min_runtime"]
        )

class SolarHousehold:
    def __init__(self):
        self.solar_panel = None
        self.battery = None
        self.charge_controller = None
        self.inverter = None
        self.appliances = []
        self.sunrise = QTime(6, 0)
        self.sunset = QTime(20, 0)
        self.system_voltage = 12

    def add_appliance(self, appliance):
        self.appliances.append(appliance)

    def remove_appliance(self, appliance):
        self.appliances.remove(appliance)

    def total_power_consumption(self):
        return sum(appliance.power for appliance in self.appliances)

    def to_dict(self):
        return {
            "solar_panel": self.solar_panel.to_dict() if self.solar_panel else None,
            "battery": self.battery.to_dict() if self.battery else None,
            "charge_controller": self.charge_controller.to_dict() if self.charge_controller else None,
            "inverter": self.inverter.to_dict() if self.inverter else None,
            "appliances": [appliance.to_dict() for appliance in self.appliances],
            "sunrise": self.sunrise.toString("HH:mm"),
            "sunset": self.sunset.toString("HH:mm"),
            "system_voltage": self.system_voltage
        }

    @classmethod
    def from_dict(cls, data):
        household = cls()
        household.solar_panel = SolarComponent.from_dict(data["solar_panel"]) if data["solar_panel"] else None
        household.battery = SolarComponent.from_dict(data["battery"]) if data["battery"] else None
        household.charge_controller = SolarComponent.from_dict(data["charge_controller"]) if data["charge_controller"] else None
        household.inverter = SolarComponent.from_dict(data["inverter"]) if data["inverter"] else None
        household.appliances = [Appliance.from_dict(app_data) for app_data in data["appliances"]]
        household.sunrise = QTime.fromString(data["sunrise"], "HH:mm")
        household.sunset = QTime.fromString(data["sunset"], "HH:mm")
        household.system_voltage = data["system_voltage"]
        return household

class SimulationGraphs(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.figure = Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        self.ax1 = self.figure.add_subplot(311)
        self.ax2 = self.figure.add_subplot(312)
        self.ax3 = self.figure.add_subplot(313)

    def update_graphs(self, results):
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()

        hours = range(len(results))
        generation = [r['generation'] for r in results]
        power_used = [r['power_used'] for r in results]
        battery_charge = [r['battery_charge'] for r in results]

        self.ax1.plot(hours, generation, label='Solar Generation')
        self.ax1.plot(hours, power_used, label='Power Used')
        self.ax1.set_ylabel('Power (Wh)')
        self.ax1.legend()
        self.ax1.set_title('Solar Generation vs Power Used')

        self.ax2.plot(hours, battery_charge)
        self.ax2.set_ylabel('Battery Charge (Wh)')
        self.ax2.set_title('Battery Charge over Time')

        appliance_runtimes = {}
        for i, result in enumerate(results):
            for appliance in result['appliances_running']:
                if appliance not in appliance_runtimes:
                    appliance_runtimes[appliance] = [0] * len(results)
                appliance_runtimes[appliance][i] = 1

        for appliance, runtime in appliance_runtimes.items():
            self.ax3.plot(hours, runtime, label=appliance)
        self.ax3.set_ylabel('Running Status')
        self.ax3.set_title('Appliance Running Status')
        self.ax3.legend()

        self.ax3.set_xlabel('Hours')
        self.figure.tight_layout()
        self.canvas.draw()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Solar Powered Household Simulator")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("""
            QWidget {
                font-size: 14px;
            }
            QLabel {
                font-weight: bold;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QLineEdit, QComboBox, QTimeEdit {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)

        self.household = SolarHousehold()
        self.solar_generation_data = {
            6: 0, 7: 0.1, 8: 0.3, 9: 0.5, 10: 0.7, 11: 0.8, 12: 0.9, 13: 1.0,
            14: 0.9, 15: 0.8, 16: 0.7, 17: 0.5, 18: 0.3, 19: 0.1, 20: 0
        }

        self.create_main_layout()

    def create_main_layout(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout()

        # Create tabs
        tab_widget = QTabWidget()
        tab_widget.addTab(self.create_setup_tab(), "Setup")
        tab_widget.addTab(self.create_simulation_tab(), "Simulation")

        main_layout.addWidget(tab_widget)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def create_setup_tab(self):
        setup_widget = QWidget()
        setup_layout = QHBoxLayout()

        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # Solar Components
        self.create_component_inputs(left_layout)

        # System Settings
        self.create_system_settings(left_layout)

        # Load/Save buttons
        self.create_load_save_buttons(left_layout)

        # Appliances
        self.create_appliance_inputs(right_layout)

        setup_layout.addLayout(left_layout)
        setup_layout.addLayout(right_layout)
        setup_widget.setLayout(setup_layout)

        return setup_widget

    def create_simulation_tab(self):
        simulation_widget = QWidget()
        simulation_layout = QVBoxLayout()

        # Simulation control
        control_layout = QHBoxLayout()
        self.simulate_btn = QPushButton("Run Simulation")
        self.simulate_btn.clicked.connect(self.run_simulation)
        control_layout.addWidget(self.simulate_btn)

        simulation_layout.addLayout(control_layout)

        # Graphs
        self.graphs = SimulationGraphs()
        simulation_layout.addWidget(self.graphs)

        simulation_widget.setLayout(simulation_layout)
        return simulation_widget

    def create_component_inputs(self, layout):
        components = [
            ("Solar Panel", "capacity (watts)"),
            ("Battery", "capacity (watt-hours)"),
            ("Charge Controller", "capacity (amps)"),
            ("Inverter", "capacity (watts)")
        ]

        component_layout = QGridLayout()
        for i, (component, unit) in enumerate(components):
            component_layout.addWidget(QLabel(f"{component} {unit}:"), i, 0)
            input_field = QLineEdit()
            input_field.setObjectName(f"{component.lower().replace(' ', '_')}_input")
            component_layout.addWidget(input_field, i, 1)

        set_components_btn = QPushButton("Set Components")
        set_components_btn.clicked.connect(self.set_components)
        component_layout.addWidget(set_components_btn, len(components), 0, 1, 2)

        layout.addLayout(component_layout)

    def create_system_settings(self, layout):
        settings_layout = QGridLayout()
        settings_layout.addWidget(QLabel("Sunrise:"), 0, 0)
        self.sunrise_edit = QTimeEdit()
        self.sunrise_edit.setTime(self.household.sunrise)
        settings_layout.addWidget(self.sunrise_edit, 0, 1)

        settings_layout.addWidget(QLabel("Sunset:"), 1, 0)
        self.sunset_edit = QTimeEdit()
        self.sunset_edit.setTime(self.household.sunset)
        settings_layout.addWidget(self.sunset_edit, 1, 1)

        settings_layout.addWidget(QLabel("System Voltage:"), 2, 0)
        self.system_voltage_combo = QComboBox()
        self.system_voltage_combo.addItems(["12V", "24V"])
        settings_layout.addWidget(self.system_voltage_combo, 2, 1)

        set_system_btn = QPushButton("Set System Settings")
        set_system_btn.clicked.connect(self.set_system_settings)
        settings_layout.addWidget(set_system_btn, 3, 0, 1, 2)

        layout.addLayout(settings_layout)

    def create_appliance_inputs(self, layout):
        appliance_layout = QGridLayout()
        appliance_layout.addWidget(QLabel("Appliance Name:"), 0, 0)
        self.appliance_name_input = QLineEdit()
        appliance_layout.addWidget(self.appliance_name_input, 0, 1)

        appliance_layout.addWidget(QLabel("Power (watts):"), 1, 0)
        self.appliance_power_input = QLineEdit()
        appliance_layout.addWidget(self.appliance_power_input, 1, 1)

        appliance_layout.addWidget(QLabel("Priority:"), 2, 0)
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Low", "Medium", "High"])
        appliance_layout.addWidget(self.priority_combo, 2, 1)

        appliance_layout.addWidget(QLabel("Start Time:"), 3, 0)
        self.start_time_edit = QTimeEdit()
        appliance_layout.addWidget(self.start_time_edit, 3, 1)

        appliance_layout.addWidget(QLabel("End Time:"), 4, 0)
        self.end_time_edit = QTimeEdit()
        appliance_layout.addWidget(self.end_time_edit, 4, 1)

        appliance_layout.addWidget(QLabel("Min Runtime (hours):"), 5, 0)
        self.min_runtime_input = QLineEdit()
        appliance_layout.addWidget(self.min_runtime_input, 5, 1)

        add_appliance_btn = QPushButton("Add Appliance")
        add_appliance_btn.clicked.connect(self.add_appliance)
        appliance_layout.addWidget(add_appliance_btn, 6, 0, 1, 2)

        self.appliance_list = QListWidget()
        appliance_layout.addWidget(self.appliance_list, 7, 0, 1, 2)

        remove_appliance_btn = QPushButton("Remove Selected Appliance")
        remove_appliance_btn.clicked.connect(self.remove_appliance)
        appliance_layout.addWidget(remove_appliance_btn, 8, 0, 1, 2)

        self.total_consumption_label = QLabel("Total Power Consumption: 0 watts")
        appliance_layout.addWidget(self.total_consumption_label, 9, 0, 1, 2)

        layout.addLayout(appliance_layout)

    def create_load_save_buttons(self, layout):
        button_layout = QHBoxLayout()
        load_btn = QPushButton("Load Configuration")
        load_btn.clicked.connect(self.load_configuration)
        button_layout.addWidget(load_btn)

        save_btn = QPushButton("Save Configuration")
        save_btn.clicked.connect(self.save_configuration)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def set_components(self):
        try:
            self.household.solar_panel = SolarComponent("Solar Panel", float(self.findChild(QLineEdit, "solar_panel_input").text()))
            self.household.battery = SolarComponent("Battery", float(self.findChild(QLineEdit, "battery_input").text()))
            self.household.charge_controller = SolarComponent("Charge Controller", float(self.findChild(QLineEdit, "charge_controller_input").text()))
            self.household.inverter = SolarComponent("Inverter", float(self.findChild(QLineEdit, "inverter_input").text()))
            QMessageBox.information(self, "Success", "Solar components set successfully!")
        except ValueError:
            QMessageBox.warning(self, "Error", "Please enter valid numeric values for all components.")

    def set_system_settings(self):
        self.household.sunrise = self.sunrise_edit.time()
        self.household.sunset = self.sunset_edit.time()
        self.household.system_voltage = int(self.system_voltage_combo.currentText().replace("V", ""))
        QMessageBox.information(self, "Success", "System settings set successfully!")

    def add_appliance(self):
        name = self.appliance_name_input.text()
        try:
            power = float(self.appliance_power_input.text())
            priority = self.priority_combo.currentText()
            start_time = self.start_time_edit.time()
            end_time = self.end_time_edit.time()
            min_runtime = float(self.min_runtime_input.text())
            
            appliance = Appliance(name, power, priority, start_time, end_time, min_runtime)
            self.household.add_appliance(appliance)
            self.appliance_list.addItem(f"{name} ({power} W) - {priority} priority - {start_time.toString('HH:mm')} to {end_time.toString('HH:mm')} - Min runtime: {min_runtime}h")
            self.update_total_consumption()
        except ValueError:
            QMessageBox.warning(self, "Error", "Please enter valid numeric values for appliance power and minimum runtime.")

    def remove_appliance(self):
        selected_item = self.appliance_list.currentItem()
        if selected_item:
            index = self.appliance_list.row(selected_item)
            self.household.remove_appliance(self.household.appliances[index])
            self.appliance_list.takeItem(index)
            self.update_total_consumption()

    def update_total_consumption(self):
        total = self.household.total_power_consumption()
        self.total_consumption_label.setText(f"Total Power Consumption: {total} watts")

    def run_simulation(self):
        if not all([self.household.solar_panel, self.household.battery, self.household.charge_controller, self.household.inverter]):
            QMessageBox.warning(self, "Error", "Please set all solar components before running the simulation.")
            return

        if not self.household.appliances:
            QMessageBox.warning(self, "Error", "Please add at least one appliance before running the simulation.")
            return

        self.simulation_results = self.simulate_days(3)  # Simulate for 3 days
        self.graphs.update_graphs(self.simulation_results)

    def simulate_days(self, num_days):
        results = []
        battery_charge = self.household.battery.capacity
        total_generation = self.household.solar_panel.capacity

        for day in range(num_days):
            # Reset daily runtime for each appliance at the start of the day
            for appliance in self.household.appliances:
                appliance.reset_daily_runtime(day)

            for hour in range(24):
                hour_result = self.simulate_hour(hour, day, battery_charge, total_generation)
                results.append(hour_result)
                battery_charge = hour_result['battery_charge']

        return results

    def simulate_hour(self, hour, day, battery_charge, total_generation):
        generation_percentage = self.solar_generation_data.get(hour, 0)
        generation = total_generation * generation_percentage

        available_power = generation + battery_charge
        power_used = 0
        appliances_running = []

        for appliance in sorted(self.household.appliances, key=lambda x: x.priority):
            start_hour = appliance.start_time.hour()
            end_hour = appliance.end_time.hour()
            
            if start_hour <= hour < end_hour or (end_hour < start_hour and (hour >= start_hour or hour < end_hour)):
                if available_power >= appliance.power and appliance.get_daily_runtime(day) < appliance.min_runtime:
                    power_used += appliance.power
                    available_power -= appliance.power
                    appliance.add_runtime(day, 1)
                    appliances_running.append(appliance.name)

        battery_charge = min(available_power, self.household.battery.capacity)

        return {
            'day': day,
            'hour': hour,
            'generation': generation,
            'power_used': power_used,
            'battery_charge': battery_charge,
            'appliances_running': appliances_running
        }

    def load_configuration(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Configuration", "", "JSON Files (*.json)")
        if file_name:
            try:
                with open(file_name, 'r') as file:
                    data = json.load(file)
                    self.household = SolarHousehold.from_dict(data)
                    self.update_ui_from_household()
                QMessageBox.information(self, "Success", "Configuration loaded successfully!")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load configuration: {str(e)}")

    def save_configuration(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Configuration", "", "JSON Files (*.json)")
        if file_name:
            try:
                with open(file_name, 'w') as file:
                    json.dump(self.household.to_dict(), file, indent=2)
                QMessageBox.information(self, "Success", "Configuration saved successfully!")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to save configuration: {str(e)}")

    def update_ui_from_household(self):
        # Update component inputs
        self.findChild(QLineEdit, "solar_panel_input").setText(str(self.household.solar_panel.capacity))
        self.findChild(QLineEdit, "battery_input").setText(str(self.household.battery.capacity))
        self.findChild(QLineEdit, "charge_controller_input").setText(str(self.household.charge_controller.capacity))
        self.findChild(QLineEdit, "inverter_input").setText(str(self.household.inverter.capacity))

        # Update system settings
        self.sunrise_edit.setTime(self.household.sunrise)
        self.sunset_edit.setTime(self.household.sunset)
        self.system_voltage_combo.setCurrentText(f"{self.household.system_voltage}V")

        # Update appliance list
        self.appliance_list.clear()
        for appliance in self.household.appliances:
            self.appliance_list.addItem(f"{appliance.name} ({appliance.power} W) - {appliance.priority} priority - {appliance.start_time.toString('HH:mm')} to {appliance.end_time.toString('HH:mm')} - Min runtime: {appliance.min_runtime}h")

        self.update_total_consumption()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())