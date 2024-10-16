# VRP_OSM.py

import requests
import math
import json
import polyline

def create_data_model(): # Fonction de création de modèle de données
    data = {}
    data['coordinates'] = [
        (48.3144, 4.0268),  # Coordonnées du dépôt
        (48.2980, 4.0771),  # Libération
        (48.2956, 4.0719),  # Audiffred
        (48.2979, 4.0736),  # Huez
        (48.2974, 4.0672),  # Gambetta - Deschainets
        (48.2983, 4.0692),  # Gambetta - N°44
        (48.2992, 4.0718),  # Gambetta - Paix
        (48.3003, 4.0761),  # Cordeliers
        (48.3025, 4.0760),  # Danton - Tour
        (48.3036, 4.0779),  # Danton - Parking
        (48.3040, 4.0829),  # Abattoir
        (48.3012, 4.0857),  # Michelet
        (48.2995, 4.0842),  # Courtine
        (48.2971, 4.0843),  # Margerite Bourgeois
        (48.2941, 4.0779),  # 14 Juillet
        (48.2920, 4.0725),  # 1er RAM
        (48.2928, 4.0713),  # Viardin
        (48.2939, 4.0732),  # Général Saussier
        (48.2951, 4.0695),  # Monnaie
        (48.2951, 4.0681),  # Carnot - Patton
        (48.2963, 4.0738),  # Urbain IV
        (48.2961, 4.0758)   # Langevin
    ]
    data['full_bins'] = [
        False, True, False, True, False, True, False, True, False, True,
        True, False, True, False, True, False, True, False, True, False,
        True, False
    ]
    data['num_camions'] = 6 # Nombre de camions
    data['depot'] = 0 # Indice du dépôt dans les coordonnées
    return data

