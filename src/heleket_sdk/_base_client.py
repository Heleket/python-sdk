"""Shared HTTP plumbing for :class:`HeleketPayment` and :class:`HeleketPayout`.

Encodes the request, signs it, dispatches via the configured ``Transport``,
dumps to the debug sink when enabled, and translates the response into either
a typed result or an exception.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from ._config import ClientOptions
from ._debug import DebugEntry
from ._errors import ApiError, HttpError, ValidationError
from ._signature import sign
from ._transport import RequestsTransport, Transport
from ._version import __version__

__all__ = ["BaseClient"]

_USER_AGENT = f"heleket-python-sdk/{__version__}"


class BaseClient:
    """Common base for the payment and payout clients.

    Carries the merchant UUID, API key, and the resolved :class:`ClientOptions`.
    Subclasses call :meth:`_post` with the path and request body.
    """

    def __init__(
        self,
        *,
        merchant_id: str,
        api_key: str,
        options: ClientOptions | None = None,
    ) -> None:
        if not merchant_id or not merchant_id.strip():
            raise ValueError("merchant_id must not be empty")
        if not api_key or not api_key.strip():
            raise ValueError("api_key must not be empty")

        self._merchant_id = merchant_id.strip()
        self._api_key = api_key.strip()
        self._options = options if options is not None else ClientOptions()
        self._transport: Transport = self._options.transport or RequestsTransport()

    # ------------------------------------------------------------------ #
    # internal helpers
    # ------------------------------------------------------------------ #

    def _post(self, path: str, params: Any = None) -> Any:
        """Send a signed POST request and return the decoded ``result`` field."""
        return self._send("POST", path, self._encode_body(params))

    def _get(self, path: str) -> Any:
        """Send a signed GET request and return the decoded ``result`` field.

        For read-only endpoints that carry all their input in the path (e.g.
        exchange rates). There is no request body, so the signed bytes are the
        empty string — exactly like a POST with no params: ``sign = md5(api_key)``.
        """
        return self._send("GET", path, "")

    def _send(self, method: str, path: str, body: str) -> Any:
        """Sign the exact body bytes, attach the auth headers, dispatch via the
        transport, and translate the response.

        Shared by :meth:`_post` and :meth:`_get` so the signing and error
        handling live in exactly one place.
        """
        signature = sign(body, self._api_key)
        url = self._options.base_url + path

        headers = {
            "merchant": self._merchant_id,
            "sign": signature,
            "Content-Type": "application/json",
            "User-Agent": _USER_AGENT,
        }

        if self._options.debug:
            self._options.logger(DebugEntry.request(method, url, body))

        try:
            response = self._transport.round_trip(method, url, headers, body, self._options.timeout)
        except HttpError:
            raise
        except Exception as exc:  # noqa: BLE001 — wrap unexpected failures
            raise HttpError(f"transport failed: {exc}") from exc

        if self._options.debug:
            self._options.logger(DebugEntry.response(response.status_code, response.body))

        return self._parse_response(response.status_code, response.body)

    @staticmethod
    def _encode_body(params: Any) -> str:
        """Encode params to JSON, returning ``""`` for null/empty payloads."""
        if params is None:
            return ""
        if isinstance(params, BaseModel):
            # by_alias=True so snake_case wire names beat the Pydantic field
            # names; exclude_none=True so optional fields don't serialise.
            data = params.model_dump(by_alias=True, exclude_none=True)
        elif isinstance(params, dict):
            data = {k: v for k, v in params.items() if v is not None}
        else:
            # Last-ditch — let json.dumps try.
            data = params

        if not data and not isinstance(data, int | float | bool):
            return ""
        return json.dumps(data, separators=(",", ":"))

    @staticmethod
    def _parse_response(status_code: int, body: str) -> Any:
        envelope: dict[str, Any] | None
        if body:
            try:
                envelope = json.loads(body)
                if not isinstance(envelope, dict):
                    envelope = None
            except json.JSONDecodeError:
                envelope = None
        else:
            envelope = None

        if status_code == 422:
            fields: dict[str, list[str]] = {}
            if envelope and isinstance(envelope.get("errors"), dict):
                for key, value in envelope["errors"].items():
                    if isinstance(value, list):
                        fields[key] = [str(v) for v in value]
                    else:
                        fields[key] = [str(value)]
            summary = _summarise_fields(fields)
            raise ValidationError(f"validation failed: {summary}", status_code, fields, body)

        if envelope is None:
            raise ApiError(f"non-JSON response (HTTP {status_code})", status_code, body)

        state = envelope.get("state")
        if state != 0:
            message = envelope.get("message", f"api error (state={state})")
            raise ApiError(str(message), status_code, body)

        return envelope.get("result")


def _summarise_fields(fields: dict[str, list[str]]) -> str:
    if not fields:
        return "(no field details)"
    return "; ".join(f"{k} ({', '.join(v)})" for k, v in fields.items())
