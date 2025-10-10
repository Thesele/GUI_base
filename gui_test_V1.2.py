import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import json

class GPSAntennaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GPS & Antenna Control System")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # Configure style
        style = ttk.Style()
        style.configure('Header.TLabel', font=('Arial', 10, 'bold'))
        
        # Create main container
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # GPS Data Section
        self.create_gps_section(main_frame)
        
        # Antenna Angles Section
        self.create_antenna_section(main_frame)
        
        # Control Buttons
        self.create_control_buttons(main_frame)
        
        # Status/Log Section
        self.create_log_section(main_frame)
        
        # Store received data
        self.received_data = {
            'gps': {'lat': 0.0, 'lon': 0.0, 'alt': 0.0},
            'antenna': {'azimuth': 0.0, 'elevation': 0.0}
        }
    
    def create_gps_section(self, parent):
        # GPS Frame
        gps_frame = ttk.LabelFrame(parent, text="GPS Data", padding="10")
        gps_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Latitude
        ttk.Label(gps_frame, text="Latitude (°):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.lat_entry = ttk.Entry(gps_frame, width=20)
        self.lat_entry.grid(row=0, column=1, padx=5, pady=2)
        self.lat_entry.insert(0, "0.0")
        
        ttk.Label(gps_frame, text="Received:").grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        self.lat_received = ttk.Label(gps_frame, text="0.0", foreground="blue")
        self.lat_received.grid(row=0, column=3, sticky=tk.W, padx=5)
        
        # Longitude
        ttk.Label(gps_frame, text="Longitude (°):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.lon_entry = ttk.Entry(gps_frame, width=20)
        self.lon_entry.grid(row=1, column=1, padx=5, pady=2)
        self.lon_entry.insert(0, "0.0")
        
        ttk.Label(gps_frame, text="Received:").grid(row=1, column=2, sticky=tk.W, padx=(10, 0))
        self.lon_received = ttk.Label(gps_frame, text="0.0", foreground="blue")
        self.lon_received.grid(row=1, column=3, sticky=tk.W, padx=5)
        
        # Altitude
        ttk.Label(gps_frame, text="Altitude (m):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.alt_entry = ttk.Entry(gps_frame, width=20)
        self.alt_entry.grid(row=2, column=1, padx=5, pady=2)
        self.alt_entry.insert(0, "0.0")
        
        ttk.Label(gps_frame, text="Received:").grid(row=2, column=2, sticky=tk.W, padx=(10, 0))
        self.alt_received = ttk.Label(gps_frame, text="0.0", foreground="blue")
        self.alt_received.grid(row=2, column=3, sticky=tk.W, padx=5)
    
    def create_antenna_section(self, parent):
        # Antenna Frame
        antenna_frame = ttk.LabelFrame(parent, text="Antenna Angles", padding="10")
        antenna_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Azimuth
        ttk.Label(antenna_frame, text="Azimuth (°):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.azimuth_entry = ttk.Entry(antenna_frame, width=20)
        self.azimuth_entry.grid(row=0, column=1, padx=5, pady=2)
        self.azimuth_entry.insert(0, "0.0")
        
        ttk.Label(antenna_frame, text="Received:").grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        self.azimuth_received = ttk.Label(antenna_frame, text="0.0", foreground="blue")
        self.azimuth_received.grid(row=0, column=3, sticky=tk.W, padx=5)
        
        # Elevation
        ttk.Label(antenna_frame, text="Elevation (°):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.elevation_entry = ttk.Entry(antenna_frame, width=20)
        self.elevation_entry.grid(row=1, column=1, padx=5, pady=2)
        self.elevation_entry.insert(0, "0.0")
        
        ttk.Label(antenna_frame, text="Received:").grid(row=1, column=2, sticky=tk.W, padx=(10, 0))
        self.elevation_received = ttk.Label(antenna_frame, text="0.0", foreground="blue")
        self.elevation_received.grid(row=1, column=3, sticky=tk.W, padx=5)
    
    def create_control_buttons(self, parent):
        # Button Frame
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Send All Button
        send_btn = ttk.Button(button_frame, text="Send All Data", command=self.send_all_data)
        send_btn.grid(row=0, column=0, padx=5)
        
        # Send GPS Button
        send_gps_btn = ttk.Button(button_frame, text="Send GPS", command=self.send_gps_data)
        send_gps_btn.grid(row=0, column=1, padx=5)
        
        # Send Antenna Button
        send_antenna_btn = ttk.Button(button_frame, text="Send Antenna", command=self.send_antenna_data)
        send_antenna_btn.grid(row=0, column=2, padx=5)
        
        # Simulate Receive Button
        receive_btn = ttk.Button(button_frame, text="Simulate Receive", command=self.simulate_receive)
        receive_btn.grid(row=0, column=3, padx=5)
        
        # Clear Log Button
        clear_btn = ttk.Button(button_frame, text="Clear Log", command=self.clear_log)
        clear_btn.grid(row=0, column=4, padx=5)
    
    def create_log_section(self, parent):
        # Log Frame
        log_frame = ttk.LabelFrame(parent, text="Activity Log", padding="10")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Text widget with scrollbar
        self.log_text = tk.Text(log_frame, height=10, width=70, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.log("System initialized and ready")
    
    def validate_float(self, value, field_name):
        try:
            return float(value)
        except ValueError:
            messagebox.showerror("Invalid Input", f"{field_name} must be a valid number")
            return None
    
    def send_gps_data(self):
        lat = self.validate_float(self.lat_entry.get(), "Latitude")
        lon = self.validate_float(self.lon_entry.get(), "Longitude")
        alt = self.validate_float(self.alt_entry.get(), "Altitude")
        
        if lat is None or lon is None or alt is None:
            return
        
        # Validate ranges
        if not (-90 <= lat <= 90):
            messagebox.showerror("Invalid Input", "Latitude must be between -90 and 90")
            return
        if not (-180 <= lon <= 180):
            messagebox.showerror("Invalid Input", "Longitude must be between -180 and 180")
            return
        
        gps_data = {
            'latitude': lat,
            'longitude': lon,
            'altitude': alt
        }
        
        self.log(f"SENT GPS: {json.dumps(gps_data, indent=2)}")
        messagebox.showinfo("Success", "GPS data sent successfully!")
    
    def send_antenna_data(self):
        azimuth = self.validate_float(self.azimuth_entry.get(), "Azimuth")
        elevation = self.validate_float(self.elevation_entry.get(), "Elevation")
        
        if azimuth is None or elevation is None:
            return
        
        # Validate ranges
        if not (0 <= azimuth <= 360):
            messagebox.showerror("Invalid Input", "Azimuth must be between 0 and 360")
            return
        if not (-90 <= elevation <= 90):
            messagebox.showerror("Invalid Input", "Elevation must be between -90 and 90")
            return
        
        antenna_data = {
            'azimuth': azimuth,
            'elevation': elevation
        }
        
        self.log(f"SENT ANTENNA: {json.dumps(antenna_data, indent=2)}")
        messagebox.showinfo("Success", "Antenna data sent successfully!")
    
    def send_all_data(self):
        lat = self.validate_float(self.lat_entry.get(), "Latitude")
        lon = self.validate_float(self.lon_entry.get(), "Longitude")
        alt = self.validate_float(self.alt_entry.get(), "Altitude")
        azimuth = self.validate_float(self.azimuth_entry.get(), "Azimuth")
        elevation = self.validate_float(self.elevation_entry.get(), "Elevation")
        
        if None in [lat, lon, alt, azimuth, elevation]:
            return
        
        # Validate ranges
        if not (-90 <= lat <= 90):
            messagebox.showerror("Invalid Input", "Latitude must be between -90 and 90")
            return
        if not (-180 <= lon <= 180):
            messagebox.showerror("Invalid Input", "Longitude must be between -180 and 180")
            return
        if not (0 <= azimuth <= 360):
            messagebox.showerror("Invalid Input", "Azimuth must be between 0 and 360")
            return
        if not (-90 <= elevation <= 90):
            messagebox.showerror("Invalid Input", "Elevation must be between -90 and 90")
            return
        
        all_data = {
            'gps': {
                'latitude': lat,
                'longitude': lon,
                'altitude': alt
            },
            'antenna': {
                'azimuth': azimuth,
                'elevation': elevation
            }
        }
        
        self.log(f"SENT ALL DATA: {json.dumps(all_data, indent=2)}")
        messagebox.showinfo("Success", "All data sent successfully!")
    
    def simulate_receive(self):
        # Simulate receiving data (in real app, this would come from external source)
        import random
        
        received_gps = {
            'latitude': round(random.uniform(-90, 90), 6),
            'longitude': round(random.uniform(-180, 180), 6),
            'altitude': round(random.uniform(0, 10000), 2)
        }
        
        received_antenna = {
            'azimuth': round(random.uniform(0, 360), 2),
            'elevation': round(random.uniform(-90, 90), 2)
        }
        
        # Update received data displays
        self.lat_received.config(text=str(received_gps['latitude']))
        self.lon_received.config(text=str(received_gps['longitude']))
        self.alt_received.config(text=str(received_gps['altitude']))
        self.azimuth_received.config(text=str(received_antenna['azimuth']))
        self.elevation_received.config(text=str(received_antenna['elevation']))
        
        # Store received data
        self.received_data['gps'] = received_gps
        self.received_data['antenna'] = received_antenna
        
        self.log(f"RECEIVED DATA: GPS={json.dumps(received_gps)}, Antenna={json.dumps(received_antenna)}")
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
        self.log("Log cleared")

def main():
    root = tk.Tk()
    app = GPSAntennaGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
