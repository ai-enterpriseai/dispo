# lkw_optimierung_v2.py
# Benötigte Bibliotheken: pulp
# Installation: pip install pulp
# encoding: utf-8

import math
import csv
import io
import os
from datetime import datetime
import random

# Versuche, pulp zu importieren und gib eine klare Fehlermeldung, falls nicht vorhanden
try:
    import pulp
except ImportError:
    print("FEHLER: Die Bibliothek 'pulp' wurde nicht gefunden.")
    print("Bitte installieren Sie sie mit: pip install pulp")
    exit()

# --- 1. Konstanten und Konfiguration ---
RANDOM_SEED = 42 # Beibehaltung für Konsistenz der generierten Daten
random.seed(RANDOM_SEED)

NUM_LKWS = 10
NUM_AUFTRAEGE = 15
MAX_KOORDINATE = 100  # km
DURCHSCHNITTSGESCHWINDIGKEIT_KMH = 50.0 # km/h

# Zeitliche Annahmen (in Stunden ab Simulationsstart, z.B. 0.0 = Mitternacht)
SIMULATIONSSTART_H = 0.0
MIN_LKW_VERFUEGBAR_AB_H = 7.0
MAX_LKW_VERFUEGBAR_AB_H = 9.0
MIN_LKW_VERFUEGBAR_DAUER_H = 8.0
MAX_LKW_VERFUEGBAR_DAUER_H = 10.0

MIN_AUFTRAG_LADEFENSTER_FRUEH_H = 8.0
MAX_AUFTRAG_LADEFENSTER_FRUEH_H = 14.0
MIN_AUFTRAG_LADEFENSTER_DAUER_H = 1.0
MAX_AUFTRAG_LADEFENSTER_DAUER_H = 4.0
MIN_LADEDAUER_H = 0.5
MAX_LADEDAUER_H = 1.5

# Kapazitäten und Gewichte
MAX_LKW_KAPAZITAET_KG = 25000
MIN_LKW_KAPAZITAET_KG = 10000
MAX_AUFTRAG_GEWICHT_KG = 12000
MIN_AUFTRAG_GEWICHT_KG = 500
PRIORITAETEN_MAP = {1: 3, 2: 2, 3: 1}  # Mapping: Prio-Wert -> Gewicht (höher ist besser)
                                      # Originale Prio-Werte: 1=Hoch, 2=Mittel, 3=Niedrig

# Faktoren für die Zielfunktion (NEU)
# Ziel: Maximiere (PRIO_GEWICHT_FAKTOR * PrioGewicht - DISTANZ_KOSTEN_FAKTOR * Distanz)
# Wähle diese Faktoren so, dass die Priorität einen größeren Einfluss hat als die Distanz.
PRIO_GEWICHT_FAKTOR = 10000  # Großer Wert, um Zuweisung von Aufträgen mit Prio zu belohnen
DISTANZ_KOSTEN_FAKTOR = 1    # Kleinerer Wert, um Distanz als "Strafe" einzubeziehen

OUTPUT_DIR = "optimierungs_ergebnisse_v2"

# --- 2. Klassendefinitionen ---
class LKW:
    def __init__(self, lkw_id, standort_x, standort_y, kapazitaet_kg, verfuegbar_ab_h, verfuegbar_bis_h):
        self.lkw_id = lkw_id
        self.standort = (standort_x, standort_y)
        self.kapazitaet_kg = kapazitaet_kg
        self.verfuegbar_ab_h = verfuegbar_ab_h
        self.verfuegbar_bis_h = verfuegbar_bis_h

    def __repr__(self):
        return (f"LKW(ID: {self.lkw_id}, Standort: {self.standort}, Kap: {self.kapazitaet_kg}kg, "
                f"Verfügbar: {self.verfuegbar_ab_h:.2f}h - {self.verfuegbar_bis_h:.2f}h)")

