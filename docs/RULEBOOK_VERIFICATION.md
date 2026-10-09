# Rulebook verification

`backend/solarsabha/data/rulebook.json` is the single source of truth for every rule and constant. Each rule carries a
`status`: **official** (from a government or regulator document), **vendor-guide-verify** (from company guides, still to be
confirmed) or **team-assumption** (our own policy threshold or illustrative number). The app shows the status next to every
rule it cites.

## Checked on 9 October 2026

Primary source: **MNRE, Guidelines for PM-Surya Ghar: Muft Bijli Yojana, Central Financial Assistance to Residential Consumers
(June 2024)**, as published by JBVNL ([PDF](https://jbvnl.co.in/SOLAR/Operational%20Guidelines%20to%20PM%20Suryaghar%207%20June%2024.pdf)).
Scheme approval: Order No. 318/17/2024-Grid Connected Rooftop, 16 March 2024. Also the CFA structure sheet
([PDF](https://jbvnl.co.in/SOLAR/CFA_structure%20for%20PM%20Suryaghar.pdf)) and the CEA CO2 Baseline Database
([user guide v21.0](https://cea.nic.in/wp-content/uploads/baseline/2025/12/User_Guide_V_21.0.pdf)).

| Rule | Value in the app | Status | What the source says | Change made |
|---|---|---|---|---|
| `subsidy_per_kw_ghs` | Rs 18,000 per kW | official | CFA table, S. No. 4: GHS/RWA common facilities incl. EV charging, Rs 18,000/kWp | Source updated |
| state override: special category | Rs 19,800 per kW | official | Same table, special category States/UTs: Rs 19,800/kWp | **Added** for Uttarakhand, Himachal Pradesh, J&K, Ladakh, the North East incl. Sikkim, A&N, Lakshadweep |
| `cap_kw_per_flat`, `cap_total_kw_ghs` | 3 kW per flat, 500 kW | official | "up to 500 kWp (@3 kWp per house)"; the limit includes plants already installed by individual residents | Note added |
| `ghs_common_facilities_only` | text | official | Section 5(f): the GHS/RWA connection serves only common facilities | **Added** |
| `registered_vendor_requirement` (was `empanelled_vendor_requirement`) | text | **official** (was verify) | Section 7(a): "implemented only through the vendors registered on the National Portal" | **Upgraded**; wording changed from "empanelled" to "registered", since the scheme ended tender empanelment |
| `min_service_years` | **5** years (was 3) | **official** (was assumption) | Section 7(d): free repairs and maintenance for a 5-year Comprehensive Maintenance Contract from commissioning | **Changed**: quotes offering less than 5 years are flagged |
| `cfa_processing_days` | 15 days | official | Section 6(t): CFA processed within 15 days of DISCOM approval | **Added**; the "Subsidy paid" stage now uses 7 to 15 days |
| `grievance_resolution_days` | 30 days | official | Section 11(a): grievances on the National Portal resolved within 30 days | **Added**; cited in the escalation letter |
| `small_system_deemed_feasible_kw` | 10 kW | official | Section 6(h): up to 10 kW deemed feasible (Electricity (Rights of Consumers) Rules, 2020) | **Added**; most society systems are larger |
| `grid_emission_factor` | 0.710 tCO2/MWh | official | CEA v21.0 (Nov 2025), weighted average FY 2024-25 | CEA has published **v22.0 (Sep 2026)**; its figures were not publicly readable when checked. Update when available |
| `cost_per_kw` | Rs 50,000 | team-assumption (was verify) | MNRE benchmark (section 5(g)): Rs 50,000/kW for the first 2 kW, Rs 45,000/kW after (Rs 55,000 / 49,500 in special category States) | Benchmark cited; the value stays an editable assumption |
| `sign_before_approval_warning` | text | team-assumption (was verify) | Not prohibited in the guidelines | Re-labelled as our caution, never shown as law |
| `missed_inspection_rule` | text | vendor-guide-verify | Not found in the guidelines | Marked "do not present as a rule" |
| `yield_kwh_per_kw_year` | 1,400 | vendor-guide-verify | Not in the guidelines; location dependent | Editable in the app |
| `price_band_per_kw`, `advance_flag_pct`, `default_tariff_inr_per_kwh`, `target_share_of_load` | various | team-assumption | Our thresholds | Unchanged; all editable or shown as assumptions |
| `stages` (1 to 5) | vendor-guide days | vendor-guide-verify | Not specified in the guidelines | Unchanged; subsidy stage now official (see above) |

## Still to do for a real launch

- [ ] Read the CEA v22.0 database figures and update `grid_emission_factor`.
- [ ] Replace the SAMPLE vendor list with the registered-vendor list for each state (from the National Portal), or keep the "sample" label.
- [ ] Add state rules only from that state's SERC/DISCOM documents (net-metering limits, sanctioned-load rules, timelines).
- [ ] Get a sourced generation figure (kWh per kW per year) per city.
- [ ] Re-check the scheme guidelines: the scheme runs to FY 2026-27 and amendments may change values.
- [ ] Run `make test` and `make evals` after any rule change.
