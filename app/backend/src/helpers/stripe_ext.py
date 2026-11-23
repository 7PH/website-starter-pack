"""
Project-specific Stripe parameters, merged into the calls core makes (helpers/stripe.py).

Empty by default: Stripe then picks the browser's language and asks for nothing extra.
A key set here wins over the core value of the same name.

Example, a French shop selling digital content with immediate access, where EU law requires the buyer to waive
the 14-day withdrawal right at checkout. `consent_collection` needs a Terms of Service URL in the Stripe
dashboard (Settings > Public details), or Stripe refuses the session:

    CHECKOUT_SESSION_PARAMS = {
        "locale": "fr",
        "consent_collection": {"terms_of_service": "required"},
        "custom_text": {
            "terms_of_service_acceptance": {
                "message": "J'accepte les [CGV](https://example.com/legal/sales) et je demande l'accès immédiat, "
                "en renonçant à mon droit de rétractation."
            }
        },
    }
    BILLING_PORTAL_PARAMS = {"locale": "fr"}
    CUSTOMER_PARAMS = {"preferred_locales": ["fr"]}  # Language of Stripe's emails and invoices
"""

from typing import Any

# stripe.checkout.Session.create, for user and organization subscriptions
CHECKOUT_SESSION_PARAMS: dict[str, Any] = {}

# stripe.billing_portal.Session.create
BILLING_PORTAL_PARAMS: dict[str, Any] = {}

# stripe.Customer.create, for users and organizations (not applied to existing customers). `metadata` is merged with
# core's (user_id / org_id, which win); other keys set here win over core's (eg `email`, `name`)
CUSTOMER_PARAMS: dict[str, Any] = {}
