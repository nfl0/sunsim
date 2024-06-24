# Solar Powered Household Simulator

## Overview
The Solar Powered Household Simulator is a tool designed to simulate the operation of a household powered by solar energy. This program allows users to set up their solar power components, define various household appliances, and run simulations to see how the system performs over multiple days.

## Features
- Define solar components: solar panels, batteries, charge controllers, and inverters.
- Set system settings including sunrise and sunset times and system voltage.
- Add and manage household appliances with specific power consumption, priority levels, operating times, and minimum runtime requirements.
- Run simulations to see the power generation, consumption, and battery charge over time.
- Save and load configurations to and from JSON files.

## Requirements
- Python 3.x
- PyQt5

## Installation
1. Ensure you have Python 3.x installed.
2. Install PyQt5 using pip:
    ```bash
    pip install PyQt5
    ```
3. Save the `main.py` script to your desired location.

## Usage
1. Run the program by executing the script:
    ```bash
    python main.py
    ```
2. Use the graphical interface to set up your solar power system, add appliances, and configure settings.
3. Click "Run Simulation" to simulate the system's performance over multiple days.
4. View simulation results and adjust settings as needed.
5. Save and load configurations using the provided buttons.

## Interface Guide
- **Solar Components**: Input fields for the capacities of solar panels, batteries, charge controllers, and inverters. Click "Set Components" to save the inputs.
- **System Settings**: Configure the sunrise and sunset times and system voltage. Click "Set System Settings" to save the settings.
- **Appliances**: Add appliances with name, power, priority, start time, end time, and minimum runtime. Click "Add Appliance" to add it to the list. Select an appliance and click "Remove Selected Appliance" to remove it.
- **Simulation**: Click "Run Simulation" to start the simulation. Use the dial to navigate through hours and view detailed simulation output.
- **Load/Save Configuration**: Use "Load Configuration" to load a saved configuration from a JSON file and "Save Configuration" to save the current configuration.

## Simulation Details
- **Generation Data**: The simulation uses predefined solar generation data based on the hour of the day.
- **Runtime Tracking**: Each appliance tracks its daily runtime to ensure it meets the minimum runtime requirements.
- **Battery Management**: The simulation manages battery charge levels based on power generation and consumption.

## Configuration Example
A sample configuration file, `config.json.example`, is included to demonstrate the structure of the configuration JSON.
