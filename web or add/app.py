from flask import Flask, render_template, jsonify, request
import random
import os
import json

app = Flask(__name__)

SAVE_FILE = "reactor_saves.json"

def load_all_accounts():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_account_data(username, credits, max_pressure, turbine_level, email="None"):
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
        "email": current_email
    })
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(accounts, f, indent=4)
    except Exception as e:
        print(f"Error saving data: {e}")

# Global state tracker for the currently running web session
session_game = {
    "is_running": False,
    "username": "Guest",
    "difficulty": "Easy",
    "hardware_mode": "Laptop",
    "credits": 1000,
    "max_pressure": 25.0,
    "turbine_level": 1,
    "email": "None",
    
    # Simulation Math Metrics
    "temperature": 300,
    "power": 400,
    "rods": 180,
    "water_supply": 10000,
    "backup_water_supply": 20000,
    "pressure": 1.0,
    "radiation": 0,
    "xenon": 0.0,
    "void_coefficient": 0.0,
    
    "scram_delayed_ticks": 0,
    "scram_active": False,
    "danger_timer": 0,
    "meltdown_limit": 20,
    "total_time": 0,
    "task_stage": 1,
    "status_msg": "SYSTEM READY",
    "log_messages": []
}

# Tasks configuration matched directly to your original difficulty profiles
def get_tasks_for_mode(mode):
    if mode == "Guided":
        return [("600MW Power", "power", 600), ("1200°C Temp", "temp", 1200), ("Pressure < 12MPa", "pres", 12), ("Shutdown < 400°C", "temp_low", 400)]
    elif mode == "Easy":
        return [("600MW", "power", 600), ("1000°C", "temp", 1000), ("1200MW", "power", 1200), ("1500°C", "temp", 1500), ("Pres < 15MPa", "pres", 15), ("Rods > 100", "rods", 100), ("Shutdown < 400°C", "temp_low", 400)]
    elif mode == "Medium":
        return [(f"Step {i}: {400 + i*200}MW", "power", 400 + i*200) for i in range(1, 6)] + [("Cooling Core", "temp_low", 800), ("Final Shutdown", "temp_low", 400)]
    elif mode == "Hard":
        return [(f"Stage {i}: {400 + i*120}MW", "power", 400 + i*120) for i in range(1, 12)] + [(f"Pres Control {i}", "pres", 20 - i) for i in range(1, 5)] + [(f"Final Cooling {i}", "temp_low", 1000 - i*150) for i in range(1, 4)] + [("Cold Shutdown", "temp_low", 400)]
    return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    return jsonify(load_all_accounts())

@app.route('/api/launcher/submit', methods=['POST'])
def launcher_submit():
    data = request.json
    username = data.get("username", "Guest").strip() or "Guest"
    difficulty = data.get("difficulty", "Easy")
    hw_mode = data.get("hardware_mode", "Laptop")
    email = data.get("email", "None").strip() or "None"
    action_type = data.get("action_type", "local") # login, register, local

    accounts = load_all_accounts()

    if action_type == "login":
        if username not in accounts:
            return jsonify({"error": f"Operator ID '{username}' not found. Switch to Register to sign up."}), 400
        acc = accounts[username]
    elif action_type == "register":
        if "@" not in email or not email:
            return jsonify({"error": "Please input a valid backup Gmail address."}), 400
        if username in accounts:
            return jsonify({"error": "Username already active in system."}), 400
        save_account_data(username, 1000, 25.0, 1, email)
        acc = {"credits": 1000, "max_pressure": 25.0, "turbine_level": 1, "email": email}
    else: # Local Override Profile
        acc = accounts.get(username, {"credits": 1000, "max_pressure": 25.0, "turbine_level": 1, "email": "None"})

    # Setup the live simulation data room
    session_game.update({
        "is_running": True, "username": username, "difficulty": difficulty, "hardware_mode": hw_mode,
        "credits": acc.get("credits", 1000), "max_pressure": acc.get("max_pressure", 25.0), "turbine_level": acc.get("turbine_level", 1), "email": acc.get("email", "None"),
        "temperature": 300, "power": 400, "rods": 180, "water_supply": 10000, "backup_water_supply": 20000, "pressure": 1.0, "radiation": 0, "xenon": 0.0, "void_coefficient": 0.0,
        "scram_delayed_ticks": 0, "scram_active": False, "danger_timer": 0, "total_time": 0, "task_stage": 1, "status_msg": "SYSTEM READY",
        "log_messages": [f"Welcome back, Operator {username}. Core online.", f"Graphics Environment: {hw_mode} Mode Active."]
    })
    
    session_game["meltdown_limit"] = {"Guided": 30, "Easy": 20, "Medium": 15, "Hard": 10, "VeryHard": 7, "Impossible": 3, "Endless": 999999}.get(difficulty, 20)
    return jsonify({"success": True, "game_state": session_game, "tasks": get_tasks_for_mode(difficulty)})

