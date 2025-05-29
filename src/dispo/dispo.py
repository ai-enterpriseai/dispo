# dispo.py
# (Based on lkw_optimierung_v2.py)
# Required libraries: pulp
# Installation: pip install pulp
# encoding: utf-8

import math
import csv
import io
import os
from datetime import datetime
import random

# Try to import pulp and give a clear error message if not available
try:
    import pulp
except ImportError:
    print("FEHLER: Die Bibliothek 'pulp' wurde nicht gefunden.")
    print("Bitte installieren Sie sie mit: pip install pulp")
    exit()

# --- 1. Constants and Configuration ---
RANDOM_SEED = 42 # Maintain for consistency of generated data
random.seed(RANDOM_SEED)

# Target scale according to requirement: approx. 200 trucks, 300 orders.
# Smaller numbers are used here for testing purposes.
NUM_TRUCKS = 10
NUM_ORDERS = 15
# MAX_COORDINATE = 100  # km - No longer used, now using real lat/lng coordinates
AVERAGE_SPEED_KMH = 80.0  # km/h - Realistic speed for trucks on European highways

# Time assumptions (in hours from simulation start, e.g. 0.0 = midnight)
SIMULATION_START_H = 0.0
MIN_TRUCK_AVAILABLE_FROM_H = 7.0
MAX_TRUCK_AVAILABLE_FROM_H = 9.0
MIN_TRUCK_AVAILABLE_DURATION_H = 8.0
MAX_TRUCK_AVAILABLE_DURATION_H = 12.0 # Slightly increased for potentially longer tours

MIN_ORDER_LOADING_WINDOW_EARLY_H = 8.0
MAX_ORDER_LOADING_WINDOW_EARLY_H = 14.0
MIN_ORDER_LOADING_WINDOW_DURATION_H = 1.0
MAX_ORDER_LOADING_WINDOW_DURATION_H = 4.0
MIN_LOADING_DURATION_H = 0.5
MAX_LOADING_DURATION_H = 1.5
MIN_UNLOADING_DURATION_H = 0.5 # NEW
MAX_UNLOADING_DURATION_H = 1.5 # NEW

# Capacities and weights
MAX_TRUCK_CAPACITY_KG = 25000
MIN_TRUCK_CAPACITY_KG = 10000
MAX_ORDER_WEIGHT_KG = 12000
MIN_ORDER_WEIGHT_KG = 500
PRIORITIES_MAP = {1: 3, 2: 2, 3: 1}  # Mapping: Priority-Value -> Weight (higher is better)
                                      # Original Priority Values: 1=High, 2=Medium, 3=Low

# Factors for objective function
# Goal: Maximize (PRIORITY_WEIGHT_FACTOR * PriorityWeight - DISTANCE_COST_FACTOR * Distance)
PRIORITY_WEIGHT_FACTOR = 10000
DISTANCE_COST_FACTOR = 1

OUTPUT_DIR = "optimierungs_ergebnisse_dispo" # Adjusted for this script

# --- 2. Class Definitions ---
class Truck:
    def __init__(self, truck_id, location_x, location_y, capacity_kg, available_from_h, available_until_h):
        self.truck_id = truck_id
        self.location = (location_x, location_y)
        self.capacity_kg = capacity_kg
        self.available_from_h = available_from_h
        self.available_until_h = available_until_h
        # TODO: Extension with specific truck properties (e.g. cooler (bool), tarp (bool), hazmat_class (str/int)).
        # self.properties = {"cooler": False, "tarp": True, ...}

    def __repr__(self):
        return (f"Truck(ID: {self.truck_id}, Location: {self.location}, Cap: {self.capacity_kg}kg, "
                f"Available: {self.available_from_h:.2f}h - {self.available_until_h:.2f}h)")

