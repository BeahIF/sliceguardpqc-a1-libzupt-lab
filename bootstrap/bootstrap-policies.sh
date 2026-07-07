#!/bin/sh

set -eu

BASE_URL="${A1_SIMULATOR_URL:-http://ric1:8085}"

echo "[bootstrap] Esperando o A1 Simulator..."

attempt=1
max_attempts=30

while [ "$attempt" -le "$max_attempts" ]; do
  if curl --silent --fail \
    "$BASE_URL/container_interfaces" \
    > /dev/null; then
    echo "[bootstrap] A1 Simulator disponível."
    break
  fi

  echo "[bootstrap] Tentativa $attempt/$max_attempts..."
  attempt=$((attempt + 1))
  sleep 2
done

if [ "$attempt" -gt "$max_attempts" ]; then
  echo "[bootstrap] O A1 Simulator não ficou disponível."
  exit 1
fi

echo "[bootstrap] Criando ou atualizando policy type 2001..."

curl --silent \
  --show-error \
  --fail-with-body \
  --request PUT \
  "$BASE_URL/a1-p/policytypes/2001" \
  --header "Content-Type: application/json" \
  --data-binary "@/policies/policytype-2001.json"

echo "[bootstrap] Criando ou atualizando policy hospital..."

curl --silent \
  --show-error \
  --fail-with-body \
  --request PUT \
  "$BASE_URL/a1-p/policytypes/2001/policies/slice-hospital-security" \
  --header "Content-Type: application/json" \
  --data-binary "@/policies/hospital.json"

echo "[bootstrap] Criando ou atualizando policy industrial..."

curl --silent \
  --show-error \
  --fail-with-body \
  --request PUT \
  "$BASE_URL/a1-p/policytypes/2001/policies/slice-industry-security" \
  --header "Content-Type: application/json" \
  --data-binary "@/policies/industry.json"

echo "[bootstrap] Criando ou atualizando policy pública..."

curl --silent \
  --show-error \
  --fail-with-body \
  --request PUT \
  "$BASE_URL/a1-p/policytypes/2001/policies/slice-public-security" \
  --header "Content-Type: application/json" \
  --data-binary "@/policies/public.json"

echo "[bootstrap] Policies registradas:"

curl --silent \
  --show-error \
  --fail-with-body \
  "$BASE_URL/a1-p/policytypes/2001/policies"

echo ""
echo "[bootstrap] Inicialização concluída."