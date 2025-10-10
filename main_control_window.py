import tkinter as tk
from tkinter import ttk
import socket
import threading
import json

class ControlCenter(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ground Station Control Center")
        self.geometry("700x600")
        self.configure(bg="#1e1e2e")

        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure("TFrame", background="#1e1e2e")
        self.style.configure("TLabel", background="#1e1e2e", foreground="white", font=("Segoe UI", 12))
        self.style.configure("TButton", font=("Segoe UI", 11, "bold"), padding=6)
        self.style.map("TButton", background=[("active", "#4cc9f0")], foreground=[("active", "black")])

        # Connection settings
        self.ip_entry = ttk.Entry(self, width=20)
        self.ip_entry.insert(0, "192.168.4.1")  # Default ESP32 AP IP
        self.ip_entry.pack(pady=5)
        self.port_entry = ttk.Entry(self, width=10)
        self.port_entry.insert(0, "3333")
        self.port_entry.pack(pady=5)
        connect_btn = ttk.Button(self, text="Connect to ESP32", command=self.connect_to_esp)
        connect_btn.pack(pady=5)

        self.sock = None
        self.connected = False

        # Notebook for modes
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Mode 1 Frame (GPS Auto)
        self.gps_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.gps_frame, text="Mode 1: Auto GPS")
        self._build_gps_frame()

        # Control Mode Frame
        self.control_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.control_frame, text="Mode 2: Control Mode")
        self._build_control_frame()

        # Received data labels
        self.own_gps_var = tk.StringVar(value="Own GPS: N/A")
        self.current_azel_var = tk.StringVar(value="Current Az-El: N/A")
        self.calc_azel_var = tk.StringVar(value="Calculated Az-El: N/A")

        received_frame = ttk.Frame(self)
        received_frame.pack(pady=10)
        ttk.Label(received_frame, textvariable=self.own_gps_var).pack()
        ttk.Label(received_frame, textvariable=self.current_azel_var).pack()
        ttk.Label(received_frame, textvariable=self.calc_azel_var).pack()

        # Status bar
        self.status_var = tk.StringVar(value="Currently pointing at: ")
        self.status_label = ttk.Label(self, textvariable=self.status_var, font=("Segoe UI", 13, "bold"), foreground="#4cc9f0")
        self.status_label.pack(side="bottom", pady=8)

    def connect_to_esp(self):
        if self.connected:
            return
        ip = self.ip_entry.get()
        port = int(self.port_entry.get())
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((ip, port))
            self.connected = True
            threading.Thread(target=self.receive_data, daemon=True).start()
            self.status_var.set("Connected to ESP32")
        except Exception as e:
            self.status_var.set(f"Connection failed: {e}")

    def receive_data(self):
        while self.connected:
            try:
                data = self.sock.recv(1024).decode()
                if data:
                    recv_dict = json.loads(data)
                    own_gps = recv_dict.get('gps', {})
                    self.own_gps_var.set(f"Own GPS: Lat {own_gps.get('lat', 'N/A')}, Lon {own_gps.get('lon', 'N/A')}, Alt {own_gps.get('alt', 'N/A')}")
                    self.current_azel_var.set(f"Current Az-El: Az {recv_dict.get('current_az', 'N/A')}°, El {recv_dict.get('current_el', 'N/A')}°")
                    self.calc_azel_var.set(f"Calculated Az-El: Az {recv_dict.get('calc_az', 'N/A')}°, El {recv_dict.get('calc_el', 'N/A')}°")
            except Exception as e:
                self.connected = False
                self.status_var.set(f"Disconnected: {e}")
                break

    def _build_gps_frame(self):
        label = ttk.Label(self.gps_frame, text="Waiting for GPS data...", font=("Segoe UI", 14, "italic"))
        label.pack(pady=30)

    def _build_control_frame(self):
        frame = ttk.Frame(self.control_frame)
        frame.pack(pady=20)

        # GPS Coordinates Entry
        gps_label = ttk.Label(frame, text="Enter GPS Coordinates:")
        gps_label.grid(row=0, column=0, columnspan=2, pady=5)

        ttk.Label(frame, text="Latitude:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.lat_entry = ttk.Entry(frame, width=20)
        self.lat_entry.grid(row=1, column=1, pady=5)

        ttk.Label(frame, text="Longitude:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.lon_entry = ttk.Entry(frame, width=20)
        self.lon_entry.grid(row=2, column=1, pady=5)

        ttk.Label(frame, text="Altitude (m):").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.alt_entry = ttk.Entry(frame, width=20)
        self.alt_entry.grid(row=3, column=1, pady=5)

        # Az/El Entry
        ttk.Label(frame, text="OR Enter Azimuth/Elevation:").grid(row=4, column=0, columnspan=2, pady=15)

        ttk.Label(frame, text="Azimuth (°):").grid(row=5, column=0, sticky="e", padx=5, pady=5)
        self.az_entry = ttk.Entry(frame, width=20)
        self.az_entry.grid(row=5, column=1, pady=5)

        ttk.Label(frame, text="Elevation (°):").grid(row=6, column=0, sticky="e", padx=5, pady=5)
        self.el_entry = ttk.Entry(frame, width=20)
        self.el_entry.grid(row=6, column=1, pady=5)

        # Submit button
        submit_btn = ttk.Button(frame, text="Set Pointing", command=self.update_pointing)
        submit_btn.grid(row=7, column=0, columnspan=2, pady=15)

    def update_pointing(self):
        if not self.connected:
            self.status_var.set("Not connected to ESP32")
            return

        # Check entries in priority: GPS first, else Az/El
        lat = self.lat_entry.get()
        lon = self.lon_entry.get()
        alt = self.alt_entry.get()
        az = self.az_entry.get()
        el = self.el_entry.get()

        send_data = {}
        if lat and lon:
            try:
                send_data = {
                    "type": "gps",
                    "lat": float(lat),
                    "lon": float(lon),
                    "alt": float(alt) if alt else 0.0
                }
                self.status_var.set(f"Sent GPS: Lat {lat}, Lon {lon}, Alt {alt if alt else '0'}")
            except ValueError:
                self.status_var.set("Invalid GPS input")
                return
        elif az and el:
            try:
                send_data = {
                    "type": "azel",
                    "az": float(az),
                    "el": float(el)
                }
                self.status_var.set(f"Sent Az-El: Az {az}°, El {el}°")
            except ValueError:
                self.status_var.set("Invalid Az-El input")
                return
        else:
            self.status_var.set("Invalid/empty input")
            return

        try:
            self.sock.send(json.dumps(send_data).encode())
        except Exception as e:
            self.status_var.set(f"Send failed: {e}")


if __name__ == "__main__":
    app = ControlCenter()
    app.mainloop()