# Travel Tracker

A Python tool to track and visualize your travels using various modes of transportation.

## Features

- **Multiple Modes of Transportation**
  - 🚂 Train (automatically searches for train stations)
  - ✈️ Flight (automatically searches for airports)
  - 🚗 Car (searches for locations)

- **Route Planning**
  - Enter starting point and destination
  - Add as many stops as you like
  - Automatically optimize the route
  - Calculate distances between all stops

- **Visualization**
  - Interactive map with the route
  - Start (green), stops (blue), and destination (red) marked
  - Connection lines between the stops
  - Popup information for each stop

- **Travel History**
  - Save trips with dates
  - Add notes for each trip
  - View all saved trips in a clear format
  - Automatically sort trips by date

## Installation

1. Ensure Python 3.x is installed.
2. Install the required packages:

```bash
pip install geopy folium tkcalendar
```

## Usage

1. Run the program:
```bash
python travel_tracker.py
```

2. Choose the mode of transport (Train, Flight, or Car)
3. Enter the starting point and destination
4. Optionally, add stops
5. Click "Calculate Route"
6. Visualize the route on the map
7. Save the trip with date and notes

## Files

- `travel_tracker.py`: Main program
- `travel_history.json`: Saved trips (created automatically)
- `route_map.html`: Temporary map file for visualization

## Requirements

- Python 3.x
- geopy
- folium
- tkcalendar
- tkinter (usually included with Python)

## Tips

- For train routes, simply enter the city name; "Station" will be automatically appended.
- For flights, enter either the airport or city name.
- For car routes, you can add any locations as stops.
- You can access the travel history at any time using the corresponding button.