def get_address_from_coordinates(latitude, longitude): # Fonction de récupération d'adresse à partir de coordonnées via Nominatim API
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        'format': 'json',
        'lat': latitude,
        'lon': longitude,
        'zoom': 18,
        'addressdetails': 1
    }
    headers = {
        'User-Agent': 'MyGeoApp'
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Ceci lève une exception pour les codes d'erreur HTTP
        data = response.json()
        address = data.get('display_name')
        return address
    except requests.RequestException as e:
        print(f"Error fetching address: {e}")
        return "Adresse non trouvée"

def distance(coord1, coord2): # Fonction de calcul de distance d'Haversine entre deux coordonnées
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    r = 6371  # Rayon terrestre en km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) * math.sin(dlon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c

def calculate_distance(data, solution):
    """Calculates the total distance traveled for the solution."""
    total_distance = 0
    for i in range(len(solution) - 1):
        total_distance += distance(data['coordinates'][solution[i]], data['coordinates'][solution[i + 1]])
    return total_distance

def nearest_neighbor(data): # Fonction de construction des itinéraires complets pour tout les camions
    unvisited_nodes = [i for i in range(len(data['coordinates'])) if data['full_bins'][i]]
    current_node = data['depot']
    solution = [current_node]

    while unvisited_nodes:
        nearest_node = min(unvisited_nodes, key=lambda x: distance(data['coordinates'][current_node], data['coordinates'][x]))
        solution.append(nearest_node)
        unvisited_nodes.remove(nearest_node)
        current_node = nearest_node

    solution.append(data['depot'])
    return solution

def get_route_from_osrm(start, end):
    """Obtient un itinéraire de OSRM entre deux points."""
    osrm_url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=full"
    response = requests.get(osrm_url)
    if response.status_code == 200:
        data = response.json()
        try:
            route_polyline = data['routes'][0]['geometry']
            route_coords = polyline.decode(route_polyline)
            route_coords = [[lat, lon] for lon, lat in route_coords]
            print("Route coordinates:", route_coords)  # Ajout de débogage pour vérifier les coordonnées
            return route_coords
        except Exception as e:  # Capture des exceptions plus générales pour le débogage
            print(f"Error parsing OSRM response: {e}")
            print("Received data:", data)
            return []
    else:
        print(f"Failed to get response from OSRM API, status code: {response.status_code}, response: {response.text}")
        return []

def run(data):
    model = create_data_model()
    model['num_camions'] = data['num_camions']
    all_nodes = [i for i in range(len(model['coordinates'])) if model['full_bins'][i]]
    routes = []

    nodes_per_camion = {i: [] for i in range(data['num_camions'])}
    for idx, node in enumerate(all_nodes):
        nodes_per_camion[idx % data['num_camions']].append(node)

    for camion_id in range(data['num_camions']):
        vehicle_route = [model['depot']] + nodes_per_camion[camion_id] + [model['depot']]
        route_coords = []
        instructions = []
        total_distance = 0

        print(f"Route for camion {camion_id}: {vehicle_route}")  # Debugging output

        for i in range(len(vehicle_route) - 1):
            start = model['coordinates'][vehicle_route[i]]
            end = model['coordinates'][vehicle_route[i + 1]]
            segment_distance = distance(start, end)  # Distance calculée par la formule de Haversine
            total_distance += segment_distance  # Distaance totale pour cet itinéraire
            route_segment = get_route_from_osrm(start, end)
            route_coords.extend(route_segment)
            start_address = get_address_from_coordinates(*start)
            end_address = get_address_from_coordinates(*end)
            instructions.append(f"Allez de {start_address} à {end_address}")

        routes.append({
            'coordinates': [(lat, lon) for lon, lat in route_coords],
            'instructions': instructions,
            'total_distance': total_distance,
            'num_stops': len(vehicle_route) - 2  # -2 car le dépôt est inclus dans la route
        })

    return {'Routes': routes}

def nearest_neighbor_for_camion(model, nodes): # Fonction de construction d'itinéraire pour un seul camion
    current_node = model['depot']
    solution = [current_node]

    unvisited_nodes = nodes.copy()

    while unvisited_nodes:
        nearest_node = min(unvisited_nodes, key=lambda x: distance(model['coordinates'][current_node], model['coordinates'][x]))
        solution.append(nearest_node)
        unvisited_nodes.remove(nearest_node)
        current_node = nearest_node

    solution.append(model['depot'])  # Assurance de terminer au dépôt
    return solution

def generate_route_for_camion(model, solution):
    route_coords = []
    instructions = []

    for i in range(len(solution) - 1):
        start_idx = solution[i]
        end_idx = solution[i + 1]
        start = model['coordinates'][start_idx]
        end = model['coordinates'][end_idx]
        start_address = get_address_from_coordinates(*start)
        end_address = get_address_from_coordinates(*end)
        route_segment = get_route_from_osrm(start, end)
        route_coords.extend(route_segment)
        instructions.append(f"Allez de {start_address} à {end_address}")

    return {
        'Objective': calculate_distance(model, solution),
        'Routes': {
            'coordinates': [(lat, lon) for lon, lat in route_coords],
            'instructions': instructions
        }
    }


def main():
    data = create_data_model()
    addresses = [get_address_from_coordinates(lat, lon) for lat, lon in data['coordinates']]
    
    solution = nearest_neighbor(data)
    total_distance = calculate_distance(data, solution)

    print('Distance totale optimisée: {:.2f} km'.format(total_distance))
    for camion_id in range(data['num_camions']):
        route = solution[camion_id::data['num_camions']]
        route.append(data['depot'])  # Chaque itinéraire doit se terminer au dépôt

        print(f'\nRoute camion {camion_id}:')
        print('- Départ :', addresses[data['depot']])
        for node in route[1:-1]:
            print('- Prochaine étape, allez à', addresses[node])
        print('- Etape finale : ', addresses[data['depot']])
        print('Distance trajet: {:.2f} km'.format(calculate_distance(data, route)))

if __name__ == '__main__':
    main()

