#!/usr/bin/env python3
"""
LKW-Auftragszuordnung System
Einfacher Greedy-Algorithmus für optimale Zuordnung von LKWs zu Transport-Aufträgen
"""

import csv
import math
import io
from dataclasses import dataclass
from typing import List, Optional

# Demo-Daten als CSV-Strings (können einfach kopiert werden)
TRUCKS_CSV = """truck_id,lat,lon,capacity,current_load,type
LKW001,52.5200,13.4050,25.0,0.0,Standard
LKW002,52.4800,13.3900,40.0,0.0,Groß
LKW003,52.5100,13.4200,18.0,5.0,Klein
LKW004,52.5300,13.3800,35.0,0.0,Standard
LKW005,52.4900,13.4100,22.0,3.0,Standard
LKW006,52.5000,13.3950,45.0,0.0,Groß
LKW007,52.5150,13.4150,20.0,8.0,Klein
LKW008,52.4950,13.4000,30.0,0.0,Standard
LKW009,52.5250,13.3900,25.0,12.0,Standard
LKW010,52.5050,13.4050,28.0,0.0,Standard"""

ORDERS_CSV = """order_id,pickup_lat,pickup_lon,delivery_lat,delivery_lon,volume,priority,customer
AUF001,52.5180,13.4080,52.5400,13.3600,8.5,high,MegaCorp
AUF002,52.4850,13.3950,52.5100,13.4300,15.2,normal,TechStart
AUF003,52.5080,13.4120,52.4800,13.3800,22.0,normal,LogiFlow
AUF004,52.5220,13.3980,52.5300,13.4200,6.8,urgent,QuickServ
AUF005,52.4980,13.4000,52.5000,13.4150,12.5,normal,StoreChain
AUF006,52.5120,13.4050,52.5350,13.3750,18.7,high,GlobalTrade
AUF007,52.5000,13.3900,52.4900,13.4100,9.3,normal,LocalBiz
AUF008,52.5280,13.4100,52.5150,13.3950,25.8,normal,HeavyGoods
AUF009,52.4920,13.4080,52.5200,13.4000,7.1,urgent,ExpressLtd
AUF010,52.5150,13.3850,52.5050,13.4200,14.6,normal,RegionalCo
AUF011,52.5040,13.4120,52.5280,13.3900,11.2,high,PrimeTrans
AUF012,52.5190,13.3920,52.4950,13.4050,16.9,normal,CityLogistics
AUF013,52.4960,13.4030,52.5100,13.3880,20.4,normal,MetroFreight
AUF014,52.5110,13.4000,52.5220,13.4100,13.7,urgent,RushDelivery
AUF015,52.5060,13.3970,52.5180,13.4080,19.1,high,TopClient"""

@dataclass
class Truck:
    truck_id: str
    lat: float
    lon: float
    capacity: float
    current_load: float
    truck_type: str
    
    @property
    def available_capacity(self) -> float:
        return self.capacity - self.current_load
    
    @property
    def position(self) -> tuple:
        return (self.lat, self.lon)

@dataclass 
class Order:
    order_id: str
    pickup_lat: float
    pickup_lon: float
    delivery_lat: float
    delivery_lon: float
    volume: float
    priority: str
    customer: str
    assigned_truck: Optional[str] = None
    
    @property
    def pickup_position(self) -> tuple:
        return (self.pickup_lat, self.pickup_lon)
    
    @property
    def delivery_position(self) -> tuple:
        return (self.delivery_lat, self.delivery_lon)

@dataclass
class Assignment:
    truck_id: str
    order_id: str
    distance_km: float
    score: float
    
def calculate_distance(pos1: tuple, pos2: tuple) -> float:
    """
    Berechnet die Entfernung zwischen zwei GPS-Koordinaten in km (Haversine-Formel)
    """
    lat1, lon1 = math.radians(pos1[0]), math.radians(pos1[1])
    lat2, lon2 = math.radians(pos2[0]), math.radians(pos2[1])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Erdradius in km
    radius = 6371
    return radius * c

