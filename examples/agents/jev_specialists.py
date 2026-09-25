"""Ten Jev specialists used by the routing examples."""

from conductor.ai.agents import JevAgent

SPECIALTIES = {
    "duplicate_charge": (
        "billing",
        "Duplicate payments or repeated invoice charges",
        {
            "check_transactions": "Compare charge identifiers and payment status",
            "refund_duplicate": "Refund a confirmed duplicate settled charge",
            "explain_hold": "Explain a pending authorization hold",
        },
    ),
    "refund": (
        "billing",
        "Refund eligibility and refund progress",
        {
            "review_eligibility": "Check purchase date and refund policy",
            "approve_refund": "Approve a refund supported by the supplied policy and evidence",
            "trace_refund": "Trace an already approved refund",
        },
    ),
    "subscription": (
        "billing",
        "Subscription renewals, cancellation and plan changes",
        {
            "review_renewal": "Check renewal timing and notice",
            "cancel_renewal": "Schedule cancellation at the end of the current term",
            "change_plan": "Review the requested plan change",
        },
    ),
    "api_errors": (
        "technical",
        "API request failures, rate limits and invalid payloads",
        {
            "inspect_request": "Collect request identifiers and validate the payload",
            "backoff": "Apply retry backoff for documented rate limiting",
            "escalate_bug": "Escalate a reproducible server defect",
        },
    ),
    "outage": (
        "technical",
        "Service outages and widespread availability failures",
        {
            "check_scope": "Verify the affected services and customers",
            "open_incident": "Open an incident for confirmed widespread impact",
            "update_incident": "Attach evidence to an existing incident",
        },
    ),
    "integration": (
        "technical",
        "Webhook delivery and third-party integration failures",
        {
            "inspect_delivery": "Inspect delivery logs and endpoint responses",
            "repair_config": "Correct an identified integration configuration error",
            "replay_delivery": "Replay a failed delivery after checking idempotency",
        },
    ),
    "onboarding": (
        "technical",
        "Initial setup, configuration and first successful request",
        {
            "collect_requirements": "Clarify the intended setup and environment",
            "provide_setup": "Provide the relevant setup steps",
            "validate_setup": "Verify the completed configuration",
        },
    ),
    "access": (
        "account",
        "Login problems, account recovery and permissions",
        {
            "verify_identity": "Verify identity before changing account access",
            "recover_account": "Use the approved account recovery process",
            "review_permissions": "Review the required role and authorization",
        },
    ),
    "security": (
        "account",
        "Suspected compromise, leaked credentials and abuse",
        {
            "investigate": "Collect evidence and assess the scope of compromise",
            "contain": "Recommend revoking confirmed compromised credentials",
            "escalate_security": "Escalate an active compromise to security response",
        },
    ),
    "privacy": (
        "account",
        "Personal data access, export and deletion requests",
        {
            "verify_request": "Verify the requester and scope of the request",
            "export_data": "Route a verified data export request",
            "delete_data": "Route a verified deletion request through policy review",
        },
    ),
}


def specialists():
    return {
        name: JevAgent(
            name=f"jev_{name}",
            model="jev-1.13",
            questions={
                "action": {
                    "type": "choice",
                    "instructions": f"Recommend the next step for {description}. Use only supplied evidence. Do not claim any action was executed.",
                    "choices": actions,
                },
                "urgency": {
                    "type": "score",
                    "instructions": "Rate urgency from low to critical based on customer impact.",
                    "scale": ["low", "normal", "high", "critical"],
                },
                "needs_more_information": {
                    "type": "boolean",
                    "instructions": "Is more information needed before taking the recommended action?",
                },
            },
        )
        for name, (_, description, actions) in SPECIALTIES.items()
    }
