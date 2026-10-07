"""Plain-code sizing, money and CO2 maths. The AI never does arithmetic; it calls these."""
from .. import rules

def size_system(annual_kwh, flats, share=None, yield_kwh_per_kw=None, max_kw_override=None) -> dict:
    """Pick a solar size (kW) from common-area use. Returns three options and the subsidy ceiling."""
    if annual_kwh <= 0 or flats <= 0:
        raise ValueError("annual_kwh and flats must be positive")
    share = rules.value("target_share_of_load") if share is None else share
    y = rules.value("yield_kwh_per_kw_year") if yield_kwh_per_kw is None else yield_kwh_per_kw
    ceiling = min(flats * rules.value("cap_kw_per_flat"), rules.value("cap_total_kw_ghs"))
    if max_kw_override is not None:
        ceiling = min(ceiling, max_kw_override)

    def opt(label, s):
        kw = max(1, min(round(annual_kwh * s / y), ceiling))
        return {"label": label, "share_of_load": s, "kw": kw}
    options = [opt("small", 0.60), opt("recommended", share), opt("large", 1.00)]
    seen, uniq = set(), []
    for o in options:
        if o["kw"] not in seen:
            seen.add(o["kw"]); uniq.append(o)
    return {"options": uniq, "recommended_kw": next(o["kw"] for o in options if o["label"] == "recommended"),
            "subsidy_ceiling_kw": ceiling, "yield_kwh_per_kw": y, "annual_kwh": annual_kwh}

def co2_avoided(generation_kwh) -> float:
    """Tonnes of CO2 avoided per year, using the CEA grid factor from the rulebook."""
    return generation_kwh / 1000.0 * rules.value("grid_emission_factor")

def money_summary(kw, cost_per_kw=None, tariff=None, yield_kwh_per_kw=None) -> dict:
    """Cost, subsidy, net cost, yearly saving, simple payback and CO2 for a system size."""
    cpk = rules.value("cost_per_kw") if cost_per_kw is None else cost_per_kw
    t = rules.value("default_tariff_inr_per_kwh") if tariff is None else tariff
    y = rules.value("yield_kwh_per_kw_year") if yield_kwh_per_kw is None else yield_kwh_per_kw
    cost = kw * cpk
    subsidy = kw * rules.value("subsidy_per_kw_ghs")
    net = cost - subsidy
    gen = kw * y
    saving = gen * t
    return {
        "kw": kw, "total_cost": cost, "subsidy": subsidy, "net_cost": net,
        "generation_kwh_year": gen, "saving_per_year": saving,
        "payback_years": round(net / saving, 1) if saving else None,
        "co2_tonnes_year": round(co2_avoided(gen), 1),
        "assumptions": {"cost_per_kw": cpk, "tariff": t, "yield_kwh_per_kw": y,
                        "caveat": "Simple payback. Ignores maintenance, panel ageing and fixed charges."},
    }
