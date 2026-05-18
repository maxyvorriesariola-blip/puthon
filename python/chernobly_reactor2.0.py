import random
import tkinter as tk
import json
import os
import time
from tkinter import messagebox, scrolledtext

SAVE_FILE = "reactor_saves.json"

def load_all_accounts():
    """
    Loads all operator profiles from the local JSON storage file.
    Handles potential file corruption or missing files gracefully by returning an empty dictionary.
    """
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[System Error] Failed to read account database: {e}")
            pass
    return {}

def save_all_accounts(data):
    """
    Persists the entire operator account dictionary into the local JSON save file.
    Includes comprehensive exception handling to prevent game state loss.
    """
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"[System Error] Error saving backup database data: {e}")

def load_account_data(username):
    """
    Fetches account statistics for a specific operator username.
    If the operator does not exist, supplies default starter stats.
    """
    accounts = load_all_accounts()
    if username in accounts:
        return accounts[username]
    return {
        "credits": 1000, 
        "max_pressure": 25.0, 
        "turbine_level": 1, 
        "mask_quality": 1,
        "shielding_level": 1,
        "email": "None"
    }

def save_account_data(username, credits, max_pressure, turbine_level, mask_quality=1, shielding_level=1, email="None"):
    """
    Updates or inserts a specific operator's profile details into the central save file.
    Preserves existing registration details such as backup email addresses.
    """
    accounts = load_all_accounts()
    if username not in accounts:
        accounts[username] = {}
    
    current_email = accounts[username].get("email", "None")
    if email != "None":
        current_email = email

    accounts[username].update({
        "credits": credits,
        "max_pressure": max_pressure,
        "turbine_level": turbine_level,
        "mask_quality": mask_quality,
        "shielding_level": shielding_level,
        "email": current_email
    })
    save_all_accounts(accounts)


