import time
import random
import tkinter as tk
import threading
import os
from tkinter import messagebox, scrolledtext

class ReactorSimulation:
    def __init__(self, root, mode="Easy"):
        self.root = root
        self.root.title("Chernobyl Unit 4 - Advanced Control Room")
        self.root.geometry("1050x750")
        self.root.configure(bg="#1a1a1a")

        self.main_canvas = tk.Canvas(self.root, bg="#1a1a1a", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.root, orient="vertical", command=self.main_canvas.yview)
        self.scrollable_frame = tk.Frame(self.main_canvas, bg="#1a1a1a")

        self.scrollable_frame.bind("<Configure>", lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all")))
        self.main_canvas.create_window((525, 0), window=self.scrollable_frame, anchor="n")
        self.main_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.main_canvas.pack(side="left", fill="both", expand=True)

        def _on_mousewheel(event):
            self.main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.root.bind_all("<MouseWheel>", _on_mousewheel)

        self.temperature = 300
        self.power = 400
        self.rods = 180
        self.water_supply = 10000 
        self.radiation = 0
        self.backup_water_supply = 20000
        self.pressure = 1.0 
        self.difficulty = mode
        self.meltdown_limit = {"Guided": 30, "Easy": 20, "Medium": 15, "Hard": 10, "VeryHard": 7, "Impossible": 3, "Endless": 999999}.get(mode, 20)
        self.danger_timer = 0
        self.total_time = 0
        self.task_stage = 1
        self.tick_counter = 0
        self.particles = []
        self.history = [self.temperature] * 20
        self.flash_state = False
        self.setup_tasks()

        tk.Label(self.scrollable_frame, text="☢️ RBMK-1000 CORE MONITOR ☢️", font=("Helvetica", 18, "bold"), bg="#1a1a1a", fg="#00ff00").pack(pady=10)
        
        self.status_lbl = tk.Label(self.scrollable_frame, text="SYSTEM READY", font=("Helvetica", 14, "bold"), bg="#1a1a1a", fg="green")
        self.status_lbl.pack()

        top_layout = tk.Frame(self.scrollable_frame, bg="#1a1a1a")
        top_layout.pack(fill="x", pady=5)

        self.task_frame = tk.LabelFrame(top_layout, text=" MISSION OBJECTIVE ", font=("Helvetica", 10, "bold"), bg="#1a1a1a", fg="#00ff00", labelanchor="n")
        self.task_frame.pack(side="left", padx=20, fill="y")
        
        self.task_text = tk.StringVar()
        tk.Label(self.task_frame, textvariable=self.task_text, font=("Courier", 11, "bold"), bg="#000", fg="#ffcc00", width=35, height=5, wraplength=250).pack(padx=10, pady=10)

        tk.Label(self.task_frame, text="--- QUICK GUIDE ---", font=("Helvetica", 10, "bold"), bg="#1a1a1a", fg="#00ff00").pack(pady=(10, 0))
        guide_text = (
            "• RODS: Pull = ↑Power/Heat\n"
            "• RODS: Insert = ↓Power/Heat\n"
            "• COOLANT: Drops Temp & Pres\n"
            "• VENT: Drops Pressure fast\n"
            "• AZ-5: Emergency Shutdown"
        )
        tk.Label(self.task_frame, text=guide_text, font=("Courier", 9), bg="#000", fg="#aaaaaa", justify="left", padx=10, pady=10).pack(fill="x")

        monitor_frame = tk.Frame(top_layout, bg="#1a1a1a")
        monitor_frame.pack(side="left", expand=True)

        self.canvas = tk.Canvas(monitor_frame, width=350, height=150, bg="#050505", highlightthickness=1)
        self.canvas.grid(row=0, column=0, padx=10)

        self.core_canvas = tk.Canvas(monitor_frame, width=200, height=150, bg="#050505", highlightthickness=1)
        self.core_canvas.grid(row=0, column=1, padx=10)
        self.init_particles()

        self.rod_canvas = tk.Canvas(monitor_frame, width=40, height=150, bg="#050505", highlightthickness=1)
        self.rod_canvas.grid(row=0, column=2, padx=10)

        self.data_text = tk.StringVar()
        tk.Label(self.scrollable_frame, textvariable=self.data_text, font=("Courier", 12), justify="center", bg="#000", fg="#00ff00", padx=10, pady=5).pack(pady=5)

        control_container = tk.Frame(self.scrollable_frame, bg="#1a1a1a")
        control_container.pack(pady=10)

        btn_frame = tk.Frame(control_container, bg="#1a1a1a")
        btn_frame.pack(side="left", padx=20)

        tk.Button(btn_frame, text="PULL RODS (-10)", bg="#ff4444", fg="white", width=15, command=self.pull_rods).grid(row=0, column=0, pady=5)
        tk.Button(btn_frame, text="INSERT RODS (+10)", bg="#4444ff", fg="white", width=15, command=self.insert_rods).grid(row=0, column=1, pady=5)

        primary_cooling_frame = tk.Frame(btn_frame, bg="#1a1a1a")
        primary_cooling_frame.grid(row=1, column=0, pady=5, sticky="ew", padx=5)
        tk.Label(primary_cooling_frame, text="Amt(L):", bg="#1a1a1a", fg="white", font=("Courier", 10)).pack(side="left")
        self.cooling_amount_entry = tk.Entry(primary_cooling_frame, width=8, bg="#333", fg="white", insertbackground="white", font=("Courier", 10))
        self.cooling_amount_entry.insert(0, "500")
        self.cooling_amount_entry.pack(side="left", padx=5)
        tk.Button(primary_cooling_frame, text="PUMP COOLANT", bg="#00ced1", fg="black", command=self.add_cooling, width=15).pack(side="left", expand=True)

        backup_cooling_frame = tk.Frame(btn_frame, bg="#1a1a1a")
        backup_cooling_frame.grid(row=1, column=1, pady=5, sticky="ew", padx=5)
        tk.Label(backup_cooling_frame, text="Amt(L):", bg="#1a1a1a", fg="white", font=("Courier", 10)).pack(side="left")
        self.backup_cooling_amount_entry = tk.Entry(backup_cooling_frame, width=8, bg="#333", fg="white", insertbackground="white", font=("Courier", 10))
        self.backup_cooling_amount_entry.insert(0, "1000")
        self.backup_cooling_amount_entry.pack(side="left", padx=5)
        tk.Button(backup_cooling_frame, text="BACKUP RESERVES", bg="#20b2aa", fg="white", command=self.add_backup_cooling, width=15).pack(side="left", expand=True)

        vent_frame = tk.Frame(btn_frame, bg="#1a1a1a")
        vent_frame.grid(row=2, column=0, columnspan=2, pady=5, sticky="ew")
        tk.Label(vent_frame, text="Amt(MPa):", bg="#1a1a1a", fg="white", font=("Courier", 10)).pack(side="left", padx=(40, 5))
        self.vent_amount_entry = tk.Entry(vent_frame, width=8, bg="#333", fg="white", insertbackground="white", font=("Courier", 10))
        self.vent_amount_entry.insert(0, "5.0")
        self.vent_amount_entry.pack(side="left", padx=5)
        self.vent_btn = tk.Button(vent_frame, text="VENT STEAM", bg="#f0e68c", fg="black", command=self.vent_pressure, width=20)
        self.vent_btn.pack(side="left")

        emergency_frame = tk.Frame(control_container, bg="#1a1a1a")
        emergency_frame.pack(side="left", padx=20)

        tk.Button(emergency_frame, text="AZ-5\n(SCRAM)", bg="red", fg="white", font=("Arial", 14, "bold"), height=3, width=12, command=self.az5_trigger).pack()
        tk.Button(emergency_frame, text="QUIT TO MENU", bg="#444", fg="white", font=("Arial", 10, "bold"), command=self.back_to_menu).pack(pady=10)

        tk.Label(self.scrollable_frame, text="OPERATIONAL LOG", font=("Helvetica", 10, "bold"), bg="#1a1a1a", fg="white").pack()
        self.log_area = scrolledtext.ScrolledText(self.scrollable_frame, width=90, height=4, bg="black", fg="#00ff00", font=("Courier", 10))
        self.log_area.pack(pady=5)

        self.log_message("System Online. Awaiting operator input.")
        self.reactor_tick()
        self.animate_core()

    def setup_tasks(self):
        self.tasks = {}
        if self.difficulty == "Guided":
            targets = [("800MW Power", "power", 800), ("1500°C Temp", "temp", 1500), ("Pressure < 10MPa", "pres", 10), ("Shutdown < 400°C", "temp_low", 400)]
        elif self.difficulty == "Easy":
            targets = [("600MW", "power", 600), ("1000°C", "temp", 1000), ("1200MW", "power", 1200), ("1500°C", "temp", 1500), ("2000MW", "power", 2000), 
                       ("Pres < 15MPa", "pres", 15), ("Rods > 100", "rods", 100), ("Temp < 1000°C", "temp_low", 1000), ("Pres < 8MPa", "pres", 8), ("Shutdown < 400°C", "temp_low", 400)]
        elif self.difficulty == "Medium":
            targets = [(f"Step {i}: {400 + i*150}MW", "power", 400 + i*150) for i in range(1, 10)] + \
                      [(f"Cooling {i}: {2000 - i*300}°C", "temp_low", 2000 - i*300) for i in range(1, 6)] + [("Final Shutdown", "temp_low", 400)]
        elif self.difficulty == "Hard":
            targets = [(f"Stage {i}: {400 + i*120}MW", "power", 400 + i*120) for i in range(1, 12)] + \
                      [(f"Pres Control {i}", "pres", 20 - i) for i in range(1, 5)] + \
                      [(f"Final Cooling {i}", "temp_low", 1000 - i*150) for i in range(1, 4)] + [("Cold Shutdown", "temp_low", 400)]
        else:
            targets = []
        
        for i, (name, type, val) in enumerate(targets):
            self.tasks[i+1] = {"desc": f"Task {i+1}: {name}", "type": type, "val": val}

    def get_current_task_desc(self):
        if self.task_stage > len(self.tasks):
            return "ALL MISSIONS COMPLETE"
        return self.tasks[self.task_stage]["desc"]

    def log_message(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.log_area.see(tk.END)

    def update_data_label(self):
        task_desc = self.get_current_task_desc()
        mode_info = f"MODE: {self.difficulty.upper()}"
        if self.difficulty == "Endless":
            mode_info += f" | SURVIVAL TIME: {self.total_time}s"
        elif self.danger_timer > 0:
            mode_info += f" | !!! MELTDOWN IN: {self.meltdown_limit - self.danger_timer}s !!!"

        self.task_text.set(task_desc if self.difficulty != 'Endless' else "SURVIVE AT ALL COSTS")

        p_tank_idx = 4 - ((self.water_supply - 1) // 2500) if self.water_supply > 0 else 4
        p_status = f"Tank {p_tank_idx}/4" if self.water_supply > 0 else "EMPTY"
        b_tank_idx = 2 - ((self.backup_water_supply - 1) // 10000) if self.backup_water_supply > 0 else 2
        b_status = f"Tank {b_tank_idx}/2" if self.backup_water_supply > 0 else "EMPTY"

        self.data_text.set(f"{mode_info}\n"
                          f"[TEMP: {self.temperature}°C] [PWR: {self.power}MW] [PRES: {self.pressure:.2f}MPa]\n"
                          f"[RODS: {self.rods}/211] [RAD: {self.radiation}mSv]\n"
                          f"WATER: {self.water_supply}L ({p_status}) | BACKUP: {self.backup_water_supply}L ({b_status})")
        
        vent_color = "orange" if self.pressure > 15.0 else "#f0e68c"
        self.vent_btn.config(bg=vent_color)

        if self.temperature > 2500 or self.pressure > 18.0 or self.radiation > 500:
            self.flash_warning()
        else:
            self.status_lbl.config(text="SYSTEM STABLE", fg="green")

    def flash_warning(self):
        self.flash_state = not self.flash_state
        color = "red" if self.flash_state else "#1a1a1a"
        msg = "!!! CRITICAL ALARM !!!"
        self.status_lbl.config(text=msg, fg=color)

    def draw_chart(self):
        self.canvas.delete("all")
        for y in range(0, 151, 30):
            self.canvas.create_line(0, y, 350, y, fill="#222")
        points = []
        max_points = 20
        recent_history = self.history[-max_points:]
        for i, val in enumerate(recent_history):
            x = (i / (max_points - 1)) * 350 if len(recent_history) > 1 else 0
            y = 150 - (val / 3200 * 150)
            points.append(x); points.append(y)
        if len(points) >= 4:
            self.canvas.create_line(points, fill="#00ff00", width=2)

    def draw_rods(self):
        self.rod_canvas.delete("all")
        # Visualizing 211 individual control rods in a grid
        cols = 8
        cell_w, cell_h = 3, 4
        gap = 1
        for i in range(211):
            col = i % cols
            row = i // cols
            x1 = 5 + col * (cell_w + gap)
            y1 = 145 - row * (cell_h + gap)
            color = "#00dfff" if i < self.rods else "#222222"
            self.rod_canvas.create_rectangle(x1, y1, x1 + cell_w, y1 - cell_h, fill=color, outline="")

    def init_particles(self):
        for _ in range(25):
            p_id = self.core_canvas.create_oval(0, 0, 4, 4, fill="cyan", outline="")
            self.particles.append({
                'id': p_id, 
                'x': random.randint(0, 200), 
                'y': random.randint(0, 150), 
                'dx': random.uniform(-1.5, 1.5), 
                'dy': random.uniform(-1, 1)
            })
        self.temp_display_id = self.core_canvas.create_text(100, 135, text="", fill="white", font=("Courier", 11, "bold"))

    def animate_core(self):
        speed = 1 + (self.power / 1000)
        color = "cyan" if self.temperature < 1500 else "orange" if self.temperature < 2500 else "red"
        for p in self.particles:
            p['x'] += p['dx'] * speed
            p['y'] += p['dy'] * speed
            if p['x'] < 0: p['x'] = 200
            if p['x'] > 200: p['x'] = 0
            if p['y'] < 0: p['y'] = 150
            if p['y'] > 150: p['y'] = 0
            
            self.core_canvas.coords(p['id'], p['x'], p['y'], p['x']+4, p['y']+4)
            self.core_canvas.itemconfig(p['id'], fill=color)
        
        self.core_canvas.itemconfig(self.temp_display_id, text=f"{self.temperature}°C")
        self.root.after(50, self.animate_core)

    def check_tasks(self):
        if self.difficulty == "Endless" or self.task_stage > len(self.tasks):
            return
        
        task = self.tasks[self.task_stage]
        done = False
        if task["type"] == "power" and self.power >= task["val"]: done = True
        elif task["type"] == "temp" and self.temperature >= task["val"]: done = True
        elif task["type"] == "temp_low" and self.temperature <= task["val"]: done = True
        elif task["type"] == "pres" and self.pressure <= task["val"]: done = True
        elif task["type"] == "rods" and self.rods >= task["val"]: done = True

        if done:
            if self.task_stage == len(self.tasks):
                self.log_message("STATION GOAL ACHIEVED: FINAL TASK COMPLETE")
                self.show_victory_screen()
                self.task_stage += 1
            else:
                next_desc = self.tasks[self.task_stage + 1]["desc"]
                self.next_task(f"{task['desc']} Complete! Next: {next_desc}")

    def show_victory_screen(self):
        win_frame = tk.Frame(self.scrollable_frame, bg="#00ff00", pady=20)
        win_frame.pack(pady=20, fill="x")
        tk.Label(win_frame, text="🏆 MISSION SUCCESS 🏆", font=("Helvetica", 18, "bold"), bg="#00ff00", fg="black").pack()
        tk.Label(win_frame, text="You have successfully stabilized Reactor 4.", font=("Helvetica", 12), bg="#00ff00", fg="black").pack()
        tk.Button(win_frame, text="RETURN TO MAIN MENU", command=self.back_to_menu, bg="black", fg="#00ff00", font=("Helvetica", 12, "bold")).pack(pady=10)
        messagebox.showinfo("VICTORY", "Hero of the USSR! Reactor 4 is safe.")

    def back_to_menu(self):
        self.root.destroy()
        start_launcher()

    def next_task(self, msg):
        self.task_stage += 1
        self.log_message(f"STATION GOAL ACHIEVED: {msg}")
        messagebox.showinfo("GOAL REACHED", msg)

    def pull_rods(self):
        if self.rods > 0:
            self.rods = max(0, self.rods - 10)
            self.log_message("Control Rods extracted. Reactivity increasing.")
            self.update_ui()

    def insert_rods(self):
        if self.rods < 211:
            self.rods = min(211, self.rods + 10)
            self.log_message("Control Rods inserted. Power dropping.")
            self.update_ui()

    def add_cooling(self):
        try:
            amount = int(self.cooling_amount_entry.get())
            if amount <= 0:
                self.log_message("WARNING: Enter a positive amount for primary cooling.")
                return
        except ValueError:
            self.log_message("ERROR: Invalid amount. Enter a number.")
            return

        if self.water_supply >= amount:
            old_tank = 4 - ((self.water_supply - 1) // 2500) if self.water_supply > 0 else 4
            self.water_supply -= amount
            new_tank = 4 - ((self.water_supply - 1) // 2500) if self.water_supply > 0 else 4
            
            if new_tank > old_tank:
                self.log_message(f"--- Tank {old_tank} Depleted. Switching to Tank {new_tank} ---")

            self.temperature = max(100, self.temperature - (amount * 0.6))
            self.pressure = max(0.1, self.pressure - (amount * 0.002))
            self.log_message(f"Primary pumps active: {amount}L coolant injected.")
            self.update_ui()
        else:
            self.log_message(f"CRITICAL: Primary supply too low! Tank 4 EMPTY.")

    def add_backup_cooling(self):
        try:
            amount = int(self.backup_cooling_amount_entry.get())
            if amount <= 0:
                self.log_message("WARNING: Enter a positive amount for backup cooling.")
                return
        except ValueError:
            self.log_message("ERROR: Invalid amount. Enter a number.")
            return

        if self.backup_water_supply >= amount:
            old_tank = 2 - ((self.backup_water_supply - 1) // 10000) if self.backup_water_supply > 0 else 2
            self.backup_water_supply -= amount
            new_tank = 2 - ((self.backup_water_supply - 1) // 10000) if self.backup_water_supply > 0 else 2

            if new_tank > old_tank:
                self.log_message(f"--- Backup Tank {old_tank} Depleted. Switching to Tank {new_tank} ---")

            self.temperature = max(100, self.temperature - (amount * 0.6))
            self.log_message(f"EMERGENCY: Backup reserves active! {amount}L injected.")
            self.update_ui()
        else:
            self.log_message(f"CRITICAL: Backup reserves empty! Tank 2 EMPTY.")

    def vent_pressure(self):
        try:
            amount = float(self.vent_amount_entry.get())
            if amount <= 0:
                self.log_message("WARNING: Enter a positive pressure value to vent.")
                return
        except ValueError:
            self.log_message("ERROR: Invalid pressure amount. Enter a number.")
            return

        if self.pressure > 1.0:
            old_pres = self.pressure
            self.pressure = max(1.0, self.pressure - amount)
            actual_vented = old_pres - self.pressure
            self.temperature -= int(actual_vented * 10)
            self.log_message(f"Steam valves opened. {actual_vented:.2f} MPa vented.")
            self.update_ui()

    def az5_trigger(self):
        self.rods = 211
        self.power = 0
        self.temperature = max(200, self.temperature - 800)
        self.log_message("!!! SCRAM INITIATED !!! AZ-5 BUTTON PRESSED.")
        messagebox.showwarning("SCRAM", "AZ-5 INITIATED. FULL ROD INSERTION.")
        self.update_ui()

    def check_meltdown(self):
        is_meltdown = False
        reason = ""
        
        if self.temperature > 3200:
            is_meltdown = True
            reason = "CORE MELTDOWN"
        elif self.pressure > 25.0:
            is_meltdown = True
            reason = "PRESSURE EXPLOSION"
        elif self.radiation > 2000:
            is_meltdown = True
            reason = "LETHAL RADIATION"
        elif self.difficulty != "Endless" and self.danger_timer >= self.meltdown_limit: # Countdown expired
            is_meltdown = True
            # Determine a more specific reason for critical limit exceeded
            if self.pressure > 22.0:
                reason = f"PRESSURE-INDUCED MELTDOWN ({self.meltdown_limit}s countdown)"
            elif self.temperature > 2800:
                reason = f"CORE OVERHEAT MELTDOWN ({self.meltdown_limit}s countdown)"
            elif self.radiation > 1000:
                reason = f"RADIATION SPIKE MELTDOWN ({self.meltdown_limit}s countdown)"
            elif self.temperature > 2500 or self.pressure > 18.0 or self.radiation > 500:
                reason = f"CRITICAL CONDITIONS MELTDOWN ({self.meltdown_limit}s countdown)"
            else: # Fallback, should not happen if danger_timer > 0
                reason = f"CRITICAL LIMIT EXCEEDED ({self.meltdown_limit}s countdown)"

        if is_meltdown:
            score_msg = f"\n\nFINAL SCORE (Survival Time): {self.total_time} seconds" if self.difficulty == "Endless" else ""
            self.log_message(f"FATAL ERROR: {reason}")
            messagebox.showerror("TERMINATED", f"CRITICAL FAILURE: {reason}{score_msg}")
            self.root.destroy()
            return True
        return False

    def update_ui(self):
        self.check_tasks()
        self.update_data_label()
        self.draw_chart()
        self.draw_rods()

    def reactor_tick(self):
        self.tick_counter += 1
        self.total_time += 1
        
        target_power = max(0, (1 - (self.rods / 211)) * 3200)
        self.power += int((target_power - self.power) * 0.1)
        
        multiplier = {"Guided": 0.5, "Easy": 1.0, "Medium": 1.5, "Hard": 2.0, "VeryHard": 2.5, "Impossible": 3.5, "Endless": 1.0}.get(self.difficulty, 1.0)
        
        if self.rods < 211:
            self.temperature += int(30 * multiplier)
        else:
            self.temperature += int(20 * multiplier)
            
        self.pressure += (self.temperature / 1800)
        
        is_critical = self.temperature > 2500 or self.pressure > 18.0 or self.radiation > 500
        if is_critical:
            if self.difficulty != "Endless":
                self.danger_timer += 1
        else:
            self.danger_timer = 0

        if self.temperature > 1500:
            self.radiation += int((self.temperature - 1500) / 100)

        self.history.append(self.temperature)
        if len(self.history) > 50: self.history.pop(0)
        
        self.update_ui()
        if not self.check_meltdown():
            self.root.after(1000, self.reactor_tick)

def start_launcher():
    launcher = tk.Tk()
    launcher.title("RBMK-1000 Startup sequence")
    launcher.geometry("450x700")
    launcher.configure(bg="#1a1a1a")

    tk.Label(launcher, text="☢️ CONTROL MODE ☢️", font=("Courier", 20, "bold"), bg="#1a1a1a", fg="#00ff00").pack(pady=20)
    
    mode_var = tk.StringVar(value="Easy")
    
    # Frame to hold radio buttons for better organization
    radio_options_frame = tk.Frame(launcher, bg="#1a1a1a")
    radio_options_frame.pack(pady=10, padx=20, fill="x")

    modes = [("GUIDED (30s Countdown)", "Guided"),
             ("EASY (20s Countdown)", "Easy"), 
             ("MEDIUM (15s Countdown)", "Medium"), 
             ("HARD (10s Countdown)", "Hard"),
             ("VERY HARD (7s Countdown)", "VeryHard"), # New mode
             ("IMPOSSIBLE (3s Countdown)", "Impossible"), # New mode
             ("ENDLESS (Survival Score)", "Endless")]
    
    # Adding more descriptive text for each mode
    mode_descriptions = {
        "Guided": "30s countdown, tutorial tasks to learn the ropes.",
        "Easy": "20s countdown, simple tasks, forgiving conditions.",
        "Medium": "15s countdown, moderate tasks, balanced challenge.",
        "Hard": "10s countdown, challenging tasks, tighter margins.",
        "VeryHard": "7s countdown, expert tasks, very little room for error.",
        "Impossible": "3s countdown, extreme challenge, for true masters.",
        "Endless": "No countdown, survive as long as possible for score."
    }

    for text, val in modes:
        full_text = f"{text} - {mode_descriptions.get(val, '')}"
        tk.Radiobutton(radio_options_frame, text=full_text, variable=mode_var, value=val, bg="#1a1a1a", fg="#00ff00", # Changed fg to green
                       selectcolor="#005500", font=("Courier", 10), # Slightly smaller font, darker green select
                       activebackground="#1a1a1a", indicatoron=0, # Flat button style
                       width=45, anchor="w", padx=10, pady=5).pack(fill="x", pady=2) # Fill x and add padding

    # Add hover effects for main buttons
    def create_hover_effect(button, default_bg, hover_bg):
        def on_enter(e): button.config(bg=hover_bg)
        def on_leave(e): button.config(bg=default_bg)
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)

    def show_tutorial():
        tutorial_text = (
            "☢️ RBMK-1000 OPERATOR MANUAL ☢️\n\n"
            "1. CONTROL RODS: Pulling rods increases power and heat. Inserting them drops it.\n"
            "2. COOLING: Use 'PUMP COOLANT' to use water from the 4 primary tanks.\n"
            "3. BACKUP: If primary tanks are empty, use 'BACKUP RESERVES'.\n"
            "4. PRESSURE: If pressure is high, click 'VENT STEAM' to avoid an explosion.\n"
            "5. SCRAM (AZ-5): This is the emergency button. It shuts everything down.\n"
            "6. MISSION: Follow the tasks on the left side of the screen to win.\n\n"
            "⚠️ DANGER: Keep Temp below 3200°C and Pressure below 25.0 MPa!"
        )
        tw = tk.Toplevel(launcher)
        tw.title("OPERATOR MANUAL")
        tw.geometry("500x550")
        tw.configure(bg="#1a1a1a")
        tk.Label(tw, text=tutorial_text, font=("Courier", 10), bg="#1a1a1a", fg="white", justify="left", padx=20, pady=20).pack()
        tk.Button(tw, text="PLAY WITH GUIDE", command=lambda: [launch("Guided"), tw.destroy()], bg="#00ced1", fg="black", font=("Courier", 12, "bold"), width=20).pack(pady=10)
        tk.Button(tw, text="CLOSE", command=tw.destroy, bg="#444", fg="white", font=("Courier", 10)).pack(pady=5)

    def launch(specific_mode=None):
        m = specific_mode if specific_mode else mode_var.get()
        launcher.destroy()
        root = tk.Tk()
        ReactorSimulation(root, m)
        root.mainloop()

    tutorial_btn = tk.Button(launcher, text="HOW TO PLAY", command=show_tutorial,
                             bg="#ffcc00", fg="black", font=("Courier", 12, "bold"), width=25)
    tutorial_btn.pack(pady=10)
    create_hover_effect(tutorial_btn, "#ffcc00", "#ffff00")

    engage_btn = tk.Button(launcher, text="ENGAGE SYSTEMS", command=launch, bg="#00ff00", fg="black", font=("Courier", 14, "bold"), width=25)
    engage_btn.pack(pady=20)
    create_hover_effect(engage_btn, "#00ff00", "#33ff33")

    quit_btn = tk.Button(launcher, text="QUIT GAME", command=launcher.destroy, bg="#444", fg="white", font=("Courier", 12, "bold"), width=25)
    quit_btn.pack(pady=5)
    create_hover_effect(quit_btn, "#444", "#666")
    launcher.mainloop()

if __name__ == "__main__":
    start_launcher()
    engage_btn = tk.Button(launcher, text="ENGAGE SYSTEMS", command=launch, bg="#00ff00", fg="black", font=("Courier", 14, "bold"), width=25)
    engage_btn.pack(pady=20)
    create_hover_effect(engage_btn, "#00ff00", "#33ff33")

    quit_btn = tk.Button(launcher, text="QUIT GAME", command=launcher.destroy, bg="#444", fg="white", font=("Courier", 12, "bold"), width=25)
    quit_btn.pack(pady=5)
    create_hover_effect(quit_btn, "#444", "#666")
    launcher.mainloop()

if __name__ == "__main__":
    start_launcher()
 