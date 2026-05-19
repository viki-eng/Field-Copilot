import json
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.main import get_store

router = APIRouter()


class RepProfile(BaseModel):
    rep_id: str
    territory_id: str
    territory_name: str
    state: str
    district: str
    tehsil_list: List[str]


@router.get("/rep/{rep_id}/profile", response_model=RepProfile)
def get_rep_profile(rep_id: str):
    ds = get_store()
    row = ds.reps[ds.reps["rep_id"] == rep_id]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"Rep {rep_id} not found")
    r = row.iloc[0]
    raw = r["tehsil_list"]
    try:
        tehsils = json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        tehsils = []
    return RepProfile(
        rep_id=r["rep_id"],
        territory_id=r["territory_id"],
        territory_name=r["territory_name"],
        state=r["state"],
        district=r["district"],
        tehsil_list=tehsils,
    )
