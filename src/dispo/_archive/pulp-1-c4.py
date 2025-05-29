#!/usr/bin/env python3
"""
LKW-Zuordnung mit Linearer Optimierung
======================================

Optimale Zuordnung von Transport-Aufträgen zu LKWs mittels Mixed Integer Linear Programming (MILP).
Verwendet PuLP für die mathematische Optimierung und berücksichtigt Kapazitäten, Zeitfenster und Kosten.

Benötigte Bibliotheken:
- pulp: pip install pulp

Autor: Optimierungssystem Demo
Version: 3.0
"""

import csv
import math
import sys
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from enum import Enum
from datetime import datetime, timedelta

# Lineare Optimierung
try:
    import pulp
    PULP_AVAILABLE = True
except ImportError:
    PULP_AVAILABLE = False
    print("⚠️  PuLP nicht installiert. Installiere mit: pip install pulp")

# ===============================================================================
# KONFIGURATION UND KONSTANTEN
# ===============================================================================

class Priority(Enum):
    """Auftragsprioritäten mit numerischen Werten für Optimierung"""
    URGENT = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4

class TruckType(Enum):
    """LKW-Typen mit verschiedenen Eigenschaften"""
    KLEIN = "Klein"
    STANDARD = "Standard"
    GROSS = "Groß"
    SPEZIAL = "Spezial"

# Optimierungsparameter
MAX_SOLVER_TIME = 300  # Maximale Lösungszeit in Sekunden
COST_PER_KM = 1.5      # Euro pro Kilometer
BIG_M = 999999.0       # Sehr große Zahl statt infinity für nicht-machbare Zuordnungen
PRIORITY_COST_MULTIPLIER = {
    Priority.URGENT: 0.5,   # Dringende Aufträge sind günstiger (bevorzugt)
    Priority.HIGH: 0.7,
    Priority.NORMAL: 1.0,
    Priority.LOW: 1.3
}

# ===============================================================================
# DATENMODELL
# ===============================================================================

@dataclass
class TimeWindow:
    """Zeitfenster für Aufträge"""
    earliest_start: float  # Stunden ab Tagesbeginn
    latest_end: float      # Spätester Endtermin
    
    def __post_init__(self):
        if self.earliest_start < 0 or self.latest_end <= self.earliest_start:
            raise ValueError(f"Ungültiges Zeitfenster: {self.earliest_start} - {self.latest_end}")
    
    @property
    def duration_hours(self) -> float:
        """Verfügbare Zeitspanne"""
        return self.latest_end - self.earliest_start
    
    def overlaps_with(self, other: 'TimeWindow') -> bool:
        """Prüft Überschneidung mit anderem Zeitfenster"""
        overlap = not (self.latest_end <= other.earliest_start or other.latest_end <= self.earliest_start)
        # Debug für Zeitfenster-Prüfung
        if not overlap:
            print(f"   🕐 Zeitfenster überschneiden sich nicht: {self.earliest_start}-{self.latest_end} vs {other.earliest_start}-{other.latest_end}")
        return overlap

@dataclass
class Truck:
    """
    LKW mit allen relevanten Eigenschaften für die Optimierung
    """
    truck_id: str
    lat: float
    lon: float
    capacity: float
    current_load: float
    truck_type: TruckType
    driver_name: str
    availability: TimeWindow
    max_driving_time: float = 10.0  # Maximale Fahrzeit pro Tag
    cost_per_km: float = COST_PER_KM
    
    def __post_init__(self):
        """Validierung"""
        if self.capacity <= 0:
            raise ValueError(f"Kapazität muss positiv sein: {self.capacity}")
        if self.current_load < 0 or self.current_load > self.capacity:
            raise ValueError(f"Ungültige aktuelle Ladung: {self.current_load}")
    
    @property
    def available_capacity(self) -> float:
        """Verfügbare Ladekapazität"""
        return self.capacity - self.current_load
    
    @property
    def position(self) -> Tuple[float, float]:
        """GPS-Position"""
        return (self.lat, self.lon)
    
    @property
    def utilization_percent(self) -> float:
        """Aktuelle Auslastung in Prozent"""
        return (self.current_load / self.capacity) * 100 if self.capacity > 0 else 0

