from fastapi import APIRouter

from api.models import OutcomeRequest, OutcomeResponse
from src.outcome_logger import log_outcome

router = APIRouter()


@router.post("/visit/outcome", response_model=OutcomeResponse)
def record_outcome(req: OutcomeRequest):
    outcome_id = log_outcome(
        rep_id=req.rep_id,
        entity_id=req.entity_id,
        visit_date=req.date,
        outcome=req.outcome,
        products_sold=req.products_sold,
        qty_sold=req.qty_sold,
        notes=req.notes,
        territory_id=req.territory_id,
    )
    return OutcomeResponse(success=True, outcome_id=outcome_id)
