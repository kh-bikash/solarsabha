"""Document and message drafts. Templates fill in facts; an LLM may polish wording but never changes facts.
Everything returned has status DRAFT. There is deliberately NO send function in this codebase."""
import uuid

def _d(kind, to, subject, body) -> dict:
    return {"id": uuid.uuid4().hex[:8], "kind": kind, "to": to, "subject": subject, "body": body, "status": "DRAFT"}

def agm_notice(society, kw, net_cost, subsidy, payback, date) -> dict:
    return _d("agm_notice", "All members", f"Notice: General Body Meeting on rooftop solar ({society})",
        f"Dear members,\n\nA general body meeting of {society} will be held on {date}.\n\nAgenda: approve a {kw:.0f} kW rooftop solar system for common facilities.\n"
        f"Estimated net cost to the society after subsidy: Rs {net_cost:,.0f} (subsidy Rs {subsidy:,.0f}). Estimated simple payback: about {payback} years.\n"
        "These are estimates from the committee's analysis tool and will be confirmed with vendor quotes and the DISCOM.\n\nSecretary")

def agm_resolution(society, kw, method) -> dict:
    return _d("agm_resolution", "Committee", "Draft resolution",
        f"RESOLVED that {society} approves, in principle, installation of a {kw:.0f} kW rooftop solar plant for common facilities, "
        f"with costs and savings shared on the '{method}' basis, subject to DISCOM approval and a verified installer. "
        "The committee is authorised to apply on the national portal and to sign only after required approvals.")

def rfq_email(society, kw, vendor) -> dict:
    return _d("rfq", vendor, f"Request for quotation: {kw:.0f} kW rooftop solar for {society}",
        f"Dear {vendor},\n\nPlease share a detailed quotation for a {kw:.0f} kW rooftop solar plant for the common facilities of {society}. "
        "Please include: price per kW, equipment brands, advance and stage payments, panel warranty, service period, proof that you are on the official empanelled list, and your experience with society projects.\n\nSecretary")

def counter_offer(vendor, price, advance_pct, service_years) -> dict:
    return _d("counter_offer", vendor, "Our counter-proposal",
        f"Dear {vendor},\n\nThank you for your quotation. We can proceed to the next stage at Rs {price:,.0f} with {advance_pct}% advance and {service_years} years of service. "
        "Payments will follow stage approvals. Please confirm.\n\nSecretary")

def proof_request(vendor) -> dict:
    return _d("proof_request", vendor, "Please share proof of empanelment",
        f"Dear {vendor},\n\nBefore we discuss price, please share proof that you are on the official empanelled installer list, with your registration details.\n\nSecretary")

def discom_reminder(stage_label, overdue_days, application_ref) -> dict:
    return _d("discom_reminder", "DISCOM office", f"Reminder: pending action on application {application_ref}",
        f"Respectfully, our application {application_ref} has been at the '{stage_label}' stage for {overdue_days} days beyond the expected time. "
        "Kindly let us know the status and any document you need.\n\nSecretary")

def discom_escalation(stage_label, overdue_days, application_ref) -> dict:
    return _d("discom_escalation", "Grievance cell", f"Escalation: delay on application {application_ref}",
        f"We wrote earlier about application {application_ref}. It remains at '{stage_label}' for {overdue_days} days past the expected time. "
        "We request an update and a date by which the stage will be completed.\n\nSecretary")