@dataclass
class Order:
    """
    Transport-Auftrag mit Optimierungsparametern
    """
    order_id: str
    pickup_lat: float
    pickup_lon: float
    delivery_lat: float
    delivery_lon: float
    volume: float
    priority: Priority
    customer: str
    time_window: TimeWindow
    service_time: float = 1.0  # Servicedauer in Stunden
    penalty_cost: float = 1000.0  # Kosten bei Nicht-Zuordnung
    assigned_truck: Optional[str] = None
    
    def __post_init__(self):
        """Validierung"""
        if self.volume <= 0:
            raise ValueError(f"Volumen muss positiv sein: {self.volume}")
        if self.service_time < 0:
            raise ValueError(f"Servicedauer darf nicht negativ sein: {self.service_time}")
    
    @property
    def pickup_position(self) -> Tuple[float, float]:
        """Abholposition"""
        return (self.pickup_lat, self.pickup_lon)
    
    @property
    def delivery_position(self) -> Tuple[float, float]:
        """Lieferposition"""
        return (self.delivery_lat, self.delivery_lon)
    
    @property
    def priority_multiplier(self) -> float:
        """Kostenmultiplikator basierend auf Priorität"""
        return PRIORITY_COST_MULTIPLIER.get(self.priority, 1.0)

@dataclass
class OptimizationResult:
    """
    Ergebnis der linearen Optimierung
    """
    assignments: List[Tuple[str, str]]  # [(truck_id, order_id), ...]
    total_cost: float
    unassigned_orders: List[str]
    solve_time: float
    status: str
    objective_value: float
    
    @property
    def assignment_rate(self) -> float:
        """Zuordnungsrate in Prozent"""
        total_orders = len(self.assignments) + len(self.unassigned_orders)
        return (len(self.assignments) / total_orders) * 100 if total_orders > 0 else 0

# ===============================================================================
# HILFSFUNKTIONEN
# ===============================================================================

