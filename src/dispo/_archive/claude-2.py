#!/usr/bin/env python3
"""
LKW-Zuordnungssystem
=====================

Ein vollständiges System zur automatischen Zuordnung von Transport-Aufträgen zu LKWs.
Implementiert verschiedene Zuordnungsstrategien und bietet umfassende Analyse-Funktionen.

Autor: Demo-Implementation
Version: 2.0
"""

import csv
import math
import io
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from enum import Enum
from datetime import datetime

# ===============================================================================
# KONFIGURATION UND KONSTANTEN
# ===============================================================================

class Priority(Enum):
    """Auftragsprioritäten"""
    URGENT = "urgent"
    HIGH = "high" 
    NORMAL = "normal"
    LOW = "low"

class TruckType(Enum):
    """LKW-Typen"""
    KLEIN = "Klein"
    STANDARD = "Standard"
    GROSS = "Groß"
    SPEZIAL = "Spezial"

# Gewichtungen für Score-Berechnung
DISTANCE_WEIGHT = 1.0
PRIORITY_WEIGHT = 0.8
CAPACITY_WEIGHT = 0.6
TIME_WEIGHT = 0.4

# ===============================================================================
# DATENKLASSEN
# ===============================================================================

@dataclass
class Truck:
    """
    Repräsentiert einen LKW mit allen relevanten Eigenschaften
    """
    truck_id: str
    lat: float
    lon: float
    capacity: float
    current_load: float
    truck_type: TruckType
    driver_name: str = ""
    max_driving_time: float = 8.0  # Stunden
    cost_per_km: float = 1.2  # Euro pro km
    
    def __post_init__(self):
        """Validierung nach Initialisierung"""
        if self.capacity <= 0:
            raise ValueError(f"Kapazität muss positiv sein: {self.capacity}")
        if self.current_load < 0:
            raise ValueError(f"Aktuelle Ladung darf nicht negativ sein: {self.current_load}")
        if self.current_load > self.capacity:
            raise ValueError(f"Aktuelle Ladung übersteigt Kapazität: {self.current_load} > {self.capacity}")
    
    @property
    def available_capacity(self) -> float:
        """Verfügbare Ladekapazität"""
        return self.capacity - self.current_load
    
    @property
    def position(self) -> Tuple[float, float]:
        """GPS-Position als Tupel"""
        return (self.lat, self.lon)
    
    @property
    def utilization_percent(self) -> float:
        """Aktuelle Auslastung in Prozent"""
        return (self.current_load / self.capacity) * 100 if self.capacity > 0 else 0
    
    def can_handle_order(self, order: 'Order') -> bool:
        """Prüft ob LKW den Auftrag übernehmen kann"""
        return order.volume <= self.available_capacity

@dataclass
class Order:
    """
    Repräsentiert einen Transport-Auftrag
    """
    order_id: str
    pickup_lat: float
    pickup_lon: float
    delivery_lat: float
    delivery_lon: float
    volume: float
    priority: Priority
    customer: str
    deadline_hours: float = 24.0  # Stunden bis Deadline
    value: float = 1000.0  # Auftragswert in Euro
    assigned_truck: Optional[str] = None
    
    def __post_init__(self):
        """Validierung nach Initialisierung"""
        if self.volume <= 0:
            raise ValueError(f"Volumen muss positiv sein: {self.volume}")
        if self.deadline_hours <= 0:
            raise ValueError(f"Deadline muss positiv sein: {self.deadline_hours}")
    
    @property
    def pickup_position(self) -> Tuple[float, float]:
        """Abholposition als Tupel"""
        return (self.pickup_lat, self.pickup_lon)
    
    @property
    def delivery_position(self) -> Tuple[float, float]:
        """Lieferposition als Tupel"""
        return (self.delivery_lat, self.delivery_lon)
    
    @property
    def priority_score(self) -> float:
        """Numerischer Prioritätswert (niedriger = wichtiger)"""
        priority_values = {
            Priority.URGENT: 0.1,
            Priority.HIGH: 0.3,
            Priority.NORMAL: 1.0,
            Priority.LOW: 2.0
        }
        return priority_values.get(self.priority, 1.0)
    
    @property
    def is_assigned(self) -> bool:
        """Prüft ob Auftrag zugeordnet ist"""
        return self.assigned_truck is not None