def calculate_score(truck: Truck, order: Order) -> float:
    """
    Berechnet einen Score für die Zuordnung (niedrigerer Wert = besser)
    Berücksichtigt: Entfernung, Priorität, Kapazitätsauslastung
    """
    distance = calculate_distance(truck.position, order.pickup_position)
    
    # Prioritäts-Gewichtung
    priority_weight = {
        'urgent': 0.5,   # Dringend = geringere Gewichtung (bevorzugt)
        'high': 0.7,
        'normal': 1.0
    }
    
    # Kapazitätsauslastung (besser wenn LKW gut ausgelastet wird)
    capacity_utilization = order.volume / truck.capacity
    capacity_bonus = 1.0 - capacity_utilization  # Bonus für gute Auslastung
    
    score = distance * priority_weight.get(order.priority, 1.0) + capacity_bonus
    return score

def load_data():
    """Lädt die Demo-Daten aus den CSV-Strings"""
    trucks = []
    orders = []
    
    # LKWs laden
    truck_reader = csv.DictReader(io.StringIO(TRUCKS_CSV))
    for row in truck_reader:
        truck = Truck(
            truck_id=row['truck_id'],
            lat=float(row['lat']),
            lon=float(row['lon']),
            capacity=float(row['capacity']),
            current_load=float(row['current_load']),
            truck_type=row['type']
        )
        trucks.append(truck)
    
    # Aufträge laden
    order_reader = csv.DictReader(io.StringIO(ORDERS_CSV))
    for row in order_reader:
        order = Order(
            order_id=row['order_id'],
            pickup_lat=float(row['pickup_lat']),
            pickup_lon=float(row['pickup_lon']),
            delivery_lat=float(row['delivery_lat']),
            delivery_lon=float(row['delivery_lon']),
            volume=float(row['volume']),
            priority=row['priority'],
            customer=row['customer']
        )
        orders.append(order)
    
    return trucks, orders

def assign_orders_greedy(trucks: List[Truck], orders: List[Order]) -> List[Assignment]:
    """
    Greedy-Algorithmus: Weist jedem LKW den besten verfügbaren Auftrag zu
    """
    assignments = []
    available_orders = orders.copy()
    
    # Sortiere LKWs nach verfügbarer Kapazität (größte zuerst)
    sorted_trucks = sorted(trucks, key=lambda t: t.available_capacity, reverse=True)
    
    for truck in sorted_trucks:
        best_order = None
        best_score = float('inf')
        
        # Finde den besten Auftrag für diesen LKW
        for order in available_orders:
            # Prüfe Kapazität
            if order.volume <= truck.available_capacity:
                score = calculate_score(truck, order)
                
                if score < best_score:
                    best_score = score
                    best_order = order
        
        # Zuordnung durchführen
        if best_order:
            distance = calculate_distance(truck.position, best_order.pickup_position)
            assignment = Assignment(
                truck_id=truck.truck_id,
                order_id=best_order.order_id,
                distance_km=distance,
                score=best_score
            )
            assignments.append(assignment)
            
            # Auftrag als vergeben markieren
            best_order.assigned_truck = truck.truck_id
            available_orders.remove(best_order)
            
            # Truck-Beladung aktualisieren
            truck.current_load += best_order.volume
    
    return assignments, available_orders