class Auftrag:
    def __init__(self, auftrag_id, ladestelle_x, ladestelle_y, entladestelle_x, entladestelle_y,
                 gewicht_kg, ladefenster_frueh_h, ladefenster_spaet_h, ladedauer_h, prioritaet):
        self.auftrag_id = auftrag_id
        self.ladestelle = (ladestelle_x, ladestelle_y)
        self.entladestelle = (entladestelle_x, entladestelle_y)
        self.gewicht_kg = gewicht_kg
        self.ladefenster_frueh_h = ladefenster_frueh_h
        self.ladefenster_spaet_h = ladefenster_spaet_h
        self.ladedauer_h = ladedauer_h
        self.prioritaet = prioritaet # Ursprünglicher Prio-Wert (1, 2 oder 3)

    def __repr__(self):
        return (f"Auftrag(ID: {self.auftrag_id}, Ladestelle: {self.ladestelle}, Gew: {self.gewicht_kg}kg, "
                f"Fenster: {self.ladefenster_frueh_h:.2f}h-{self.ladefenster_spaet_h:.2f}h, "
                f"Ladedauer: {self.ladedauer_h:.2f}h, Prio: {self.prioritaet})")

# --- 3. Hilfsfunktionen ---
def berechne_distanz(punkt1, punkt2):
    return math.sqrt((punkt1[0] - punkt2[0])**2 + (punkt1[1] - punkt2[1])**2)

def berechne_fahrzeit_h(distanz_km):
    if DURCHSCHNITTSGESCHWINDIGKEIT_KMH <= 0:
        return float('inf')
    return distanz_km / DURCHSCHNITTSGESCHWINDIGKEIT_KMH

def daten_zu_csv_string(daten_liste_objekte, klassen_name):
    if not daten_liste_objekte:
        return f"Keine Daten für {klassen_name} vorhanden.\n"
    daten_liste_dicts = [vars(obj) for obj in daten_liste_objekte]
    output = io.StringIO()
    feldnamen = list(daten_liste_dicts[0].keys())
    writer = csv.DictWriter(output, fieldnames=feldnamen)
    writer.writeheader()
    writer.writerows(daten_liste_dicts)
    return output.getvalue()

def speichere_csv_datei(csv_string, dateiname_praefix):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dateiname = f"{dateiname_praefix}_{timestamp}.csv"
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
        voller_pfad = os.path.join(OUTPUT_DIR, dateiname)
        with open(voller_pfad, 'w', newline='', encoding='utf-8') as f:
            f.write(csv_string)
        print(f"Daten erfolgreich gespeichert in: {voller_pfad}")
        return True
    except IOError as e:
        print(f"Fehler beim Speichern der Datei {dateiname}: {e}")
        return False

