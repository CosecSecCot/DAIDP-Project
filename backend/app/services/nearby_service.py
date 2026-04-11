import httpx
import math
from typing import List, Dict, Any


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R        = 6371000
    phi1     = math.radians(lat1)
    phi2     = math.radians(lat2)
    d_phi    = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a        = (math.sin(d_phi / 2) ** 2
                + math.cos(phi1) * math.cos(phi2)
                * math.sin(d_lambda / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


async def fetch_nearby_hospitals(lat: float, lon: float, radius_m: int) -> List[Dict]:
    # Convert radius in metres to degrees (rough approximation)
    # 1 degree ≈ 111,000 metres
    delta = radius_m / 111000

    # Bounding box: south, west, north, east
    viewbox = f"{lon - delta},{lat - delta},{lon + delta},{lat + delta}"

    params = {
        "q"              : "hospital",
        "format"         : "json",
        "limit"          : 20,
        "viewbox"        : viewbox,
        "bounded"        : 1,               # only return results inside the viewbox
        "addressdetails" : 1,
        "extratags"      : 1,
    }

    headers = {
        # Nominatim requires a User-Agent identifying your app
        "User-Agent": "HospitalNetworkApp/1.0"
    }

    results = []

    async with httpx.AsyncClient(timeout=15.0) as client:
        # Search for hospitals
        response = await client.get(NOMINATIM_URL, params=params, headers=headers)
        response.raise_for_status()
        hospitals = response.json()
        results.extend(hospitals)

        # Also search for clinics
        params["q"] = "clinic"
        response = await client.get(NOMINATIM_URL, params=params, headers=headers)
        response.raise_for_status()
        clinics = response.json()
        results.extend(clinics)

    # Deduplicate by osm_id
    seen   = set()
    unique = []
    for item in results:
        osm_id = str(item.get("osm_id", ""))
        if osm_id not in seen:
            seen.add(osm_id)
            unique.append(item)

    # Parse and calculate distance
    parsed = []
    for item in unique:
        item_lat = float(item.get("lat", 0))
        item_lon = float(item.get("lon", 0))
        distance = haversine_distance(lat, lon, item_lat, item_lon)

        address_obj = item.get("address", {})
        address_parts = filter(None, [
            address_obj.get("house_number"),
            address_obj.get("road"),
            address_obj.get("suburb"),
            address_obj.get("city") or address_obj.get("town") or address_obj.get("village"),
            address_obj.get("state"),
            address_obj.get("postcode"),
            address_obj.get("country"),
        ])
        address = ", ".join(address_parts) or item.get("display_name")

        extratags = item.get("extratags", {}) or {}

        parsed.append({
            "osm_id"    : str(item.get("osm_id")),
            "name"      : item.get("name") or item.get("display_name", "Unnamed"),
            "lat"       : item_lat,
            "lon"       : item_lon,
            "address"   : address,
            "phone"     : extratags.get("phone") or extratags.get("contact:phone"),
            "website"   : extratags.get("website") or extratags.get("contact:website"),
            "distance_m": round(distance, 1),
        })

    # Sort by closest first
    parsed.sort(key=lambda x: x["distance_m"])

    return parsed