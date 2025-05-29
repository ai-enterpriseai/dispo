# lkw_optimierung.py
# Python 3.x
# Benötigte Bibliothek: PuLP (pip install pulp)

import csv
import random
import math
import os
import pulp

# -------------------------------
# Datenklassen
# -------------------------------
class Truck:
    def __init__(self, id, capacity, lat, lon, avail_start, avail_end):
        self.id = id
        self.capacity = capacity
        self.lat = lat
        self.lon = lon
        self.avail_start = avail_start
        self.avail_end = avail_end

class Order:
    def __init__(self, id, weight, lat, lon, time_start, time_end, priority):
        self.id = id
        self.weight = weight
        self.lat = lat
        self.lon = lon
        self.time_start = time_start
        self.time_end = time_end
        self.priority = priority

# -------------------------------
# Hilfsfunktionen
# -------------------------------
def euclidean_distance(a_lat, a_lon, b_lat, b_lon):
    return math.hypot(a_lat - b_lat, a_lon - b_lon)

# CSV speichern
def save_csv(filename, fieldnames, rows):
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

# -------------------------------
# Demo-Datensatz generieren
# -------------------------------
def generate_demo_data(num_trucks=10, num_orders=15, seed=42):
    random.seed(seed)
    trucks = []
    orders = []
    # LKWs
    for i in range(1, num_trucks + 1):
        capacity = random.randint(20, 40)  # erhöhte Kapazität
        lat = random.uniform(0, 100)
        lon = random.uniform(0, 100)
        # Zeiten hier nur zur Vollständigkeit, aber nicht genutzt
        avail_start = 0
        avail_end = 100
        trucks.append(Truck(f"T{i}", capacity, lat, lon, avail_start, avail_end))
    # Aufträge
    for j in range(1, num_orders + 1):
        weight = random.randint(1, 10)
        lat = random.uniform(0, 100)
        lon = random.uniform(0, 100)
        time_start = 0
        time_end = 100
        priority = random.randint(1, 5)
        orders.append(Order(f"O{j}", weight, lat, lon, time_start, time_end, priority))
    return trucks, orders

# -------------------------------
# Optimierungsmodell aufbauen
# -------------------------------
def build_and_solve(trucks, orders):
    # Problem initialisieren
    prob = pulp.LpProblem("LKW_Zuweisung", pulp.LpMinimize)

    # Entscheidungsvariablen x[t,o] ∈ {0,1} für alle Kombinationen
    x = {}
    cost = {}
    for t in trucks:
        for o in orders:
            var = pulp.LpVariable(f"x_{t.id}_{o.id}", cat='Binary')
            x[(t.id, o.id)] = var
            d = euclidean_distance(t.lat, t.lon, o.lat, o.lon)
            cost[(t.id, o.id)] = d

    # Zielfunktion: Minimierung Gesamtstrecke gewichtet mit Priorität
    prob += pulp.lpSum(cost[(t.id, o.id)] * (6 - o.priority) * x[(t.id, o.id)]
                       for t in trucks for o in orders), "Minimiere_Strecke"

    # Jeder Auftrag genau einem LKW zugewiesen
    for o in orders:
        prob += pulp.lpSum(x[(t.id, o.id)] for t in trucks) == 1, f"AssignOrder_{o.id}"

    # Kapazitätsbeschränkung je LKW
    for t in trucks:
        prob += pulp.lpSum(o.weight * x[(t.id, o.id)] for o in orders) <= t.capacity, f"Cap_{t.id}"

    # Problem lösen
    solver = pulp.PULP_CBC_CMD(msg=True)
    result_status = prob.solve(solver)

    return prob, x, result_status

# -------------------------------
# Ergebnis verarbeiten und ausgeben
# -------------------------------
def process_results(trucks, orders, x, status):
    status_str = pulp.LpStatus[status]
    print(f"Optimierungsstatus: {status_str}\n")
    if status_str != 'Optimal':
        print("Keine optimale Lösung gefunden.")
        return

    assignments = []
    total_cost = 0.0
    utilization = {t.id: 0.0 for t in trucks}

    for (t_id, o_id), var in x.items():
        if var.value() > 0.5:
            t = next(t for t in trucks if t.id == t_id)
            o = next(o for o in orders if o.id == o_id)
            d = euclidean_distance(t.lat, t.lon, o.lat, o.lon)
            assignments.append({
                'truck_id': t_id,
                'order_id': o_id,
                'distance': round(d, 2),
                'weight': o.weight,
                'priority': o.priority
            })
            total_cost += d * (6 - o.priority)
            utilization[t_id] += o.weight

    # CSV speichern
    save_csv('assignments.csv', ['truck_id', 'order_id', 'distance', 'weight', 'priority'], assignments)
    print(f"Assignments saved to 'assignments.csv' (Anzahl: {len(assignments)})")

    # Metriken anzeigen
    print(f"Gesamtkosten (distanz*Gewichtung): {round(total_cost,2)}")
    print("Auslastung der LKWs:")
    for t in trucks:
        print(f" - {t.id}: {utilization[t.id]}/{t.capacity} Kapazität genutzt")

# -------------------------------
# Hauptablauf
# -------------------------------
def main():
    # Demo generieren, falls CSV nicht existiert
    csv_trucks = 'trucks.csv'
    csv_orders = 'orders.csv'
    if not os.path.exists(csv_trucks) or not os.path.exists(csv_orders):
        trucks, orders = generate_demo_data()
        save_csv(csv_trucks,
                 ['id','capacity','lat','lon','avail_start','avail_end'],
                 [{
                     'id': t.id,
                     'capacity': t.capacity,
                     'lat': t.lat,
                     'lon': t.lon,
                     'avail_start': t.avail_start,
                     'avail_end': t.avail_end
                 } for t in trucks])
        save_csv(csv_orders,
                 ['id','weight','lat','lon','time_start','time_end','priority'],
                 [{
                     'id': o.id,
                     'weight': o.weight,
                     'lat': o.lat,
                     'lon': o.lon,
                     'time_start': o.time_start,
                     'time_end': o.time_end,
                     'priority': o.priority
                 } for o in orders])
        print(f"Demo-Datensatz erstellt: '{csv_trucks}', '{csv_orders}'")
    else:
        trucks, orders = generate_demo_data()

    prob, x, status = build_and_solve(trucks, orders)
    process_results(trucks, orders, x, status)

if __name__ == '__main__':
    main()
