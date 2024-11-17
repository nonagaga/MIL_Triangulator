import math
import gmplot
import re

def bearing_to_slope(bearing: float) -> float:
    rad_bearing = math.radians(bearing)
    if bearing == 0:
        return math.inf
    elif 0 < bearing < 90:
        return 1/math.tan(rad_bearing)
    elif bearing == 90:
        return 0
    elif 90 < bearing < 180:
        return -math.tan(rad_bearing-math.pi/2)
    elif bearing == 180:
        return -math.inf
    elif 180 < bearing < 270:
        return 1/math.tan(rad_bearing-math.pi)
    elif bearing == 270:
        return 0
    elif 270 < bearing < 360:
        return -math.tan(rad_bearing-math.pi*(3/2))

def degree_minutes_seconds_to_decimal_degrees(degrees: str) -> float:
    components = re.split("°|'|\"", degrees)
    decimal_degrees = float(components[0])
    decimal_degrees += float(components[1])/60
    decimal_degrees += float(components[2])/3600
    return decimal_degrees

def forward_equirectangular_projection(lat, lon) -> (float, float):
    x = (lon - avg_lon) * math.cos(math.radians(avg_lat))
    y = (lat - avg_lat)
    return x,y

def reverse_equirectangular_projection(x, y) -> (float, float):
    lon = x/math.cos(math.radians(avg_lat)) + avg_lon
    lat = y + avg_lat
    return lat, lon


# takes 2 points in lat, long and their bearings to find a third point in lat long
def triangulate(coords1: (float, float), bearing1: float, coords2: (float, float), bearing2: float) -> (float, float):
    m1 = bearing_to_slope(bearing1)
    m2 = bearing_to_slope(bearing2)

    x1, y1 = forward_equirectangular_projection(coords1[0], coords1[1])
    x2, y2 = forward_equirectangular_projection(coords2[0], coords2[1])
    b1 = y1 - (m1 * x1)
    b2 = y2 - (m2 * x2)

    tri_x: float = 0
    tri_y: float = 0

    # handle edge cases where slope is infinite or 0
    if abs(m1) == math.inf:
        tri_x = x1
        if m2 == 0:
            tri_y = y2
        else:
            tri_y = m2 * tri_x + b2
    elif abs(m2) == math.inf:
        tri_x = x2
        if m1 == 0:
            tri_y = y1
        else:
            tri_y = m1 * tri_x + b1
    elif m1 == 0:
        tri_y = y1
        if m2 == math.inf:
            tri_x = x2
        else:
            tri_x = (tri_y - b2) / m2
    elif m2 == 0:
        tri_y = y2
        if m1 == math.inf:
            tri_x = x1
        else:
            tri_x = (tri_y - b1) / m1
    # normal case
    else:
        tri_x = (b2 - b1) / (m1 - m2)
        tri_y = m1 * tri_x + b1

    tri_lat, tri_lon = reverse_equirectangular_projection(tri_x, tri_y)
    return tri_lat, tri_lon


def bound_coordinates(coords, tri_coords):
    # gets bounding box for plotted coordinates
    max_lat = coords[0][1]
    min_lat = coords[0][1]
    max_lon = coords[1][1]
    min_lon = coords[1][1]
    for coord in coords[1:]:
        if coord[0] > max_lat:
            max_lat = coord[0]
        if coord[0] < min_lat:
            min_lat = coord[0]
        if coord[1] > max_lon:
            max_lon = coord[1]
        if coord[1] < min_lon:
            min_lon = coord[1]
    for tri_coord in tri_coords:
        if tri_coord[0] > max_lat:
            tri_lat = tri_coord[0]
        if tri_coord[0] < min_lat:
            tri_lat = tri_coord[0]
        if tri_coord[1] > max_lon:
            tri_lon = tri_coord[1]
        if tri_coord[1] < min_lon:
            tri_lon = tri_coord[1]
    return max_lat, min_lat, max_lon, min_lon

