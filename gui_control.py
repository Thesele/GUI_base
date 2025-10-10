
""" - 'My Location' frame shows my_fix (I2C GPS) — read-only.
- 'Target' frame shows target_fix (from UART or GUI) and az/el.
- Manual mode: user sets Az/El -> sends SET_MODE MANUAL + SET_AZ_EL; GUI clears target display.
- GPS target: user sets Lat/Lon/Alt -> sends SET_MODE GPS + SET_TARGET; GUI displays computed az/el from device ACK.

Connects to ESP32 AP (default 192.168.4.1:5000) and exchanges newline-terminated JSON.

MY GOD THIS IS A LOT OF CODE for a growing boy
 """

import socket
import threading
import json
import time
import tkinter as tk
from tkinter import ttk, messagebox

ESP32_HOST = "192.168.4.1"
ESP32_PORT = 5000

class TrackerGUI:
    def __init__(self, root):
        self.root = root
        root.title("Tracker Control (TCP)")

        # Connection state
        self.sock = None
        self.connected = False
        self.recv_thread = None
        self.stop_event = threading.Event()

        # Status variables
        self.my_lat = tk.StringVar()
        self.my_lon = tk.StringVar()
        self.my_alt = tk.StringVar()

        self.tgt_lat = tk.StringVar()
        self.tgt_lon = tk.StringVar()
        self.tgt_alt = tk.StringVar()

        self.az_var = tk.StringVar()
        self.el_var = tk.StringVar()
        self.mode_var = tk.StringVar(value="GPS")

        # UI build
        self._build_ui()

        # connect in background
        t = threading.Thread(target=self._connect_loop, daemon=True)
        t.start()

    def _build_ui(self):
        # My Location frame
        mf = ttk.LabelFrame(self.root, text="My Location (Tracker)")
        mf.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")
        ttk.Label(mf, text="Lat").grid(row=0,column=0); ttk.Label(mf, textvariable=self.my_lat).grid(row=0,column=1)
        ttk.Label(mf, text="Lon").grid(row=1,column=0); ttk.Label(mf, textvariable=self.my_lon).grid(row=1,column=1)
        ttk.Label(mf, text="Alt").grid(row=2,column=0); ttk.Label(mf, textvariable=self.my_alt).grid(row=2,column=1)

        # Target frame
        tf = ttk.LabelFrame(self.root, text="Target (AUTO  or Manual)")
        tf.grid(row=1, column=0, padx=6, pady=6, sticky="nsew")
        ttk.Label(tf, text="Lat").grid(row=0,column=0); ttk.Label(tf, textvariable=self.tgt_lat).grid(row=0,column=1)
        ttk.Label(tf, text="Lon").grid(row=1,column=0); ttk.Label(tf, textvariable=self.tgt_lon).grid(row=1,column=1)
        ttk.Label(tf, text="Alt").grid(row=2,column=0); ttk.Label(tf, textvariable=self.tgt_alt).grid(row=2,column=1)
        ttk.Label(tf, text="Az").grid(row=3,column=0); ttk.Label(tf, textvariable=self.az_var).grid(row=3,column=1)
        ttk.Label(tf, text="El").grid(row=4,column=0); ttk.Label(tf, textvariable=self.el_var).grid(row=4,column=1)

        # Control frame (inputs)
        cf = ttk.LabelFrame(self.root, text="Controls")
        cf.grid(row=0, column=1, rowspan=2, padx=6, pady=6, sticky="nsew")

        # Mode radio
        ttk.Label(cf, text="Mode").grid(row=0,column=0)
        self.mode_gps_rb = ttk.Radiobutton(cf, text="GPS", variable=self.mode_var, value="GPS")
        self.mode_man_rb = ttk.Radiobutton(cf, text="MANUAL", variable=self.mode_var, value="MANUAL")
        self.mode_gps_rb.grid(row=0,column=1); self.mode_man_rb.grid(row=0,column=2)

        # Az/El entry (manual)
        ttk.Label(cf, text="Az").grid(row=1,column=0); self.az_entry = ttk.Entry(cf); self.az_entry.grid(row=1,column=1)
        ttk.Label(cf, text="El").grid(row=2,column=0); self.el_entry = ttk.Entry(cf); self.el_entry.grid(row=2,column=1)
        ttk.Button(cf, text="Apply Manual Az/El", command=self.apply_manual_azel).grid(row=3,column=0, columnspan=2, pady=6)

        # Lat/Lon/Alt entry (target)
        ttk.Label(cf, text="Tgt Lat").grid(row=4,column=0); self.lat_entry = ttk.Entry(cf); self.lat_entry.grid(row=4,column=1)
        ttk.Label(cf, text="Tgt Lon").grid(row=5,column=0); self.lon_entry = ttk.Entry(cf); self.lon_entry.grid(row=5,column=1)
        ttk.Label(cf, text="Tgt Alt").grid(row=6,column=0); self.alt_entry = ttk.Entry(cf); self.alt_entry.grid(row=6,column=1)
        ttk.Button(cf, text="Set Target (GPS)", command=self.apply_target).grid(row=7,column=0, columnspan=2, pady=6)

        # Get status
        ttk.Button(cf, text="Get Status", command=self.request_status).grid(row=8,column=0, columnspan=2, pady=6)

        # log
        lf = ttk.LabelFrame(self.root, text="Ack / Log")
        lf.grid(row=2, column=0, columnspan=2, padx=6, pady=6, sticky="nsew")
        self.log = tk.Text(lf, height=10, width=80); self.log.pack(fill="both", expand=True)

    def _connect_loop(self):
        while not self.stop_event.is_set():
            if not self.connected:
                try:
                    self.sock = socket.create_connection((ESP32_HOST, ESP32_PORT), timeout=5)
                    self.sock.settimeout(1.0)
                    self.connected = True
                    self.log_msg("Connected to tracker")
                    self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
                    self.recv_thread.start()
                except Exception as e:
                    self.log_msg("Connect failed: %s; retrying..." % e)
                    time.sleep(2.0)
            else:
                time.sleep(1.0)

    def _recv_loop(self):
        buffer = b""
        try:
            while self.connected and not self.stop_event.is_set():
                try:
                    data = self.sock.recv(4096)
                    if not data:
                        self.log_msg("Socket closed by server")
                        break
                    buffer += data
                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        if not line:
                            continue
                        try:
                            text = line.decode("utf-8", errors="ignore").strip()
                            obj = json.loads(text)
                        except Exception as e:
                            self.log_msg("Malformed JSON: %s" % e)
                            continue
                        # Distinguish ack vs status
                        if "cmd" in obj or "status" in obj:
                            self.log_msg("ACK: %s" % json.dumps(obj))
                            # if reply to SET_TARGET contains az/el in msg, parse it
                            if "cmd" in obj and obj.get("status") == "OK" and isinstance(obj.get("msg"), str):
                                # look for "az=... el=..."
                                msg = obj.get("msg")
                                if "az=" in msg and "el=" in msg:
                                    try:
                                        parts = msg.split()
                                        az = float(parts[1].split("=")[1])
                                        el = float(parts[2].split("=")[1])
                                        self.az_var.set("%.2f" % az)
                                        self.el_var.set("%.2f" % el)
                                    except:
                                        pass
                        elif "my_fix" in obj or "target_fix" in obj:
                            self._update_status(obj)
                        else:
                            self.log_msg("MSG: %s" % json.dumps(obj))
                except socket.timeout:
                    continue
                except Exception as e:
                    self.log_msg("Recv error: %s" % e)
                    break
        finally:
            self.connected = False
            try:
                self.sock.close()
            except:
                pass
            self.log_msg("Disconnected, will reconnect")

    def _update_status(self, data):
        myf = data.get("my_fix", {})
        self.my_lat.set(str(myf.get("lat","")))
        self.my_lon.set(str(myf.get("lon","")))
        self.my_alt.set(str(myf.get("alt","")))

        tgt = data.get("target_fix", {})
        if tgt.get("valid", False):
            self.tgt_lat.set(str(tgt.get("lat","")))
            self.tgt_lon.set(str(tgt.get("lon","")))
            self.tgt_alt.set(str(tgt.get("alt","")))
        else:
            self.tgt_lat.set("")
            self.tgt_lon.set("")
            self.tgt_alt.set("")

        azel = data.get("azel", {})
        if azel:
            self.az_var.set("%.2f" % azel.get("az", 0.0))
            self.el_var.set("%.2f" % azel.get("el", 0.0))

        mode = data.get("mode", "")
        if mode:
            self.mode_var.set(mode)

        self.log_msg("[{}] Status updated".format(time.strftime("%H:%M:%S")))

    def apply_manual_azel(self):
        if not self.connected:
            messagebox.showerror("Connection", "Not connected")
            return
        try:
            az = float(self.az_entry.get())
            el = float(self.el_entry.get())
        except:
            messagebox.showerror("Input", "Invalid az/el")
            return
        # send SET_MODE MANUAL then SET_AZ_EL
        self._send_cmd({"command":"SET_MODE", "mode":"MANUAL"})
        time.sleep(0.05)
        self._send_cmd({"command":"SET_AZ_EL", "az":az, "el":el})
        # GUI clears target display because manual takes precedence
        self.tgt_lat.set(""); self.tgt_lon.set(""); self.tgt_alt.set("")

    def apply_target(self):
        if not self.connected:
            messagebox.showerror("Connection", "Not connected")
            return
        try:
            lat = float(self.lat_entry.get())
            lon = float(self.lon_entry.get())
            alt = float(self.alt_entry.get()) if self.alt_entry.get() else 0.0
        except:
            messagebox.showerror("Input", "Invalid lat/lon/alt")
            return
        # set mode GPS and then set target
        self._send_cmd({"command":"SET_MODE", "mode":"GPS"})
        time.sleep(0.05)
        self._send_cmd({"command":"SET_TARGET", "lat":lat, "lon":lon, "alt":alt})

    def request_status(self):
        if not self.connected:
            messagebox.showerror("Connection", "Not connected")
            return
        self._send_cmd({"command":"GET_STATUS"})

    def _send_cmd(self, obj):
        try:
            s = json.dumps(obj) + "\n"
            self.sock.sendall(s.encode("utf-8"))
        except Exception as e:
            self.log_msg("Send failed: %s" % e)

    def log_msg(self, s):
        self.log.insert("end", s + "\n")
        self.log.see("end")

    def stop(self):
        self.stop_event.set()
        try:
            if self.sock:
                self.sock.close()
        except:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    g = TrackerGUI(root)
    try:
        root.mainloop()
    finally:
        g.stop()