class Order:
    def __init__(self, order_id, loading_site_x, loading_site_y, unloading_site_x, unloading_site_y,
                 weight_kg, loading_window_early_h, loading_window_late_h, loading_duration_h, unloading_duration_h, priority): # unloading_duration_h added
        self.order_id = order_id
        self.loading_site = (loading_site_x, loading_site_y)
        self.unloading_site = (unloading_site_x, unloading_site_y)
        self.weight_kg = weight_kg
        self.loading_window_early_h = loading_window_early_h
        self.loading_window_late_h = loading_window_late_h
        self.loading_duration_h = loading_duration_h
        self.unloading_duration_h = unloading_duration_h # NEW
        self.priority = priority
        # TODO: Extension with specific order requirements (e.g. requires_cooler (bool), hazmat (bool)).
        # self.requirements = {"requires_cooler": False, ...}

    def __repr__(self):
        return (f"Order(ID: {self.order_id}, Load: {self.loading_site}, Unload: {self.unloading_site}, Weight: {self.weight_kg}kg, "
                f"Window: {self.loading_window_early_h:.2f}h-{self.loading_window_late_h:.2f}h, "
                f"LoadDur: {self.loading_duration_h:.2f}h, UnloadDur: {self.unloading_duration_h:.2f}h, Prio: {self.priority})") # unloading_duration_h added

# --- 3. Helper Functions ---
def calculate_distance(point1, point2):
    """
    Calculate the distance between two geographic points using the Haversine formula.
    Points are expected to be (latitude, longitude) tuples.
    Returns distance in kilometers.
    """
    lat1, lon1 = point1
    lat2, lon2 = point2
    
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    
    # Calculate the distance
    distance_km = c * r
    
    return round(distance_km, 2)

def calculate_travel_time_h(distance_km):
    if AVERAGE_SPEED_KMH <= 0:
        return float('inf')
    return distance_km / AVERAGE_SPEED_KMH

def data_to_csv_string(data_list_objects, class_name):
    if not data_list_objects:
        return f"Keine Daten für {class_name} vorhanden.\n"
    # Ensure all objects are of the same type or at least vars() applicable
    try:
        data_list_dicts = [vars(obj) for obj in data_list_objects]
        if not data_list_dicts: # If list is empty after filtering or initially empty
             return f"Keine serialisierbaren Daten für {class_name} vorhanden.\n"
    except TypeError:
        return f"Nicht serialisierbare Objekte in {class_name}.\n"

    output = io.StringIO()
    # Take field names from first object, if available
    field_names = list(data_list_dicts[0].keys()) if data_list_dicts else []
    if not field_names:
        return f"Keine Feldnamen für {class_name} ermittelbar.\n"

    writer = csv.DictWriter(output, fieldnames=field_names)
    writer.writeheader()
    writer.writerows(data_list_dicts)
    return output.getvalue()

def save_csv_file(csv_string, filename_prefix):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.csv"
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
        full_path = os.path.join(OUTPUT_DIR, filename)
        with open(full_path, 'w', newline='', encoding='utf-8') as f:
            f.write(csv_string)
        print(f"Daten erfolgreich gespeichert in: {full_path}")
        return True
    except IOError as e:
        print(f"Fehler beim Speichern der Datei {filename}: {e}")
        return False

# --- 4. Data Generation ---

def generate_european_coordinates():
    """
    Generate realistic coordinates for Germany, Netherlands, France, and Belgium.
    Returns (latitude, longitude) tuple.
    """
    # Define bounding boxes for each country (approximate lat/lng bounds)
    countries = {
        'germany': {
            'lat_min': 47.3, 'lat_max': 55.1,
            'lng_min': 5.9, 'lng_max': 15.0,
            'weight': 0.4  # 40% of points in Germany
        },
        'netherlands': {
            'lat_min': 50.8, 'lat_max': 53.6,
            'lng_min': 3.4, 'lng_max': 7.2,
            'weight': 0.2  # 20% of points in Netherlands
        },
        'france': {
            'lat_min': 42.3, 'lat_max': 51.1,
            'lng_min': -4.8, 'lng_max': 8.2,
            'weight': 0.25  # 25% of points in France
        },
        'belgium': {
            'lat_min': 49.5, 'lat_max': 51.5,
            'lng_min': 2.5, 'lng_max': 6.4,
            'weight': 0.15  # 15% of points in Belgium
        }
    }
    
    # Choose country based on weights
    country_names = list(countries.keys())
    weights = [countries[c]['weight'] for c in country_names]
    chosen_country = random.choices(country_names, weights=weights)[0]
    
    # Generate coordinates within the chosen country
    country_bounds = countries[chosen_country]
    lat = round(random.uniform(country_bounds['lat_min'], country_bounds['lat_max']), 4)
    lng = round(random.uniform(country_bounds['lng_min'], country_bounds['lng_max']), 4)
    
    return lat, lng

