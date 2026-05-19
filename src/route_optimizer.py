"""
Greedy nearest-neighbor route optimizer.

Given a list of entities to visit in a territory (sorted by priority),
reorders them to minimize travel by clustering on tehsil.
Entities in the same tehsil are grouped together; tehsil order is
determined by alphabetical proximity (a simple proxy since we have no
GPS coordinates — tehsil names are used as cluster keys).

Returns the same list reordered with a 'visit_sequence' column.
"""

import pandas as pd


def optimize_route(entities: pd.DataFrame) -> pd.DataFrame:
    """
    Reorder entities for minimal travel using greedy tehsil clustering.

    entities must have columns: id, tehsil (or visit_tehsil), final_priority_score.
    Returns entities with added 'visit_sequence' column (1-indexed).
    """
    if entities.empty:
        return entities

    tehsil_col = "tehsil" if "tehsil" in entities.columns else "visit_tehsil"
    if tehsil_col not in entities.columns:
        entities["visit_sequence"] = range(1, len(entities) + 1)
        return entities

    # Group by tehsil; within each tehsil sort by priority descending
    grouped = (
        entities
        .assign(_tehsil=entities[tehsil_col].fillna("unknown"))
        .sort_values(["_tehsil", "final_priority_score"], ascending=[True, False])
    )

    # Order tehsils: start with the tehsil containing the highest-priority entity
    top_tehsil = (
        entities.loc[entities["final_priority_score"].idxmax(), tehsil_col]
        if tehsil_col in entities.columns else "unknown"
    )
    tehsils = sorted(grouped["_tehsil"].unique())
    if top_tehsil in tehsils:
        tehsils = [top_tehsil] + [t for t in tehsils if t != top_tehsil]

    ordered_ids = []
    for tehsil in tehsils:
        chunk = grouped[grouped["_tehsil"] == tehsil]
        ordered_ids.extend(chunk["id"].tolist())

    id_order = {eid: i + 1 for i, eid in enumerate(ordered_ids)}
    result = entities.copy()
    result["visit_sequence"] = result["id"].map(id_order).fillna(len(entities) + 1).astype(int)
    return result.sort_values("visit_sequence").reset_index(drop=True)
