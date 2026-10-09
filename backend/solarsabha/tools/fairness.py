"""How could the society share the cost and the savings? Shows each flat what changes for them."""

def fairness_table(net_cost, saving_per_year, flat_areas_sqft, total_flats=None) -> dict:
    """Compare equal split vs split by flat area. Savings are assumed shared the same way as cost.
    flat_areas_sqft may list only some flats (or none); total_flats is the society's real count. When only a
    sample is listed, the total area is estimated from the sample's average area, and the note says so."""
    listed = len(flat_areas_sqft)
    n = total_flats or listed
    if n < 1:
        raise ValueError("need the number of flats")
    if n < listed:
        raise ValueError("total_flats is smaller than the number of flats listed")
    equal = {"cost": round(net_cost / n), "saving_year": round(saving_per_year / n)}
    rows = []
    if listed:
        total_area = sum(flat_areas_sqft.values()) / listed * n
        for flat, area in flat_areas_sqft.items():
            rows.append({
                "flat": flat, "area_sqft": area,
                "equal_cost": equal["cost"], "area_cost": round(net_cost * area / total_area),
                "equal_saving_year": equal["saving_year"], "area_saving_year": round(saving_per_year * area / total_area),
            })
    note = "Choosing between these models is the committee's decision, not ours."
    if not listed:
        note += " Add flat areas to compare the by-area split."
    elif n > listed:
        note += (f" Showing {listed} of {n} flats. Total area is estimated from these flats' average;"
                 " enter every flat's area for exact by-area figures.")
    return {"models": ["equal", "by_area"] if listed else ["equal"], "flats": rows, "equal_per_flat": equal,
            "total_flats": n, "listed_flats": listed, "note": note}