def calculate_distance_km(pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
    """
    Berechnet Luftlinie-Entfernung zwischen GPS-Koordinaten (Haversine-Formel)
    """
    try:
        lat1, lon1 = math.radians(pos1[0]), math.radians(pos1[1])
        lat2, lon2 = math.radians(pos2[0]), math.radians(pos2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        distance = 6371 * c  # Erdradius in km
        
        # Sicherstellen, dass wir eine gültige Zahl zurückgeben
        if math.isnan(distance) or math.isinf(distance):
            return 9999.0  # Große, aber endliche Entfernung
        
        return max(0.1, distance)  # Mindestens 100m Entfernung
        
    except Exception as e:
        print(f"⚠️  Entfernungsberechnung fehlgeschlagen für {pos1} -> {pos2}: {e}")
        return 9999.0  # Fallback-Entfernung

def estimate_travel_time_hours(distance_km: float, avg_speed_kmh: float = 45.0) -> float:
    """
    Schätzt Reisezeit basierend auf Entfernung und Durchschnittsgeschwindigkeit
    """
    if avg_speed_kmh <= 0 or distance_km < 0:
        return 999.0  # Sehr lange, aber endliche Zeit
    
    travel_time = distance_km / avg_speed_kmh
    
    # Sicherstellen, dass wir eine gültige Zahl zurückgeben
    if math.isnan(travel_time) or math.isinf(travel_time):
        return 999.0
    
    return max(0.01, travel_time)  # Mindestens 0.6 Minuten

def calculate_assignment_cost(truck: Truck, order: Order) -> Tuple[float, Dict[str, float]]:
    """
    Berechnet Kosten für eine Truck-Order-Zuordnung
    
    Returns:
        Tuple (Gesamtkosten, Kostendetails)
    """
    try:
        # Entfernungskosten (Truck zu Pickup + Pickup zu Delivery)
        distance_to_pickup = calculate_distance_km(truck.position, order.pickup_position)
        delivery_distance = calculate_distance_km(order.pickup_position, order.delivery_position)
        total_distance = distance_to_pickup + delivery_distance
        
        # Grundkosten
        distance_cost = total_distance * truck.cost_per_km
        
        # Prioritäts-Anpassung
        priority_adjusted_cost = distance_cost * order.priority_multiplier
        
        # Zeitkosten (vereinfacht)
        travel_time = estimate_travel_time_hours(total_distance)
        time_cost = travel_time * 50  # 50€ pro Stunde Fahrzeit
        
        # Gesamtkosten
        total_cost = priority_adjusted_cost + time_cost
        
        # Validierung der Ergebnisse
        if math.isnan(total_cost) or math.isinf(total_cost) or total_cost < 0:
            total_cost = BIG_M
            
        details = {
            'distance_cost': distance_cost,
            'priority_adjustment': priority_adjusted_cost - distance_cost,
            'time_cost': time_cost,
            'total_distance_km': total_distance,
            'travel_time_hours': travel_time
        }
        
        return total_cost, details
        
    except Exception as e:
        print(f"⚠️  Kostenbererechnung fehlgeschlagen für {truck.truck_id} -> {order.order_id}: {e}")
        return BIG_M, {
            'distance_cost': BIG_M,
            'priority_adjustment': 0,
            'time_cost': 0,
            'total_distance_km': 9999,
            'travel_time_hours': 999
        }

# ===============================================================================
# DEMO-DATEN GENERIERUNG
# ===============================================================================

def generate_demo_trucks() -> List[Truck]:
    """Generiert 10 realistische Demo-LKWs mit erweiterten Verfügbarkeitszeiten"""
    
    trucks_data = [
        # (ID, lat, lon, capacity, current_load, type, driver, avail_start, avail_end)
        ("LKW001", 52.5200, 13.4050, 25.0, 0.0, TruckType.STANDARD, "Hans Müller", 6.0, 20.0),
        ("LKW002", 52.4800, 13.3900, 40.0, 0.0, TruckType.GROSS, "Maria Schmidt", 5.0, 22.0),
        ("LKW003", 52.5100, 13.4200, 18.0, 2.0, TruckType.KLEIN, "Peter Wagner", 7.0, 19.0),  # Reduzierte Vorlast
        ("LKW004", 52.5300, 13.3800, 35.0, 0.0, TruckType.STANDARD, "Anna Fischer", 6.0, 21.0),
        ("LKW005", 52.4900, 13.4100, 22.0, 1.0, TruckType.STANDARD, "Thomas Weber", 8.0, 20.0),  # Reduzierte Vorlast
        ("LKW006", 52.5000, 13.3950, 45.0, 0.0, TruckType.GROSS, "Sabine Meyer", 5.0, 23.0),
        ("LKW007", 52.5150, 13.4150, 20.0, 3.0, TruckType.KLEIN, "Michael Bauer", 9.0, 21.0),  # Reduzierte Vorlast
        ("LKW008", 52.4950, 13.4000, 30.0, 0.0, TruckType.STANDARD, "Lisa Hoffmann", 6.0, 22.0),
        ("LKW009", 52.5250, 13.3900, 25.0, 5.0, TruckType.STANDARD, "Jörg Schulz", 7.0, 21.0),  # Reduzierte Vorlast
        ("LKW010", 52.5050, 13.4050, 28.0, 0.0, TruckType.SPEZIAL, "Petra Koch", 5.0, 24.0)
    ]
    
    trucks = []
    for data in trucks_data:
        truck = Truck(
            truck_id=data[0],
            lat=data[1],
            lon=data[2],
            capacity=data[3],
            current_load=data[4],
            truck_type=data[5],
            driver_name=data[6],
            availability=TimeWindow(data[7], data[8])
        )
        trucks.append(truck)
    
    return trucks

def generate_demo_orders() -> List[Order]:
    """Generiert 15 realistische Demo-Aufträge mit kompatiblen Zeitfenstern"""
    
    orders_data = [
        # (ID, pickup_lat, pickup_lon, delivery_lat, delivery_lon, volume, priority, customer, time_start, time_end)
        ("AUF001", 52.5180, 13.4080, 52.5400, 13.3600, 8.5, Priority.HIGH, "MegaCorp GmbH", 8.0, 18.0),
        ("AUF002", 52.4850, 13.3950, 52.5100, 13.4300, 15.2, Priority.NORMAL, "TechStart AG", 9.0, 20.0),
        ("AUF003", 52.5080, 13.4120, 52.4800, 13.3800, 18.0, Priority.NORMAL, "LogiFlow Ltd", 7.0, 21.0),  # Erweitert
        ("AUF004", 52.5220, 13.3980, 52.5300, 13.4200, 6.8, Priority.URGENT, "QuickServ Express", 10.0, 16.0),
        ("AUF005", 52.4980, 13.4000, 52.5000, 13.4150, 12.5, Priority.NORMAL, "StoreChain Plus", 11.0, 19.0),
        ("AUF006", 52.5120, 13.4050, 52.5350, 13.3750, 16.0, Priority.HIGH, "GlobalTrade Corp", 8.0, 18.0),  # Reduziertes Volumen
        ("AUF007", 52.5000, 13.3900, 52.4900, 13.4100, 9.3, Priority.NORMAL, "LocalBiz Services", 12.0, 22.0),
        ("AUF008", 52.5280, 13.4100, 52.5150, 13.3950, 20.0, Priority.NORMAL, "HeavyGoods Transport", 6.0, 23.0),  # Reduziertes Volumen
        ("AUF009", 52.4920, 13.4080, 52.5200, 13.4000, 7.1, Priority.URGENT, "ExpressLtd Courier", 9.0, 15.0),
        ("AUF010", 52.5150, 13.3850, 52.5050, 13.4200, 14.6, Priority.NORMAL, "RegionalCo Shipping", 10.0, 20.0),
        ("AUF011", 52.5040, 13.4120, 52.5280, 13.3900, 11.2, Priority.HIGH, "PrimeTrans Solutions", 7.0, 19.0),
        ("AUF012", 52.5190, 13.3920, 52.4950, 13.4050, 14.0, Priority.NORMAL, "CityLogistics Pro", 13.0, 21.0),  # Reduziertes Volumen
        ("AUF013", 52.4960, 13.4030, 52.5100, 13.3880, 17.0, Priority.LOW, "MetroFreight Hub", 6.0, 23.0),  # Reduziertes Volumen
        ("AUF014", 52.5110, 13.4000, 52.5220, 13.4100, 10.0, Priority.URGENT, "RushDelivery 24h", 8.0, 14.0),  # Reduziertes Volumen
        ("AUF015", 52.5060, 13.3970, 52.5180, 13.4080, 16.0, Priority.HIGH, "TopClient Premium", 9.0, 19.0)  # Reduziertes Volumen
    ]
    
    orders = []
    for data in orders_data:
        order = Order(
            order_id=data[0],
            pickup_lat=data[1],
            pickup_lon=data[2],
            delivery_lat=data[3],
            delivery_lon=data[4],
            volume=data[5],
            priority=data[6],
            customer=data[7],
            time_window=TimeWindow(data[8], data[9]),
            service_time=0.5  # Reduzierte Servicezeit
        )
        orders.append(order)
    
    return orders

# ===============================================================================
# LINEARE OPTIMIERUNG
# ===============================================================================

class TruckOrderOptimizer:
    """
    Hauptklasse für die lineare Optimierung der LKW-Auftragszuordnung
    """
    
    def __init__(self, trucks: List[Truck], orders: List[Order]):
        self.trucks = trucks
        self.orders = orders
        self.cost_matrix = {}
        self.model = None
        self.variables = {}
        
    def _calculate_cost_matrix(self) -> None:
        """
        Berechnet Kostenmatrix für alle Truck-Order-Kombinationen
        """
        print("📊 Berechne Kostenmatrix...")
        
        feasible_count = 0
        infeasible_reasons = {"Kapazität": 0, "Zeitfenster": 0, "Fahrzeit": 0}
        
        for truck in self.trucks:
            for order in self.orders:
                # Prüfe Machbarkeit
                if not self._is_feasible_assignment(truck, order, debug=False):  # Debug nur bei erster Prüfung
                    # Verwende sehr große, aber endliche Zahl statt infinity
                    self.cost_matrix[(truck.truck_id, order.order_id)] = BIG_M
                    
                    # Sammle Statistiken über Ablehnungsgründe
                    if order.volume > truck.available_capacity:
                        infeasible_reasons["Kapazität"] += 1
                    elif not truck.availability.overlaps_with(order.time_window):
                        infeasible_reasons["Zeitfenster"] += 1
                    else:
                        infeasible_reasons["Fahrzeit"] += 1
                else:
                    cost, _ = calculate_assignment_cost(truck, order)
                    self.cost_matrix[(truck.truck_id, order.order_id)] = cost
                    feasible_count += 1
        
        print(f"✅ Kostenmatrix berechnet: {len(self.cost_matrix)} Kombinationen")
        print(f"   📊 Machbar: {feasible_count}, Nicht machbar: {len(self.cost_matrix) - feasible_count}")
        print(f"   📊 Ablehnungsgründe: Kapazität: {infeasible_reasons['Kapazität']}, "
              f"Zeitfenster: {infeasible_reasons['Zeitfenster']}, Fahrzeit: {infeasible_reasons['Fahrzeit']}")
        
        if feasible_count == 0:
            print("⚠️  WARNUNG: Keine machbaren Zuordnungen gefunden!")
            print("   🔍 Prüfe Demo-Daten auf Kompatibilität...")
    
    def _is_feasible_assignment(self, truck: Truck, order: Order, debug: bool = True) -> bool:
        """
        Prüft ob Zuordnung grundsätzlich möglich ist
        """
        # Kapazitätsprüfung
        if order.volume > truck.available_capacity:
            if debug:
                print(f"❌ {truck.truck_id} -> {order.order_id}: Kapazität ({order.volume}t > {truck.available_capacity}t)")
            return False
        
        # Zeitfenster-Überschneidung
        if not truck.availability.overlaps_with(order.time_window):
            if debug:
                print(f"❌ {truck.truck_id} -> {order.order_id}: Zeitfenster (LKW: {truck.availability.earliest_start}-{truck.availability.latest_end}h vs Auftrag: {order.time_window.earliest_start}-{order.time_window.latest_end}h)")
            return False
        
        # Fahrzeit vs. verfügbare Zeit
        distance = calculate_distance_km(truck.position, order.pickup_position)
        delivery_distance = calculate_distance_km(order.pickup_position, order.delivery_position)
        total_travel_time = estimate_travel_time_hours(distance + delivery_distance)
        
        if total_travel_time + order.service_time > truck.availability.duration_hours:
            if debug:
                print(f"❌ {truck.truck_id} -> {order.order_id}: Zeit ({total_travel_time:.1f}h + {order.service_time}h > {truck.availability.duration_hours}h)")
            return False
        
        # Erfolgreiche Zuordnung
        if debug:
            print(f"✅ {truck.truck_id} -> {order.order_id}: Machbar (Dist: {distance:.1f}km, Zeit: {total_travel_time:.1f}h)")
        return True
    
    def _create_optimization_model(self) -> None:
        """
        Erstellt das mathematische Optimierungsmodell
        """
        print("🔧 Erstelle Optimierungsmodell...")
        
        # Erstelle das Modell
        self.model = pulp.LpProblem("TruckOrderAssignment", pulp.LpMinimize)
        
        # Entscheidungsvariablen: x[i,j] = 1 wenn LKW i Auftrag j übernimmt
        self.variables = {}
        for truck in self.trucks:
            for order in self.orders:
                var_name = f"x_{truck.truck_id}_{order.order_id}"
                self.variables[(truck.truck_id, order.order_id)] = pulp.LpVariable(
                    var_name, cat='Binary'
                )
        
        # Zielfunktion: Minimiere Gesamtkosten
        total_cost = pulp.lpSum([
            self.cost_matrix.get((truck.truck_id, order.order_id), BIG_M) * 
            self.variables[(truck.truck_id, order.order_id)]
            for truck in self.trucks
            for order in self.orders
        ])
        self.model += total_cost, "TotalCost"
        
        # Nebenbedingung 1: Jeder Auftrag wird höchstens einmal zugeordnet
        for order in self.orders:
            self.model += (
                pulp.lpSum([
                    self.variables[(truck.truck_id, order.order_id)]
                    for truck in self.trucks
                ]) <= 1,
                f"OrderAssignment_{order.order_id}"
            )
        
        # Nebenbedingung 2: Kapazitätsbeschränkungen
        for truck in self.trucks:
            self.model += (
                pulp.lpSum([
                    order.volume * self.variables[(truck.truck_id, order.order_id)]
                    for order in self.orders
                ]) <= truck.available_capacity,
                f"CapacityConstraint_{truck.truck_id}"
            )
        
        # Nebenbedingung 3: Nur machbare Zuordnungen
        for truck in self.trucks:
            for order in self.orders:
                if self.cost_matrix.get((truck.truck_id, order.order_id)) == BIG_M:
                    self.model += (
                        self.variables[(truck.truck_id, order.order_id)] == 0,
                        f"Infeasible_{truck.truck_id}_{order.order_id}"
                    )
        
        print(f"✅ Modell erstellt: {len(self.variables)} Variablen, {len(self.model.constraints)} Nebenbedingungen")
    
    def solve(self) -> OptimizationResult:
        """
        Löst das Optimierungsproblem
        """
        if not PULP_AVAILABLE:
            raise ImportError("PuLP ist nicht verfügbar. Installiere mit: pip install pulp")
        
        print("🚀 Starte Optimierung...")
        start_time = time.time()
        
        # Kostenmatrix berechnen
        self._calculate_cost_matrix()
        
        # Modell erstellen
        self._create_optimization_model()
        
        # Solver konfigurieren
        solver = pulp.PULP_CBC_CMD(
            timeLimit=MAX_SOLVER_TIME,
            msg=True,
            gapRel=0.01  # 1% Optimalitätslücke akzeptabel
        )
        
        # Lösung finden
        self.model.solve(solver)
        
        solve_time = time.time() - start_time
        
        # Ergebnisse extrahieren
        assignments = []
        unassigned_orders = []
        
        if self.model.status == pulp.LpStatusOptimal or self.model.status == pulp.LpStatusFeasible:
            # Zuordnungen extrahieren
            for truck in self.trucks:
                for order in self.orders:
                    if self.variables[(truck.truck_id, order.order_id)].value() == 1:
                        assignments.append((truck.truck_id, order.order_id))
            
            # Nicht zugeordnete Aufträge
            assigned_order_ids = {order_id for _, order_id in assignments}
            unassigned_orders = [order.order_id for order in self.orders 
                               if order.order_id not in assigned_order_ids]
            
            total_cost = pulp.value(self.model.objective)
            status = "Optimal" if self.model.status == pulp.LpStatusOptimal else "Feasible"
            
        else:
            # Keine Lösung gefunden
            total_cost = float('inf')
            status = "Infeasible"
            unassigned_orders = [order.order_id for order in self.orders]
        
        result = OptimizationResult(
            assignments=assignments,
            total_cost=total_cost,
            unassigned_orders=unassigned_orders,
            solve_time=solve_time,
            status=status,
            objective_value=pulp.value(self.model.objective) if self.model.objective else 0
        )
        
        print(f"✅ Optimierung abgeschlossen: {status} in {solve_time:.2f}s")
        return result

# ===============================================================================
# CSV-EXPORT UND ANALYSE
# ===============================================================================

def export_trucks_csv(trucks: List[Truck], filename: str = "trucks_linear_opt.csv") -> bool:
    """Exportiert LKW-Daten"""
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                'truck_id', 'lat', 'lon', 'capacity', 'current_load', 'available_capacity',
                'truck_type', 'driver_name', 'availability_start', 'availability_end',
                'max_driving_time', 'cost_per_km'
            ])
            
            for truck in trucks:
                writer.writerow([
                    truck.truck_id, truck.lat, truck.lon, truck.capacity, truck.current_load,
                    truck.available_capacity, truck.truck_type.value, truck.driver_name,
                    truck.availability.earliest_start, truck.availability.latest_end,
                    truck.max_driving_time, truck.cost_per_km
                ])
        
        print(f"✅ LKW-Daten exportiert: {filename}")
        return True
    except Exception as e:
        print(f"❌ LKW-Export Fehler: {e}")
        return False

