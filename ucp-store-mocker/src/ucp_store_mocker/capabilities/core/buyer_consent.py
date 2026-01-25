"""Buyer consent capability definition."""

from dataclasses import dataclass
from typing import Any


@dataclass
class BuyerConsentCapability:
    """UCP Buyer Consent capability for GDPR compliance."""

    id: str = "dev.ucp.shopping.buyer_consent"
    name: str = "Buyer Consent"

    def get_routes(self) -> list[str]:
        """Get route templates needed for this capability."""
        return []  # Integrated into checkout

    def get_services(self) -> list[str]:
        """Get service templates needed for this capability."""
        return []

    def get_discovery_actions(self) -> list[dict[str, Any]]:
        """Get UCP discovery profile actions for this capability."""
        return [
            {
                "id": "set_buyer_consent",
                "type": "dev.ucp.action.set_buyer_consent",
                "description": "Set buyer consent flags on checkout",
            },
        ]

    def get_consent_types(self) -> list[str]:
        """Get supported consent types."""
        return [
            "marketing_emails",
            "data_sharing",
            "terms_of_service",
            "privacy_policy",
        ]

    def get_models(self) -> list[str]:
        """Get model imports needed for this capability."""
        return [
            "BuyerConsent",
        ]
