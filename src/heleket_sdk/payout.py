"""Client for the Heleket Payouts API and balance transfers.

Construct with the merchant UUID and the **payout** API key — distinct from
the payment key (see :class:`HeleketPayment`).

Thread-safe.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote

from ._base_client import BaseClient
from .types import (
    CalculateRequest,
    Calculation,
    CreatePayoutRequest,
    HistoryOptions,
    HistoryPage,
    InfoOptions,
    Payout,
    RefundRequest,
    RefundResult,
    Service,
    Transfer,
)

if TYPE_CHECKING:
    from ._config import ClientOptions

__all__ = ["HeleketPayout"]


class HeleketPayout(BaseClient):
    """Client for ``/v1/payout/*`` and ``/v1/transfer/*``."""

    def __init__(
        self,
        *,
        merchant_id: str,
        api_key: str,
        options: ClientOptions | None = None,
    ) -> None:
        super().__init__(merchant_id=merchant_id, api_key=api_key, options=options)

    # ---------- payouts ----------------------------------------------------

    def create_payout(self, request: CreatePayoutRequest) -> Payout:
        """Create a withdrawal."""
        result = self._post("/v1/payout", request)
        return Payout.model_validate(result)

    def refund(self, request: RefundRequest) -> RefundResult:
        """Refund a paid invoice in full or in part.

        Hits ``POST /v1/payment/refund`` but is signed with the **payout** API
        key, so it lives on :class:`HeleketPayout` rather than
        :class:`HeleketPayment`. Required: ``address``, ``is_subtract``; one of
        ``uuid`` / ``order_id``.
        """
        if request.is_empty():
            raise ValueError("heleket: one of uuid or order_id must be set")
        result = self._post("/v1/payment/refund", request)
        return RefundResult.model_validate(result)

    def get_info(self, options: InfoOptions) -> Payout:
        """Look up a payout by UUID or ``order_id``."""
        if options.is_empty():
            raise ValueError("heleket: one of uuid or order_id must be set")
        result = self._post("/v1/payout/info", options)
        return Payout.model_validate(result)

    def list_history(self, options: HistoryOptions) -> HistoryPage[Payout]:
        """Paginated payout history."""
        path = "/v1/payout/list"
        if options.cursor:
            path = f"{path}?cursor={quote(options.cursor)}"
        result = self._post(path, options)
        return HistoryPage[Payout].model_validate(result)

    def calculate_withdrawal(self, request: CalculateRequest) -> Calculation:
        """Preview commission and final amount for a hypothetical payout."""
        result = self._post("/v1/payout/calculate", request)
        return Calculation.model_validate(result)

    def list_services(self) -> list[Service]:
        """Catalogue of supported (currency, network) pairs for payouts."""
        result = self._post("/v1/payout/services")
        if result is None:
            return []
        return [Service.model_validate(item) for item in result]

    # ---------- transfers --------------------------------------------------

    def transfer_to_personal(self, amount: str, currency: str) -> Transfer:
        """Move funds from the business balance to the personal wallet."""
        result = self._post(
            "/v1/transfer/to-personal",
            {"amount": amount, "currency": currency},
        )
        return Transfer.model_validate(result)

    def transfer_to_business(self, amount: str, currency: str) -> Transfer:
        """Move funds from the personal balance to the business balance."""
        result = self._post(
            "/v1/transfer/to-business",
            {"amount": amount, "currency": currency},
        )
        return Transfer.model_validate(result)