def export_orders_csv(orders: List[Order], filename: str = "orders_linear_opt.csv") -> bool:
    """Exportiert Auftragsdaten"""
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                'order_id', 'pickup_lat', 'pickup_lon', 'delivery_lat', 'delivery_lon',
                'volume', 'priority', 'customer', 'time_window_start', 'time_window_end',
                'service_time', 'penalty_cost', 'assigned_truck'
            ])
            
            for order in orders:
                writer.writerow([
                    order.order_id, order.pickup_lat, order.pickup_lon,
                    order.delivery_lat, order.delivery_lon, order.volume,
                    order.priority.name, order.customer,
                    order.time_window.earliest_start, order.time_window.latest_end,
                    order.service_time, order.penalty_cost, order.assigned_truck or "UNASSIGNED"
                ])
        
        print(f"✅ Auftrags-Daten exportiert: {filename}")
        return True
    except Exception as e:
        print(f"❌ Auftrags-Export Fehler: {e}")
        return False

def export_optimization_results_csv(result: OptimizationResult, trucks: List[Truck], 
                                   orders: List[Order], filename: str = "optimization_results.csv") -> bool:
    """Exportiert Optimierungsergebnisse"""
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                'truck_id', 'order_id', 'distance_km', 'travel_time_hours', 'assignment_cost',
                'truck_capacity_used', 'order_priority', 'customer'
            ])
            
            for truck_id, order_id in result.assignments:
                truck = next(t for t in trucks if t.truck_id == truck_id)
                order = next(o for o in orders if o.order_id == order_id)
                
                cost, details = calculate_assignment_cost(truck, order)
                
                writer.writerow([
                    truck_id, order_id, 
                    round(details['total_distance_km'], 2),
                    round(details['travel_time_hours'], 2),
                    round(cost, 2),
                    order.volume,
                    order.priority.name,
                    order.customer
                ])
        
        print(f"✅ Optimierungsergebnisse exportiert: {filename}")
        return True
    except Exception as e:
        print(f"❌ Ergebnis-Export Fehler: {e}")
        return False

