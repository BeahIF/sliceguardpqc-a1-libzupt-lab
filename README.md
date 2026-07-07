# SliceGuardPQC A1 + libzupt Lab

Reproducible Docker-based lab for testing **SliceGuardPQC** with **O-RAN A1 policies** and **libzupt-based hybrid post-quantum cryptography enforcement**.

This repository contains the experimental environment used to validate the first functional POC of SliceGuardPQC integrated with libzupt.

---

## 1. What this lab does

This lab demonstrates how an adaptive security policy can select whether a network slice should use hybrid post-quantum cryptography.

The POC simulates three network slices:

| Slice    | Policy ID                 | Crypto Profile   | Expected Behavior                 |
| -------- | ------------------------- | ---------------- | --------------------------------- |
| Hospital | `slice-hospital-security` | `LIBZUPT_HYBRID` | Payload is encrypted with libzupt |
| Industry | `slice-industry-security` | `LIBZUPT_HYBRID` | Payload is encrypted with libzupt |
| Public   | `slice-public-security`   | `NONE`           | Payload is not encrypted          |

The core idea is:

```text
A1 Policy
   ↓
security-agent
   ↓
crypto_profile decision
   ↓
libzupt or no encryption
   ↓
POC evidence
```

---

## 2. Main components

### `ric1`

O-RAN SC A1 Simulator.

It is used to simulate the A1 policy interface and receive SliceGuardPQC security policies.

Default exposed ports:

```text
8085 → A1 Simulator HTTP API
8185 → Additional simulator port
```

### `a1pms`

O-RAN SC A1 Policy Management Service.

Default exposed ports:

```text
8081 → A1PMS API
8433 → A1PMS HTTPS/API port
```

### `policy-bootstrap`

Small bootstrap container based on `curlimages/curl`.

It creates or updates:

```text
policy type 2001
slice-hospital-security
slice-industry-security
slice-public-security
```

This is necessary because the A1 Simulator stores policies in memory. If the simulator container is recreated, the policies disappear.

### `security-agent`

Python-based enforcement agent.

It:

1. reads a policy;
2. extracts `statement.crypto_profile`;
3. decides whether to apply libzupt;
4. encrypts/decrypts a simulated payload;
5. prints evidence such as payload size, ciphertext size, header size, overhead and integrity status.

---

## 3. Repository structure

```text
openran-a1-lab/
├── docker-compose.yml
├── policytype-2001.json
├── hospital.json
├── industry.json
├── public.json
├── bootstrap/
│   └── bootstrap-policies.sh
└── security-agent/
    ├── Dockerfile
    ├── app.py
    ├── crypto_adapter.py
    ├── policy_client.py
    ├── requirements.txt
    └── keys/
        └── .gitkeep
```

---

## 4. Policy model

The policy type used in this lab is `security_profile_v1`, registered as policy type `2001`.

Each policy follows this structure:

```json
{
  "scope": {
    "slice_id": "hospital",
    "sector": "hospital"
  },
  "statement": {
    "security_level": "L1",
    "crypto_profile": "LIBZUPT_HYBRID",
    "ttl_seconds": 3600,
    "reason": "Sensitive healthcare data"
  }
}
```

The most important field for the POC is:

```json
"crypto_profile": "LIBZUPT_HYBRID"
```

or:

```json
"crypto_profile": "NONE"
```

The `security-agent` uses this value to decide whether libzupt should be applied.

---

## 5. Prerequisites

You need:

- Docker Desktop;
- Docker Compose;
- Git;
- PowerShell;
- internet access for the first build, because the `security-agent` Dockerfile clones and compiles libzupt.

Check Docker:

```powershell
docker --version
docker compose version
```

---

## 6. First-time setup

Clone the repository:

```powershell
git clone https://github.com/BeahIF/sliceguardpqc-a1-libzupt-lab.git
cd sliceguardpqc-a1-libzupt-lab
```

Build the `security-agent` image:

```powershell
docker compose build security-agent
```

This may take a few minutes because the image compiles libzupt and its Python bindings.

---

## 7. Starting the lab

Start the A1 Simulator and A1PMS:

```powershell
docker compose up -d ric1 a1pms
```

Run the policy bootstrap:

```powershell
docker compose run --rm policy-bootstrap
```

Expected output:

```text
[bootstrap] Esperando o A1 Simulator...
[bootstrap] A1 Simulator disponível.
[bootstrap] Criando ou atualizando policy type 2001...
[bootstrap] Criando ou atualizando policy hospital...
[bootstrap] Criando ou atualizando policy industrial...
[bootstrap] Criando ou atualizando policy pública...
[bootstrap] Policies registradas:
["slice-hospital-security", "slice-industry-security", "slice-public-security"]
[bootstrap] Inicialização concluída.
```

---

## 8. Validating the policies

Check the policies from the host machine:

```powershell
curl.exe -s "http://localhost:8085/a1-p/policytypes/2001/policies"
```

Expected result:

```json
["slice-hospital-security", "slice-industry-security", "slice-public-security"]
```

Check the active A1 interface:

```powershell
curl.exe -i "http://localhost:8085/container_interfaces"
```

Expected interface:

```text
Current interface: OSC_2.1.0
```

---

## 9. Running the POC

### Hospital slice

```powershell
docker compose run --rm --no-deps `
  -e POLICY_ID=slice-hospital-security `
  security-agent
```

Expected behavior:

```text
requested_crypto_profile: LIBZUPT_HYBRID
applied_crypto_profile: LIBZUPT_HYBRID
encrypted: true
integrity_confirmed: true
```

