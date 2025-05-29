import csv
import math
import random
import os

def generate_demo_data(num_trucks=200, num_orders=300, seed=42):
    random.seed(seed)
    trucks = []
    orders = []
    # Generate random coords in a 100x100 grid
    for i in range(1, num_trucks + 1):
        lat = random.uniform(0, 100)
        lon = random.uniform(0, 100)
        trucks.append({'id': f'Truck_{i}', 'lat': lat, 'lon': lon})
    for j in range(1, num_orders + 1):
        lat = random.uniform(0, 100)
        lon = random.uniform(0, 100)
        orders.append({'id': f'Order_{j}', 'lat': lat, 'lon': lon})
    return trucks, orders


def save_to_csv(data, filename, fieldnames):
    with open(filename, mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def load_from_csv(filename):
    with open(filename, mode='r', newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)


def euclidean_distance(a, b):
    return math.hypot(float(a['lat']) - float(b['lat']), float(a['lon']) - float(b['lon']))


def greedy_assignment(trucks, orders):
    assignments = []
    remaining_trucks = trucks.copy()
    remaining_orders = orders.copy()

    while remaining_trucks and remaining_orders:
        best_pair = None
        best_dist = float('inf')
        # find global closest pair
        for t in remaining_trucks:
            for o in remaining_orders:
                d = euclidean_distance(t, o)
                if d < best_dist:
                    best_dist = d
                    best_pair = (t, o)
        # assign the best pair
        t, o = best_pair
        assignments.append({'truck_id': t['id'], 'order_id': o['id'], 'distance': round(best_dist, 2)})
        # remove assigned
        remaining_trucks.remove(t)
        remaining_orders.remove(o)

    return assignments


def main():
    # Filenames
    trucks_file = 'trucks.csv'
    orders_file = 'orders.csv'
    output_file = 'assignments.csv'

    # Generate demo CSVs if not exist
    if not os.path.exists(trucks_file) or not os.path.exists(orders_file):
        trucks, orders = generate_demo_data()
        save_to_csv(trucks, trucks_file, fieldnames=['id', 'lat', 'lon'])
        save_to_csv(orders, orders_file, fieldnames=['id', 'lat', 'lon'])
        print(f"Demo data generated: {trucks_file}, {orders_file}")

    # Load data
    trucks = load_from_csv(trucks_file)
    orders = load_from_csv(orders_file)

    # Compute assignments
    assignments = greedy_assignment(trucks, orders)

    # Save assignments
    save_to_csv(assignments, output_file, fieldnames=['truck_id', 'order_id', 'distance'])
    print(f"Assignments saved to {output_file}")

if __name__ == '__main__':
    main()