def analyze_optimization_results(result: OptimizationResult, trucks: List[Truck], 
                                orders: List[Order]) -> Dict:
    """Analysiert die Optimierungsergebnisse"""
    
    analysis = {
        'total_orders': len(orders),
        'assigned_orders': len(result.assignments),
        'unassigned_orders': len(result.unassigned_orders),
        'assignment_rate': result.assignment_rate,
        'total_cost': result.total_cost,
        'solve_time': result.solve_time,
        'status': result.status
    }
    
    if result.assignments:
        # Detailanalyse
        distances = []
        costs = []
        assigned_volume = 0
        
        for truck_id, order_id in result.assignments:
            truck = next(t for t in trucks if t.truck_id == truck_id)
            order = next(o for o in orders if o.order_id == order_id)
            
            cost, details = calculate_assignment_cost(truck, order)
            distances.append(details['total_distance_km'])
            costs.append(cost)
            assigned_volume += order.volume
        
        analysis.update({
            'avg_distance_km': sum(distances) / len(distances),
            'total_distance_km': sum(distances),
            'avg_cost_per_assignment': sum(costs) / len(costs),
            'assigned_volume_tons': assigned_volume,
            'total_volume_tons': sum(o.volume for o in orders)
        })
        
        # LKW-Auslastung
        truck_utilizations = []
        for truck in trucks:
            assigned_orders = [order_id for truck_id, order_id in result.assignments 
                             if truck_id == truck.truck_id]
            if assigned_orders:
                truck_volume = sum(next(o.volume for o in orders if o.order_id == order_id) 
                                 for order_id in assigned_orders)
                utilization = ((truck.current_load + truck_volume) / truck.capacity) * 100
            else:
                utilization = truck.utilization_percent
            truck_utilizations.append(utilization)
        
        analysis['avg_truck_utilization'] = sum(truck_utilizations) / len(truck_utilizations)
    
    return analysis