if __name__ == "__main__":
    # Create the map plotter:
    # Requires a google maps API key
    apikey = '' # (your API key here)

    coord1 = input("Enter first coordinate as latitude, longitude: ")
    bearing1 = input("Enter first bearing: ")
    coord2 = input("Enter second coordinate as latitude, longitude: ")
    bearing2 = input("Enter second bearing: ")

    lat1 = float(coord1.split(", ")[0])
    lon1 = float(coord1.split(", ")[1])
    lat2 = float(coord2.split(", ")[0])
    lon2 = float(coord2.split(", ")[1])

    decimal_lat1 = float(lat1)
    decimal_lat2 = float(lat2)
    decimal_lon1 = float(lon1)
    decimal_lon2 = float(lon2)

    bearing1 = float(bearing1)
    bearing2 = float(bearing2)

    coords: list[tuple[float, float]] = [(decimal_lat1, decimal_lon1), (decimal_lat2, decimal_lon2)]
    bearings: list[float] = [bearing1, bearing2]

    if abs(float(bearing1) - float(bearing2)) == 0 or abs(float(bearing2) - float(bearing1)) == 180:
        print("Bearings cannot be 0 or 180 degrees apart!")
        exit(1)

    third_coord_confirm = input("Would you like to enter a 3rd coordinate for higher precision? (y/n): ")
    if third_coord_confirm == 'y':
        coord3 = input("Enter third coordinate as latitude, longitude: ")
        bearing3 = input("Enter third bearing: ")
        lat3 = float(coord3.split(", ")[0])
        lon3 = float(coord3.split(", ")[1])
        bearing3 = float(bearing3)

        coords.append((lat3, lon3))
        bearings.append(bearing3)


    sum_lat: float = 0
    sum_lon: float = 0
    for tri_coord in coords:
        sum_lat += tri_coord[0]
        sum_lon += tri_coord[1]

    avg_lat = sum_lat/len(coords)
    avg_lon = sum_lon/len(coords)

    tri_coords: list[tuple[float, float]] = []
    if len(coords) == 2:
        tri_lat, tri_lon = triangulate(coords[0], bearings[0], coords[1], bearings[1])
        tri_coords.append((tri_lat, tri_lon))
    if len(coords) == 3:
        for i in range(3):
            tri_lat, tri_lon = triangulate(coords[i%3], bearings[i%3], coords[(i+1)%3], bearings[(i+1)%3])
            tri_coords.append((tri_lat, tri_lon))

    gmap = gmplot.GoogleMapPlotter(lat=avg_lat, lng=avg_lon, zoom=20, apikey=apikey, map_type='Satellite')

    max_lat, min_lat, max_lon, min_lon = bound_coordinates(coords, tri_coords)

    colors = ['red', 'green', 'blue', 'orange', 'cyan', 'purple']
    #plots each known coordinate with a label
    for i, coord in enumerate(coords):
        gmap.marker(coord[0], coord[1], label=chr(ord('A')+i))
        print(f"Point {chr(ord('A')+i)} - Lat: {coord[0]} Lon: {coord[1]} Bearing: {bearings[i]}")

    #plots each triangulated coordinate with a label. 2 known points gives 1 triangulated point, and 3 known point gives 3 triangulated points
    tri_sum = (0,0)
    for i, tri_coord in enumerate(tri_coords):
        gmap.marker(tri_coord[0], tri_coord[1], label=chr(ord('A')+i+len(coords)))
        print(f"Triangulated Point {chr(ord('A')+i+len(coords))} - Lat: {tri_coord[0]} Lon: {tri_coord[1]}")
        path = zip(*[
            (coords[i][0], coords[i][1]),
            (tri_coord[0], tri_coord[1])
        ])
        gmap.plot(*path, edge_width=3, color=colors[i+len(coords)])
        path = zip(*[
            (coords[(i+1)%3][0], coords[(i+1)%3][1]),
            (tri_coord[0], tri_coord[1])
        ])
        gmap.plot(*path, edge_width=3, color=colors[i + len(coords)])
        tri_sum = (tri_sum[0] + tri_coord[0], tri_sum[1] + tri_coord[1])

    tri_avg = (tri_sum[0]/len(coords), tri_sum[1]/len(coords))
    gmap.marker(tri_avg[0], tri_avg[1], label='T')
    print(f"Average triangulated value - Lat: {tri_avg[0]} Lon: {tri_avg[1]}")
    # Draw the map to an HTML file:
    gmap.draw('map.html')
