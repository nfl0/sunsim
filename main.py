import sys
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QListWidget, QMessageBox, 
                             QComboBox, QTextEdit, QTimeEdit, QFileDialog, QDial)
from PyQt5.QtCore import Qt, QTime

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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Solar Powered Household Simulator")
        self.setGeometry(100, 100, 1200, 800)

        self.household = SolarHousehold()
        self.solar_generation_data = {
            6: 0, 7: 0.1, 8: 0.3, 9: 0.5, 10: 0.7, 11: 0.8, 12: 0.9, 13: 1.0,
            14: 0.9, 15: 0.8, 16: 0.7, 17: 0.5, 18: 0.3, 19: 0.1, 20: 0
        }

        main_widget = QWidget()
        main_layout = QHBoxLayout()

        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # Solar Components
        self.create_component_inputs(left_layout)

        # System Settings
        self.create_system_settings(left_layout)

        # Appliances
        self.create_appliance_inputs(right_layout)

        # Simulation
        self.create_simulation_section(right_layout)

        # Load/Save buttons
        self.create_load_save_buttons(left_layout)

        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def create_component_inputs(self, layout):
        components = [
            ("Solar Panel", "capacity (watts)"),
            ("Battery", "capacity (watt-hours)"),
            ("Charge Controller", "capacity (amps)"),
            ("Inverter", "capacity (watts)")
        ]

        for component, unit in components:
            layout.addWidget(QLabel(f"{component} {unit}:"))
            input_field = QLineEdit()
            input_field.setObjectName(f"{component.lower().replace(' ', '_')}_input")
            layout.addWidget(input_field)

        set_components_btn = QPushButton("Set Components")
        set_components_btn.clicked.connect(self.set_components)
        layout.addWidget(set_components_btn)

    def create_system_settings(self, layout):
        layout.addWidget(QLabel("Sunrise:"))
        self.sunrise_edit = QTimeEdit()
        self.sunrise_edit.setTime(self.household.sunrise)
        layout.addWidget(self.sunrise_edit)

        layout.addWidget(QLabel("Sunset:"))
        self.sunset_edit = QTimeEdit()
        self.sunset_edit.setTime(self.household.sunset)
        layout.addWidget(self.sunset_edit)

        layout.addWidget(QLabel("System Voltage:"))
        self.system_voltage_combo = QComboBox()
        self.system_voltage_combo.addItems(["12V", "24V"])
        layout.addWidget(self.system_voltage_combo)

        set_system_btn = QPushButton("Set System Settings")
        set_system_btn.clicked.connect(self.set_system_settings)
        layout.addWidget(set_system_btn)

    def create_appliance_inputs(self, layout):
        layout.addWidget(QLabel("Appliance Name:"))
        self.appliance_name_input = QLineEdit()
        layout.addWidget(self.appliance_name_input)

        layout.addWidget(QLabel("Appliance Power (watts):"))
        self.appliance_power_input = QLineEdit()
        layout.addWidget(self.appliance_power_input)

        layout.addWidget(QLabel("Priority Level:"))
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Low", "Medium", "High"])
        layout.addWidget(self.priority_combo)

        layout.addWidget(QLabel("Start Time:"))
        self.start_time_edit = QTimeEdit()
        layout.addWidget(self.start_time_edit)

        layout.addWidget(QLabel("End Time:"))
        self.end_time_edit = QTimeEdit()
        layout.addWidget(self.end_time_edit)

        layout.addWidget(QLabel("Minimum Runtime (hours):"))
        self.min_runtime_input = QLineEdit()
        layout.addWidget(self.min_runtime_input)

        add_appliance_btn = QPushButton("Add Appliance")
        add_appliance_btn.clicked.connect(self.add_appliance)
        layout.addWidget(add_appliance_btn)

        self.appliance_list = QListWidget()
        layout.addWidget(self.appliance_list)

        remove_appliance_btn = QPushButton("Remove Selected Appliance")
        remove_appliance_btn.clicked.connect(self.remove_appliance)
        layout.addWidget(remove_appliance_btn)

        self.total_consumption_label = QLabel("Total Power Consumption: 0 watts")
        layout.addWidget(self.total_consumption_label)

    def create_simulation_section(self, layout):
        self.simulate_btn = QPushButton("Run Simulation")
        self.simulate_btn.clicked.connect(self.run_simulation)
        layout.addWidget(self.simulate_btn)

        self.hour_dial = QDial()
        self.hour_dial.setMinimum(0)
        self.hour_dial.setMaximum(71)  # 3 full days (24 * 3 - 1)
        self.hour_dial.setNotchesVisible(True)
        self.hour_dial.setWrapping(True)
        self.hour_dial.valueChanged.connect(self.update_simulation_output)
        layout.addWidget(self.hour_dial)

        self.hour_label = QLabel("Hour: 0")
        layout.addWidget(self.hour_label)

        self.simulation_output = QTextEdit()
        self.simulation_output.setReadOnly(True)
        layout.addWidget(self.simulation_output)

    def create_load_save_buttons(self, layout):
        load_btn = QPushButton("Load Configuration")
        load_btn.clicked.connect(self.load_configuration)
        layout.addWidget(load_btn)

        save_btn = QPushButton("Save Configuration")
        save_btn.clicked.connect(self.save_configuration)
        layout.addWidget(save_btn)

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

        self.simulation_results = self.simulate_day()
        self.update_simulation_output(0)

    def simulate_day(self):
        results = []
        battery_charge = self.household.battery.capacity
        total_generation = self.household.solar_panel.capacity

        for day in range(3):  # Simulate 3 days
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

        for appliance in self.household.appliances:
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

    def update_simulation_output(self, value):
        hour = value % 24
        day = value // 24
        self.hour_label.setText(f"Day {day + 1}, Hour: {hour}")
        if hasattr(self, 'simulation_results'):
            result = self.simulation_results[value]
            output = f"Day {day + 1}, Hour {hour}:\n"
            output += f"Solar generation: {result['generation']:.2f} Wh\n"
            output += f"Power used: {result['power_used']:.2f} Wh\n"
            output += f"Battery charge: {result['battery_charge']:.2f} Wh\n"
            output += "Appliances running:\n"
            for appliance in result['appliances_running']:
                output += f"  - {appliance}\n"
            self.simulation_output.setText(output)

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