# Rulebook verification checklist (do before the demo)

Open `backend/solarsabha/data/rulebook.json`. For each `vendor-guide-verify` item, find the official text (national rooftop solar portal, MNRE guidelines, your state's DISCOM/SERC rules) and update value, source, as_of, status.

- [ ] subsidy_per_kw_ghs, cap_kw_per_flat, cap_total_kw_ghs: confirm still current (sheet dated 2024-03)
- [ ] grid_emission_factor: newest CEA CO2 Baseline Database version
- [ ] yield_kwh_per_kw_year: a sourced value for the demo city
- [ ] cost_per_kw and price_band_per_kw: recent quotes or an official benchmark
- [ ] stages (days): any official timeline for your state
- [ ] sign_before_approval_warning, empanelled_vendor_requirement, missed_inspection_rule: find the official wording; if you cannot, keep status vendor-guide-verify and keep the UI warning
- [ ] approved vendor list: replace the SAMPLE list with the real one for your state, or keep it labelled SAMPLE
- [ ] Pick ONE state/DISCOM and read its society process end to end once
- [ ] Run `make test` after any change (tests encode the worked example)
