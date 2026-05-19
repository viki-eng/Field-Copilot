from typing import List, Optional
from pydantic import BaseModel


class ItineraryItem(BaseModel):
    rank: int
    visit_sequence: int
    entity_id: str
    entity_type: str
    district: str
    tehsil: Optional[str] = None
    priority_score: float
    reason_codes: List[str]
    top_sku_to_discuss: Optional[str] = None
    visit_type_suggestion: str


class AlertItem(BaseModel):
    alert_type: str
    severity: str
    entity_id: str
    district: str
    detail: str
    action: str


class DailyPlanResponse(BaseModel):
    rep_id: str
    date: str
    territory_id: str
    itinerary: List[ItineraryItem]
    alerts: List[AlertItem]


class NBAResponse(BaseModel):
    entity_id: str
    nba: dict


class OutcomeRequest(BaseModel):
    rep_id: str
    entity_id: str
    date: str
    outcome: str   # sale | no_purchase | follow_up
    products_sold: List[str] = []
    qty_sold: int = 0
    notes: str = ""
    territory_id: Optional[str] = None


class OutcomeResponse(BaseModel):
    success: bool
    outcome_id: int


class AnalyticsResponse(BaseModel):
    territory_id: str
    period_weeks: int
    visit_coverage: float
    conversion_rate: float
    top_skus: List[str]
    high_priority_unvisited: List[str]
