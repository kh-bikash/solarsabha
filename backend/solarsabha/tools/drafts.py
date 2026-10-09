"""Document and message drafts, written the way a housing society's office actually writes them. Templates fill in
facts; an LLM may polish wording but never changes facts. Everything returned has status DRAFT.
There is deliberately NO send function in this codebase."""
import hashlib

def draft_id(kind, to) -> str:
    """Stable id: the same kind of letter to the same recipient keeps its id across recalculations,
    so edits and approvals stay attached to it."""
    return hashlib.sha1(f"{kind}|{to}".encode()).hexdigest()[:8]

def _d(kind, to, subject, body) -> dict:
    return {"id": draft_id(kind, to), "kind": kind, "to": to, "subject": subject, "body": body, "status": "DRAFT"}

def _rs(x) -> str:
    """Indian digit grouping: Rs 11,52,000"""
    whole = f"{round(x):d}"
    head, tail = whole[:-3], whole[-3:]
    groups = []
    while len(head) > 2:
        groups.insert(0, head[-2:]); head = head[:-2]
    if head:
        groups.insert(0, head)
    return "Rs " + ",".join(groups + [tail]) if groups else "Rs " + tail

def _sign(soc) -> str:
    return f"Yours faithfully,\nFor {soc['name']}\n\n\nHon. Secretary"

def _discom(soc) -> str:
    return soc.get("discom") or "the electricity distribution company (DISCOM)"

def _ref_line(soc) -> str:
    parts = [f"application no. {soc.get('application_ref') or '[application no.]'}"]
    if soc.get("consumer_no"):
        parts.append(f"consumer no. {soc['consumer_no']}")
    return ", ".join(parts)

def agm_notice(soc, kw, total_cost, subsidy, net_cost, payback, date) -> dict:
    return _d("agm_notice", f"All members of {soc['name']}", "Notice of Special General Body Meeting: rooftop solar for common facilities",
        f"Notice is hereby given that a Special General Body Meeting of the members of {soc['name']} will be held on {date} "
        "in the society premises to transact the following business:\n\n"
        f"1. To consider and approve, in principle, the installation of a {kw:.0f} kW grid-connected rooftop solar power plant on the "
        "society terrace for the common facilities (lifts, water pumps, common lighting).\n"
        f"2. To consider the estimated project cost of {_rs(total_cost)}, the central financial assistance of {_rs(subsidy)} available "
        f"under PM Surya Ghar: Muft Bijli Yojana, and the net cost to the society of {_rs(net_cost)}, with an estimated simple "
        f"payback of about {payback} years.\n"
        "3. To decide how the cost and the savings will be shared among members: an equal share per flat, or in proportion to flat area.\n"
        f"4. To authorise the Managing Committee to apply on the national rooftop solar portal, obtain approvals from {_discom(soc)}, "
        "and select an empanelled vendor after comparing quotations.\n"
        "5. Any other matter with the permission of the Chair.\n\n"
        "The figures above are estimates prepared from the society's electricity bills. They will be confirmed with vendor quotations "
        "and the DISCOM before any order is placed. Members are requested to attend. If there is no quorum, the meeting will stand "
        "adjourned as per the bye-laws of the society.\n\n"
        "By order of the Managing Committee\n\n\nHon. Secretary")

def agm_resolution(soc, kw, method) -> dict:
    basis = "an equal share per flat" if method == "equal" else "in proportion to the area of each flat"
    return _d("agm_resolution", "Managing Committee", "Draft resolution for the General Body Meeting",
        f"RESOLVED THAT the General Body of {soc['name']} hereby approves, in principle, the installation of a grid-connected "
        f"rooftop solar power plant of about {kw:.0f} kW for the common facilities of the society.\n\n"
        f"RESOLVED FURTHER THAT the net cost after central financial assistance, and the resulting savings, be shared among members on {basis}.\n\n"
        "RESOLVED FURTHER THAT the Managing Committee be and is hereby authorised to apply on the national rooftop solar portal, "
        f"to obtain the required approvals from {_discom(soc)}, to invite and compare quotations from empanelled vendors, and to "
        "place a work order only after DISCOM feasibility approval.\n\n"
        "RESOLVED FURTHER THAT the Hon. Secretary be authorised to sign and submit all documents required for the above purpose.")