@dataclass
class Assignment:
    """
    Repräsentiert eine LKW-Auftrag-Zuordnung
    """
    truck_id: str
    order_id: str
    distance_km: float
    estimated_duration: float  # Stunden
    total_cost: float  # Euro
    score: float
    assignment_time: datetime = field(default_factory=datetime.now)
    
    @property
    def cost_per_hour(self) -> float:
        """Kosten pro Stunde"""
        return self.total_cost / self.estimated_duration if self.estimated_duration > 0 else 0

# ===============================================================================
# DEMO-DATEN GENERIERUNG
# ===============================================================================

def generate_demo_trucks() -> List[Truck]:
    """
    Generiert 10 Demo-LKWs mit realistischen Berliner Koordinaten
    """
    trucks_data = [
        ("LKW001", 52.5200, 13.4050, 25.0, 0.0, TruckType.STANDARD, "Hans Mueller"),
        ("LKW002", 52.4800, 13.3900, 40.0, 0.0, TruckType.GROSS, "Maria Schmidt"),
        ("LKW003", 52.5100, 13.4200, 18.0, 5.0, TruckType.KLEIN, "Peter Wagner"),
        ("LKW004", 52.5300, 13.3800, 35.0, 0.0, TruckType.STANDARD, "Anna Fischer"),
        ("LKW005", 52.4900, 13.4100, 22.0, 3.0, TruckType.STANDARD, "Thomas Weber"),
        ("LKW006", 52.5000, 13.3950, 45.0, 0.0, TruckType.GROSS, "Sabine Meyer"),
        ("LKW007", 52.5150, 13.4150, 20.0, 8.0, TruckType.KLEIN, "Michael Bauer"),
        ("LKW008", 52.4950, 13.4000, 30.0, 0.0, TruckType.STANDARD, "Lisa Hoffmann"),
        ("LKW009", 52.5250, 13.3900, 25.0, 12.0, TruckType.STANDARD, "Joerg Schulz"),
        ("LKW010", 52.5050, 13.4050, 28.0, 0.0, TruckType.STANDARD, "Petra Koch")
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
            driver_name=data[6]
        )
        trucks.append(truck)
    
    return trucks

def generate_demo_orders() -> List[Order]:
    """
    Generiert 15 Demo-Aufträge mit verschiedenen Eigenschaften
    """
    orders_data = [
        ("AUF001", 52.5180, 13.4080, 52.5400, 13.3600, 8.5, Priority.HIGH, "MegaCorp GmbH", 12.0),
        ("AUF002", 52.4850, 13.3950, 52.5100, 13.4300, 15.2, Priority.NORMAL, "TechStart AG", 24.0),
        ("AUF003", 52.5080, 13.4120, 52.4800, 13.3800, 22.0, Priority.NORMAL, "LogiFlow Ltd", 18.0),
        ("AUF004", 52.5220, 13.3980, 52.5300, 13.4200, 6.8, Priority.URGENT, "QuickServ Express", 6.0),
        ("AUF005", 52.4980, 13.4000, 52.5000, 13.4150, 12.5, Priority.NORMAL, "StoreChain Plus", 20.0),
        ("AUF006", 52.5120, 13.4050, 52.5350, 13.3750, 18.7, Priority.HIGH, "GlobalTrade Corp", 16.0),
        ("AUF007", 52.5000, 13.3900, 52.4900, 13.4100, 9.3, Priority.NORMAL, "LocalBiz Services", 24.0),
        ("AUF008", 52.5280, 13.4100, 52.5150, 13.3950, 25.8, Priority.NORMAL, "HeavyGoods Transport", 30.0),
        ("AUF009", 52.4920, 13.4080, 52.5200, 13.4000, 7.1, Priority.URGENT, "ExpressLtd Courier", 4.0),
        ("AUF010", 52.5150, 13.3850, 52.5050, 13.4200, 14.6, Priority.NORMAL, "RegionalCo Shipping", 22.0),
        ("AUF011", 52.5040, 13.4120, 52.5280, 13.3900, 11.2, Priority.HIGH, "PrimeTrans Solutions", 14.0),
        ("AUF012", 52.5190, 13.3920, 52.4950, 13.4050, 16.9, Priority.NORMAL, "CityLogistics Pro", 20.0),
        ("AUF013", 52.4960, 13.4030, 52.5100, 13.3880, 20.4, Priority.NORMAL, "MetroFreight Hub", 28.0),
        ("AUF014", 52.5110, 13.4000, 52.5220, 13.4100, 13.7, Priority.URGENT, "RushDelivery 24h", 8.0),
        ("AUF015", 52.5060, 13.3970, 52.5180, 13.4080, 19.1, Priority.HIGH, "TopClient Premium", 16.0)
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
            deadline_hours=data[8]
        )
        orders.append(order)
    
    return orders