@app.route('/api/simulation/tick', methods=['GET'])
def simulation_tick():
    if not session_game["is_running"]:
        return jsonify(session_game)

    session_game["total_time"] += 1

    # Xenon poisoning calculation
    if session_game["power"] < 600:
        session_game["xenon"] = min(1.0, session_game["xenon"] + 0.04)
    else:
        session_game["xenon"] = max(0.0, session_game["xenon"] - 0.02)

    # Steam void coefficient logic
    if session_game["water_supply"] < 5000:
        session_game["void_coefficient"] = min(2.5, (5000 - session_game["water_supply"]) / 1500)
    elif session_game["temperature"] > 1500:
        session_game["void_coefficient"] = min(1.5, (session_game["temperature"] - 1500) / 1000)
    else:
        session_game["void_coefficient"] = 0.0

    target_power = max(0, (1 - (session_game["rods"] / 211)) * 3200)
    if session_game["xenon"] > 0.0:
        target_power = max(0, target_power * (1 - (session_game["xenon"] * 0.75)))
    if session_game["void_coefficient"] > 0.1:
        target_power += int(target_power * (session_game["void_coefficient"] ** 2) * 1.8)

    # Graphite tip detonation trigger handle
    if session_game["scram_delayed_ticks"] > 0:
        session_game["scram_delayed_ticks"] -= 1
        session_game["power"] += 2800
        session_game["temperature"] += 650
        session_game["pressure"] += 4.5
        session_game["log_messages"].append(f"CRITICAL FLUID FLASH: Graphite tips displacing liquid water! T-Minus {session_game['scram_delayed_ticks']}s")
        if session_game["scram_delayed_ticks"] == 0:
            execute_scram_shutdown()
            return jsonify(session_game)
    else:
        session_game["power"] += int((target_power - session_game["power"]) * 0.1)

    multiplier = {"Guided": 0.5, "Easy": 1.0, "Medium": 1.5, "Hard": 2.0, "VeryHard": 2.5, "Impossible": 3.5, "Endless": 1.0}.get(session_game["difficulty"], 1.0)
    if session_game["rods"] < 211:
        session_game["temperature"] += int((30 + (session_game["power"] * 0.06)) * multiplier)
    else:
        session_game["temperature"] += int(20 * multiplier)

    session_game["pressure"] += (session_game["temperature"] / 1500) + (session_game["void_coefficient"] * 0.6)

    if session_game["temperature"] > 1500:
        session_game["radiation"] += int((session_game["temperature"] - 1500) / 100)

    # Automatic turbine credit rewards
    if session_game["total_time"] % 5 == 0:
        session_game["credits"] += (25 + (session_game["turbine_level"] - 1) * 15)
        save_account_data(session_game["username"], session_game["credits"], session_game["max_pressure"], session_game["turbine_level"])

    # Core crisis boundaries checking
    is_critical = (session_game["temperature"] > 2500 or 
                   session_game["pressure"] > (session_game["max_pressure"] - 7.0) or 
                   session_game["radiation"] > 500 or 
                   session_game["rods"] < 30 or 
                   session_game["scram_delayed_ticks"] > 0)
    if is_critical:
        if session_game["difficulty"] != "Endless":
            session_game["danger_timer"] += 1
        session_game["status_msg"] = "!!! CRITICAL ALARM !!!"
    else:
        session_game["danger_timer"] = 0
        session_game["status_msg"] = "SYSTEM STABLE"

    check_meltdown_conditions()
    return jsonify(session_game)