# --- 4. Datengenerierung ---
def generiere_lkw_daten(anzahl):
    lkws = []
    for i in range(1, anzahl + 1):
        verfuegbar_ab = round(random.uniform(MIN_LKW_VERFUEGBAR_AB_H, MAX_LKW_VERFUEGBAR_AB_H), 2)
        verfuegbar_bis = round(verfuegbar_ab + random.uniform(MIN_LKW_VERFUEGBAR_DAUER_H, MAX_LKW_VERFUEGBAR_DAUER_H), 2)
        lkws.append(LKW(
            lkw_id=f"LKW{i}",
            standort_x=round(random.uniform(0, MAX_KOORDINATE), 2),
            standort_y=round(random.uniform(0, MAX_KOORDINATE), 2),
            kapazitaet_kg=random.randint(MIN_LKW_KAPAZITAET_KG // 1000, MAX_LKW_KAPAZITAET_KG // 1000) * 1000,
            verfuegbar_ab_h=verfuegbar_ab,
            verfuegbar_bis_h=verfuegbar_bis
        ))
    return lkws

def generiere_auftrags_daten(anzahl):
    auftraege = []
    for i in range(1, anzahl + 1):
        ladefenster_frueh = round(random.uniform(MIN_AUFTRAG_LADEFENSTER_FRUEH_H, MAX_AUFTRAG_LADEFENSTER_FRUEH_H), 2)
        ladefenster_spaet = round(ladefenster_frueh + random.uniform(MIN_AUFTRAG_LADEFENSTER_DAUER_H, MAX_AUFTRAG_LADEFENSTER_DAUER_H), 2)
        ladedauer = round(random.uniform(MIN_LADEDAUER_H, MAX_LADEDAUER_H), 2)
        if ladefenster_spaet < ladefenster_frueh + ladedauer:
            ladefenster_spaet = ladefenster_frueh + ladedauer + 0.1
        auftraege.append(Auftrag(
            auftrag_id=f"AUF{i}",
            ladestelle_x=round(random.uniform(0, MAX_KOORDINATE), 2),
            ladestelle_y=round(random.uniform(0, MAX_KOORDINATE), 2),
            entladestelle_x=round(random.uniform(0, MAX_KOORDINATE), 2),
            entladestelle_y=round(random.uniform(0, MAX_KOORDINATE), 2),
            gewicht_kg=random.randint(MIN_AUFTRAG_GEWICHT_KG // 100, MAX_AUFTRAG_GEWICHT_KG // 100) * 100,
            ladefenster_frueh_h=ladefenster_frueh,
            ladefenster_spaet_h=ladefenster_spaet,
            ladedauer_h=ladedauer,
            prioritaet=random.choice(list(PRIORITAETEN_MAP.keys())) # Wählt 1, 2 oder 3
        ))
    return auftraege

# --- 5. LO-Modellierungsfunktionen ---
def ermittle_zulaessige_paare_und_werte(lkw_liste, auftrags_liste):
    """
    Ermittelt zulässige LKW-Auftrag-Paare und berechnet zugehörige Werte für die Zielfunktion.
    Ein Paar (lkw, auftrag) ist zulässig, wenn Kapazität und Zeitfenster passen.
    Zurückgegeben wird ein Dictionary:
    Key: (lkw.lkw_id, auftrag.auftrag_id)
    Value: Dictionary mit "distanz_gesamt", "prio_gewicht", "ladebeginn_calc_h", "ladeende_calc_h", etc.
    """
    zulaessige_paare = {}
    print("\nErmittle zulässige LKW-Auftrag-Paare und zugehörige Werte:")
    for lkw in lkw_liste:
        for auftrag in auftrags_liste:
            if lkw.kapazitaet_kg < auftrag.gewicht_kg:
                continue

            distanz_anfahrt = berechne_distanz(lkw.standort, auftrag.ladestelle)
            fahrzeit_anfahrt_h = berechne_fahrzeit_h(distanz_anfahrt)
            ankunft_ladestelle_real_h = lkw.verfuegbar_ab_h + fahrzeit_anfahrt_h
            ladebeginn_moeglich_h = max(ankunft_ladestelle_real_h, auftrag.ladefenster_frueh_h)
            ladeende_moeglich_h = ladebeginn_moeglich_h + auftrag.ladedauer_h

            if ladebeginn_moeglich_h > auftrag.ladefenster_spaet_h + 0.01: # Epsilon für Rundungstoleranz
                continue
            if ladebeginn_moeglich_h + auftrag.ladedauer_h > auftrag.ladefenster_spaet_h + 0.01:
                 continue
            if ladeende_moeglich_h > lkw.verfuegbar_bis_h + 0.01:
                continue
            
            distanz_transport = berechne_distanz(auftrag.ladestelle, auftrag.entladestelle)
            gesamtdistanz_fuer_auftrag = distanz_anfahrt + distanz_transport
            
            zulaessige_paare[(lkw.lkw_id, auftrag.auftrag_id)] = {
                "distanz_anfahrt": distanz_anfahrt,
                "distanz_transport": distanz_transport,
                "distanz_gesamt_fuer_auftrag": gesamtdistanz_fuer_auftrag,
                "prio_original": auftrag.prioritaet,
                "prio_gewicht": PRIORITAETEN_MAP.get(auftrag.prioritaet, 0), # Wert aus Mapping holen
                "ladebeginn_calc_h": ladebeginn_moeglich_h,
                "ladeende_calc_h": ladeende_moeglich_h
            }
    print(f"Anzahl zulässiger LKW-Auftrag-Paare gefunden: {len(zulaessige_paare)}")
    return zulaessige_paare

def erstelle_lo_modell(lkw_liste, auftrags_liste, zulaessige_paare_mit_werten):
    """Erstellt das lineare Optimierungsproblem mit PuLP."""
    
    # Problem definieren (Maximierung des "Nutzwerts")
    prob = pulp.LpProblem("LKW_Auftrags_Zuweisung_V2", pulp.LpMaximize)

    # Entscheidungsvariablen
    x_vars = pulp.LpVariable.dicts("x", 
                                   zulaessige_paare_mit_werten.keys(), 
                                   cat='Binary')

    # Zielfunktion: Maximiere (PRIO_GEWICHT_FAKTOR * PrioGewicht - DISTANZ_KOSTEN_FAKTOR * Distanz)
    # Dies belohnt Aufträge mit hoher Priorität und bestraft lange Distanzen.
    ziel_komponenten = []
    for paar_key, werte_dict in zulaessige_paare_mit_werten.items():
        belohnung_prio = PRIO_GEWICHT_FAKTOR * werte_dict["prio_gewicht"]
        strafe_distanz = DISTANZ_KOSTEN_FAKTOR * werte_dict["distanz_gesamt_fuer_auftrag"]
        nettowert_zuweisung = belohnung_prio - strafe_distanz
        ziel_komponenten.append(nettowert_zuweisung * x_vars[paar_key])
        
    prob += pulp.lpSum(ziel_komponenten), "Maximiere_Gewichteten_Nutzwert"

    # Nebenbedingungen:
    for auftrag in auftrags_liste:
        prob += pulp.lpSum([x_vars[(lkw.lkw_id, auftrag.auftrag_id)] 
                            for lkw in lkw_liste 
                            if (lkw.lkw_id, auftrag.auftrag_id) in x_vars]) <= 1, f"Auftrag_{auftrag.auftrag_id}_max_einmal"

    for lkw in lkw_liste:
        prob += pulp.lpSum([x_vars[(lkw.lkw_id, auftrag.auftrag_id)] 
                            for auftrag in auftrags_liste 
                            if (lkw.lkw_id, auftrag.auftrag_id) in x_vars]) <= 1, f"LKW_{lkw.lkw_id}_max_ein_Auftrag"
    
    return prob, x_vars # Gebe auch die Variablen zurück für einfachere Ergebnisextraktion

# --- 6. Lösungs- und Ergebnisfunktionen ---
def loese_optimierungsproblem(problem):
    print("\nStarte PuLP Optimierung...")
    # problem.writeLP("LKWZuordnungModell_v2.lp") # Optional zum Debuggen
    status = problem.solve()
    print(f"PuLP Optimierungsstatus: {pulp.LpStatus[status]}")
    return status

def extrahiere_und_zeige_ergebnisse(prob_obj, x_variablen_dict, lkw_liste, auftrags_liste, zulaessige_paare_mit_werten, status):
    zugewiesene_auftraege_details = []
    nicht_zugewiesene_auftraege_obj = list(auftrags_liste)
    lkw_auslastung = {lkw.lkw_id: {"zugewiesener_auftrag": None, "details": None} for lkw in lkw_liste}
    gesamter_zielfunktionswert = 0

    if status == pulp.LpStatusOptimal or status == pulp.LpStatusFeasible:
        print("\n--- Optimale Zuweisungsergebnisse ---")
        gesamter_zielfunktionswert = pulp.value(prob_obj.objective)
        print(f"Maximierter Gesamtnutzwert (Zielfunktion): {gesamter_zielfunktionswert:.2f}")
        
        aktive_zuweisungen_keys = []
        for key_tuple, pulp_var in x_variablen_dict.items():
            if pulp_var.varValue > 0.5: # Ist die Variable auf 1 gesetzt?
                aktive_zuweisungen_keys.append(key_tuple)
        
        print(f"Anzahl getätigter Zuweisungen: {len(aktive_zuweisungen_keys)}")

        for lkw_id, auftrag_id in aktive_zuweisungen_keys:
            werte_info = zulaessige_paare_mit_werten.get((lkw_id, auftrag_id))
            if not werte_info:
                print(f"Warnung: Werteinfo für aktive Zuweisung {lkw_id}-{auftrag_id} nicht gefunden.")
                continue

            lkw_obj = next((l for l in lkw_liste if l.lkw_id == lkw_id), None)
            auftrag_obj = next((a for a in auftrags_liste if a.auftrag_id == auftrag_id), None)

            if not lkw_obj or not auftrag_obj:
                print(f"Warnung: LKW oder Auftrag für Zuweisung {lkw_id}-{auftrag_id} nicht im Originaldatensatz gefunden.")
                continue

            detail = {
                "lkw_id": lkw_id,
                "auftrag_id": auftrag_id,
                "anfahrt_dist_km": werte_info["distanz_anfahrt"],
                "transport_dist_km": werte_info["distanz_transport"],
                "gesamtdistanz_fuer_auftrag_km": werte_info["distanz_gesamt_fuer_auftrag"],
                "ladebeginn_h": werte_info["ladebeginn_calc_h"],
                "ladeende_h": werte_info["ladeende_calc_h"],
                "auftrag_prio_original": auftrag_obj.prioritaet, # ursprüngliche Prio-Zahl
                "auftrag_prio_gewicht": werte_info["prio_gewicht"], # verwendetes Gewicht
                "auftrag_gewicht_kg": auftrag_obj.gewicht_kg,
                "lkw_kapazitaet_kg": lkw_obj.kapazitaet_kg
            }
            zugewiesene_auftraege_details.append(detail)
            lkw_auslastung[lkw_id]["zugewiesener_auftrag"] = auftrag_id
            lkw_auslastung[lkw_id]["details"] = detail
            
            if auftrag_obj in nicht_zugewiesene_auftraege_obj:
                nicht_zugewiesene_auftraege_obj.remove(auftrag_obj)

        zugewiesene_auftraege_details.sort(key=lambda x: (x["auftrag_prio_original"], x["lkw_id"]) ) # Sortierung
        gesamtdistanz_final_km = 0
        for detail in zugewiesene_auftraege_details:
            print(f"  LKW {detail['lkw_id']} -> Auftrag {detail['auftrag_id']} "
                  f"(Prio: {detail['auftrag_prio_original']}, Gew: {detail['auftrag_gewicht_kg']}kg, "
                  f"Gesamt-Dist: {detail['gesamtdistanz_fuer_auftrag_km']:.2f}km, "
                  f"Ladezeit: {detail['ladebeginn_h']:.2f}h-{detail['ladeende_h']:.2f}h)")
            gesamtdistanz_final_km += detail["gesamtdistanz_fuer_auftrag_km"]
        if zugewiesene_auftraege_details:
            print(f"Summe der Gesamtdistanzen für zugewiesene Aufträge: {gesamtdistanz_final_km:.2f} km")


    elif status == pulp.LpStatusInfeasible:
        print("Problem ist unlösbar (Infeasible). Keine gültige Zuweisung unter den gegebenen Bedingungen möglich.")
    else:
        print(f"Optimierung nicht erfolgreich. Status: {pulp.LpStatus[status]}")

    print("\n--- Nicht zugewiesene Aufträge ---")
    if nicht_zugewiesene_auftraege_obj:
        nicht_zugewiesene_auftraege_obj.sort(key=lambda a: (a.prioritaet, a.auftrag_id))
        for auftrag in nicht_zugewiesene_auftraege_obj:
            print(f"  Auftrag {auftrag.auftrag_id} (Prio: {auftrag.prioritaet}, Gew: {auftrag.gewicht_kg}kg, "
                  f"Fenster: {auftrag.ladefenster_frueh_h:.2f}-{auftrag.ladefenster_spaet_h:.2f})")
    else:
        print("  Alle Aufträge konnten zugewiesen werden oder es gab keine Aufträge.")
        
    return zugewiesene_auftraege_details, nicht_zugewiesene_auftraege_obj, lkw_auslastung

def ergebnisse_zu_csv_strings_lo(zugewiesene_details, nicht_zugewiesene_obj, lkw_auslastung_info, lkw_liste):
    zugewiesene_csv = io.StringIO()
    if zugewiesene_details:
        feldnamen_z = list(zugewiesene_details[0].keys())
        writer_z = csv.DictWriter(zugewiesene_csv, fieldnames=feldnamen_z)
        writer_z.writeheader()
        writer_z.writerows(zugewiesene_details)
    else:
        zugewiesene_csv.write("Keine Aufträge zugewiesen.\n")

    nicht_zug_csv = io.StringIO()
    if nicht_zugewiesene_obj:
        nicht_zug_dicts = [vars(obj) for obj in nicht_zugewiesene_obj]
        feldnamen_nz = list(nicht_zug_dicts[0].keys()) if nicht_zug_dicts else []
        if feldnamen_nz:
             writer_nz = csv.DictWriter(nicht_zug_csv, fieldnames=feldnamen_nz)
             writer_nz.writeheader()
             writer_nz.writerows(nicht_zug_dicts)
        else:
            nicht_zug_csv.write("Keine nicht zugewiesenen Aufträge zu melden (oder keine Felder definiert).\n")

    else:
        nicht_zug_csv.write("Alle Aufträge wurden zugewiesen oder es gab keine Aufträge.\n")
        
    lkw_auslast_csv = io.StringIO()
    lkw_auslast_daten = []
    for lkw in lkw_liste:
        auslastung = lkw_auslastung_info.get(lkw.lkw_id, {})
        details_dict = auslastung.get("details") 
        lkw_daten_eintrag = {
            "lkw_id": lkw.lkw_id,
            "kapazitaet_kg": lkw.kapazitaet_kg,
            "verfuegbar_ab_h": lkw.verfuegbar_ab_h,
            "verfuegbar_bis_h": lkw.verfuegbar_bis_h,
            "zugewiesener_auftrag_id": auslastung.get("zugewiesener_auftrag"),
            "anfahrt_dist_km": details_dict.get("anfahrt_dist_km") if details_dict else None,
            "transport_dist_km": details_dict.get("transport_dist_km") if details_dict else None,
            "gesamtdistanz_fuer_auftrag_km": details_dict.get("gesamtdistanz_fuer_auftrag_km") if details_dict else None,
            "ladebeginn_h": details_dict.get("ladebeginn_h") if details_dict else None,
            "ladeende_h": details_dict.get("ladeende_h") if details_dict else None
        }
        lkw_auslast_daten.append(lkw_daten_eintrag)
    
    if lkw_auslast_daten:
        feldnamen_lkw = list(lkw_auslast_daten[0].keys())
        writer_lkw = csv.DictWriter(lkw_auslast_csv, fieldnames=feldnamen_lkw)
        writer_lkw.writeheader()
        writer_lkw.writerows(lkw_auslast_daten)
    else:
        lkw_auslast_csv.write("Keine LKW-Daten vorhanden.\n")

    return zugewiesene_csv.getvalue(), nicht_zug_csv.getvalue(), lkw_auslast_csv.getvalue()

# --- 7. Main Funktion ---
def main_lo():
    print("=== LKW Zuweisungs-System mit Linearer Optimierung (PuLP) V2 ===")
    
    print(f"\nKonfiguration der Zielfunktion:")
    print(f"  PRIO_GEWICHT_FAKTOR: {PRIO_GEWICHT_FAKTOR} (Belohnung pro Prio-Gewichtspunkt)")
    print(f"  DISTANZ_KOSTEN_FAKTOR: {DISTANZ_KOSTEN_FAKTOR} (Strafe pro km Distanz)")
    print(f"  PRIORITAETEN_MAP (Prio -> Gewicht): {PRIORITAETEN_MAP}")

    # 1. Datengenerierung
    print("\n1. Generiere Demo-Datensätze...")
    lkw_liste = generiere_lkw_daten(NUM_LKWS)
    auftrags_liste = generiere_auftrags_daten(NUM_AUFTRAEGE)
    print(f"   {len(lkw_liste)} LKWs generiert.")
    print(f"   {len(auftrags_liste)} Aufträge generiert.")

    speichere_csv_datei(daten_zu_csv_string(lkw_liste, "LKW"), "rohdaten_lkw")
    speichere_csv_datei(daten_zu_csv_string(auftrags_liste, "Auftrag"), "rohdaten_auftraege")

    # 2. Ermittle zulässige Paare und Werte für Zielfunktion
    zulaessige_paare_mit_werten = ermittle_zulaessige_paare_und_werte(lkw_liste, auftrags_liste)
    if not zulaessige_paare_mit_werten:
        print("Keine zulässigen LKW-Auftrag-Paare gefunden. Abbruch der Optimierung.")
        return

    # 3. Erstelle LO-Modell
    print("\n2. Erstelle Lineares Optimierungsmodell...")
    optimierungsproblem, x_entscheidungsvariablen = erstelle_lo_modell(
        lkw_liste, auftrags_liste, zulaessige_paare_mit_werten
    )

    # 4. Löse Optimierungsproblem
    print("\n3. Löse Optimierungsproblem...")
    status = loese_optimierungsproblem(optimierungsproblem)
    
    # 5. Ergebnisse extrahieren und anzeigen
    print("\n4. Extrahiere und zeige Ergebnisse...")
    zug_details, nicht_zug_obj, lkw_auslast = extrahiere_und_zeige_ergebnisse(
        optimierungsproblem, x_entscheidungsvariablen, 
        lkw_liste, auftrags_liste, zulaessige_paare_mit_werten, status
    )

    # 6. Ergebnisse als CSV speichern
    print("\n5. Speichere Ergebnisse als CSV-Dateien...")
    csv_zug, csv_nicht_zug, csv_lkw_auslast = ergebnisse_zu_csv_strings_lo(
        zug_details, nicht_zug_obj, lkw_auslast, lkw_liste
    )
    speichere_csv_datei(csv_zug, "ergebnisse_zugewiesene_auftraege")
    speichere_csv_datei(csv_nicht_zug, "ergebnisse_nicht_zugewiesene_auftraege")
    speichere_csv_datei(csv_lkw_auslast, "ergebnisse_lkw_auslastung")

    print("\n=== Programm beendet ===")

if __name__ == "__main__":
    main_lo()