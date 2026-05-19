from typing import Optional
from fastapi import APIRouter, Query

from api.main import get_store
from api.models import NBAResponse
from src.nba_engine import get_nba

router = APIRouter()


@router.get("/visit/{entity_id}/nba", response_model=NBAResponse)
def next_best_action(
    entity_id: str,
    rep_id: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
):
    ds = get_store()
    nba = get_nba(entity_id, ds, ds.priority_scores, as_of_date=date)
    return NBAResponse(entity_id=entity_id, nba=nba)