def generate_truck_data(count):
    trucks = []
    for i in range(1, count + 1):
        available_from = round(random.uniform(MIN_TRUCK_AVAILABLE_FROM_H, MAX_TRUCK_AVAILABLE_FROM_H), 2)
        available_until = round(available_from + random.uniform(MIN_TRUCK_AVAILABLE_DURATION_H, MAX_TRUCK_AVAILABLE_DURATION_H), 2)
        
        # Generate realistic European coordinates
        location_lat, location_lng = generate_european_coordinates()
        
        trucks.append(Truck(
            truck_id=f"LKW{i}",
            location_x=location_lat,  # Now using latitude
            location_y=location_lng,  # Now using longitude
            capacity_kg=random.randint(MIN_TRUCK_CAPACITY_KG // 1000, MAX_TRUCK_CAPACITY_KG // 1000) * 1000,
            available_from_h=available_from,
            available_until_h=available_until
        ))
    return trucks

def generate_order_data(count):
    orders = []
    for i in range(1, count + 1):
        loading_window_early = round(random.uniform(MIN_ORDER_LOADING_WINDOW_EARLY_H, MAX_ORDER_LOADING_WINDOW_EARLY_H), 2)
        loading_duration = round(random.uniform(MIN_LOADING_DURATION_H, MAX_LOADING_DURATION_H), 2)
        unloading_duration = round(random.uniform(MIN_UNLOADING_DURATION_H, MAX_UNLOADING_DURATION_H), 2) # NEW
        
        # Revised logic for loading window end:
        # 1. The minimum duration of the window must cover the loading duration AND respect MIN_ORDER_LOADING_WINDOW_DURATION_H.
        min_effective_window_duration = max(loading_duration, MIN_ORDER_LOADING_WINDOW_DURATION_H)
        
        # 2. The maximum duration of the window is determined by MAX_ORDER_LOADING_WINDOW_DURATION_H,
        #    but must be at least as large as the min_effective_window_duration.
        #    This prevents MAX_ORDER_LOADING_WINDOW_DURATION_H from being ignored when it's very small,
        #    but ensures that the window is still long enough for the loading duration.
        max_effective_window_duration = max(min_effective_window_duration, MAX_ORDER_LOADING_WINDOW_DURATION_H)

        # 3. Generate a random window duration in the valid range.
        #    If min_effective_window_duration >= max_effective_window_duration (e.g. when MAX_ORDER_LOADING_WINDOW_DURATION_H
        #    was configured too small or equals min_effective_window_duration),
        #    the window duration is set to min_effective_window_duration to guarantee validity.
        if min_effective_window_duration >= max_effective_window_duration:
            generated_window_duration = min_effective_window_duration
        else:
            generated_window_duration = round(random.uniform(min_effective_window_duration, max_effective_window_duration), 2)
            
        loading_window_late = round(loading_window_early + generated_window_duration, 2)

        # Generate realistic European coordinates for both loading and unloading sites
        loading_lat, loading_lng = generate_european_coordinates()
        unloading_lat, unloading_lng = generate_european_coordinates()

        orders.append(Order(
            order_id=f"AUF{i}",
            loading_site_x=loading_lat,    # Now using latitude
            loading_site_y=loading_lng,    # Now using longitude
            unloading_site_x=unloading_lat,  # Now using latitude
            unloading_site_y=unloading_lng,  # Now using longitude
            weight_kg=random.randint(MIN_ORDER_WEIGHT_KG // 100, MAX_ORDER_WEIGHT_KG // 100) * 100,
            loading_window_early_h=loading_window_early,
            loading_window_late_h=loading_window_late,
            loading_duration_h=loading_duration,
            unloading_duration_h=unloading_duration, # NEW
            priority=random.choice(list(PRIORITIES_MAP.keys()))
        ))
    return orders

# --- 5. LP Modeling Functions ---
def determine_permissible_pairs_and_values(truck_list, order_list):
    """
    Determines permissible truck-order pairs and calculates associated values.
    A pair is permissible if capacity and the entire time planning (approach, loading,
    transport, unloading) fit.
    """
    permissible_pairs = {}
    print("\nErmittle zulässige LKW-Auftrag-Paare und zugehörige Werte (erweiterte Zeitprüfung):")
    for truck in truck_list:
        for order in order_list:
            # 1. Capacity check
            if truck.capacity_kg < order.weight_kg:
                continue
            
            # TODO: Here insert check of specific truck properties against order requirements.
            # Example: if order.requirements.get("requires_cooler") and not truck.properties.get("cooler"):
            #               continue

            # 2. Time calculations for the entire tour
            approach_distance = calculate_distance(truck.location, order.loading_site)
            approach_time_h = calculate_travel_time_h(approach_distance)
            
            arrival_loading_site_truck_h = truck.available_from_h + approach_time_h
            
            # Earliest possible loading start considering truck arrival time and order window
            loading_start_calc_h = max(arrival_loading_site_truck_h, order.loading_window_early_h)
            
            # Latest loading start according to order window
            latest_loading_start_order_h = order.loading_window_late_h - order.loading_duration_h
            
            if loading_start_calc_h > latest_loading_start_order_h + 0.01: # Epsilon for rounding
                continue # Loading start no longer possible in the (adjusted) window of the order

            loading_end_calc_h = loading_start_calc_h + order.loading_duration_h

            # NEW: Time calculation for transport and unloading
            transport_distance = calculate_distance(order.loading_site, order.unloading_site)
            transport_time_h = calculate_travel_time_h(transport_distance)
            
            arrival_unloading_site_calc_h = loading_end_calc_h + transport_time_h
            unloading_end_calc_h = arrival_unloading_site_calc_h + order.unloading_duration_h

            # 3. Complete time window check
            # a) Loading end must be before end of order loading window -> This check is redundant,
            #    since the check on `latest_loading_start_order_h` already ensures that the loading start
            #    is early enough to complete the loading duration within the window.
            # if loading_end_calc_h > order.loading_window_late_h + 0.01: # Epsilon
            #      continue
            
            # b) Entire tour (end of unloading) must be before end of truck availability
            if unloading_end_calc_h > truck.available_until_h + 0.01: # Epsilon
                continue
            
            total_distance_for_order = approach_distance + transport_distance
            
            permissible_pairs[(truck.truck_id, order.order_id)] = {
                "distanz_anfahrt": approach_distance,
                "distanz_transport": transport_distance,
                "distanz_gesamt_fuer_auftrag": total_distance_for_order,
                "prio_original": order.priority,
                "prio_gewicht": PRIORITIES_MAP.get(order.priority, 0),
                "anfahrt_lkw_h": arrival_loading_site_truck_h, # informative
                "ladebeginn_calc_h": loading_start_calc_h,
                "ladeende_calc_h": loading_end_calc_h,
                "ankunft_entladestelle_calc_h": arrival_unloading_site_calc_h, # informative
                "entladung_ende_calc_h": unloading_end_calc_h, # important for check and info
                "gesamtdauer_auftrag_ab_lkw_start_h": unloading_end_calc_h - truck.available_from_h # informative
            }
    print(f"Anzahl zulässiger LKW-Auftrag-Paare nach erweiterter Prüfung: {len(permissible_pairs)}")
    return permissible_pairs

def create_lp_model(truck_list, order_list, permissible_pairs_with_values):
    """Creates the linear optimization problem with PuLP."""
    
    prob = pulp.LpProblem("Truck_Order_Assignment_Dispo", pulp.LpMaximize) # Name adjusted

    # Decision variables: x_ij = 1 if truck i takes order j, otherwise 0
    x_vars = pulp.LpVariable.dicts("x", 
                                   permissible_pairs_with_values.keys(), 
                                   cat='Binary')

    # Objective function: Maximize Sum( (PriorityFactor * PriorityWeight - DistanceFactor * Distance) * x_ij )
    # This maximizes the "utility" of each assignment.
    objective_components = []
    for pair_key, values_dict in permissible_pairs_with_values.items():
        priority_reward = PRIORITY_WEIGHT_FACTOR * values_dict["prio_gewicht"]
        # TODO: Extension of cost calculation with more detailed factors (toll, fuel etc.),
        # if this data is made available per truck-order pair.
        # Currently: distance_penalty = DISTANCE_COST_FACTOR * values_dict["distanz_gesamt_fuer_auftrag"]
        # In future could be: total_cost_penalty = calculate_total_costs(truck, order, values_dict)
        distance_penalty = DISTANCE_COST_FACTOR * values_dict["distanz_gesamt_fuer_auftrag"]
        net_value_assignment = priority_reward - distance_penalty
        objective_components.append(net_value_assignment * x_vars[pair_key])
        
    prob += pulp.lpSum(objective_components), "Maximize_Weighted_Utility"

    # Constraints:
    # 1. Each order is assigned to at most one truck.
    for order in order_list:
        prob += pulp.lpSum([x_vars[(truck.truck_id, order.order_id)] 
                            for truck in truck_list 
                            if (truck.truck_id, order.order_id) in x_vars]) <= 1, f"Order_{order.order_id}_max_once"

    # 2. Each truck takes at most one order.
    for truck in truck_list:
        prob += pulp.lpSum([x_vars[(truck.truck_id, order.order_id)] 
                            for order in order_list 
                            if (truck.truck_id, order.order_id) in x_vars]) <= 1, f"Truck_{truck.truck_id}_max_one_order"
    
    return prob, x_vars

# --- 6. Solution and Result Functions ---
def solve_optimization_problem(problem):
    print("\nStarte PuLP Optimierung...")
    # problem.writeLP("TruckAssignmentModel_Dispo.lp") # Optional for debugging the LP model
    status = problem.solve() # Uses default solver (CBC if nothing else configured)
    print(f"PuLP Optimierungsstatus: {pulp.LpStatus[status]}")
    return status

def extract_and_show_results(prob_obj, x_variables_dict, truck_list, order_list, permissible_pairs_with_values, status):
    assigned_orders_details = []
    unassigned_orders_obj = list(order_list) # Copy for modification
    truck_utilization = {truck.truck_id: {"zugewiesener_auftrag": None, "details": None} for truck in truck_list}
    total_objective_value = 0
    total_distance_final_km = 0
    number_of_assigned_orders = 0

    if status == pulp.LpStatusOptimal or status == pulp.LpStatusFeasible: # Feasible also OK, if e.g. time limit reached
        print("\n--- Optimale/Gefundene Zuweisungsergebnisse ---")
        total_objective_value = pulp.value(prob_obj.objective) if prob_obj.objective else 0
        print(f"Maximierter Gesamtnutzwert (Zielfunktion): {total_objective_value:.2f}")
        
        active_assignments_keys = [key_tuple for key_tuple, pulp_var in x_variables_dict.items() if pulp_var.varValue > 0.5]
        number_of_assigned_orders = len(active_assignments_keys)
        print(f"Anzahl getätigter Zuweisungen: {number_of_assigned_orders}")

        for truck_id, order_id in active_assignments_keys:
            values_info = permissible_pairs_with_values.get((truck_id, order_id))
            truck_obj = next((t for t in truck_list if t.truck_id == truck_id), None)
            order_obj = next((o for o in order_list if o.order_id == order_id), None)

            if not values_info or not truck_obj or not order_obj:
                print(f"Warnung: Dateninkonsistenz für Zuweisung {truck_id}-{order_id}. Übersprungen.")
                continue

            detail = {
                "lkw_id": truck_id,
                "auftrag_id": order_id,
                "anfahrt_dist_km": values_info["distanz_anfahrt"],
                "transport_dist_km": values_info["distanz_transport"],
                "gesamtdistanz_fuer_auftrag_km": values_info["distanz_gesamt_fuer_auftrag"],
                "ladebeginn_h": values_info["ladebeginn_calc_h"],
                "ladeende_h": values_info["ladeende_calc_h"],
                "entladung_ende_h": values_info["entladung_ende_calc_h"], # NEW for info
                "auftrag_prio_original": order_obj.priority,
                "auftrag_prio_gewicht": values_info["prio_gewicht"],
                "auftrag_gewicht_kg": order_obj.weight_kg,
                "lkw_kapazitaet_kg": truck_obj.capacity_kg,
                "lkw_verfuegbar_bis_h": truck_obj.available_until_h # NEW for info
            }
            assigned_orders_details.append(detail)
            truck_utilization[truck_id]["zugewiesener_auftrag"] = order_id
            truck_utilization[truck_id]["details"] = detail
            total_distance_final_km += values_info["distanz_gesamt_fuer_auftrag"]
            
            if order_obj in unassigned_orders_obj:
                unassigned_orders_obj.remove(order_obj)

        assigned_orders_details.sort(key=lambda x: (x["auftrag_prio_original"], x["lkw_id"]))
        for detail in assigned_orders_details:
            print(f"  LKW {detail['lkw_id']} -> Auftrag {detail['auftrag_id']} "
                  f"(Prio: {detail['auftrag_prio_original']}, Gew: {detail['auftrag_gewicht_kg']}kg, "
                  f"Dist: {detail['gesamtdistanz_fuer_auftrag_km']:.2f}km, "
                  f"Lade: {detail['ladebeginn_h']:.2f}h-{detail['ladeende_h']:.2f}h, "
                  f"EntlEnde: {detail['entladung_ende_h']:.2f}h vs LKW Ende: {detail['lkw_verfuegbar_bis_h']:.2f}h)")
        if assigned_orders_details:
            print(f"Summe der Gesamtdistanzen für zugewiesene Aufträge: {total_distance_final_km:.2f} km")
            print(f"Durchschnittliche Distanz pro zugewiesenem Auftrag: {(total_distance_final_km / number_of_assigned_orders) if number_of_assigned_orders > 0 else 0:.2f} km")

    elif status == pulp.LpStatusInfeasible:
        print("Problem ist unlösbar (Infeasible). Keine gültige Zuweisung unter den gegebenen Bedingungen möglich.")
    elif status == pulp.LpStatusNotSolved:
        print("Problem wurde nicht gelöst (Not Solved). Möglicherweise wurde der Solver nicht richtig aufgerufen oder es gab einen internen Fehler.")
    elif status == pulp.LpStatusUndefined:
         print("Lösungsstatus ist undefiniert (Undefined). Dies kann auf Probleme im Modell oder Solver hindeuten.")
    else: # e.g. LpStatusNoSolutionFound
        print(f"Optimierung nicht erfolgreich oder keine Lösung gefunden. Status: {pulp.LpStatus[status]}")


    print("\n--- Nicht zugewiesene Aufträge ---")
    if unassigned_orders_obj:
        unassigned_orders_obj.sort(key=lambda a: (a.priority, a.order_id))
        for order in unassigned_orders_obj:
            print(f"  Auftrag {order.order_id} (Prio: {order.priority}, Gew: {order.weight_kg}kg, "
                  f"Fenster: {order.loading_window_early_h:.2f}-{order.loading_window_late_h:.2f}, "
                  f"Ladedauer: {order.loading_duration_h:.2f}h, Entladedauer: {order.unloading_duration_h:.2f}h)")
    else:
        if number_of_assigned_orders == len(order_list) and len(order_list) > 0 :
            print("  Alle Aufträge konnten zugewiesen werden.")
        elif not order_list:
             print("  Keine Aufträge vorhanden.")
        else: # Should not happen if correctly handled above
             print("  Keine nicht zugewiesenen Aufträge (oder alle zugewiesen).")
        
    return assigned_orders_details, unassigned_orders_obj, truck_utilization

def results_to_csv_strings_lp(assigned_details, unassigned_obj, truck_utilization_info, truck_list):
    assigned_csv = io.StringIO()
    if assigned_details:
        field_names_a = list(assigned_details[0].keys())
        writer_a = csv.DictWriter(assigned_csv, fieldnames=field_names_a)
        writer_a.writeheader()
        writer_a.writerows(assigned_details)
    else:
        assigned_csv.write("Keine Aufträge zugewiesen.\n")

    unassigned_csv = io.StringIO()
    if unassigned_obj:
        unassigned_dicts = [vars(obj) for obj in unassigned_obj]
        field_names_u = list(unassigned_dicts[0].keys()) if unassigned_dicts else []
        if field_names_u:
             writer_u = csv.DictWriter(unassigned_csv, fieldnames=field_names_u)
             writer_u.writeheader()
             writer_u.writerows(unassigned_dicts)
        else:
            unassigned_csv.write("Keine nicht zugewiesenen Aufträge zu melden (oder keine Felder definiert).\n")
    else:
        unassigned_csv.write("Alle Aufträge wurden zugewiesen oder es gab keine Aufträge.\n")
        
    truck_util_csv = io.StringIO()
    truck_util_data = []
    for truck in truck_list: # Iterate over original truck list to capture all trucks
        utilization_truck_specific = truck_utilization_info.get(truck.truck_id, {})
        details_dict = utilization_truck_specific.get("details") 
        
        truck_data_entry = {
            "lkw_id": truck.truck_id,
            "kapazitaet_kg": truck.capacity_kg,
            "verfuegbar_ab_h": truck.available_from_h,
            "verfuegbar_bis_h": truck.available_until_h,
            "zugewiesener_auftrag_id": utilization_truck_specific.get("zugewiesener_auftrag"), # Can be None
            "anfahrt_dist_km": details_dict.get("anfahrt_dist_km") if details_dict else None,
            "transport_dist_km": details_dict.get("transport_dist_km") if details_dict else None,
            "gesamtdistanz_fuer_auftrag_km": details_dict.get("gesamtdistanz_fuer_auftrag_km") if details_dict else None,
            "ladebeginn_h": details_dict.get("ladebeginn_h") if details_dict else None,
            "ladeende_h": details_dict.get("ladeende_h") if details_dict else None,
            "entladung_ende_h": details_dict.get("entladung_ende_h") if details_dict else None # NEW
        }
        truck_util_data.append(truck_data_entry)
    
    if truck_util_data:
        field_names_truck = list(truck_util_data[0].keys())
        writer_truck = csv.DictWriter(truck_util_csv, fieldnames=field_names_truck)
        writer_truck.writeheader()
        writer_truck.writerows(truck_util_data)
    else:
        truck_util_csv.write("Keine LKW-Daten vorhanden.\n")

    return assigned_csv.getvalue(), unassigned_csv.getvalue(), truck_util_csv.getvalue()

# --- 7. Main Function ---
def main_dispo():
    print("=== LKW Zuweisungs-System mit Linearer Optimierung (PuLP) - Dispo Version ===")
    
    print(f"\nKonfiguration der Zielfunktion:")
    print(f"  PRIORITY_WEIGHT_FACTOR: {PRIORITY_WEIGHT_FACTOR} (Belohnung pro Prio-Gewichtspunkt)")
    print(f"  DISTANCE_COST_FACTOR: {DISTANCE_COST_FACTOR} (Strafe pro km Distanz)")
    print(f"  PRIORITIES_MAP (Prio -> Gewicht): {PRIORITIES_MAP}")
    print(f"  NUM_TRUCKS: {NUM_TRUCKS}, NUM_ORDERS: {NUM_ORDERS} (Ziel: 200 LKWs, 300 Aufträge)")


    # 1. Data generation
    print("\n1. Generiere Demo-Datensätze...")
    truck_list = generate_truck_data(NUM_TRUCKS)
    order_list = generate_order_data(NUM_ORDERS)
    print(f"   {len(truck_list)} LKWs generiert.")
    print(f"   {len(order_list)} Aufträge generiert.")

    save_csv_file(data_to_csv_string(truck_list, "LKW"), "rohdaten_lkw")
    save_csv_file(data_to_csv_string(order_list, "Auftrag"), "rohdaten_auftraege")

    # 2. Determine permissible pairs and values for objective function
    permissible_pairs_with_values = determine_permissible_pairs_and_values(truck_list, order_list)
    if not permissible_pairs_with_values:
        print("Keine zulässigen LKW-Auftrag-Paare gefunden. Abbruch der Optimierung.")
        print("Mögliche Gründe: Zu enge Zeitfenster, zu kurze LKW-Verfügbarkeiten, Kapazitätsprobleme oder Distanzen.")
        return

    # 3. Create LP model
    print("\n2. Erstelle Lineares Optimierungsmodell...")
    optimization_problem, x_decision_variables = create_lp_model(
        truck_list, order_list, permissible_pairs_with_values
    )

    # 4. Solve optimization problem
    print("\n3. Löse Optimierungsproblem...")
    status = solve_optimization_problem(optimization_problem)
    
    # 5. Extract and display results
    print("\n4. Extrahiere und zeige Ergebnisse...")
    assigned_details, unassigned_obj, truck_util = extract_and_show_results(
        optimization_problem, x_decision_variables, 
        truck_list, order_list, permissible_pairs_with_values, status
    )

    # 6. Save results as CSV
    print("\n5. Speichere Ergebnisse als CSV-Dateien...")
    if status == pulp.LpStatusOptimal or status == pulp.LpStatusFeasible :
        csv_assigned, csv_unassigned, csv_truck_util = results_to_csv_strings_lp(
            assigned_details, unassigned_obj, truck_util, truck_list
        )
        save_csv_file(csv_assigned, "ergebnisse_zugewiesene_auftraege")
        save_csv_file(csv_unassigned, "ergebnisse_nicht_zugewiesene_auftraege")
        save_csv_file(csv_truck_util, "ergebnisse_lkw_auslastung")
    else:
        print("Keine Ergebnisse zum Speichern aufgrund des Optimierungsstatus.")

    print("\n=== Programm beendet ===")

if __name__ == "__main__":
    main_dispo() 