def rfq_email(soc, kw, vendor) -> dict:
    return _d("rfq", vendor, f"Request for quotation: {kw:.0f} kW rooftop solar plant for {soc['name']}",
        f"Dear Sir/Madam,\n\n{soc['name']} intends to install a grid-connected rooftop solar plant of about {kw:.0f} kW for its "
        "common facilities. Kindly send your detailed quotation, including: price per kW and total price inclusive of GST; make and "
        "specification of panels and inverter; payment stages; panel and inverter warranty; free operation and maintenance period; "
        "proof of registration as an empanelled vendor on the national portal; and details of society projects you have completed.\n\n"
        + _sign(soc))

def counter_offer(soc, vendor, price, advance_pct, service_years) -> dict:
    return _d("counter_offer", vendor, f"Your quotation for the rooftop solar plant at {soc['name']}",
        "Dear Sir/Madam,\n\nThank you for your quotation. After reviewing it, the Managing Committee proposes the following terms:\n\n"
        f"1. Total price: {_rs(price)}, inclusive of GST.\n"
        f"2. Advance: {advance_pct}% with the work order; the balance linked to delivery and commissioning.\n"
        f"3. Free operation and maintenance: {service_years} years.\n"
        "4. The work order will be placed only after DISCOM feasibility approval.\n\n"
        "Kindly confirm these terms in writing. Please note that this letter is not a work order.\n\n" + _sign(soc))

def proof_request(soc, vendor) -> dict:
    return _d("proof_request", vendor, "Documents required before we consider your quotation",
        "Dear Sir/Madam,\n\nThank you for your quotation. Before the Managing Committee can consider it, kindly send:\n\n"
        "1. Proof of your registration as an empanelled vendor on the national rooftop solar portal.\n"
        "2. Your GST registration certificate.\n"
        "3. Details of at least two housing society projects you have completed, with contact persons.\n"
        "4. Your panel warranty, inverter warranty and free maintenance terms, which are not stated in the quotation.\n\n"
        "We will not discuss price until these are received and verified.\n\n" + _sign(soc))

def details_request(soc, vendor) -> dict:
    return _d("details_request", vendor, "Complete quotation required",
        "Dear Sir/Madam,\n\nThank you for your quotation. We could not find the total price and the system size in it. Kindly send a "
        "complete quotation with the price per kW and total price inclusive of GST, the make of panels and inverter, payment stages, "
        "warranty and free maintenance period.\n\n" + _sign(soc))

def discom_reminder(soc, stage_label, overdue_days) -> dict:
    return _d("discom_reminder", f"The Assistant Engineer (Rooftop Solar), {_discom(soc)}", f"Request for status: rooftop solar {_ref_line(soc)}",
        f"Respected Sir/Madam,\n\nThis is regarding the rooftop solar application of {soc['name']} for its common facilities "
        f"({_ref_line(soc)}). The application has been at the '{stage_label}' stage for {overdue_days} days beyond the usual time.\n\n"
        "We request you to kindly let us know its present status and any document or site visit required from our side. "
        "We will be glad to arrange it at the earliest.\n\nThank you for your help.\n\n" + _sign(soc))

def discom_escalation(soc, stage_label, overdue_days) -> dict:
    return _d("discom_escalation", f"The Grievance Redressal Cell, {_discom(soc)}", f"Grievance: delay in rooftop solar {_ref_line(soc)}",
        f"Respected Sir/Madam,\n\nWe wish to bring to your notice a delay in the rooftop solar application of {soc['name']} "
        f"({_ref_line(soc)}). The application has remained at the '{stage_label}' stage for {overdue_days} days beyond the usual "
        "time, despite our earlier follow-up with the sub-division office.\n\n"
        "We request you to kindly look into the matter and give us a written update, with a date by which this stage will be "
        "completed, within 7 days. Copies of our application and earlier correspondence can be provided on request.\n\n" + _sign(soc))