def print_optimization_results(result: OptimizationResult, trucks: List[Truck], 
                              orders: List[Order], analysis: Dict):
    """Druckt formatierte Optimierungsergebnisse"""
    
    print("=" * 100)
    print("🎯 LINEARE OPTIMIERUNG - ERGEBNISSE")
    print("=" * 100)
    
    # Optimierungsübersicht
    print(f"\n📊 OPTIMIERUNGSÜBERSICHT:")
    print("-" * 60)
    print(f"Status:                  {result.status}")
    print(f"Lösungszeit:             {result.solve_time:>8.2f} Sekunden")
    print(f"Gesamtkosten:            {result.total_cost:>8.2f} €")
    print(f"Zugeordnete Aufträge:    {len(result.assignments):>3} / {len(orders)}")
    print(f"Zuordnungsrate:          {result.assignment_rate:>8.1f} %")
    
    if result.assignments:
        print(f"Durchschnittliche Kosten: {analysis.get('avg_cost_per_assignment', 0):>7.2f} € pro Auftrag")
        print(f"Gesamtstrecke:           {analysis.get('total_distance_km', 0):>8.1f} km")
        print(f"Durchschnittsstrecke:    {analysis.get('avg_distance_km', 0):>8.1f} km pro Auftrag")
    
    # Zuordnungen
    if result.assignments:
        print(f"\n✅ OPTIMALE ZUORDNUNGEN ({len(result.assignments)}):")
        print("-" * 100)
        print(f"{'LKW':>7} → {'Auftrag':<8} | {'Dist[km]':>8} | {'Zeit[h]':>7} | {'Kosten[€]':>9} | {'Vol[t]':>6} | {'Priorität':>8} | {'Kunde'}")
        print("-" * 100)
        
        # Sortiere nach Kosten
        assignment_details = []
        for truck_id, order_id in result.assignments:
            truck = next(t for t in trucks if t.truck_id == truck_id)
            order = next(o for o in orders if o.order_id == order_id)
            cost, details = calculate_assignment_cost(truck, order)
            assignment_details.append((truck_id, order_id, cost, details, order))
        
        assignment_details.sort(key=lambda x: x[2])  # Sortiere nach Kosten
        
        for truck_id, order_id, cost, details, order in assignment_details:
            print(f"{truck_id:>7} → {order_id:<8} | "
                  f"{details['total_distance_km']:>8.1f} | {details['travel_time_hours']:>7.1f} | "
                  f"{cost:>9.2f} | {order.volume:>6.1f} | {order.priority.name:>8} | "
                  f"{order.customer}")
    
    # Nicht zugeordnete Aufträge
    if result.unassigned_orders:
        print(f"\n❌ NICHT ZUGEORDNETE AUFTRÄGE ({len(result.unassigned_orders)}):")
        print("-" * 80)
        print(f"{'Auftrag':<8} | {'Vol[t]':>6} | {'Priorität':>8} | {'Zeitfenster':>12} | {'Kunde'}")
        print("-" * 80)
        
        for order_id in result.unassigned_orders:
            order = next(o for o in orders if o.order_id == order_id)
            time_window = f"{order.time_window.earliest_start:.0f}-{order.time_window.latest_end:.0f}h"
            print(f"{order.order_id:<8} | {order.volume:>6.1f} | {order.priority.name:>8} | "
                  f"{time_window:>12} | {order.customer}")
    
    # LKW-Auslastung nach Optimierung
    print(f"\n🚛 LKW-AUSLASTUNG NACH OPTIMIERUNG:")
    print("-" * 90)
    print(f"{'LKW-ID':<7} | {'Fahrer':<15} | {'Vorher[t]':>9} | {'Nachher[t]':>10} | {'Auslastung[%]':>13} | {'Zugeordnet'}")
    print("-" * 90)
    
    for truck in sorted(trucks, key=lambda t: t.truck_id):
        assigned_orders = [order_id for truck_id, order_id in result.assignments 
                          if truck_id == truck.truck_id]
        
        if assigned_orders:
            additional_volume = sum(next(o.volume for o in orders if o.order_id == order_id) 
                                  for order_id in assigned_orders)
            new_load = truck.current_load + additional_volume
            new_utilization = (new_load / truck.capacity) * 100
            assigned_order = ", ".join(assigned_orders)
        else:
            new_load = truck.current_load
            new_utilization = truck.utilization_percent
            assigned_order = "---"
        
        print(f"{truck.truck_id:<7} | {truck.driver_name:<15} | {truck.current_load:>9.1f} | "
              f"{new_load:>10.1f} | {new_utilization:>13.1f} | {assigned_order}")

