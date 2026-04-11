from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.config.database import get_db
from app.config.roles import any_authenticated
from app.schemas.hospital import (
    NearbySearchRequest,
    NearbySearchResponse,
    NearbyHospitalSearchResponse
)
from app.controllers.nearby_controller import (
    search_and_store_nearby_hospitals,
    get_past_searches
)

router = APIRouter(tags=["Nearby Hospitals"])


@router.post("/patients/{patient_id}/nearby-hospitals/", response_model=NearbySearchResponse)
async def find_nearby(
    patient_id   : int,
    data         : NearbySearchRequest,
    db           : Session = Depends(get_db),
    current_user = Depends(any_authenticated)
):
    return await search_and_store_nearby_hospitals(patient_id, data, db)


@router.get("/patients/{patient_id}/nearby-hospitals/", response_model=List[NearbyHospitalSearchResponse])
def past_searches(
    patient_id   : int,
    db           : Session = Depends(get_db),
    current_user = Depends(any_authenticated)
):
    return get_past_searches(patient_id, db)