def print_results(assignments: List[Assignment], unassigned_orders: List[Order], 
                 trucks: List[Truck], orders: List[Order]):
    """Gibt die Ergebnisse formatiert aus"""
    
    print("=" * 80)
    print("🚛 LKW-AUFTRAGSZUORDNUNG - ERGEBNISSE")
    print("=" * 80)
    
    # Zuordnungen anzeigen
    print(f"\n✅ ERFOLGREICHE ZUORDNUNGEN ({len(assignments)}):")
    print("-" * 60)
    
    for assignment in sorted(assignments, key=lambda a: a.truck_id):
        # Finde entsprechende Objekte für Details
        truck = next(t for t in trucks if t.truck_id == assignment.truck_id)
        order = next(o for o in orders if o.order_id == assignment.order_id)
        
        print(f"{assignment.truck_id:>7} → {assignment.order_id:<7} | "
              f"Entfernung: {assignment.distance_km:>5.1f}km | "
              f"Volumen: {order.volume:>5.1f}t | "
              f"Priorität: {order.priority:>6} | "
              f"Kunde: {order.customer}")
    
    # Nicht zugeordnete Aufträge
    if unassigned_orders:
        print(f"\n❌ NICHT ZUGEORDNETE AUFTRÄGE ({len(unassigned_orders)}):")
        print("-" * 60)
        for order in unassigned_orders:
            print(f"{order.order_id} | Volumen: {order.volume:>5.1f}t | "
                  f"Priorität: {order.priority:>6} | Kunde: {order.customer}")
    
    # Statistiken
    print(f"\n📊 STATISTIKEN:")
    print("-" * 30)
    total_volume_assigned = sum(next(o for o in orders if o.order_id == a.order_id).volume 
                               for a in assignments)
    total_volume_orders = sum(o.volume for o in orders)
    avg_distance = sum(a.distance_km for a in assignments) / len(assignments) if assignments else 0
    
    print(f"Zugeordnete Aufträge: {len(assignments):>3} / {len(orders)}")
    print(f"Zugeordnetes Volumen: {total_volume_assigned:>6.1f}t / {total_volume_orders:.1f}t")
    print(f"Durchschnittliche Entfernung: {avg_distance:>5.1f}km")
    
    # LKW-Auslastung
    print(f"\n🚛 LKW-AUSLASTUNG:")
    print("-" * 40)
    for truck in sorted(trucks, key=lambda t: t.truck_id):
        utilization = (truck.current_load / truck.capacity) * 100
        assigned_order = next((a.order_id for a in assignments if a.truck_id == truck.truck_id), "---")
        print(f"{truck.truck_id}: {truck.current_load:>5.1f}t / {truck.capacity:>5.1f}t "
              f"({utilization:>5.1f}%) → {assigned_order}")

def save_results_csv(assignments: List[Assignment], filename: str = "zuordnung_ergebnisse.csv"):
    """Speichert die Ergebnisse als CSV-Datei"""
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['LKW_ID', 'Auftrag_ID', 'Entfernung_km', 'Score'])
        
        for assignment in assignments:
            writer.writerow([
                assignment.truck_id,
                assignment.order_id,
                round(assignment.distance_km, 2),
                round(assignment.score, 3)
            ])
    
    print(f"\n💾 Ergebnisse gespeichert in: {filename}")

def main():
    """Hauptfunktion"""
    print("🚀 Starte LKW-Auftragszuordnung...")
    
    # Daten laden
    trucks, orders = load_data()
    print(f"✅ Daten geladen: {len(trucks)} LKWs, {len(orders)} Aufträge")
    
    # Zuordnung durchführen
    assignments, unassigned_orders = assign_orders_greedy(trucks, orders)
    
    # Ergebnisse anzeigen
    print_results(assignments, unassigned_orders, trucks, orders)
    
    # Optional: CSV speichern
    try:
        save_results_csv(assignments)
    except Exception as e:
        print(f"⚠️  CSV-Export fehlgeschlagen: {e}")
    
    print(f"\n🎯 Zuordnung abgeschlossen!")

if __name__ == "__main__":
    main()

# ===============================================================================
# DEMO-DATEN ZUM KOPIEREN:
# ===============================================================================

# TRUCKS_CSV (10 LKWs):
# truck_id,lat,lon,capacity,current_load,type
# LKW001,52.5200,13.4050,25.0,0.0,Standard
# LKW002,52.4800,13.3900,40.0,0.0,Groß
# ... (siehe TRUCKS_CSV Variable oben)

# ORDERS_CSV (15 Aufträge):  
# order_id,pickup_lat,pickup_lon,delivery_lat,delivery_lon,volume,priority,customer
# AUF001,52.5180,13.4080,52.5400,13.3600,8.5,high,MegaCorp
# AUF002,52.4850,13.3950,52.5100,13.4300,15.2,normal,TechStart
# ... (siehe ORDERS_CSV Variable oben)