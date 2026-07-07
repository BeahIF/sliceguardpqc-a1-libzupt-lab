import json
import os
import sys
import time
from typing import Any

from crypto_adapter import CryptoAdapter
from policy_client import PolicyClient


DEFAULT_POLICY_ID = "slice-hospital-security"


def calculate_overhead(
    original_size: int,
    ciphertext_size: int,
    header_size: int,
) -> tuple[int, float]:
    total_size = ciphertext_size + header_size
    overhead_bytes = total_size - original_size

    if original_size == 0:
        return overhead_bytes, 0.0

    overhead_percent = overhead_bytes / original_size * 100

    return overhead_bytes, overhead_percent


def execute_policy_test(
    policy_id: str,
    payload: bytes,
) -> dict[str, Any]:
    policy_client = PolicyClient()
    crypto = CryptoAdapter()

    print(f"[policy] Consultando {policy_id}")

    policy = policy_client.get_policy(policy_id)

    print(
        json.dumps(
            policy,
            indent=2,
            ensure_ascii=False,
        )
    )

    scope = policy.get("scope", {})
    statement = policy.get("statement", {})

    slice_id = scope.get("slice_id")
    security_level = statement.get("security_level")
    crypto_profile = statement.get("crypto_profile")

    if not crypto_profile:
        raise ValueError(
            "A policy não possui statement.crypto_profile."
        )

    encryption_start = time.perf_counter()

    result = crypto.encrypt(
        payload=payload,
        profile=crypto_profile,
    )

    encryption_time_ms = (
        time.perf_counter() - encryption_start
    ) * 1000

    decryption_start = time.perf_counter()

    decrypted_payload = crypto.decrypt(
        ciphertext=result["ciphertext"],
        header=result["header"],
        profile=result["profile"],
    )

    decryption_time_ms = (
        time.perf_counter() - decryption_start
    ) * 1000

    original_size = len(payload)
    ciphertext_size = len(result["ciphertext"])
    header_size = len(result["header"])

    overhead_bytes, overhead_percent = calculate_overhead(
        original_size,
        ciphertext_size,
        header_size,
    )

    integrity_confirmed = decrypted_payload == payload

    return {
        "policy_id": policy_id,
        "slice_id": slice_id,
        "security_level": security_level,
        "requested_crypto_profile": crypto_profile,
        "applied_crypto_profile": result["profile"],
        "encrypted": result["encrypted"],
        "original_size_bytes": original_size,
        "ciphertext_size_bytes": ciphertext_size,
        "header_size_bytes": header_size,
        "total_transmitted_bytes": (
            ciphertext_size + header_size
        ),
        "overhead_bytes": overhead_bytes,
        "overhead_percent": round(overhead_percent, 2),
        "encryption_time_ms": round(
            encryption_time_ms,
            4,
        ),
        "decryption_time_ms": round(
            decryption_time_ms,
            4,
        ),
        "integrity_confirmed": integrity_confirmed,
    }


def main() -> None:
    policy_id = os.getenv(
        "POLICY_ID",
        DEFAULT_POLICY_ID,
    )

    payload = (
        b'{"slice_id":"hospital","patient_id":"123",'
        b'"data":"simulated-sensitive-data"}'
    )

    try:
        evidence = execute_policy_test(
            policy_id=policy_id,
            payload=payload,
        )
    except Exception as error:
        print(
            f"[erro] Falha na POC: {error}",
            file=sys.stderr,
        )
        raise

    print()
    print("=== Evidência SliceGuardPQC + libzupt ===")
    print(
        json.dumps(
            evidence,
            indent=2,
            ensure_ascii=False,
        )
    )

    if not evidence["integrity_confirmed"]:
        raise RuntimeError(
            "O payload recuperado difere do original."
        )

    print()
    print("Policy aplicada e integridade confirmada.")


if __name__ == "__main__":
    main()