import json
import os
from pathlib import Path
from typing import Any

import requests


class PolicyClient:
    def __init__(
        self,
        base_url: str | None = None,
        policy_type_id: str = "2001",
        timeout_seconds: float = 5.0,
    ) -> None:
        self.base_url = (
            base_url
            or os.getenv("A1PMS_BASE_URL")
            or "http://ric1:8085"
        ).rstrip("/")

        self.policy_type_id = policy_type_id
        self.timeout_seconds = timeout_seconds

        self.policy_source = os.getenv(
            "POLICY_SOURCE",
            "a1",
        ).strip().lower()

        self.policy_files_dir = Path(
            os.getenv(
                "POLICY_FILES_DIR",
                "/policies",
            )
        )

    def get_policy(self, policy_id: str) -> dict[str, Any]:
        if self.policy_source == "file":
            return self._get_policy_from_file(policy_id)

        return self._get_policy_from_a1(policy_id)

    def _get_policy_from_file(
        self,
        policy_id: str,
    ) -> dict[str, Any]:
        path = self.policy_files_dir / f"{policy_id}.json"

        print(f"[policy] FILE {path}")

        if not path.exists():
            raise FileNotFoundError(
                f"Policy file não encontrada: {path}"
            )

        with path.open("r", encoding="utf-8") as file:
            policy = json.load(file)

        if not isinstance(policy, dict):
            raise ValueError(
                f"Formato inválido para a policy {policy_id}"
            )

        return policy

    def _get_policy_from_a1(
        self,
        policy_id: str,
    ) -> dict[str, Any]:
        url = (
            f"{self.base_url}/a1-p/policytypes/"
            f"{self.policy_type_id}/policies/{policy_id}"
        )

        print(f"[policy] GET {url}")

        response = requests.get(
            url,
            timeout=self.timeout_seconds,
        )

        print(f"[policy] Status HTTP: {response.status_code}")

        if not response.ok:
            print(f"[policy] Resposta: {response.text!r}")

        response.raise_for_status()

        policy = response.json()

        if not isinstance(policy, dict):
            raise ValueError(
                f"Formato inválido para a policy {policy_id}"
            )

        return policy