def execute_scram_shutdown():
    session_game["rods"] = 211
    session_game["power"] = 0
    session_game["temperature"] = max(150, session_game["temperature"] - 1200)
    session_game["pressure"] = max(1.0, session_game["pressure"] - 10.0)
    session_game["log_messages"].append("!!! SCRAM CONCLUDED !!! AZ-5 fully seated.")
    
    if not verify_meltdown_check():
        session_game["is_running"] = False
        session_game["status_msg"] = "CONCLUDED"
        save_account_data(session_game["username"], session_game["credits"], session_game["max_pressure"], session_game["turbine_level"])

def check_meltdown_conditions():
    verify_meltdown_check()

def verify_meltdown_check():
    reason = ""
    if session_game["temperature"] > 3200:
        reason = "CORE MELTDOWN (Fuel channels ruptured & shielding melted)"
    elif session_game["pressure"] > session_game["max_pressure"]:
        reason = f"STEAM EXPLOSION (Upper Biological Shield blown clear at {session_game['max_pressure']:.1f} MPa)"
    elif session_game["radiation"] > 2000:
        reason = "LETHAL DOSE (Total area radioactive containment failure)"
    elif session_game["difficulty"] != "Endless" and session_game["danger_timer"] >= session_game["meltdown_limit"]:
        reason = f"CRITICAL OVERHEAT TIMEOUT ({session_game['meltdown_limit']}s threshold crossed)"

    if reason:
        session_game["is_running"] = False
        session_game["credits"] = max(0, session_game["credits"] - 200)
        session_game["status_msg"] = "TERMINATED"
        session_game["log_messages"].append(f"CRITICAL FAILURE: {reason} | Penalty Applied: -200 Credits.")
        save_account_data(session_game["username"], session_game["credits"], session_game["max_pressure"], session_game["turbine_level"])
        return True
    return False