class ReactorSimulation:
    def __init__(self, root, mode="Easy", hw_mode="Laptop", username="Guest"):
        """
        Initializes the comprehensive RBMK-1000 Core Monitor simulation interface.
        Configures internal state variables, layout metrics, canvas environments, 
        and launches physical clock threads.
        """
        self.root = root
        self.username = username
        self.difficulty = mode
        self.hardware_mode = hw_mode
        self.root.title(f"Chernobyl Nuclear Station Unit 4 - Operator: {self.username} [ADVANCED MODE]")
        self.root.geometry("1100x920")
        self.root.configure(bg="#121212")

        # Load persisted operator data
        acc_data = load_account_data(username)
        self.credits = acc_data.get("credits", 1000)
        self.explosion_pressure_limit = acc_data.get("max_pressure", 25.0)
        self.turbine_level = acc_data.get("turbine_level", 1)
        self.mask_quality = acc_data.get("mask_quality", 1)
        self.shielding_level = acc_data.get("shielding_level", 1)
        self.user_email = acc_data.get("email", "None")

        # Layout scrolling infrastructure
        self.main_canvas = tk.Canvas(self.root, bg="#121212", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.root, orient="vertical", command=self.main_canvas.yview)
        self.scrollable_frame = tk.Frame(self.main_canvas, bg="#121212")

        self.scrollable_frame.bind(
            "<Configure>", 
            lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )
        self.canvas_window = self.main_canvas.create_window((550, 0), window=self.scrollable_frame, anchor="n")
        self.main_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.main_canvas.pack(side="left", fill="both", expand=True)
        self.main_canvas.bind('<Configure>', lambda event: self.main_canvas.itemconfig(self.canvas_window, width=event.width))

        def _on_mousewheel(event):
            self.main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.root.bind_all("<MouseWheel>", _on_mousewheel)

        # Core Physical Metrics
        self.temperature = 300.0       # Core thermal temperature (°C)
        self.power = 400.0             # Reactor thermal power output (MW)
        self.rods = 180                # Active control rods inserted (0 - 211)
        self.water_supply = 10000      # Main water coolant reservoir (Liters)
        self.backup_water_supply = 20000 # Emergency emergency backup reserves (Liters)
        self.pressure = 1.0            # Saturated steam loop pressure (MPa)
        
        # Advanced Realism Metrics
        self.iodine = 10.0             # Iodine-135 concentration percentage
        self.xenon = 0.0               # Xenon-135 neutron poisoning absorption factor
        self.void_coefficient = 0.0    # Dynamic void reactivity impact index
        self.pump_efficiency = 100.0   # Mechanical status of circulation loop pumps
        
        # Operator Health & Gas Mask System Metrics
        self.health = 100.0            # Operator biometric health status percentage
        self.radiation = 0.0           # Ambient control room radiation exposure (mSv)
        self.air_toxicity = 0.0        # Atmospheric chemical/radioactive toxic particle index
        self.mask_on = False           # Flag identifying toggled state of the breathing apparatus
        self.mask_filters = 100.0      # Active filter core remaining structural lifetime %

        # System control automation flags
        self.scram_delayed_ticks = 0
        self.scram_active = False
        self.is_active = True  
        self.flash_state = False
        
        # Scoring and tracking
        self.danger_timer = 0
        self.total_time = 0
        self.task_stage = 1
        self.tick_counter = 0
        self.particles = []
        self.history = [self.temperature] * 20

        # Game Difficulty Scaling Matrix
        self.meltdown_limit = {
            "Guided": 35, "Easy": 25, "Medium": 18, "Hard": 12, "VeryHard": 8, "Impossible": 4, "Endless": 999999
        }.get(mode, 25)
        
        # Graphics Engine Constraints
        self.particle_count = {"Phone": 8, "Laptop": 18, "PC": 34}.get(hw_mode, 18)
        self.animation_speed = {"Phone": 140, "Laptop": 90, "PC": 45}.get(hw_mode, 90)

        # Initialize core mission schedules
        self.setup_tasks()

        # Build UI Header Layout
        tk.Label(
            self.scrollable_frame, 
            text="☢️ RBMK-1000 ADVANCED OPERATOR CONTROL CONSOLE ☢️", 
            font=("Helvetica", 16, "bold"), 
            bg="#121212", 
            fg="#00ff00"
        ).pack(pady=12)
        
        self.status_lbl = tk.Label(
            self.scrollable_frame, 
            text="ALL CORES STABLE - ROOM AIR QUALITY: GOOD", 
            font=("Helvetica", 12, "bold"), 
            bg="#121212", 
            fg="green"
        )
        self.status_lbl.pack(pady=2)

        # Main Monitor Workspace Layout
        top_layout = tk.Frame(self.scrollable_frame, bg="#121212")
        top_layout.pack(pady=5)

        # Objective and Instructions Panel
        self.task_frame = tk.LabelFrame(
            top_layout, 
            text=" COMMAND HQ MISSION ORDERS ", 
            font=("Helvetica", 10, "bold"), 
            bg="#121212", 
            fg="#00ff00", 
            labelanchor="n"
        )
        self.task_frame.pack(side="left", padx=15, fill="y")
        
        self.task_text = tk.StringVar()
        tk.Label(
            self.task_frame, 
            textvariable=self.task_text, 
            font=("Courier", 11, "bold"), 
            bg="#050505", 
            fg="#ffcc00", 
            width=36, 
            height=5, 
            wraplength=260
        ).pack(padx=10, pady=8)

        tk.Label(
            self.task_frame, 
            text="--- CHERNOBYL OPERATOR MANUAL ---", 
            font=("Helvetica", 10, "bold"), 
            bg="#121212", 
            fg="#00ff00"
        ).pack(pady=(8, 0))
        
        guide_text = (
            "• PULL RODS: Increases nuclear flux, thermal power, & heat.\n"
            "• INSERT RODS: Suppresses reactivity, lowers power levels.\n"
            "• VOID EFFECT: Loss of cooling water causes massive power spike!\n"
            "• IODINE PIT: Low power yields Iodine which degrades into Xenon.\n"
            "• TOXIC AIR / RADS: High core thermal load leaks poison gases.\n"
            "• EMERGENCY MASK: Toggle gas mask to survive toxic atmosphere.\n"
            "• CRITICAL FLAW: SCRAM with rods under 30 causes short-term spike!"
        )
        tk.Label(
            self.task_frame, 
            text=guide_text, 
            font=("Courier", 8), 
            bg="#050505", 
            fg="#b0b0b0", 
            justify="left", 
            padx=10, 
            pady=8
        ).pack(fill="x", padx=5, pady=5)

        # Telemetry Display Framework
        monitor_frame = tk.Frame(top_layout, bg="#121212")
        monitor_frame.pack(side="left", padx=15)

        # Graph Canvas
        tk.Label(monitor_frame, text="CORE THERMAL HISTORY CHART", font=("Courier", 9, "bold"), bg="#121212", fg="#00ff00").grid(row=0, column=0)
        self.canvas = tk.Canvas(monitor_frame, width=350, height=160, bg="#030303", highlightthickness=1, highlightbackground="#333")
        self.canvas.grid(row=1, column=0, padx=8, pady=2)
        self.init_chart_grid()

        # Kinetic Reactor Canvas
        tk.Label(monitor_frame, text="NEUTRON THERMAL FLUX", font=("Courier", 9, "bold"), bg="#121212", fg="#00ff00").grid(row=0, column=1)
        self.core_canvas = tk.Canvas(monitor_frame, width=200, height=160, bg="#030303", highlightthickness=1, highlightbackground="#333")
        self.core_canvas.grid(row=1, column=1, padx=8, pady=2)
        self.init_particles()

        # Control Rod Stack Visualization
        tk.Label(monitor_frame, text="RODS", font=("Courier", 8, "bold"), bg="#121212", fg="#00ff00").grid(row=0, column=2)
        self.rod_canvas = tk.Canvas(monitor_frame, width=45, height=160, bg="#030303", highlightthickness=1, highlightbackground="#333")
        self.rod_canvas.grid(row=1, column=2, padx=8, pady=2)
        self.init_rods_display()

        # Biometric Operator Health Monitor Frame
        biometric_frame = tk.LabelFrame(self.scrollable_frame, text=" BIOMETRIC ENVIRONMENT DIAGNOSTICS ", font=("Helvetica", 10, "bold"), bg="#121212", fg="#ff4444", labelanchor="n")
        biometric_frame.pack(pady=8, fill="x", padx=25)

        bio_container = tk.Frame(biometric_frame, bg="#121212")
        bio_container.pack(pady=6, padx=10, fill="x")

        # Health Display Layout
        health_subframe = tk.Frame(bio_container, bg="#121212")
        health_subframe.pack(side="left", padx=15, expand=True)
        tk.Label(health_subframe, text="OPERATOR HEALTH STATUS:", font=("Courier", 10, "bold"), bg="#121212", fg="white").pack(anchor="w")
        self.health_canvas = tk.Canvas(health_subframe, width=260, height=22, bg="#222", highlightthickness=1, highlightbackground="#444")
        self.health_canvas.pack(pady=2)
        self.health_bar_id = self.health_canvas.create_rectangle(0, 0, 260, 22, fill="#22c55e", outline="")
        self.health_text_id = self.health_canvas.create_text(130, 11, text="100.0%", fill="white", font=("Courier", 10, "bold"))

        # Filter Durability Layout
        filter_subframe = tk.Frame(bio_container, bg="#121212")
        filter_subframe.pack(side="left", padx=15, expand=True)
        tk.Label(filter_subframe, text="MASK FILTER INTEGRITY:", font=("Courier", 10, "bold"), bg="#121212", fg="white").pack(anchor="w")
        self.filter_canvas = tk.Canvas(filter_subframe, width=260, height=22, bg="#222", highlightthickness=1, highlightbackground="#444")
        self.filter_canvas.pack(pady=2)
        self.filter_bar_id = self.filter_canvas.create_rectangle(0, 0, 260, 22, fill="#3b82f6", outline="")
        self.filter_text_id = self.filter_canvas.create_text(130, 11, text="100.0% (STANDBY)", fill="white", font=("Courier", 10, "bold"))

        # Dedicated Safety Equipment Action Toggle Button
        self.mask_toggle_btn = tk.Button(
            bio_container, 
            text="😷 EQUIP GAS MASK", 
            bg="#ff9900", 
            fg="black", 
            font=("Arial", 11, "bold"), 
            width=18, 
            height=2,
            command=self.toggle_gas_mask
        )
        self.mask_toggle_btn.pack(side="right", padx=10)

        # Primary Telemetry Values Text Row
        self.data_text = tk.StringVar()
        tk.Label(
            self.scrollable_frame, 
            textvariable=self.data_text, 
            font=("Courier", 11), 
            justify="center", 
            bg="#020202", 
            fg="#00ff00", 
            padx=12, 
            pady=6,
            highlightthickness=1,
            highlightbackground="#222"
        ).pack(pady=6, fill="x", padx=25)

        # Physical Actuator Interface Framework
        control_container = tk.Frame(self.scrollable_frame, bg="#121212")
        control_container.pack(pady=4)

        btn_frame = tk.Frame(control_container, bg="#121212")
        btn_frame.pack(side="left", padx=15)

        # Control rod mechanisms
        tk.Button(btn_frame, text="PULL RODS (-10)", bg="#ef4444", fg="white", font=("Courier", 10, "bold"), width=18, command=self.pull_rods).grid(row=0, column=0, pady=4, padx=4)
        tk.Button(btn_frame, text="INSERT RODS (+10)", bg="#3b82f6", fg="white", font=("Courier", 10, "bold"), width=18, command=self.insert_rods).grid(row=0, column=1, pady=4, padx=4)

        # Cooling water pump systems
        primary_cooling_frame = tk.Frame(btn_frame, bg="#121212")
        primary_cooling_frame.grid(row=1, column=0, pady=4, sticky="ew", padx=4)
        tk.Label(primary_cooling_frame, text="Amt:", bg="#121212", fg="white", font=("Courier", 9)).pack(side="left")
        self.cooling_amount_entry = tk.Entry(primary_cooling_frame, width=6, bg="#252525", fg="white", insertbackground="white", font=("Courier", 10))
        self.cooling_amount_entry.insert(0, "500")
        self.cooling_amount_entry.pack(side="left", padx=2)
        tk.Button(primary_cooling_frame, text="PUMP COOLANT", bg="#06b6d4", fg="black", font=("Helvetica", 9, "bold"), command=self.add_cooling, width=13).pack(side="left", expand=True)

        backup_cooling_frame = tk.Frame(btn_frame, bg="#121212")
        backup_cooling_frame.grid(row=1, column=1, pady=4, sticky="ew", padx=4)
        tk.Label(backup_cooling_frame, text="Amt:", bg="#121212", fg="white", font=("Courier", 9)).pack(side="left")
        self.backup_cooling_amount_entry = tk.Entry(backup_cooling_frame, width=6, bg="#252525", fg="white", insertbackground="white", font=("Courier", 10))
        self.backup_cooling_amount_entry.insert(0, "1000")
        self.backup_cooling_amount_entry.pack(side="left", padx=2)
        tk.Button(backup_cooling_frame, text="BACKUP RESERVES", bg="#14b8a6", fg="white", font=("Helvetica", 9, "bold"), command=self.add_backup_cooling, width=13).pack(side="left", expand=True)

        # Steam venting apparatus
        vent_frame = tk.Frame(btn_frame, bg="#121212")
        vent_frame.grid(row=2, column=0, columnspan=2, pady=4, sticky="ew")
        tk.Label(vent_frame, text="Vent Volume (MPa):", bg="#121212", fg="white", font=("Courier", 9)).pack(side="left", padx=(15, 2))
        self.vent_amount_entry = tk.Entry(vent_frame, width=7, bg="#252525", fg="white", insertbackground="white", font=("Courier", 10))
        self.vent_amount_entry.insert(0, "5.0")
        self.vent_amount_entry.pack(side="left", padx=4)
        self.vent_btn = tk.Button(vent_frame, text="VENT OVERPRESSURE STEAM", bg="#eab308", fg="black", font=("Helvetica", 9, "bold"), command=self.vent_pressure, width=24)
        self.vent_btn.pack(side="left", padx=4)

        # Emergency override panel
        emergency_frame = tk.Frame(control_container, bg="#121212")
        emergency_frame.pack(side="left", padx=15)

        tk.Button(emergency_frame, text="AZ-5\n(SCRAM)", bg="#dc2626", fg="white", font=("Arial", 13, "bold"), height=2, width=12, command=self.az5_trigger).pack(pady=2)
        tk.Button(emergency_frame, text="ABORT EXPERIMENT", bg="#444444", fg="white", font=("Arial", 9, "bold"), command=self.back_to_menu).pack(pady=4)

        # Advanced Plant Shop Interface Infrastructure
        shop_frame = tk.LabelFrame(self.scrollable_frame, text=" 💰 STATION MANAGEMENT & PROCUREMENT SUBSYSTEM 💰 ", font=("Helvetica", 10, "bold"), bg="#121212", fg="#eab308", labelanchor="n")
        shop_frame.pack(pady=6, fill="x", padx=25)
        
        self.shop_lbl = tk.Label(shop_frame, text="", font=("Courier", 10, "bold"), bg="#121212", fg="white")
        self.shop_lbl.pack(pady=4)

        shop_btn_layout = tk.Frame(shop_frame, bg="#121212")
        shop_btn_layout.pack(pady=4)

        self.buy_water_btn = tk.Button(shop_btn_layout, text="BUY WATER +2500L\n(Cost: 200 Cr)", bg="#22c55e", fg="black", font=("Helvetica", 9, "bold"), width=24, command=self.shop_buy_water)
        self.buy_water_btn.grid(row=0, column=0, padx=4, pady=3)
        
        self.buy_valve_btn = tk.Button(shop_btn_layout, text="REINFORCE VALVES +2MPa\n(Cost: 500 Cr)", bg="#eab308", fg="black", font=("Helvetica", 9, "bold"), width=24, command=self.shop_upgrade_valves)
        self.buy_valve_btn.grid(row=0, column=1, padx=4, pady=3)

        self.buy_turbine_btn = tk.Button(shop_btn_layout, text="", bg="#a855f7", fg="white", font=("Helvetica", 9, "bold"), width=24, command=self.shop_upgrade_turbine)
        self.buy_turbine_btn.grid(row=0, column=2, padx=4, pady=3)

        self.buy_nitro_btn = tk.Button(shop_btn_layout, text="NITRO FLUSH (-1000°C)\n(Cost: 600 Cr)", bg="#3b82f6", fg="white", font=("Helvetica", 9, "bold"), width=24, command=self.shop_buy_nitrogen)
        self.buy_nitro_btn.grid(row=0, column=3, padx=4, pady=3)

        # Extended Safety Upgrades (Row 2 of Shop)
        self.buy_filters_btn = tk.Button(shop_btn_layout, text="REPLENISH MASK FILTERS\n(Cost: 150 Cr)", bg="#10b981", fg="white", font=("Helvetica", 9, "bold"), width=24, command=self.shop_replenish_filters)
        self.buy_filters_btn.grid(row=1, column=0, padx=4, pady=3)

        self.buy_mask_grade_btn = tk.Button(shop_btn_layout, text="UPGRADE MASK GRADE\n(Cost: 450 Cr)", bg="#f59e0b", fg="black", font=("Helvetica", 9, "bold"), width=24, command=self.shop_upgrade_mask_grade)
        self.buy_mask_grade_btn.grid(row=1, column=1, padx=4, pady=3)

        self.buy_shielding_btn = tk.Button(shop_btn_layout, text="REINFORCE CONSOLE SHIELD\n(Cost: 550 Cr)", bg="#6366f1", fg="white", font=("Helvetica", 9, "bold"), width=24, command=self.shop_upgrade_shielding)
        self.buy_shielding_btn.grid(row=1, column=2, padx=4, pady=3)

        self.pump_maintenance_btn = tk.Button(shop_btn_layout, text="SERVICE CONDENSER PUMPS\n(Cost: 300 Cr)", bg="#ec4899", fg="white", font=("Helvetica", 9, "bold"), width=24, command=self.shop_service_pumps)
        self.pump_maintenance_btn.grid(row=1, column=3, padx=4, pady=3)

        # Logging Console Workspace
        tk.Label(self.scrollable_frame, text="REAL-TIME SECTOR LOGICAL ARCHIVE FEED", font=("Helvetica", 10, "bold"), bg="#121212", fg="white").pack()
        self.log_area = scrolledtext.ScrolledText(self.scrollable_frame, width=100, height=5, bg="black", fg="#00ff00", font=("Courier", 10))
        self.log_area.pack(pady=6)

        # Establish Initial Simulator Boot Sequences
        self.log_message(f"RBMK Core Emulation Initialized. Welcome operator {self.username}.")
        self.log_message(f"System configuration profile assigned: {self.hardware_mode} optimization loop matrix.")
        if self.user_email != "None":
            self.log_message(f"Remote profile sync confirmed for storage container identifier: {self.user_email}")
        
        self.update_shop_ui()
        self.reactor_tick()
        self.animate_core()

    def toggle_gas_mask(self):
        """
        Toggles the operator's hazardous gas mask safety gear.
        When active, shifts chemical ingestion filters to filter decay loop tracking.
        """
        if not self.is_active: 
            return
        self.mask_on = not self.mask_on
        if self.mask_on:
            self.mask_toggle_btn.config(text="😷 REMOVE GAS MASK", bg="#ef4444", fg="white")
            self.log_message("TACTICAL SAFETY: Fitted protective breathing mask. Ambient inhalation minimized.")
        else:
            self.mask_toggle_btn.config(text="😷 EQUIP GAS MASK", bg="#ff9900", fg="black")
            self.log_message("TACTICAL SAFETY: Removed breathing mask. Respirator channels open to atmosphere.")
        self.update_ui()

    def shop_buy_water(self):
        if self.credits >= 200:
            self.credits -= 200
            self.water_supply += 2500
            self.log_message("LOGISTICS PROCUREMENT: Injected 2500 Liters of purified cooling matrix.")
            self.update_shop_ui()
            self.update_ui()
            self.sync_account_to_disk()
        else:
            self.log_message("FINANCIAL FAULT: Insufficient capital matrix for cooling buffer expansion.")

    def shop_upgrade_valves(self):
        if self.explosion_pressure_limit >= 35.0:
            self.log_message("ENGINEERING ERROR: Structural limits of secondary emergency ventilation system maxed at 35.0 MPa.")
            return
        if self.credits >= 500:
            self.credits -= 500
            self.explosion_pressure_limit = min(35.0, self.explosion_pressure_limit + 2.0)
            self.log_message(f"HARDWARE RENEWAL: High pressure safety parameters elevated to {self.explosion_pressure_limit:.1f} MPa.")
            self.update_shop_ui()
            self.update_ui()
            self.sync_account_to_disk()
        else:
            self.log_message("FINANCIAL FAULT: Insufficient configuration credits for heavy structural retrofit.")

    def shop_upgrade_turbine(self):
        cost = self.turbine_level * 400
        if self.credits >= cost:
            self.credits -= cost
            self.turbine_level += 1
            self.log_message(f"HARDWARE RENEWAL: Steam energy converter upgraded to Grade {self.turbine_level}. Core payout yields enhanced.")
            self.update_shop_ui()
            self.sync_account_to_disk()
        else:
            self.log_message("FINANCIAL FAULT: Insufficient capital metrics for generating unit modernization.")

    def shop_buy_nitrogen(self):
        if self.credits >= 600:
            self.credits -= 600
            self.temperature = max(100.0, self.temperature - 1000.0)
            self.pressure = max(1.0, self.pressure - 6.0)
            self.log_message("EMERGENCY MITIGATION: Liquid Nitrogen containment burst sequence executed. Internal thermal loads dropped.")
            self.update_shop_ui()
            self.update_ui()
            self.sync_account_to_disk()
        else:
            self.log_message("FINANCIAL FAULT: Nitrogen flush module procurement requires additional credit values.")

    def shop_replenish_filters(self):
        if self.credits >= 150:
            self.credits -= 150
            self.mask_filters = 100.0
            self.log_message("LOGISTICS PROCUREMENT: Replaced inner charcoal respirating filter canister. Protection efficiency reset.")
            self.update_shop_ui()
            self.update_ui()
            self.sync_account_to_disk()
        else:
            self.log_message("FINANCIAL FAULT: Inadequate balance resources for breathing filter acquisition.")

    def shop_upgrade_mask_grade(self):
        if self.mask_quality >= 4:
            self.log_message("SAFETY UPGRADE ERROR: Personal breathing apparatus is already at maximum military grade filtration.")
            return
        if self.credits >= 450:
            self.credits -= 450
            self.mask_quality += 1
            self.log_message(f"SAFETY UPGRADE: Mask assembly upgraded to Level {self.mask_quality}. Degradation rate halved.")
            self.update_shop_ui()
            self.sync_account_to_disk()
        else:
            self.log_message("FINANCIAL FAULT: Upgraded operator gas mask equipment unavailable at current asset levels.")

    def shop_upgrade_shielding(self):
        if self.shielding_level >= 4:
            self.log_message("SAFETY UPGRADE ERROR: Control center leaded biological shielding has been reinforced to absolute threshold limits.")
            return
        if self.credits >= 550:
            self.credits -= 550
            self.shielding_level += 1
            self.log_message(f"SAFETY UPGRADE: Enhanced console workstation radiation mitigation blocks to level {self.shielding_level}.")
            self.update_shop_ui()
            self.sync_account_to_disk()
        else:
            self.log_message("FINANCIAL FAULT: Lead wall block allocation rejected due to inadequate budget balance.")

    def shop_service_pumps(self):
        if self.credits >= 300:
            self.credits -= 300
            self.pump_efficiency = min(100.0, self.pump_efficiency + 40.0)
            self.log_message("MAINTENANCE TASK: Mechanical overhaul of hydraulic loop pump bearings finalized. Flow rates normalized.")
            self.update_shop_ui()
            self.update_ui()
            self.sync_account_to_disk()
        else:
            self.log_message("FINANCIAL FAULT: Maintenance request cancelled. Insufficient operational funding metrics.")

    def sync_account_to_disk(self):
        """
        Utility subroutine to compile current operator profiles and write safely to local JSON file.
        """
        save_account_data(
            self.username, self.credits, self.explosion_pressure_limit, 
            self.turbine_level, self.mask_quality, self.shielding_level
        )

    def update_shop_ui(self):
        """
        Refreshes buttons text and state rules within the station procurement shop matrix block.
        """
        self.shop_lbl.config(
            text=f"BALANCE: {self.credits} CREDITS | LIMIT: {self.explosion_pressure_limit:.1f} MPa | "
                 f"TURBINE: Lvl {self.turbine_level} | MASK GRADE: Lvl {self.mask_quality} | SHIELDING: Lvl {self.shielding_level}"
        )
        if self.explosion_pressure_limit >= 35.0:
            self.buy_valve_btn.config(text="VALVES REINFORCED MAX\n(35 MPa)", state="disabled", bg="#555555")
        
        turbine_cost = self.turbine_level * 400
        self.buy_turbine_btn.config(text=f"UPGRADE TURBINE (Lvl {self.turbine_level+1})\n(Cost: {turbine_cost} Cr)")
        
        if self.mask_quality >= 4:
            self.buy_mask_grade_btn.config(text="MASK ARCHITECTURE MAXED\n(Grade 4)", state="disabled", bg="#555555")
        if self.shielding_level >= 4:
            self.buy_shielding_btn.config(text="LEAD BULKHEAD MAXED\n(Lvl 4)", state="disabled", bg="#555555")

    def setup_tasks(self):
        """
        Populates task schedules based on the assigned difficulty parameters.
        Each task specifies descriptions, operational data parameters, and success criteria targets.
        """
        self.tasks = {}
        if self.difficulty == "Guided":
            targets = [
                ("Power stabilization 600MW", "power", 600), 
                ("Preheat system to 1200°C", "temp", 1200), 
                ("Regulate Loop Pressure < 12MPa", "pres", 12), 
                ("Safe Shutdown Sequence Temp < 450°C", "temp_low", 450)
            ]
        elif self.difficulty == "Easy":
            targets = [
                ("Elevate Flux to 600MW", "power", 600), 
                ("Thermal check 1000°C", "temp", 1000), 
                ("Advance output 1200MW", "power", 1200), 
                ("Thermal check 1500°C", "temp", 1500), 
                ("Maintain overpressure < 15MPa", "pres", 15), 
                ("Stabilize Rod Position Count > 120", "rods", 120), 
                ("Conclude experiment with Temp < 400°C", "temp_low", 400)
            ]
        elif self.difficulty == "Medium":
            targets = [
                ("Step A: 600MW output", "power", 600),
                ("Step B: 900MW output", "power", 900),
                ("Step C: Thermal check 1600°C", "temp", 1600),
                ("Step D: 1400MW output", "power", 1400),
                ("Step E: High load 1800MW", "power", 1800),
                ("Cool core sector below 900°C", "temp_low", 900),
                ("Perform AZ-5 Safe Cold Close < 400°C", "temp_low", 400)
            ]
        elif self.difficulty == "Hard":
            targets = [
                ("Stage 1: Thermal target 1000°C", "temp", 1000),
                ("Stage 2: Drive energy to 800MW", "power", 800),
                ("Stage 3: Drive energy to 1300MW", "power", 1300),
                ("Stage 4: Drive energy to 1700MW", "power", 1700),
                ("Stage 5: High power 2200MW", "power", 2200),
                ("Stage 6: Overpressure test < 18MPa", "pres", 18),
                ("Stage 7: Stabilize rod buffer > 140", "rods", 140),
                ("Stage 8: Cool core below 1200°C", "temp_low", 1200),
                ("Stage 9: Cool core below 700°C", "temp_low", 700),
                ("Stage 10: Complete fission lock < 400°C", "temp_low", 400)
            ]
        elif self.difficulty == "VeryHard":
            targets = [
                ("Crisis Power Curve 1200MW", "power", 1200),
                ("Crisis Power Curve 2400MW", "power", 2400),
                ("Pressure containment < 14MPa", "pres", 14),
                ("Rapid thermal reduction < 500°C", "temp_low", 500)
            ]
        elif self.difficulty == "Impossible":
            targets = [
                ("Ultimate Stress Load 2800MW", "power", 2800),
                ("Absolute overpressure gate < 10MPa", "pres", 10),
                ("Extreme Core Drawdown < 400°C", "temp_low", 400)
            ]
        else:
            targets = []
        
        for i, (name, t_type, val) in enumerate(targets):
            self.tasks[i+1] = {"desc": f"Order {i+1}: {name}", "type": t_type, "val": val}

    def get_current_task_desc(self):
        if self.task_stage > len(self.tasks):
            return "ALL MISSIONS COMPLETE. INITIATE AZ-5 TO SECURE STATION CORES."
        return self.tasks[self.task_stage]["desc"]

    def log_message(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.log_area.see(tk.END)

    def update_data_label(self):
        """
        Recalculates display text variables reflecting full core and environment metrics.
        Manages control layout warning flashes for health parameters.
        """
        task_desc = self.get_current_task_desc()
        mode_info = f"DIFFICULTY: {self.difficulty.upper()} | PLATFORM SPEC: {self.hardware_mode.upper()} | ENGINEER: {self.username.upper()}"
        if self.difficulty == "Endless":
            mode_info += f" | SURVIVAL RUNTIME: {self.total_time}s"
        elif self.danger_timer > 0:
            mode_info += f" | ⚠️ EXPLOSION THRESHOLD T-MINUS: {self.meltdown_limit - self.danger_timer}s ⚠️"

        self.task_text.set(task_desc if self.difficulty != 'Endless' else "ENDLESS THREAT ASSESSMENT: MAINTAIN BALANCED CORES AT ALL COST")

        p_tank_idx = 4 - ((self.water_supply - 1) // 2500) if self.water_supply > 0 else 4
        p_status = f"Tank Block {p_tank_idx}/4" if self.water_supply > 0 else "EMPTY"
        b_tank_idx = 2 - ((self.backup_water_supply - 1) // 10000) if self.backup_water_supply > 0 else 2
        b_status = f"Tank Block {b_tank_idx}/2" if self.backup_water_supply > 0 else "EMPTY"

        void_pct = self.void_coefficient * 100
        void_alert = f"STABLE RATIO ({void_pct:.0f}%)" if self.void_coefficient < 0.2 else f"💥 BOILING STEAM VOID CRITICAL ({void_pct:.0f}%)"
        
        mask_status_txt = "SEALED ACTIVE" if self.mask_on else "NOT EQUIPPED"
        air_safety_txt = "CLEAN" if self.air_toxicity < 15.0 else "POISONED / TOXIC AIR" if self.air_toxicity < 50.0 else "LETHAL BIOLOGICAL THREAT"

        self.data_text.set(
            f"{mode_info}\n"
            f"[THERMAL LOAD: {self.temperature:.1f}°C] [NEUTRON POWER: {self.power:.1f} MW] [STEAM VALVE LOAD: {self.pressure:.2f} / {self.explosion_pressure_limit:.1f} MPa]\n"
            f"[CONTROL ROD STACK: {self.rods} / 211] [XENON ABSORBER: {self.xenon*100:.1f}%] [IODINE CONTENT: {self.iodine:.1f}%] [VOID CORRELATION: {void_alert}]\n"
            f"[ROOM TOXICITY: {self.air_toxicity:.1f}% - {air_safety_txt}] [AMBIENT RADS: {self.radiation:.1f} mSv] [RESPIRATOR APPARATUS: {mask_status_txt}]\n"
            f"PRIMARY HYDRAULIC FEED: {self.water_supply}L ({p_status}) | BACKUP RECIRCULATION SYSTEM: {self.backup_water_supply}L ({b_status}) | PUMP EFFICIENCY: {self.pump_efficiency:.1f}%"
        )
        
        vent_color = "#f97316" if self.pressure > (self.explosion_pressure_limit - 5.0) else "#eab308"
        self.vent_btn.config(bg=vent_color)

        # Trigger alarm flash scenarios
        is_alarm = (
            self.temperature > 2500 or 
            self.pressure > (self.explosion_pressure_limit - 7.0) or 
            self.radiation > 400 or 
            self.air_toxicity > 25.0 or
            self.health < 40.0 or
            self.rods < 30 or 
            self.scram_delayed_ticks > 0
        )
        if is_alarm:
            self.flash_warning()
        else:
            self.status_lbl.config(text="ALL SYSTEMS FUNCTIONING WITHIN DESIGN MARGINS", fg="#22c55e")

    def flash_warning(self):
        """
        Manages cyclic blinking of screen alerts for anomalous core states.
        """
        self.flash_state = not self.flash_state
        color = "#dc2626" if self.flash_state else "#121212"
        
        if self.health < 45.0:
            msg = "⚠️ MEDICAL ALARM: OPERATOR SUFFERING ACUTE ARS / ASPHYXIATION! CHECK HEALTH AND MASK! ⚠️"
        elif self.air_toxicity > 25.0 and not self.mask_on:
            msg = "⚠️ ATMOSPHERE CRITICAL ALERT: POISONED ROOM AIR! CAPTURE AND EQUIP GAS MASK IMMEDIATELY! ⚠️"
        elif self.scram_delayed_ticks > 0:
            msg = f"☢️ GRAPHITE INSERTS INDUCING POSITIVE REACTIVITY CAVITATION! AZ-5 DETONATION IN {self.scram_delayed_ticks}s ☢️"
        elif self.rods < 30:
            msg = "⚠️ OPERATIONAL SAFETY MARGIN BREACH: CONTROL CORE INSERTION TOO LOW! GRAPHITE FLAW ARMED ⚠️"
        elif self.xenon > 0.45:
            msg = "⚠️ NUCLEAR REACTOR CONSOLE POISONED BY XENON MATRIX PIT WELL ⚠️"
        else:
            msg = "!!! ALARM CRITICAL: ANOMALOUS TELEMETRY OUTSIDE STANDARD TOLERANCE !!!"
            
        self.status_lbl.config(text=msg, fg=color)

    def init_chart_grid(self):
        for y in range(0, 161, 32):
            self.canvas.create_line(0, y, 350, y, fill="#222222")
        self.chart_line_id = None

    def draw_chart(self):
        if self.chart_line_id:
            self.canvas.delete(self.chart_line_id)
            self.chart_line_id = None
        points = []
        max_points = 20
        recent_history = self.history[-max_points:]
        for i, val in enumerate(recent_history):
            x = (i / (max_points - 1)) * 350 if len(recent_history) > 1 else 0
            y = 160 - (val / 4500.0 * 160.0)
            points.append(x)
            points.append(y)
        if len(points) >= 4:
            self.chart_line_id = self.canvas.create_line(points, fill="#00ff00", width=2)

    def init_rods_display(self):
        self.rod_rects = []
        cols = 8
        cell_w, cell_h = 4, 5
        gap = 1
        for i in range(211):
            col = i % cols
            row = i // cols
            x1 = 4 + col * (cell_w + gap)
            y1 = 155 - row * (cell_h + gap)
            r_id = self.rod_canvas.create_rectangle(x1, y1, x1 + cell_w, y1 - cell_h, fill="#1a1a1a", outline="")
            self.rod_rects.append(r_id)

    def draw_rods(self):
        for i in range(211):
            color = "#22d3ee" if i < self.rods else "#262626"
            self.rod_canvas.itemconfig(self.rod_rects[i], fill=color)

    def init_particles(self):
        for _ in range(self.particle_count):
            p_id = self.core_canvas.create_oval(0, 0, 4, 4, fill="cyan", outline="")
            self.particles.append({
                'id': p_id, 
                'x': random.randint(5, 195), 
                'y': random.randint(5, 155), 
                'dx': random.uniform(-1.6, 1.6), 
                'dy': random.uniform(-1.1, 1.1)
            })
        self.temp_display_id = self.core_canvas.create_text(100, 140, text="", fill="white", font=("Courier", 11, "bold"))
        self.mask_rect_id = self.core_canvas.create_rectangle(0, 0, 200, 160, fill="#7f1d1d", state="hidden", stipple="gray25")

    def animate_core(self):
        """
        Performs continuous kinetic rendering loops inside the atomic flux visualizer canvas window.
        Changes tint behaviors to visualize high air contamination levels or mask filter usage.
        """
        if not self.is_active: 
            return
        speed = 1.0 + (self.power / 900.0)
        
        if self.air_toxicity > 35.0 and not self.mask_on:
            self.core_canvas.itemconfig(self.mask_rect_id, state="normal" if self.flash_state else "hidden")
            color = "#ef4444"
        elif self.mask_on:
            self.core_canvas.itemconfig(self.mask_rect_id, state="normal")
            color = "#10b981"
        else:
            self.core_canvas.itemconfig(self.mask_rect_id, state="hidden")
            color = "#22d3ee" if self.temperature < 1400 else "#f97316" if self.temperature < 2400 else "#ef4444"
            
        for p in self.particles:
            p['x'] += p['dx'] * speed
            p['y'] += p['dy'] * speed
            if p['x'] < 0: p['x'] = 200
            if p['x'] > 200: p['x'] = 0
            if p['y'] < 0: p['y'] = 160
            if p['y'] > 160: p['y'] = 0
            
            self.core_canvas.coords(p['id'], p['x'], p['y'], p['x'] + 4, p['y'] + 4)
            self.core_canvas.itemconfig(p['id'], fill=color)
        
        self.core_canvas.itemconfig(self.temp_display_id, text=f"{self.temperature:.0f}°C")
        self.root.after(self.animation_speed, self.animate_core)

    def draw_biometric_canvases(self):
        """
        Redraws visual indicator bars for operator health and breathing equipment filter capacity.
        """
        # Render biometric health bar component
        self.health_canvas.delete(self.health_bar_id)
        w_health = int((self.health / 100.0) * 260)
        h_color = "#22c55e" if self.health > 60 else "#eab308" if self.health > 30 else "#ef4444"
        self.health_bar_id = self.health_canvas.create_rectangle(0, 0, w_health, 22, fill=h_color, outline="")
        self.health_canvas.itemconfig(self.health_text_id, text=f"HEALTH: {self.health:.1f}%")
        self.health_canvas.lift(self.health_text_id)

        # Render filter lifespan indicator bar component
        self.filter_canvas.delete(self.filter_bar_id)
        w_filter = int((self.mask_filters / 100.0) * 260)
        f_color = "#3b82f6" if self.mask_on else "#64748b"
        self.filter_bar_id = self.filter_canvas.create_rectangle(0, 0, w_filter, 22, fill=f_color, outline="")
        
        status_string = "ACTIVE" if self.mask_on else "STANDBY"
        if self.mask_filters <= 0.0:
            status_string = "EXHAUSTED / FAILED"
        self.filter_canvas.itemconfig(self.filter_text_id, text=f"FILTER: {self.mask_filters:.1f}% ({status_string})")
        self.filter_canvas.lift(self.filter_text_id)

    def check_tasks(self):
        """
        Verifies execution milestones for the current assigned test schedule objective line.
        Supplies credits bonuses upon completion sequences.
        """
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
            self.credits += 350 
            self.update_shop_ui()
            self.sync_account_to_disk()
            if self.task_stage == len(self.tasks):
                self.log_message("STATION CONTROL MESSAGE: ALL CRITICAL SUB-PHASES RESOLVED SUCCESSFULLY.")
                self.show_victory_screen()
                self.task_stage += 1
            else:
                next_desc = self.tasks[self.task_stage + 1]["desc"]
                self.advance_task_sequence(f"{task['desc']} Complete! (+350 Credits Awarded) Next Goal: {next_desc}")

    def advance_task_sequence(self, msg):
        self.task_stage += 1
        self.log_message(f"DIAGNOSTIC TARGET ACHIEVED: {msg}")
        messagebox.showinfo("OBJECTIVE COMPLETED", msg)

    def show_victory_screen(self):
        self.is_active = False
        self.sync_account_to_disk()
        self.show_conclusion_report_screen("🏆 HISTORICAL TEST VICTORY 🏆\nUnit 4 Stabilized with Total Containment Preservation!")

    def back_to_menu(self):
        self.is_active = False
        self.sync_account_to_disk()
        self.root.destroy()
        start_launcher()

    def pull_rods(self):
        if not self.is_active: 
            return
        if self.rods > 0:
            self.rods = max(0, self.rods - 10)
            self.log_message("ACTUATOR TRIGGERED: Withdrawing control rod matrix groups.")
            if self.xenon > 0.35:
                self.log_message("⚠️ REACTOR KINETICS WARNING: Xenon pit neutron capture dampens reactive rod configuration response.")
            if self.rods < 30:
                self.log_message("⚠️ SAFETY THRESHOLD BREACH: Total control rods inside core below safety boundary limits.")
            self.update_ui()

    def insert_rods(self):
        if not self.is_active: 
            return
        if self.rods < 211:
            self.rods = min(211, self.rods + 10)
            self.log_message("ACTUATOR TRIGGERED: Inserting absorbing control rod stack assemblies.")
            self.update_ui()

    def add_cooling(self):
        if not self.is_active: 
            return
        try:
            amount = int(self.cooling_amount_entry.get())
            if amount <= 0: 
                return
        except ValueError: 
            return

        eff_ratio = self.pump_efficiency / 100.0
        actual_pumped = int(amount * eff_ratio)

        if self.water_supply >= actual_pumped:
            self.water_supply -= actual_pumped
            self.temperature = max(90.0, self.temperature - (actual_pumped * 0.55))
            self.pressure = max(0.1, self.pressure - (actual_pumped * 0.0025))
            self.log_message(f"HYDRAULIC ACTUATION: Primary feed loop injected {actual_pumped} Liters water (Pump Efficiency: {self.pump_efficiency:.1f}%).")
            if self.pump_efficiency < 60.0:
                self.log_message("⚠️ MECHANIC WARNING: Degraded pumps restrict fluid transmission throughput parameters.")
            self.update_ui()
        else:
            self.log_message("HYDRAULIC CRITICALITY: Primary cooling water inventory inadequate for commanded pump pulse.")

    def add_backup_cooling(self):
        if not self.is_active: 
            return
        try:
            amount = int(self.backup_cooling_amount_entry.get())
            if amount <= 0: 
                return
        except ValueError: 
            return

        if self.backup_water_supply >= amount:
            self.backup_water_supply -= amount
            self.temperature = max(90.0, self.temperature - (amount * 0.6))
            self.log_message(f"EMERGENCY INJECTION: Secondary backup hydraulic reserve forced {amount} Liters directly into channel block.")
            self.update_ui()
        else:
            self.log_message("HYDRAULIC CRITICALITY: Emergency standby water storage blocks fully drained.")

    def vent_pressure(self):
        if not self.is_active: 
            return
        try:
            amount = float(self.vent_amount_entry.get())
            if amount <= 0: 
                return
        except ValueError: 
            return

        if self.pressure > 1.0:
            old_pres = self.pressure
            self.pressure = max(1.0, self.pressure - amount)
            actual_vented = old_pres - self.pressure
            
            # Realism update: Venting high pressure steam releases radioactive airborne toxicity into environment
            toxicity_leak = actual_vented * 6.5
            self.air_toxicity = min(100.0, self.air_toxicity + toxicity_leak)
            
            self.temperature = max(100.0, self.temperature - int(actual_vented * 12))
            self.log_message(f"VALVE VENTING: Opened release stack. Discharged {actual_vented:.2f} MPa overpressure steam.")
            self.log_message(f"⚠️ ENVIRONMENTAL IMPACT: Released toxic steam cloud increased room airborne toxicity index by +{toxicity_leak:.1f}%.")
            self.update_ui()

    def az5_trigger(self):
        if not self.is_active or self.scram_active: 
            return
        
        if self.rods < 30:
            self.log_message("!!! DESIGN FLAW EXPLOSION PATHWAY TRIGGERED !!!")
            self.log_message("Displaced water columns by graphite rod follower tips create localized steam bubbles...")
            self.scram_delayed_ticks = 3  
            self.scram_active = True
        else:
            self.execute_final_scram()

    def execute_final_scram(self):
        self.rods = 211
        self.power = 0.0
        self.temperature = max(120.0, self.temperature - 1300.0)
        self.pressure = max(1.0, self.pressure - 9.0)
        self.log_message("!!! AUTOMATIC PROTECTIVE INTERLOCK CONCLUDED !!! All control rod channels completely seated.")
        self.update_ui()
        
        if not self.check_meltdown():
            self.is_active = False 
            self.sync_account_to_disk()
            self.show_conclusion_report_screen("EMERGENCY CORE SCRAM SEPARATION SEQUENCE STATUS: ACCOMPLISHED")

    def show_conclusion_report_screen(self, title_text):
        success_window = tk.Toplevel(self.root)
        success_window.title("REACTOR DISPOSITION DOSSIER REPORT")
        success_window.geometry("540x460")
        success_window.configure(bg="#080808")
        success_window.transient(self.root) 
        success_window.grab_set()          

        border_color = "#00ff00" if "🏆" in title_text else "#22d3ee"
        border_frame = tk.Frame(success_window, bg=border_color, padx=3, pady=3)
        border_frame.pack(pady=25, padx=25, fill="both", expand=True)

        inner_content = tk.Frame(border_frame, bg="#111111")
        inner_content.pack(fill="both", expand=True)

        tk.Label(inner_content, text="⚙️ FINAL DIAGNOSTIC TELEMETRY LOG ⚙️", font=("Courier", 13, "bold"), bg="#111111", fg=border_color).pack(pady=15)
        tk.Label(inner_content, text=title_text, font=("Courier", 11, "bold"), bg="#111111", fg="#ffffff", justify="center").pack(pady=4)
        
        report_data = (
            f"--------------------------------------------------\n"
            f"Terminal Temperature Profile:  {self.temperature:.1f} °C\n"
            f"Terminal Neutron Energy Flux:  {self.power:.1f} MW\n"
            f"Terminal Core Vapor Pressure:  {self.pressure:.2f} MPa\n"
            f"Absorber Configuration Stack:  {self.rods} / 211 rods\n"
            f"Operator Total Radiation Dose: {self.radiation:.1f} mSv\n"
            f"Operator Final Health Metrics: {self.health:.1f}%\n"
            f"Total Simulation Run Phase:    {self.total_time} seconds\n"
            f"--------------------------------------------------\n"
            f"STATUS CONFIRMATION: MISSION CONCLUDED STANDBY FOR SECTOR SPLIT."
        )
        
        tk.Label(inner_content, text=report_data, font=("Courier", 10), bg="#111111", fg="#cccccc", justify="left").pack(pady=8)

        def exit_to_launcher_interface():
            success_window.destroy()
            self.back_to_menu()

        tk.Button(
            inner_content, text="RETURN TO MONITOR COMMAND", command=exit_to_launcher_interface, 
            bg=border_color, fg="black", font=("Courier", 11, "bold"), padx=15, pady=6, bd=0
        ).pack(pady=15)

    def check_meltdown(self):
        """
        Evaluates safety trip parameters. If validation constraints are broken,
        shuts down emulation and inflicts financial context penalties.
        """
        if not self.is_active: 
            return False
        is_meltdown = False
        reason = ""
        
        if self.temperature > 3200.0:
            is_meltdown = True
            reason = "CORE DISINTEGRATION MELTDOWN (Uranium fuel loops sheared, structural grid mass liquefied)"
        elif self.pressure > self.explosion_pressure_limit:
            is_meltdown = True
            reason = f"CATASTROPHE VAPOR DETONATION (Biological shield blown clear through deck plate at {self.explosion_pressure_limit:.1f} MPa)"
        elif self.radiation > 2000.0:
            is_meltdown = True
            reason = "DOSIMETER BREAKDOWN (Operator received immediate lethal dose of prompt ionizing emission)"
        elif self.health <= 0.0:
            is_meltdown = True
            reason = "OPERATOR INCAPACITATED (Fatal acute radiation sickness and inhalation of highly toxic atmospheric environment)"
        elif self.difficulty != "Endless" and self.danger_timer >= self.meltdown_limit:
            is_meltdown = True
            reason = f"CRITICAL OVERHEAT FAILURE DETECTOR TIMEOUT ({self.meltdown_limit}s threshold exceeded)"

        if is_meltdown:
            self.is_active = False
            self.credits = max(0, self.credits - 250) 
            self.sync_account_to_disk()
            messagebox.showerror("CRITICAL SIMULATION TERMINATION", f"EMULATION FAULT: {reason}\n\nDemotion Fine Applied: -250 Credits.")
            self.root.destroy()
            return True
        return False

    def update_ui(self):
        self.check_tasks()
        self.update_data_label()
        self.draw_chart()
        self.draw_rods()
        self.draw_biometric_canvases()

    def reactor_tick(self):
        """
        The definitive physical simulation clock function. Executes complex differential mathematical
        correlations for fission power, xenon buildup, structural breakdown, and radioactive air poisoning.
        Updates worker health states iteratively.
        """
        if not self.is_active: 
            return
        self.tick_counter += 1
        self.total_time += 1
        
        # Coupled Isotopic Fission Decay Loop Simulation (Iodine-135 -> Xenon-135)
        if self.power > 100.0:
            # Fission directly yields Iodine concentration
            self.iodine = min(100.0, self.iodine + (self.power * 0.004))
        
        # Iodine constantly breaks down into Xenon poison matrix
        iodine_decay = self.iodine * 0.015
        self.iodine = max(0.0, self.iodine - iodine_decay)
        self.xenon = min(1.0, self.xenon + (iodine_decay * 0.05))

        # Fission neutron flux burns off Xenon-135 isotopes based on high power intensity
        if self.power > 700.0:
            burnout = (self.power - 700.0) * 0.0001
            self.xenon = max(0.0, self.xenon - burnout)
        elif self.power < 500.0:
            # Low fission allows xenon pit accumulation to expand naturally
            self.xenon = min(1.0, self.xenon + 0.012)

        # Volumetric fluid state tracking for positive void reactivity equations
        if self.water_supply < 5000:
            self.void_coefficient = min(2.5, (5000 - self.water_supply) / 1400.0)
        elif self.temperature > 1500.0:
            self.void_coefficient = min(1.6, (self.temperature - 1500.0) / 900.0)
        else:
            self.void_coefficient = max(0.0, self.void_coefficient - 0.05)

        # Target dynamic base fission rate correlation based on current structural rod stack height
        target_power = max(0.0, (1.0 - (self.rods / 211.0)) * 3300.0)
        
        # Apply Xenon poison shielding dampener factors
        if self.xenon > 0.0:
            target_power = max(0.0, target_power * (1.0 - (self.xenon * 0.78)))

        # Apply Positive Void Reactivity multiplier loops
        if self.void_coefficient > 0.08:
            target_power += int(target_power * (self.void_coefficient ** 1.8) * 1.95)

        # Handle explicit graphite follow-tip displacement explosion spikes (AZ-5 Flaw)
        if self.scram_delayed_ticks > 0:
            self.scram_delayed_ticks -= 1
            self.power += 2950.0
            self.temperature += 680.0
            self.pressure += 4.8
            self.air_toxicity = min(100.0, self.air_toxicity + 8.5)
            self.log_message(f"🚨 CRITICAL SYSTEM FLASH: Liquid water boiling immediately inside bottom core! T-Minus {self.scram_delayed_ticks}s")
            
            if self.scram_delayed_ticks == 0:
                self.execute_final_scram()
                return
        else:
            # Thermal latency power lag adjustments
            self.power += int((target_power - self.power) * 0.12)

        # Scale intensity curve according to core baseline difficulties
        difficulty_multiplier = {
            "Guided": 0.4, "Easy": 1.0, "Medium": 1.5, "Hard": 2.1, "VeryHard": 2.8, "Impossible": 3.8, "Endless": 1.1
        }.get(self.difficulty, 1.0)
        
        if self.rods < 211:
            self.temperature += int((35.0 + (self.power * 0.065)) * difficulty_multiplier)
        else:
            self.temperature += int(18.0 * difficulty_multiplier)
            
        # Core boiling vapor calculation correlations
        self.pressure += (self.temperature / 1450.0) + (self.void_coefficient * 0.65)
        
        # Gradually degrade hydraulic recirculation pumps if internal temperature metrics run critical
        if self.temperature > 2000.0:
            pump_degrade = (self.temperature - 2000.0) * 0.002
            self.pump_efficiency = max(20.0, self.pump_efficiency - pump_degrade)
            if self.tick_counter % 4 == 0:
                self.log_message(f"⚠️ STRUCTURAL ANOMALY: Cavitation heat warping main recirculation pump rings. Efficiency degraded by -{pump_degrade:.1f}%.")

        # AIR TOXICITY & AMBIENT CONTAMINATION CALCULATIONS (More Realism)
        # Core thermal loads leaking fission particulates into standard station control space
        if self.temperature > 1400.0:
            toxic_generation = ((self.temperature - 1400.0) / 1000.0) * 1.4 * difficulty_multiplier
            self.air_toxicity = min(100.0, self.air_toxicity + toxic_generation)
        else:
            # Ambient air circulation filters slowly clean safe spaces over time
            if self.air_toxicity > 0.0:
                self.air_toxicity = max(0.0, self.air_toxicity - 0.8)

        # CONTROL ROOM RADIATION LEAKAGE MATRIX
        if self.temperature > 1600.0:
            shield_factor = 1.0 - (self.shielding_level - 1) * 0.22
            rad_leak = int(((self.temperature - 1600.0) / 85.0) * shield_factor * difficulty_multiplier)
            self.radiation += rad_leak

        # BIOMETRIC PLAYER HEALTH INTEGRATION SIMULATION LAYER
        health_impact_incident = False
        health_loss_summary = 0.0

        # Loss path A: Ambient ionizing gamma radiation poisoning dose
        if self.radiation > 300.0:
            rad_damage = (self.radiation - 300.0) * 0.0018
            self.health -= rad_damage
            health_loss_summary += rad_damage
            health_impact_incident = True

        # Loss path B: Atmospheric poison inhalation tracking
        if self.air_toxicity > 10.0:
            if self.mask_on and self.mask_filters > 0.0:
                # Mask equipped with active filter dramatically buffers toxic damage inhalation paths
                filter_depletion_rate = (self.air_toxicity * 0.05) / self.mask_quality
                self.mask_filters = max(0.0, self.mask_filters - filter_depletion_rate)
                
                # Leaked residual factor based on filter wear levels
                residual_tox_damage = (self.air_toxicity * 0.003)
                self.health -= residual_tox_damage
                health_loss_summary += residual_tox_damage
                if self.mask_filters <= 0.0:
                    self.log_message("😷 MASK CRITICAL FAILURE: Internal charcoal filter layers completely saturated. Gas protection lost!")
            else:
                # Unprotected airways suffer profound chemical lung damage vectors
                unprotected_toxic_damage = (self.air_toxicity * 0.045)
                self.health -= unprotected_toxic_damage
                health_loss_summary += unprotected_toxic_damage
                health_impact_incident = True

        # Handle passive medical stabilization loops if environment conditions are secure
        if not health_impact_incident and self.health < 100.0:
            self.health = min(100.0, self.health + 0.3)

        # Force structural values limits constraints boundaries
        self.health = max(0.0, min(100.0, self.health))

        # Log respiratory health status profiles to operators console feed frame
        if self.tick_counter % 6 == 0:
            if self.air_toxicity > 20.0 and not self.mask_on:
                self.log_message("⚠️ SAFETY BIOMETRIC CONTEXT: Operator inhaling contaminated dust layers! Equip mask to protect health.")
            elif self.mask_on and self.mask_filters <= 15.0 and self.mask_filters > 0.0:
                self.log_message("😷 SAFETY BIOMETRIC CONTEXT: Gas mask filter canisters are near saturation limits! Purchase spares.")
            if health_loss_summary > 0.5:
                self.log_message(f"💔 DIAGNOSTIC ERROR: Operator body absorbing cellular degradation. Health down (-{health_loss_summary:.2f}%/s).")

        # Check for countdown safety triggers constraints thresholds
        is_critical_state = (
            self.temperature > 2500.0 or 
            self.pressure > (self.explosion_pressure_limit - 7.0) or 
            self.radiation > 500.0 or 
            self.air_toxicity > 30.0 or
            self.rods < 30 or 
            self.scram_delayed_ticks > 0
        )
        if is_critical_state:
            if self.difficulty != "Endless":
                self.danger_timer += 1
        else:
            self.danger_timer = 0

        # Process periodic commercial monetary payouts from generator rotation loops
        if self.tick_counter % 5 == 0:
            base_payout = 30
            efficiency_bonus = (self.turbine_level - 1) * 20
            self.credits += (base_payout + efficiency_bonus)
            self.update_shop_ui()

        # Update historical trend buffers
        self.history.append(self.temperature)
        if len(self.history) > 20: 
            self.history.pop(0)
        
        self.update_ui()
        if not self.check_meltdown():
            self.root.after(1000, self.reactor_tick)


def start_launcher():
    """
    Constructs the operational launch configuration frame matrix interface window.
    Coordinates database verification portals and security registration subsegments.
    """
    launcher = tk.Tk()
    launcher.title("Chernobyl Station Command Terminal - RBMK Launcher")
    launcher.geometry("600x950")
    launcher.configure(bg="#111111")

    # Header Authentication Identity Bar Layout
    top_bar = tk.Frame(launcher, bg="#080808", height=50)
    top_bar.pack(fill="x", side="top")
    top_bar.pack_propagate(False)

    user_status_lbl = tk.Label(top_bar, text="STATION ENGINEER STATUS: Guest (Unverified Local Profile)", font=("Courier", 9, "bold"), bg="#080808", fg="#999999")
    user_status_lbl.pack(side="left", padx=12)

    def open_account_portal():
        portal = tk.Toplevel(launcher)
        portal.title("State Security Authentication Archive")
        portal.geometry("380x350")
        portal.configure(bg="#050505")
        portal.transient(launcher)
        portal.grab_set()

        tk.Label(portal, text="⚙️ ADMINISTRATIVE IDENTITY ACCESS ⚙️", font=("Courier", 11, "bold"), bg="#050505", fg="#00ff00").pack(pady=15)

        mode_frame = tk.Frame(portal, bg="#050505")
        mode_frame.pack(pady=4)
        
        portal_mode = tk.StringVar(value="login")

        def toggle_view_context():
            if portal_mode.get() == "login":
                action_btn.config(text="ACCESS SECURE ARCHIVE", bg="#2563eb")
                email_label.config(text="RECOVERY SIGNATURE (Optional):")
                info_lbl.config(text="Query local system indices to restore operator credit balances.")
            else:
                action_btn.config(text="GENERATE WORKER DOSSIER", bg="#16a34a")
                email_label.config(text="CENTRAL GMAIL ROUTING ADDRESS:")
                info_lbl.config(text="Registers a verified digital record containing progress storage slots.")

        tk.Radiobutton(mode_frame, text="LOG IN PROFILE", variable=portal_mode, value="login", command=toggle_view_context, bg="#050505", fg="white", selectcolor="#1f1f1f").pack(side="left", padx=12)
        tk.Radiobutton(mode_frame, text="REGISTER DOSSIER", variable=portal_mode, value="register", command=toggle_view_context, bg="#050505", fg="white", selectcolor="#1f1f1f").pack(side="left", padx=12)

        tk.Label(portal, text="OPERATOR CODENAME SIGNATURE:", font=("Courier", 9), bg="#050505", fg="#cccccc").pack(pady=(12, 2))
        id_entry = tk.Entry(portal, font=("Courier", 10), bg="#1e1e1e", fg="white", insertbackground="white", width=28)
        id_entry.pack()

        email_label = tk.Label(portal, text="RECOVERY SIGNATURE (Optional):", font=("Courier", 9), bg="#050505", fg="#cccccc")
        email_label.pack(pady=(12, 2))
        email_entry = tk.Entry(portal, font=("Courier", 10), bg="#1e1e1e", fg="white", insertbackground="white", width=28)
        email_entry.pack()

        info_lbl = tk.Label(portal, text="Query local system indices to restore operator credit balances.", font=("Arial", 8, "italic"), bg="#050505", fg="#777777", wraplength=320)
        info_lbl.pack(pady=12)

        def verify_portal_transaction():
            uid = id_entry.get().strip()
            mail = email_entry.get().strip()

            if not uid:
                messagebox.showwarning("SECURITY REJECTION", "Operator signature identifier field cannot remain blank.")
                return

            accounts = load_all_accounts()

            if portal_mode.get() == "login":
                if uid in accounts:
                    user_entry.delete(0, tk.END)
                    user_entry.insert(0, uid)
                    user_status_lbl.config(text=f"STATION ENGINEER: {uid} (Dossier Verified)", fg="#22c55e")
                    messagebox.showinfo("ACCESS AUTHORIZED", f"Welcome back to station monitor, Engineer {uid}!\nProfile indices restored.")
                    portal.destroy()
                else:
                    messagebox.showerror("AUTHENTICATION REJECTION", f"Operator signature ID '{uid}' absent from local records.\nSwitch toggle to REGISTER DOSSIER.")
            else:
                if not mail or "@" not in mail:
                    messagebox.showwarning("VALIDATION ERROR", "Dossier creation requires a valid Gmail routing format parameter.")
                    return
                if uid in accounts:
                    messagebox.showerror("IDENTITY COLLISION", "Operational codename signature already allocated inside database.")
                else:
                    save_account_data(uid, credits=1000, max_pressure=25.0, turbine_level=1, mask_quality=1, shielding_level=1, email=mail)
                    user_entry.delete(0, tk.END)
                    user_entry.insert(0, uid)
                    user_status_lbl.config(text=f"STATION ENGINEER: {uid} (Cloud Database Synced)", fg="#10b981")
                    messagebox.showinfo("DOSSIER RECORD GENERATED", f"New personnel account index '{uid}' successfully formatted!\nRouting vector bound: {mail}")
                    portal.destroy()

        action_btn = tk.Button(portal, text="ACCESS SECURE ARCHIVE", bg="#2563eb", fg="white", font=("Courier", 10, "bold"), width=26, command=verify_portal_transaction)
        action_btn.pack(pady=15)

    account_portal_btn = tk.Button(top_bar, text="🔑 CENTRAL IDENTITY ACCESS", bg="#222222", fg="#eab308", font=("Helvetica", 9, "bold"), bd=1, relief="raised", command=open_account_portal)
    account_portal_btn.pack(side="right", padx=6, pady=5)

    tk.Label(launcher, text="☢️ ADMINISTRATIVE HARDWARE CONTROL UNIT ☢️", font=("Courier", 11, "bold"), bg="#111111", fg="#eab308").pack(pady=(15, 4))
    
    user_frame = tk.Frame(launcher, bg="#111111")
    user_frame.pack(pady=2)
    tk.Label(user_frame, text="COMANDING TECH SIGNATURE:", font=("Courier", 10), bg="#111111", fg="white").pack(side="left", padx=4)
    user_entry = tk.Entry(user_frame, font=("Courier", 11), bg="#262626", fg="white", insertbackground="white", width=16)
    user_entry.insert(0, "Guest")
    user_entry.pack(side="left", padx=4)

    def process_live_key_sync(*args):
        current = user_entry.get().strip()
        if current in load_all_accounts():
            user_status_lbl.config(text=f"STATION ENGINEER: {current} (Active Profile Indexed)", fg="#22c55e")
        else:
            user_status_lbl.config(text=f"STATION ENGINEER: {current} (Local Sandbox)", fg="#888888")
    user_entry.bind("<KeyRelease>", process_live_key_sync)

    # -------------------------------------------------------------
    # CONTROL INTERFACE BLOCK 1: CORE REACTIVITY RISK LEVEL SELECT
    # -------------------------------------------------------------
    difficulty_container = tk.LabelFrame(launcher, text=" ☢️ CONFIGURATION OF CORE FISSION RISK PARAMETERS ☢️ ", font=("Courier", 10, "bold"), bg="#111111", fg="#22c55e", labelanchor="n")
    difficulty_container.pack(pady=8, padx=20, fill="x")

    mode_var = tk.StringVar(value="Easy")
    
    difficulties = [
        ("GUIDED ASSIGNMENT", "Guided", "35-second emergency safety clock buffer. Explicit training path instructions."),
        ("EASY REGULATORY OPERATIONS", "Easy", "25-second countdown threshold. Standard physics curves applied."),
        ("MEDIUM STRESS TESTING", "Medium", "18-second timeout safety gate. Multi-tiered operation milestones active."),
        ("HARD EXPERIMENTAL SEQUENCE", "Hard", "12-second core trip limit. Accelerated power and thermal accumulation loops."),
        ("VERY HARD DEVIATION TRIAL", "VeryHard", "8-second safety margin. Severe positive feedback void coefficients."),
        ("IMPOSSIBLE CORE STRESS FAULT", "Impossible", "4-second zero-error threshold. Hyper-volatile neutron kinetics."),
        ("ENDLESS COMBAT DECAY ITERATION", "Endless", "Clock limits completely bypassed! Test your limits for highest survival durations.")
    ]

    for title, val, desc in difficulties:
        fmt_txt = f"{title}\n -> {desc}"
        tk.Radiobutton(
            difficulty_container, text=fmt_txt, variable=mode_var, value=val, 
            bg="#111111", fg="#e5e5e5", selectcolor="#171717", activebackground="#111111", activeforeground="white",
            font=("Courier", 9), justify="left", anchor="w"
        ).pack(fill="x", padx=12, pady=3)

    # -------------------------------------------------------------
    # CONTROL INTERFACE BLOCK 2: RND GRAPHICS ENGINE RENDERING FRAME
    # -------------------------------------------------------------
    hardware_container = tk.LabelFrame(launcher, text=" 💻 RND GRAPHICS DENSITY RESOLUTION PROFILE 💻 ", font=("Courier", 10, "bold"), bg="#111111", fg="#3b82f6", labelanchor="n")
    hardware_container.pack(pady=8, padx=20, fill="x")

    hw_var = tk.StringVar(value="Laptop")

    hw_specs = [
        ("LOW-RAM MOBILE ARCHITECTURE (PHONE)", "Phone", "Restricted density index (8 particles) & 140ms update delays. Lower execution overhead."),
        ("BALANCED WORKSTATION PROFILE (LAPTOP)", "Laptop", "Standard profile configuration (18 particles) & 90ms update intervals. Default preset."),
        ("MAX HIGH-PERFORMANCE MAINFRAME (PC)", "PC", "Max ultra particle arrays (34 kinetic dots) & 45ms update loops. Smooth fluid curves.")
    ]

    for title, val, desc in hw_specs:
        fmt_txt = f"{title}\n -> {desc}"
        tk.Radiobutton(
            hardware_container, text=fmt_txt, variable=hw_var, value=val, 
            bg="#111111", fg="#e5e5e5", selectcolor="#171717", activebackground="#111111", activeforeground="white",
            font=("Courier", 9), justify="left", anchor="w"
        ).pack(fill="x", padx=12, pady=3)

 # Launcher Execution Activator Button
    # =====================================================================
    # INTERMEDIATE PROTOCOL BRIEFING MATRIX (THE NEW WINDOW)
    # =====================================================================
    def display_controls_briefing(selected_mode, selected_hw, op_name):
        briefing = tk.Tk()
        briefing.title("🔑 CLASSIFIED PROTOCOL BRIEFING MATRIX")
        briefing.geometry("600x670")
        briefing.configure(bg="#111111")

        header = tk.Label(briefing, text="📋 CHERNOBYL CORE KEYBOARD INPUT MATRIX", 
                          font=("Courier", 12, "bold"), bg="#080808", fg="#dc2626", bd=1, relief="solid", pady=10)
        header.pack(fill="x", padx=20, pady=20)

        info_text = (
            f"OPERATOR CODE: {op_name.upper()}\n"
            f"CHOSEN SECTOR: {selected_mode.upper()}\n"
            f"HARDWARE SPEC: {selected_hw.upper()}\n"
            "--------------------------------------------------\n"
            "Do not move your mouse! Use these hotkeys directly\n"
            "on the terminal dashboard to control Unit IV:\n"
            "--------------------------------------------------\n\n"
            " ⌨️ [◄ ] LEFT ARROW  -->  PULL OUT CONTROL RODS\n"
            "                      (Raises Heat / Flux Yield)\n\n"
            " ⌨️ [► ] RIGHT ARROW -->  INSERT CONTROL RODS\n"
            "                      (Lowers Flux Generation)\n\n"
            " ⌨️ [ C ] OR [ W ]   -->  INJECT WATER LOOP COOLANT\n"
            "                      (Cools Core Down Instantly)\n\n"
            " ⌨️ [ V ] KEY        -->  OPEN OVERPRESSURE VALVES\n"
            "                      (Vents Dangerous Core Steam)\n\n"
            " ⌨️ [ M ] KEY        -->  EQUIP BIOLOGICAL GAS MASK\n"
            "                      (Protects From Radiation)\n\n"
            " ⌨️ [ SPACEBAR ]     -->  🚨 ACTIVATE AZ-5 SCRAM 🚨\n"
            "                      (EMERGENCY COLD SHUTDOWN)"
        )

        display_box = tk.Label(briefing, text=info_text, font=("Courier", 10), bg="#050505", 
                               fg="#e5e5e5", justify="left", bd=1, relief="sunken", padx=20, pady=20)
        display_box.pack(fill="both", expand=True, padx=20, pady=5)

        def trigger_game_start():
            briefing.destroy()
            game_window = tk.Tk()
            # Launches your original reactor interface perfectly with hotkeys bound!
            ReactorSimulation(game_window, mode=selected_mode, hw_mode=selected_hw, username=op_name)
            game_window.mainloop()

        start_btn = tk.Button(briefing, text="☢️ INITIALIZE SYSTEM CORE ☢️", font=("Courier", 12, "bold"), 
                              bg="#dc2626", fg="white", bd=3, relief="raised", command=trigger_game_start)
        start_btn.pack(pady=25, fill="x", padx=35, ipady=6)

        briefing.mainloop()

    def execute_core_launch_sequence():
        selected_mode = mode_var.get()
        selected_hw = hw_var.get()
        op_name = user_entry.get().strip()
        if not op_name:
            op_name = "Guest"
            
        launcher.destroy()
        display_controls_briefing(selected_mode, selected_hw, op_name)

    launch_btn = tk.Button(
        launcher, text="⚡ ENGAGE RBMK CRITICAL CORE SYSTEM OVERRIDE ⚡", 
        font=("Courier", 11, "bold"), bg="#dc2626", fg="white", bd=3, relief="raised", 
        command=execute_core_launch_sequence
    )
    launch_btn.pack(pady=15, fill="x", padx=35)

    launcher.mainloop()


# Context Execution Gateway
if __name__ == "__main__":
    start_launcher()