"""Counter-offer logic for the negotiation arena.

HONESTY NOTE: vendor replies here are SIMULATED by simple personas with hidden floors. The UI must label the
arena 'SIMULATION'. Real negotiation happens by email over days. The agent never invents competing quotes:
it only uses quotes the committee actually uploaded.
"""
from .. import rules

PERSONAS = {
    "Suryakiran Rooftop Solar Pvt Ltd": {"floor": 0.92, "concession": 0.5, "advance_floor": 5},
    "Urja Prime Energy LLP": {"floor": 0.88, "concession": 0.4, "advance_floor": 10},
}

def target_terms(quote) -> dict:
    band = rules.value("price_band_per_kw")
    floor_total = band["low"] * quote["capacity_kw"]
    price = max(round(quote["total_price_inr"] * 0.93), round(floor_total))
    return {"price": min(price, quote["total_price_inr"]), "advance_pct": 5, "service_years": 5}

def run_simulated_negotiation(quote, audit, max_rounds=3) -> dict:
    """Return rounds for the arena. RED vendors are not negotiated with: we ask for proof first."""
    vendor = quote["vendor"]
    if audit["verdict"] == "RED":
        return {"vendor": vendor, "simulated": True, "skipped": True, "rounds": [
            {"round": 1, "from": "committee", "kind": "request_proof", "price": None,
             "message": "Before we discuss price, please share proof of your registration on the PM Surya Ghar National Portal. We will not negotiate until it is verified."}]}
    if not quote.get("total_price_inr") or not quote.get("capacity_kw"):
        return {"vendor": vendor, "simulated": True, "skipped": True, "rounds": [
            {"round": 1, "from": "committee", "kind": "request_details", "price": None,
             "message": "Please send a complete quotation with the total price and system size before we discuss terms."}]}
    persona = PERSONAS.get(vendor, {"floor": 0.95, "concession": 0.3, "advance_floor": 10})
    tgt = target_terms(quote)
    price, adv = quote["total_price_inr"], quote.get("advance_pct") or 10
    floor = round(quote["total_price_inr"] * persona["floor"])
    rounds = []
    for r in range(1, max_rounds + 1):
        rounds.append({"round": r, "from": "committee", "kind": "counter", "price": tgt["price"], "advance_pct": tgt["advance_pct"],
                       "message": f"Our counter: Rs {tgt['price']:,} total, {tgt['advance_pct']}% advance, {tgt['service_years']} years service."})
        new_price = max(floor, round(price - (price - tgt["price"]) * persona["concession"]))
        new_adv = max(persona["advance_floor"], adv - 5)
        conceded = new_price < price or new_adv < adv
        price, adv = new_price, new_adv
        rounds.append({"round": r, "from": "vendor", "kind": "offer" if conceded else "hold", "price": price, "advance_pct": adv,
                       "message": f"Vendor offer: Rs {price:,}, {adv}% advance."})
        if (price <= tgt["price"] and adv <= tgt["advance_pct"]) or not conceded:
            break
    return {"vendor": vendor, "simulated": True, "skipped": False, "start_price": quote["total_price_inr"],
            "final_price": price, "final_advance_pct": adv, "rounds": rounds}
