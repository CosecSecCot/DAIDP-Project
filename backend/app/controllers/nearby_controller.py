from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.hospital import Hospital, NearbyHospitalSearch, HospitalSource, HospitalType
from app.schemas.hospital import NearbySearchRequest
from app.services.nearby_service import fetch_nearby_hospitals


async def search_and_store_nearby_hospitals(
    patient_id : int,
    data       : NearbySearchRequest,
    db         : Session
):
    # Validate coordinates
    if not (-90 <= data.lat <= 90):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Latitude must be between -90 and 90"
        )
    if not (-180 <= data.lon <= 180):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Longitude must be between -180 and 180"
        )
    if data.radius_m < 100 or data.radius_m > 50000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Radius must be between 100m and 50000m"
        )

    # Call Nominatim
    try:
        nearby = await fetch_nearby_hospitals(data.lat, data.lon, data.radius_m)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not reach location service: {str(e)}"
        )

    if not nearby:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hospitals found near this location"
        )

    search_results = []

    for h in nearby:
        # Check if this OSM hospital already exists in our hospitals table
        existing_hospital = db.query(Hospital).filter(
            Hospital.osm_id == h["osm_id"]
        ).first()

        if existing_hospital:
            # Already in DB — just use it, update info if needed
            hospital = existing_hospital
            if h.get("phone") and not hospital.phone:
                hospital.phone = h["phone"]
            if h.get("website") and not hospital.website:
                hospital.website = h["website"]
            db.commit()
        else:
            # Brand new hospital — insert into hospitals table
            hospital = Hospital(
                name    = h["name"],
                address = h["address"],
                city    = _extract_city(h["address"]),
                phone   = h["phone"],
                website = h["website"],
                lat     = h["lat"],
                lon     = h["lon"],
                osm_id  = h["osm_id"],
                source  = HospitalSource.OSM,
                type    = HospitalType.HOSPITAL,
                is_active = True
            )
            db.add(hospital)
            db.commit()
            db.refresh(hospital)

        # Record the search result linking patient → hospital
        search_entry = NearbyHospitalSearch(
            patient_id      = patient_id,
            search_lat      = data.lat,
            search_lon      = data.lon,
            search_radius_m = data.radius_m,
            hospital_id     = hospital.id,
            distance_m      = h["distance_m"]
        )
        db.add(search_entry)
        db.commit()
        db.refresh(search_entry)

        # Attach hospital object for the response
        search_entry.hospital = hospital
        search_results.append(search_entry)

    return {
        "total"  : len(search_results),
        "results": search_results
    }


def get_past_searches(patient_id: int, db: Session):
    searches = db.query(NearbyHospitalSearch).filter(
        NearbyHospitalSearch.patient_id == patient_id
    ).order_by(NearbyHospitalSearch.searched_at.desc()).all()

    for s in searches:
        s.hospital = db.query(Hospital).filter(
            Hospital.id == s.hospital_id
        ).first()

    return searches


def _extract_city(address: str) -> str:
    """
    Tries to extract city from a comma separated address string.
    Returns the second-to-last part which is usually the city.
    """
    if not address:
        return None
    parts = [p.strip() for p in address.split(",")]
    if len(parts) >= 2:
        return parts[-2]
    return parts[0] if parts else None