@app.route('/api/simulation/action', methods=['POST'])
def action_handle():
    if not session_game["is_running"]:
        return jsonify(session_game)
        
    data = request.json
    act = data.get("action")
    amt = data.get("amount", 0)

    if act == "pull":
        session_game["rods"] = max(0, session_game["rods"] - 10)
        session_game["log_messages"].append("Control Rods extracted.")
        if session_game["xenon"] > 0.3:
            session_game["log_messages"].append("⚠️ WARNING: Xenon poisoning absorbing neutron flux. Pulling rods has minimal response!")
        if session_game["rods"] < 30:
            session_game["log_messages"].append("⚠️ CRITICAL ERROR: Safety boundary broken! Graphite tips fully exposed at the core boundary!")
            
    elif act == "insert":
        session_game["rods"] = min(211, session_game["rods"] + 10)
        session_game["log_messages"].append("Control Rods inserted. Power dropping.")
        
    elif act == "cool":
        if session_game["water_supply"] >= amt:
            session_game["water_supply"] -= amt
            session_game["temperature"] = max(100, session_game["temperature"] - (amt * 0.6))
            session_game["pressure"] = max(0.1, session_game["pressure"] - (amt * 0.002))
            session_game["log_messages"].append(f"Primary cooling active: {amt}L injected.")
        else:
            session_game["log_messages"].append("CRITICAL: Primary supply too low!")
            
    elif act == "backup":
        if session_game["backup_water_supply"] >= amt:
            session_game["backup_water_supply"] -= amt
            session_game["temperature"] = max(100, session_game["temperature"] - (amt * 0.6))
            session_game["log_messages"].append(f"EMERGENCY: Backup cooling active! {amt}L injected.")
        else:
            session_game["log_messages"].append("CRITICAL: Backup reservoir empty!")
            
    elif act == "vent":
        if session_game["pressure"] > 1.0:
            old_p = session_game["pressure"]
            session_game["pressure"] = max(1.0, session_game["pressure"] - amt)
            actual_vented = old_p - session_game["pressure"]
            session_game["temperature"] -= int(actual_vented * 10)
            session_game["log_messages"].append(f"Steam valves opened. {actual_vented:.2f} MPa vented.")
            
    elif act == "az5":
        if not session_game["scram_active"]:
            if session_game["rods"] < 30:
                session_game["log_messages"].append("!!! EMERGENCY SCRAM FLAW ACTIVATED !!!")
                session_game["log_messages"].append("Graphite displacement tips enter simultaneously. Displacing water...")
                session_game["scram_delayed_ticks"] = 3
                session_game["scram_active"] = True
            else:
                execute_scram_shutdown()

    # Shop mechanics handlers
    elif act == "shop_water" and session_game["credits"] >= 200:
        session_game["credits"] -= 200
        session_game["water_supply"] += 2500
        session_game["log_messages"].append("SHOP: Purchased 2500L primary coolant water.")
    elif act == "shop_valves" and session_game["credits"] >= 500 and session_game["max_pressure"] < 35.0:
        session_game["credits"] -= 500
        session_game["max_pressure"] = min(35.0, session_game["max_pressure"] + 2.0)
        session_game["log_messages"].append(f"SHOP: Valves reinforced! Max safe limit increased to {session_game['max_pressure']:.1f} MPa.")
    elif act == "shop_turbine" and session_game["credits"] >= (session_game["turbine_level"] * 400):
        session_game["credits"] -= (session_game["turbine_level"] * 400)
        session_game["turbine_level"] += 1
        session_game["log_messages"].append(f"SHOP: Turbine upgraded to Level {session_game['turbine_level']}! Credit payout increased.")
    elif act == "shop_nitro" and session_game["credits"] >= 600:
        session_game["credits"] -= 600
        session_game["temperature"] = max(100, session_game["temperature"] - 1000)
        session_game["pressure"] = max(1.0, session_game["pressure"] - 6.0)
        session_game["log_messages"].append("SHOP: Emergency Liquid Nitrogen Flush active! Core temperature slashed by 1000°C.")

    # Objective task completion payout checkpoint
    tasks = get_tasks_for_mode(session_game["difficulty"])
    if session_game["difficulty"] != "Endless" and session_game["task_stage"] <= len(tasks):
        task = tasks[session_game["task_stage"] - 1]
        done = False
        if task[1] == "power" and session_game["power"] >= task[2]: done = True
        elif task[1] == "temp" and session_game["temperature"] >= task[2]: done = True
        elif task[1] == "temp_low" and session_game["temperature"] <= task[2]: done = True
        elif task[1] == "pres" and session_game["pressure"] <= task[2]: done = True
        elif task[1] == "rods" and session_game["rods"] >= task[2]: done = True

        if done:
            session_game["credits"] += 300
            session_game["task_stage"] += 1
            if session_game["task_stage"] > len(tasks):
                session_game["log_messages"].append("STATION GOAL ACHIEVED: FINAL TASK COMPLETE.🏆 MISSION VICTORY 🏆")
                session_game["is_running"] = False
                session_game["status_msg"] = "VICTORY"
            else:
                next_t = tasks[session_game["task_stage"] - 1]
                session_game["log_messages"].append(f"STATION GOAL ACHIEVED: Task completed! (+300 Cr) Next: Task {session_game['task_stage']}: {next_t[0]}")

    save_account_data(session_game["username"], session_game["credits"], session_game["max_pressure"], session_game["turbine_level"])
    return jsonify(session_game)

@app.route('/api/simulation/quit', methods=['POST'])
def quit_simulation():
    session_game["is_running"] = False
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True)