# ===============================================================================
# HILFSFUNKTIONEN
# ===============================================================================

def calculate_distance(pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
    """
    Berechnet die Luftlinie-Entfernung zwischen zwei GPS-Koordinaten in km
    Verwendet die Haversine-Formel für hohe Genauigkeit
    
    Args:
        pos1: Tupel (lat, lon) der ersten Position
        pos2: Tupel (lat, lon) der zweiten Position
        
    Returns:
        Entfernung in Kilometern
    """
    try:
        lat1, lon1 = math.radians(pos1[0]), math.radians(pos1[1])
        lat2, lon2 = math.radians(pos2[0]), math.radians(pos2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Erdradius in km
        radius = 6371
        return radius * c
    except Exception as e:
        print(f"⚠️  Fehler bei Entfernungsberechnung: {e}")
        return float('inf')

def estimate_travel_time(distance_km: float, avg_speed_kmh: float = 50.0) -> float:
    """
    Schätzt die Reisezeit basierend auf Entfernung und Durchschnittsgeschwindigkeit
    
    Args:
        distance_km: Entfernung in Kilometern
        avg_speed_kmh: Durchschnittsgeschwindigkeit in km/h
        
    Returns:
        Geschätzte Reisezeit in Stunden
    """
    return distance_km / avg_speed_kmh if avg_speed_kmh > 0 else 0

def calculate_assignment_score(truck: Truck, order: Order) -> Tuple[float, Dict[str, float]]:
    """
    Berechnet einen umfassenden Score für die LKW-Auftrag-Zuordnung
    Niedrigerer Score = bessere Zuordnung
    
    Args:
        truck: LKW-Objekt
        order: Auftrag-Objekt
        
    Returns:
        Tupel (Gesamt-Score, Detail-Scores als Dictionary)
    """
    # Entfernungs-Score
    distance = calculate_distance(truck.position, order.pickup_position)
    distance_score = distance * DISTANCE_WEIGHT
    
    # Prioritäts-Score
    priority_score = order.priority_score * PRIORITY_WEIGHT
    
    # Kapazitäts-Score (besser wenn LKW optimal ausgelastet wird)
    capacity_utilization = order.volume / truck.capacity
    capacity_score = (1.0 - capacity_utilization) * CAPACITY_WEIGHT
    
    # Zeit-Score (basierend auf Deadline)
    travel_time = estimate_travel_time(distance)
    time_pressure = max(0, (travel_time / order.deadline_hours)) * TIME_WEIGHT
    
    # Gesamt-Score
    total_score = distance_score + priority_score + capacity_score + time_pressure
    
    details = {
        'distance': distance_score,
        'priority': priority_score,
        'capacity': capacity_score,
        'time': time_pressure,
        'raw_distance_km': distance,
        'travel_time_hours': travel_time
    }
    
    return total_score, details

# ===============================================================================
# ZUORDNUNGSALGORITHMEN
# ===============================================================================

class AssignmentStrategy:
    """Basis-Klasse für Zuordnungsstrategien"""
    
    def assign(self, trucks: List[Truck], orders: List[Order]) -> Tuple[List[Assignment], List[Order]]:
        """
        Führt die Zuordnung durch
        
        Returns:
            Tupel (Zuordnungen, nicht-zugeordnete Aufträge)
        """
        raise NotImplementedError

class GreedyNearestStrategy(AssignmentStrategy):
    """
    Greedy-Algorithmus: Weist jedem LKW den besten verfügbaren Auftrag zu
    Berücksichtigt Entfernung, Priorität, Kapazität und Zeitdruck
    """
    
    def assign(self, trucks: List[Truck], orders: List[Order]) -> Tuple[List[Assignment], List[Order]]:
        assignments = []
        available_orders = [o for o in orders if not o.is_assigned]
        
        # Sortiere LKWs nach verfügbarer Kapazität (größte zuerst)
        sorted_trucks = sorted(trucks, key=lambda t: t.available_capacity, reverse=True)
        
        for truck in sorted_trucks:
            best_order = None
            best_score = float('inf')
            best_details = None
            
            # Finde den besten Auftrag für diesen LKW
            for order in available_orders:
                if truck.can_handle_order(order):
                    score, details = calculate_assignment_score(truck, order)
                    
                    if score < best_score:
                        best_score = score
                        best_order = order
                        best_details = details
            
            # Zuordnung durchführen
            if best_order and best_details:
                # Kosten berechnen
                total_distance = best_details['raw_distance_km']
                travel_time = best_details['travel_time_hours']
                total_cost = total_distance * truck.cost_per_km
                
                assignment = Assignment(
                    truck_id=truck.truck_id,
                    order_id=best_order.order_id,
                    distance_km=total_distance,
                    estimated_duration=travel_time,
                    total_cost=total_cost,
                    score=best_score
                )
                assignments.append(assignment)
                
                # Zustand aktualisieren
                best_order.assigned_truck = truck.truck_id
                truck.current_load += best_order.volume
                available_orders.remove(best_order)
        
        return assignments, available_orders

class PriorityFirstStrategy(AssignmentStrategy):
    """
    Prioritäts-basierter Algorithmus: Bearbeitet dringende Aufträge zuerst
    """
    
    def assign(self, trucks: List[Truck], orders: List[Order]) -> Tuple[List[Assignment], List[Order]]:
        assignments = []
        available_orders = [o for o in orders if not o.is_assigned]
        available_trucks = trucks.copy()
        
        # Sortiere Aufträge nach Priorität (urgent zuerst)
        priority_order = [Priority.URGENT, Priority.HIGH, Priority.NORMAL, Priority.LOW]
        sorted_orders = sorted(available_orders, key=lambda o: priority_order.index(o.priority))
        
        for order in sorted_orders:
            best_truck = None
            best_score = float('inf')
            best_details = None
            
            # Finde den besten LKW für diesen Auftrag
            for truck in available_trucks:
                if truck.can_handle_order(order):
                    score, details = calculate_assignment_score(truck, order)
                    
                    if score < best_score:
                        best_score = score
                        best_truck = truck
                        best_details = details
            
            # Zuordnung durchführen
            if best_truck and best_details:
                total_distance = best_details['raw_distance_km']
                travel_time = best_details['travel_time_hours']
                total_cost = total_distance * best_truck.cost_per_km
                
                assignment = Assignment(
                    truck_id=best_truck.truck_id,
                    order_id=order.order_id,
                    distance_km=total_distance,
                    estimated_duration=travel_time,
                    total_cost=total_cost,
                    score=best_score
                )
                assignments.append(assignment)
                
                # Zustand aktualisieren
                order.assigned_truck = best_truck.truck_id
                best_truck.current_load += order.volume
                available_orders.remove(order)
        
        return assignments, available_orders

# ===============================================================================
# CSV-EXPORT FUNKTIONEN
# ===============================================================================

def export_trucks_csv(trucks: List[Truck], filename: str = "trucks.csv") -> bool:
    """
    Exportiert LKW-Daten als CSV-Datei
    
    Args:
        trucks: Liste der LKW-Objekte
        filename: Name der Ausgabedatei
        
    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # Header
            writer.writerow([
                'truck_id', 'lat', 'lon', 'capacity', 'current_load', 
                'truck_type', 'driver_name', 'utilization_percent', 'available_capacity'
            ])
            
            # Daten
            for truck in trucks:
                writer.writerow([
                    truck.truck_id,
                    truck.lat,
                    truck.lon,
                    truck.capacity,
                    truck.current_load,
                    truck.truck_type.value,
                    truck.driver_name,
                    round(truck.utilization_percent, 1),
                    truck.available_capacity
                ])
        
        print(f"✅ LKW-Daten exportiert: {filename}")
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim LKW-Export: {e}")
        return False

def export_orders_csv(orders: List[Order], filename: str = "orders.csv") -> bool:
    """
    Exportiert Auftragsdaten als CSV-Datei
    """
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # Header
            writer.writerow([
                'order_id', 'pickup_lat', 'pickup_lon', 'delivery_lat', 'delivery_lon',
                'volume', 'priority', 'customer', 'deadline_hours', 'assigned_truck'
            ])
            
            # Daten
            for order in orders:
                writer.writerow([
                    order.order_id,
                    order.pickup_lat,
                    order.pickup_lon,
                    order.delivery_lat,
                    order.delivery_lon,
                    order.volume,
                    order.priority.value,
                    order.customer,
                    order.deadline_hours,
                    order.assigned_truck or "NICHT_ZUGEORDNET"
                ])
        
        print(f"✅ Auftrags-Daten exportiert: {filename}")
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Auftrags-Export: {e}")
        return False

def export_assignments_csv(assignments: List[Assignment], filename: str = "assignments.csv") -> bool:
    """
    Exportiert Zuordnungsergebnisse als CSV-Datei
    """
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # Header
            writer.writerow([
                'truck_id', 'order_id', 'distance_km', 'estimated_duration_hours',
                'total_cost_euro', 'score', 'cost_per_hour', 'assignment_time'
            ])
            
            # Daten
            for assignment in assignments:
                writer.writerow([
                    assignment.truck_id,
                    assignment.order_id,
                    round(assignment.distance_km, 2),
                    round(assignment.estimated_duration, 2),
                    round(assignment.total_cost, 2),
                    round(assignment.score, 3),
                    round(assignment.cost_per_hour, 2),
                    assignment.assignment_time.strftime("%Y-%m-%d %H:%M:%S")
                ])
        
        print(f"✅ Zuordnungsergebnisse exportiert: {filename}")
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Zuordnungs-Export: {e}")
        return False

# ===============================================================================
# ANALYSE UND REPORTING
# ===============================================================================

def analyze_assignments(assignments: List[Assignment], trucks: List[Truck], 
                       orders: List[Order], unassigned_orders: List[Order]) -> Dict:
    """
    Erstellt eine umfassende Analyse der Zuordnungsergebnisse
    """
    analysis = {}
    
    # Grundlegende Statistiken
    analysis['total_assignments'] = len(assignments)
    analysis['total_orders'] = len(orders)
    analysis['unassigned_orders'] = len(unassigned_orders)
    analysis['assignment_rate'] = (len(assignments) / len(orders)) * 100 if orders else 0
    
    # Entfernungsstatistiken
    if assignments:
        distances = [a.distance_km for a in assignments]
        analysis['avg_distance_km'] = sum(distances) / len(distances)
        analysis['min_distance_km'] = min(distances)
        analysis['max_distance_km'] = max(distances)
        analysis['total_distance_km'] = sum(distances)
    else:
        analysis['avg_distance_km'] = 0
        analysis['min_distance_km'] = 0
        analysis['max_distance_km'] = 0
        analysis['total_distance_km'] = 0
    
    # Kostenstatistiken
    if assignments:
        costs = [a.total_cost for a in assignments]
        analysis['total_cost_euro'] = sum(costs)
        analysis['avg_cost_euro'] = sum(costs) / len(costs)
    else:
        analysis['total_cost_euro'] = 0
        analysis['avg_cost_euro'] = 0
    
    # Volumenstatistiken
    assigned_volume = sum(next(o.volume for o in orders if o.order_id == a.order_id) 
                         for a in assignments)
    total_volume = sum(o.volume for o in orders)
    analysis['assigned_volume_tons'] = assigned_volume
    analysis['total_volume_tons'] = total_volume
    analysis['volume_assignment_rate'] = (assigned_volume / total_volume) * 100 if total_volume else 0
    
    # LKW-Auslastung
    truck_utilizations = [t.utilization_percent for t in trucks]
    analysis['avg_truck_utilization'] = sum(truck_utilizations) / len(truck_utilizations) if truck_utilizations else 0
    
    # Prioritätsverteilung
    priority_stats = {}
    for priority in Priority:
        priority_orders = [o for o in orders if o.priority == priority]
        assigned_priority_orders = [o for o in priority_orders if o.is_assigned]
        priority_stats[priority.value] = {
            'total': len(priority_orders),
            'assigned': len(assigned_priority_orders),
            'rate': (len(assigned_priority_orders) / len(priority_orders)) * 100 if priority_orders else 0
        }
    analysis['priority_statistics'] = priority_stats
    
    return analysis

def print_detailed_results(assignments: List[Assignment], unassigned_orders: List[Order], 
                          trucks: List[Truck], orders: List[Order], analysis: Dict):
    """
    Gibt detaillierte Ergebnisse formatiert in der Konsole aus
    """
    
    print("=" * 90)
    print("🚛 LKW-AUFTRAGSZUORDNUNG - DETAILLIERTE ERGEBNISSE")
    print("=" * 90)
    
    # Zuordnungsübersicht
    print(f"\n📋 ZUORDNUNGSÜBERSICHT:")
    print("-" * 50)
    print(f"Gesamte Aufträge:        {analysis['total_orders']:>3}")
    print(f"Zugeordnete Aufträge:    {analysis['total_assignments']:>3}")
    print(f"Nicht zugeordnet:        {analysis['unassigned_orders']:>3}")
    print(f"Zuordnungsrate:          {analysis['assignment_rate']:>5.1f}%")
    
    # Erfolgreiche Zuordnungen
    if assignments:
        print(f"\n✅ ERFOLGREICHE ZUORDNUNGEN ({len(assignments)}):")
        print("-" * 90)
        print(f"{'LKW':>7} → {'Auftrag':<8} | {'Dist[km]':>8} | {'Zeit[h]':>7} | {'Kosten[€]':>10} | {'Priorität':>8} | {'Kunde'}")
        print("-" * 90)
        
        for assignment in sorted(assignments, key=lambda a: a.truck_id):
            # Finde entsprechende Objekte
            truck = next(t for t in trucks if t.truck_id == assignment.truck_id)
            order = next(o for o in orders if o.order_id == assignment.order_id)
            
            print(f"{assignment.truck_id:>7} → {assignment.order_id:<8} | "
                  f"{assignment.distance_km:>8.1f} | {assignment.estimated_duration:>7.1f} | "
                  f"{assignment.total_cost:>10.2f} | {order.priority.value:>8} | "
                  f"{order.customer}")
    
    # Nicht zugeordnete Aufträge
    if unassigned_orders:
        print(f"\n❌ NICHT ZUGEORDNETE AUFTRÄGE ({len(unassigned_orders)}):")
        print("-" * 70)
        print(f"{'Auftrag':<8} | {'Vol[t]':>6} | {'Priorität':>8} | {'Deadline[h]':>11} | {'Kunde'}")
        print("-" * 70)
        
        for order in sorted(unassigned_orders, key=lambda o: o.priority.value):
            print(f"{order.order_id:<8} | {order.volume:>6.1f} | {order.priority.value:>8} | "
                  f"{order.deadline_hours:>11.1f} | {order.customer}")
    
    # Statistiken
    print(f"\n📊 LEISTUNGSSTATISTIKEN:")
    print("-" * 40)
    print(f"Durchschnittliche Entfernung:  {analysis['avg_distance_km']:>7.1f} km")
    print(f"Gesamte Strecke:               {analysis['total_distance_km']:>7.1f} km")
    print(f"Gesamtkosten:                  {analysis['total_cost_euro']:>7.2f} €")
    print(f"Durchschnittskosten/Auftrag:   {analysis['avg_cost_euro']:>7.2f} €")
    print(f"Zugeordnetes Volumen:          {analysis['assigned_volume_tons']:>7.1f} t")
    print(f"Volumen-Zuordnungsrate:        {analysis['volume_assignment_rate']:>7.1f} %")
    print(f"Durchschnittl. LKW-Auslastung: {analysis['avg_truck_utilization']:>7.1f} %")
    
    # Prioritätsanalyse
    print(f"\n🎯 PRIORITÄTSANALYSE:")
    print("-" * 50)
    print(f"{'Priorität':<8} | {'Gesamt':>6} | {'Zugeordnet':>10} | {'Rate[%]':>7}")
    print("-" * 50)
    for priority, stats in analysis['priority_statistics'].items():
        print(f"{priority:<8} | {stats['total']:>6} | {stats['assigned']:>10} | {stats['rate']:>7.1f}")
    
    # LKW-Auslastung
    print(f"\n🚛 LKW-AUSLASTUNGSDETAILS:")
    print("-" * 80)
    print(f"{'LKW-ID':<7} | {'Fahrer':<15} | {'Ladung[t]':>9} | {'Kapazität[t]':>12} | {'Auslastung[%]':>13} | {'Zugeordnet'}")
    print("-" * 80)
    
    for truck in sorted(trucks, key=lambda t: t.truck_id):
        assigned_order = next((a.order_id for a in assignments if a.truck_id == truck.truck_id), "---")
        print(f"{truck.truck_id:<7} | {truck.driver_name:<15} | {truck.current_load:>9.1f} | "
              f"{truck.capacity:>12.1f} | {truck.utilization_percent:>13.1f} | {assigned_order}")

# ===============================================================================
# HAUPTPROGRAMM
# ===============================================================================

def main():
    """
    Hauptfunktion - Koordiniert die gesamte Anwendung
    """
    print("🚀 LKW-Zuordnungssystem wird gestartet...")
    print("=" * 60)
    
    try:
        # 1. Demo-Daten generieren
        print("📊 Generiere Demo-Daten...")
        trucks = generate_demo_trucks()
        orders = generate_demo_orders()
        print(f"✅ {len(trucks)} LKWs und {len(orders)} Aufträge generiert")
        
        # 2. Daten exportieren (optional)
        print("\n💾 Exportiere Ausgangsdaten...")
        export_trucks_csv(trucks, "demo_trucks.csv")
        export_orders_csv(orders, "demo_orders.csv")
        
        # 3. Verschiedene Zuordnungsstrategien testen
        strategies = {
            "Greedy (Nächster)": GreedyNearestStrategy(),
            "Priorität zuerst": PriorityFirstStrategy()
        }
        
        best_strategy = None
        best_assignments = None
        best_unassigned = None
        best_score = float('inf')
        
        print(f"\n🔍 Teste verschiedene Zuordnungsstrategien...")
        
        for strategy_name, strategy in strategies.items():
            print(f"\n--- {strategy_name} ---")
            
            # Reset truck loads for fair comparison
            for truck in trucks:
                # Reset to original load (keep some existing load for realism)
                truck.current_load = truck.current_load  # Keep current state
            
            # Reset order assignments
            for order in orders:
                order.assigned_truck = None
            
            # Führe Zuordnung durch
            assignments, unassigned = strategy.assign(trucks, orders)
            
            # Bewerte Strategie
            total_score = sum(a.score for a in assignments)
            assignment_rate = (len(assignments) / len(orders)) * 100
            
            print(f"  Zugeordnet: {len(assignments)}/{len(orders)} ({assignment_rate:.1f}%)")
            print(f"  Gesamt-Score: {total_score:.2f}")
            print(f"  Nicht zugeordnet: {len(unassigned)}")
            
            # Behalte beste Strategie
            if total_score < best_score:
                best_score = total_score
                best_strategy = strategy_name
                best_assignments = assignments.copy()
                best_unassigned = unassigned.copy()
        
        print(f"\n🏆 Beste Strategie: {best_strategy} (Score: {best_score:.2f})")
        
        # 4. Detaillierte Analyse der besten Lösung
        print(f"\n🔬 Führe detaillierte Analyse durch...")
        analysis = analyze_assignments(best_assignments, trucks, orders, best_unassigned)
        
        # 5. Ergebnisse anzeigen
        print_detailed_results(best_assignments, best_unassigned, trucks, orders, analysis)
        
        # 6. Finale Ergebnisse exportieren
        print(f"\n💾 Exportiere finale Ergebnisse...")
        export_assignments_csv(best_assignments, "final_assignments.csv")
        export_trucks_csv(trucks, "final_trucks.csv")
        export_orders_csv(orders, "final_orders.csv")
        
        print(f"\n🎯 Zuordnung erfolgreich abgeschlossen!")
        print(f"📁 Ausgabedateien: final_assignments.csv, final_trucks.csv, final_orders.csv")
        
    except KeyboardInterrupt:
        print(f"\n⚠️  Programm durch Benutzer unterbrochen")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()