### Industry slice

```powershell
docker compose run --rm --no-deps `
  -e POLICY_ID=slice-industry-security `
  security-agent
```

Expected behavior:

```text
requested_crypto_profile: LIBZUPT_HYBRID
applied_crypto_profile: LIBZUPT_HYBRID
encrypted: true
integrity_confirmed: true
```

### Public slice

```powershell
docker compose run --rm --no-deps `
  -e POLICY_ID=slice-public-security `
  security-agent
```

Expected behavior:

```text
requested_crypto_profile: NONE
applied_crypto_profile: NONE
encrypted: false
integrity_confirmed: true
```

---

## 10. Example output

For a hospital payload, the POC may output something like:

```json
{
  "policy_id": "slice-hospital-security",
  "slice_id": "hospital",
  "security_level": "L1",
  "requested_crypto_profile": "LIBZUPT_HYBRID",
  "applied_crypto_profile": "LIBZUPT_HYBRID",
  "encrypted": true,
  "original_size_bytes": 76,
  "ciphertext_size_bytes": 128,
  "header_size_bytes": 1137,
  "total_transmitted_bytes": 1265,
  "overhead_bytes": 1189,
  "overhead_percent": 1564.47,
  "integrity_confirmed": true
}
```

This confirms that:

1. the policy was read;
2. the crypto profile was interpreted;
3. libzupt was applied;
4. the decrypted payload matched the original payload.

---

## 11. Important operational note

The A1 Simulator stores policy types and policy instances in memory.

This means that policies may disappear when:

```powershell
docker compose down
```

is executed, or when the `ric1` container is recreated.

For this reason, always run the bootstrap after starting the simulator:

```powershell
docker compose up -d ric1 a1pms
docker compose run --rm policy-bootstrap
```

The bootstrap is part of the reproducibility strategy of this lab.

---

## 12. Useful daily workflow

```powershell
cd "C:\Users\...\openran-a1-lab"

docker compose up -d ric1 a1pms

docker compose run --rm policy-bootstrap

curl.exe -s "http://localhost:8085/a1-p/policytypes/2001/policies"

docker compose run --rm --no-deps `
  -e POLICY_ID=slice-hospital-security `
  security-agent

docker compose run --rm --no-deps `
  -e POLICY_ID=slice-public-security `
  security-agent
```

---

## 13. Stopping the lab

To stop the containers without removing them:

```powershell
docker compose stop
```

To start again:

```powershell
docker compose start
docker compose run --rm policy-bootstrap
```

To remove the environment:

```powershell
docker compose down
```

After `docker compose down`, run the bootstrap again when restarting the lab.

---

## 14. Troubleshooting

### The policy list returns `[]`

Run the bootstrap again:

```powershell
docker compose run --rm policy-bootstrap
```

Then check:

```powershell
curl.exe -s "http://localhost:8085/a1-p/policytypes/2001/policies"
```

### The `security-agent` returns `404`

The policy probably does not exist in the simulator anymore.

Run:

```powershell
docker compose run --rm policy-bootstrap
```

Then run the agent again.

### The `security-agent` cannot resolve `ric1`

Check whether the `security-agent` and `ric1` are on the same Docker network:

```powershell
docker compose config
```

Both should use:

```yaml
networks:
  - nonrtric-docker-net
```

You can also test DNS resolution:

```powershell
docker compose run --rm --no-deps `
  security-agent `
  python3 -c "import socket; print(socket.gethostbyname('ric1'))"
```

### The bootstrap fails with HTTP 400

Check whether the JSON files match the schema in `policytype-2001.json`.

Common issue:

```json
"sector": "industrial"
```

should be:

```json
"sector": "industry"
```

### The agent says `statement.crypto_profile` is missing

Check that the policy contains:

```json
"statement": {
  "crypto_profile": "LIBZUPT_HYBRID"
}
```

or:

```json
"statement": {
  "crypto_profile": "NONE"
}
```

---

## 15. Security note

The libzupt key files are generated inside:

```text
security-agent/keys/
```

Do not commit private keys.

The repository should ignore:

```gitignore
security-agent/keys/*
!security-agent/keys/.gitkeep
```

If a private key was accidentally staged, remove it before committing:

```powershell
git restore --staged security-agent/keys/private.zupt-key
git restore --staged security-agent/keys/public.zupt-key
```

---

## 16. What POC 1 proves

POC 1 demonstrates functional feasibility:

- libzupt can be compiled inside the Docker environment;
- the Python binding can be imported by the `security-agent`;
- hybrid post-quantum encryption can be applied to a payload;
- the payload can be decrypted successfully;
- integrity is preserved;
- overhead can be measured;
- SliceGuardPQC policies can define different crypto profiles per slice;
- the `security-agent` can enforce different behavior based on the selected policy.

This POC does not yet prove production readiness or performance suitability.

---

## 17. Next steps

Planned next steps:

1. **POC 2 — Benchmarking**
   - compare `NONE` vs `LIBZUPT_HYBRID`;
   - test multiple payload sizes;
   - measure encryption/decryption time;
   - generate CSV results;
   - analyze overhead.

2. **POC 3 — Dynamic policy switching**
   - change the policy at runtime;
   - measure how fast the agent reacts;
   - evaluate crypto-agility behavior.

3. **Documentation and dissemination**
   - write the POC 1 report;
   - create educational material about libzupt;
   - prepare a LinkedIn post and workshop proposal.

```

```
