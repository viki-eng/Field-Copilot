import json
from typing import List, Optional
from fastapi import APIRouter, Query

from api.main import get_store
from api.models import AlertItem
from src.anomaly_detector import detect_anomalies

router = APIRouter()


def _parse_tehsils(raw) -> List[str]:
    if isinstance(raw, list):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return []


@router.get("/alerts", response_model=List[AlertItem])
def get_alerts(
    territory_id: str = Query(..., description="Territory ID e.g. TER_0001"),
    rep_id: Optional[str] = Query(None, description="Rep ID — scopes alerts to rep's tehsils"),
    severity: Optional[str] = Query(None, description="Filter: low|medium|high|critical"),
    date: Optional[str] = Query(None),
):
    ds = get_store()

    tehsil_list = None
    if rep_id:
        rep_row = ds.reps[ds.reps["rep_id"] == rep_id]
        if not rep_row.empty:
            tehsil_list = _parse_tehsils(rep_row["tehsil_list"].values[0])

    raw = detect_anomalies(
        ds, territory_id, as_of_date=date,
        priority_scores=ds.priority_scores,
        tehsil_list=tehsil_list,
    )

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
