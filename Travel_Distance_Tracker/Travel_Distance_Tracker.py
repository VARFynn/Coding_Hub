import tkinter as tk
from tkinter import ttk, messagebox
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import threading
import queue
import folium
import webbrowser
import os
import json
from datetime import datetime
from tkcalendar import DateEntry

class ModernBahnhofDistanzApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bahnhof-Distanz Rechner")
        self.root.geometry("600x800")  # Erhöht für zusätzliche Elemente
        self.root.configure(bg='#ffffff')
        
        # Queue für Thread-Kommunikation
        self.queue = queue.Queue()
        
        # Style konfigurieren
        style = ttk.Style()
        style.theme_use('clam')
        
        # Hauptcontainer
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Überschrift
        title_label = ttk.Label(
            main_frame, 
            text="Bahnhof-Distanz Rechner", 
            font=('Helvetica', 16, 'bold')
        )
        title_label.pack(pady=10)

        # Start Station
        start_frame = ttk.LabelFrame(main_frame, text="Start", padding="10")
        start_frame.pack(fill=tk.X, pady=5)
        self.start_entry = ttk.Entry(start_frame)
        self.start_entry.pack(fill=tk.X)

        # Container für Zwischenstationen
        self.stops_container = ttk.Frame(main_frame)
        self.stops_container.pack(fill=tk.X)
        
        # Liste für Zwischenstop-Entries
        self.stop_entries = []

        # Button für neue Zwischenstationen
        self.add_stop_btn = ttk.Button(
            main_frame, 
            text="+ Zwischenhalt hinzufügen",
            command=self.add_stop
        )
        self.add_stop_btn.pack(pady=5)

        # End Station
        end_frame = ttk.LabelFrame(main_frame, text="Ziel", padding="10")
        end_frame.pack(fill=tk.X, pady=5)
        self.end_entry = ttk.Entry(end_frame)
        self.end_entry.pack(fill=tk.X)

        # Calculate Button
        self.calc_button = ttk.Button(
            main_frame,
            text="Route berechnen",
            command=self.start_calculation
        )
        self.calc_button.pack(pady=10)

        # Map Button
        self.map_button = ttk.Button(
            main_frame,
            text="Route auf Karte anzeigen",
            command=self.show_map,
            state='disabled'
        )
        self.map_button.pack(pady=5)

        # Frame für Reise speichern
        save_frame = ttk.LabelFrame(main_frame, text="Reise speichern", padding="10")
        save_frame.pack(fill=tk.X, pady=10)
        
        # Datum Auswahl
        date_frame = ttk.Frame(save_frame)
        date_frame.pack(fill=tk.X, pady=5)
        ttk.Label(date_frame, text="Reisedatum:").pack(side=tk.LEFT, padx=5)
        self.date_picker = DateEntry(date_frame, width=12, background='darkblue',
                                    foreground='white', borderwidth=2)
        self.date_picker.pack(side=tk.LEFT, padx=5)
        
        # Notizen
        note_frame = ttk.Frame(save_frame)
        note_frame.pack(fill=tk.X, pady=5)
        ttk.Label(note_frame, text="Notizen:").pack(side=tk.LEFT, padx=5)
        self.note_entry = ttk.Entry(note_frame)
        self.note_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Speichern Button
        self.save_button = ttk.Button(
            save_frame,
            text="Reise speichern",
            command=self.save_journey,
            state='disabled'
        )
        self.save_button.pack(pady=5)
        
        # Button zum Anzeigen der Historie
        self.history_button = ttk.Button(
            main_frame,
            text="Reisehistorie anzeigen",
            command=self.show_history
        )
        self.history_button.pack(pady=5)

        # Progress Bar
        self.progress = ttk.Progressbar(
            main_frame,
            mode='indeterminate',
            length=400
        )

        # Result Area
        self.result_text = tk.Text(
            main_frame,
            height=12,
            width=50,
            wrap=tk.WORD,
            font=('Helvetica', 10)
        )
        self.result_text.pack(pady=10, fill=tk.BOTH, expand=True)

        # Status
        self.status_var = tk.StringVar(value="Bereit")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var)
        self.status_label.pack()

        # Geocoder
        self.geolocator = Nominatim(user_agent="train_journey_tracker")
        
        # Letzte Route speichern
        self.last_route = None
        
        # Dateiname für die Reisehistorie
        self.history_file = "reisehistorie.json"

        # Timer für Queue-Check
        self.check_queue()

    def add_stop(self):
        """Fügt ein neues Zwischenstop-Eingabefeld hinzu"""
        frame = ttk.LabelFrame(self.stops_container, text=f"Zwischenhalt", padding="10")
        frame.pack(fill=tk.X, pady=5)
        
        entry_frame = ttk.Frame(frame)
        entry_frame.pack(fill=tk.X)
        
        entry = ttk.Entry(entry_frame)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        remove_btn = ttk.Button(
            entry_frame, 
            text="×",
            width=3,
            command=lambda: self.remove_stop(frame)
        )
        remove_btn.pack(side=tk.RIGHT, padx=5)
        
        self.stop_entries.append((frame, entry))

    def remove_stop(self, frame):
        """Entfernt einen Zwischenstop"""
        for i, (f, e) in enumerate(self.stop_entries):
            if f == frame:
                self.stop_entries.pop(i)
                frame.destroy()
                break

    def save_journey(self):
        """Speichert die aktuelle Reise in der Historie"""
        if not self.last_route:
            messagebox.showerror("Fehler", "Bitte erst eine Route berechnen!")
            return
            
        # Erstelle Eintrag für die Historie
        journey = {
            "datum": self.date_picker.get_date().strftime("%Y-%m-%d"),
            "zeitpunkt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "stationen": [],
            "distanz": 0,
            "notizen": self.note_entry.get().strip()
        }
        
        # Füge alle Stationen hinzu
        total_distance = 0
        for i, (name, address, coords) in enumerate(self.last_route):
            station = {
                "name": name,
                "address": address,
                "koordinaten": {"lat": coords[0], "lon": coords[1]}
            }
            journey["stationen"].append(station)
            
            # Berechne Distanz zum nächsten Halt
            if i < len(self.last_route) - 1:
                next_coords = self.last_route[i + 1][2]
                distance = geodesic(coords, next_coords).kilometers
                total_distance += distance
        
        journey["distanz"] = round(total_distance, 1)
        
        # Lade bestehende Historie oder erstelle neue
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            history = []
        
        # Füge neue Reise hinzu
        history.append(journey)
        
        # Speichere aktualisierte Historie
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        
        messagebox.showinfo("Erfolg", "Reise wurde gespeichert!")
        self.note_entry.delete(0, tk.END)

    def show_history(self):
        """Zeigt die Reisehistorie in einem neuen Fenster an"""
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except FileNotFoundError:
            messagebox.showinfo("Info", "Noch keine Reisen gespeichert.")
            return
        
        # Erstelle neues Fenster
        history_window = tk.Toplevel(self.root)
        history_window.title("Reisehistorie")
        history_window.geometry("600x400")
        
        # Textbereich für Historie
        text = tk.Text(history_window, wrap=tk.WORD, font=('Helvetica', 10))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=text.yview)
        
        # Formatiere und zeige Historie
        for journey in sorted(history, key=lambda x: x["datum"], reverse=True):
            text.insert(tk.END, f"Datum: {journey['datum']}\n")
            text.insert(tk.END, "Route:\n")
            
            for i, station in enumerate(journey["stationen"]):
                text.insert(tk.END, f"  {i+1}. {station['name']}\n")
            
            text.insert(tk.END, f"Distanz: {journey['distanz']} km\n")
            if journey["notizen"]:
                text.insert(tk.END, f"Notizen: {journey['notizen']}\n")
            text.insert(tk.END, "\n" + "-"*50 + "\n\n")
        
        text.config(state=tk.DISABLED)  # Readonly

    def calculate_route(self):
        """Berechnet die optimierte Route"""
        try:
            self.queue.put(("status", "Suche Stationen..."))
            
            # Sammle alle Stationen
            stations = []
            
            # Start
            start_name = self.start_entry.get().strip()
            if not start_name:
                raise ValueError("Bitte Startbahnhof eingeben")
            start = self.geolocator.geocode(f"{start_name} bahnhof", exactly_one=True)
            if not start:
                raise ValueError(f"Konnte '{start_name}' nicht finden")
            stations.append((start_name, start.address, (start.latitude, start.longitude)))
            
            # Zwischenstops
            for _, entry in self.stop_entries:
                stop_name = entry.get().strip()
                if stop_name:  # Ignoriere leere Zwischenstops
                    stop = self.geolocator.geocode(f"{stop_name} bahnhof", exactly_one=True)
                    if stop:
                        stations.append((stop_name, stop.address, (stop.latitude, stop.longitude)))
            
            # Ziel
            end_name = self.end_entry.get().strip()
            if not end_name:
                raise ValueError("Bitte Zielbahnhof eingeben")
            end = self.geolocator.geocode(f"{end_name} bahnhof", exactly_one=True)
            if not end:
                raise ValueError(f"Konnte '{end_name}' nicht finden")
            stations.append((end_name, end.address, (end.latitude, end.longitude)))
            
            # Route optimieren
            if len(stations) > 2:  # Nur optimieren wenn Zwischenstops vorhanden
                optimized = [stations[0]]  # Start ist fix
                remaining = stations[1:-1]  # Zwischenstops
                
                while remaining:
                    current = optimized[-1][2]  # Koordinaten der letzten Station
                    closest = min(remaining, key=lambda x: geodesic(current, x[2]).kilometers)
                    optimized.append(closest)
                    remaining.remove(closest)
                
                optimized.append(stations[-1])  # Ziel ist fix
                stations = optimized

            # Speichere optimierte Route
            self.last_route = stations
            
            # Aktiviere die Buttons
            self.root.after(0, lambda: self.map_button.config(state='normal'))
            self.root.after(0, lambda: self.save_button.config(state='normal'))

            # Route formatieren und Distanz berechnen
            total_distance = 0
            result = "Route:\n\n"
            
            for i, (name, address, coords) in enumerate(stations):
                result += f"[{name}]\n{address}"
                if i < len(stations) - 1:
                    next_coords = stations[i + 1][2]
                    distance = geodesic(coords, next_coords).kilometers
                    total_distance += distance
                    result += f"\n\n    ↓ {round(distance, 1)} km\n\n"
            
            result += f"\nGesamtstrecke: {round(total_distance, 1)} km"
            
            self.queue.put(("result", result))
            self.queue.put(("status", "Fertig"))
            
        except Exception as e:
            self.queue.put(("error", str(e)))
            self.queue.put(("status", "Fehler aufgetreten"))
            self.last_route = None
            self.root.after(0, lambda: self.map_button.config(state='disabled'))
            self.root.after(0, lambda: self.save_button.config(state='disabled'))
            
        finally:
            self.queue.put(("done", None))

    def create_route_map(self):
        """Erstellt eine Karte mit der Route"""
        if not self.last_route:
            return None
            
        # Erstelle Karte zentriert auf dem Mittelpunkt der Route
        lats = [coord[2][0] for coord in self.last_route]
        lons = [coord[2][1] for coord in self.last_route]
        center_lat = sum(lats) / len(lats)
        center_lon = sum(lons) / len(lons)
        
        # Erstelle Karte
        m = folium.Map(location=[center_lat, center_lon], zoom_start=6)
        
        # Füge Marker für jede Station hinzu
        for i, (name, address, coords) in enumerate(self.last_route):
            color = 'green' if i == 0 else 'red' if i == len(self.last_route)-1 else 'blue'
            folium.Marker(
                coords,
                popup=f"<b>{name}</b><br>{address}<br>Station {i+1} von {len(self.last_route)}",
                icon=folium.Icon(color=color)
            ).add_to(m)
        
        # Zeichne Linien zwischen den Stationen
        points = [(coord[2][0], coord[2][1]) for coord in self.last_route]
        folium.PolyLine(
            points,
            weight=2,
            color='blue',
            opacity=0.8
        ).add_to(m)
        
        # Speichere Karte
        map_path = "route_map.html"
        m.save(map_path)
        return map_path

    def show_map(self):
        """Zeigt die Routenkarte im Standardbrowser"""
        if self.last_route:
            map_path = self.create_route_map()
            if map_path:
                abs_path = os.path.abspath(map_path)
                webbrowser.open('file://' + abs_path)

    def check_queue(self):
        """Prüft die Queue auf Nachrichten vom Worker-Thread"""
        try:
            while True:
                msg = self.queue.get_nowait()
                if msg[0] == "status":
                    self.status_var.set(msg[1])
                elif msg[0] == "result":
                    self.result_text.delete(1.0, tk.END)
                    self.result_text.insert(tk.END, msg[1])
                elif msg[0] == "error":
                    messagebox.showerror("Fehler", msg[1])
                elif msg[0] == "done":
                    self.calc_button.config(state='normal')
                    self.progress.stop()
                    self.progress.pack_forget()
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.check_queue)

    def start_calculation(self):
        """Startet die Berechnung in einem separaten Thread"""
        self.calc_button.config(state='disabled')
        self.result_text.delete(1.0, tk.END)
        self.progress.pack(pady=10)
        self.progress.start()
        
        thread = threading.Thread(target=self.calculate_route)
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernBahnhofDistanzApp(root)
    root.mainloop()