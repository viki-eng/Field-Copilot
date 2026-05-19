from typing import List, Optional
from fastapi import APIRouter, Query

from api.main import get_store
from api.models import AlertItem
from src.anomaly_detector import detect_anomalies

router = APIRouter()


@router.get("/alerts", response_model=List[AlertItem])
def get_alerts(
    territory_id: str = Query(..., description="Territory ID e.g. TER_0001"),
    severity: Optional[str] = Query(None, description="Filter: low|medium|high|critical"),
    date: Optional[str] = Query(None),
):
    ds = get_store()
    raw = detect_anomalies(ds, territory_id, as_of_date=date, priority_scores=ds.priority_scores)

    SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    if severity:
        min_level = SEVERITY_ORDER.get(severity, 0)
        raw = [a for a in raw if SEVERITY_ORDER.get(a.severity, 0) >= min_level]

    raw.sort(key=lambda a: SEVERITY_ORDER.get(a.severity, 0), reverse=True)

    return [
        AlertItem(
            alert_type=a.alert_type, severity=a.severity, entity_id=a.entity_id,
            district=a.district, detail=a.detail, action=a.action,
        )
        for a in raw
    ]
