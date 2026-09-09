"""API Client utility module.
Provides rate-limited, exponential backoff HTTP requests with response validation.
"""

import json
import logging
import time
from typing import Any, Dict, Optional
import requests

logger = logging.getLogger("earnings_engine.api_client")


class RobustAPIClient:
    """HTTP Client with defensive retry, exponential backoff, and rate limiting."""

    def __init__(
        self,
        initial_delay: float = 1.0,
        max_delay: float = 16.0,
        max_retries: int = 4,
        timeout: float = 15.0,
    ):
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = requests.Session()

    def get_json(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        service_name: str = "API"
    ) -> Optional[Dict[str, Any]]:
        """Makes a GET request and parses the JSON response with retry and backoff."""
        delay = self.initial_delay

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout
                )

                # Rate limiting HTTP statuses
                if response.status_code in (429, 503):
                    logger.warning(
                        f"[{service_name}] Rate limited (HTTP {response.status_code}). "
                        f"Attempt {attempt}/{self.max_retries}. Backing off {delay:.1f}s."
                    )
                    time.sleep(delay)
                    delay = min(delay * 2.0, self.max_delay)
                    continue

                if response.status_code != 200:
                    logger.warning(
                        f"[{service_name}] HTTP {response.status_code} received from {url}. "
                        f"Attempt {attempt}/{self.max_retries}."
                    )
                    time.sleep(delay)
                    delay = min(delay * 2.0, self.max_delay)
                    continue

                # Content validation
                content_type = response.headers.get("Content-Type", "")
                if "application/json" not in content_type and not response.text.strip().startswith(("{", "[")):
                    logger.warning(f"[{service_name}] Non-JSON payload received: {response.text[:100]}...")
                    return None

                data = response.json()

                # Detect API-level rate limit messages in JSON
                if isinstance(data, dict):
                    if "Note" in data and "call frequency" in str(data.get("Note")):
                        logger.warning(f"[{service_name}] API rate limit notice in response: {data['Note']}")
                        time.sleep(delay)
                        delay = min(delay * 2.0, self.max_delay)
                        continue
                    if "Error Message" in data:
                        logger.warning(f"[{service_name}] API error in response: {data['Error Message']}")
                        return None

                return data

            except requests.exceptions.Timeout:
                logger.warning(f"[{service_name}] Request timed out after {self.timeout}s. Attempt {attempt}/{self.max_retries}.")
                time.sleep(delay)
                delay = min(delay * 2.0, self.max_delay)
            except requests.exceptions.RequestException as e:
                logger.warning(f"[{service_name}] Connection error: {e}. Attempt {attempt}/{self.max_retries}.")
                time.sleep(delay)
                delay = min(delay * 2.0, self.max_delay)
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"[{service_name}] Malformed JSON response: {e}")
                return None

        logger.error(f"[{service_name}] All {self.max_retries} request attempts exhausted for {url}.")
        return None