# ===============================================================================
# HAUPTPROGRAMM
# ===============================================================================

def main():
    """
    Hauptfunktion der linearen Optimierung
    """
    print("🎯 LKW-Zuordnung mit Linearer Optimierung")
    print("=" * 70)
    
    # Prüfe PuLP-Verfügbarkeit
    if not PULP_AVAILABLE:
        print("❌ PuLP ist nicht installiert!")
        print("   Installiere mit: pip install pulp")
        sys.exit(1)
    
    try:
        # 1. Demo-Daten generieren
        print("📊 Generiere realistische Demo-Daten...")
        trucks = generate_demo_trucks()
        orders = generate_demo_orders()
        print(f"✅ {len(trucks)} LKWs und {len(orders)} Aufträge generiert")
        
        # 2. Ausgangsdaten exportieren
        print("\n💾 Exportiere Ausgangsdaten...")
        export_trucks_csv(trucks)
        export_orders_csv(orders)
        
        # 3. Lineare Optimierung durchführen
        print(f"\n🔧 Initialisiere Optimierer...")
        optimizer = TruckOrderOptimizer(trucks, orders)
        
        # 3.1 Validiere Demo-Daten
        print(f"🔍 Validiere Daten...")
        valid_assignments = 0
        for truck in trucks:
            for order in orders:
                cost, _ = calculate_assignment_cost(truck, order)
                if cost < BIG_M:
                    valid_assignments += 1
        
        print(f"✅ {valid_assignments} von {len(trucks) * len(orders)} Zuordnungen sind theoretisch möglich")
        
        if valid_assignments == 0:
            print("❌ Keine gültigen Zuordnungen möglich! Prüfe Daten.")
            return
        
        # 4. Optimierung lösen
        result = optimizer.solve()
        
        # 5. Ergebnisse aktualisieren
        print(f"\n🔄 Aktualisiere Zuordnungen...")
        for truck_id, order_id in result.assignments:
            order = next(o for o in orders if o.order_id == order_id)
            order.assigned_truck = truck_id
        
        # 6. Analyse durchführen
        print(f"\n🔬 Analysiere Ergebnisse...")
        analysis = analyze_optimization_results(result, trucks, orders)
        
        # 7. Ergebnisse anzeigen
        print_optimization_results(result, trucks, orders, analysis)
        
        # 8. Finale Ergebnisse exportieren
        print(f"\n💾 Exportiere Optimierungsergebnisse...")
        export_optimization_results_csv(result, trucks, orders)
        export_trucks_csv(trucks, "trucks_after_optimization.csv")
        export_orders_csv(orders, "orders_after_optimization.csv")
        
        # 9. Zusammenfassung
        print(f"\n🎯 OPTIMIERUNG ABGESCHLOSSEN!")
        print("-" * 50)
        print(f"Status:           {result.status}")
        print(f"Lösungszeit:      {result.solve_time:.2f} Sekunden")
        print(f"Zuordnungsrate:   {result.assignment_rate:.1f}%")
        print(f"Gesamtkosten:     {result.total_cost:.2f} €")
        print(f"📁 Dateien:       optimization_results.csv, trucks_after_optimization.csv, orders_after_optimization.csv")
        
        if result.status == "Optimal":
            print("✅ Optimale Lösung gefunden!")
        elif result.status == "Feasible":
            print("✅ Gute Lösung gefunden (nahe optimal)!")
        else:
            print("⚠️  Keine zulässige Lösung gefunden!")
        
    except KeyboardInterrupt:
        print(f"\n⚠️  Programm durch Benutzer unterbrochen")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()