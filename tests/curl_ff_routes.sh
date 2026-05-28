#!/usr/bin/env bash
# Смоук-тест FF-роутеров через curl: ожидается HTTP 200 при переданном docId.
#
# Переменные окружения (все опциональны, есть значения по умолчанию):
#   BASE_URL      — базовый URL сервиса (по умолчанию http://localhost:8080)
#   DOC_ID        — query docId (по умолчанию 12643)
#   PRODUCT_CODE  — поле productCode в JSON (по умолчанию fdmshowcaseapp)
#   CALL_ID       — UUID для callId (по умолчанию генерируется через uuidgen)
#
# Пример:
#   chmod +x tests/curl_ff_routes.sh
#   ./tests/curl_ff_routes.sh
#   BASE_URL=http://127.0.0.1:9000 DOC_ID=1 ./tests/curl_ff_routes.sh

set -uo pipefail

BASE_URL="${BASE_URL:-http://localhost:8080}"
DOC_ID="${DOC_ID:-12660}"
PRODUCT_CODE="${PRODUCT_CODE:-fdmshowcaseapp}"
if [[ -n "${CALL_ID:-}" ]]; then
  CALL_ID="$CALL_ID"
else
  if command -v uuidgen >/dev/null 2>&1; then
    CALL_ID="$(uuidgen | tr 'A-Z' 'a-z')"
  else
    CALL_ID="00000000-0000-4000-8000-000000000001"
  fi
fi

BASE_URL="${BASE_URL%/}"

failures=0
body_file="$(mktemp -t ff_curl_body.XXXXXX)"
trap 'rm -f "$body_file"' EXIT

json_body="$(printf '{"callId":"%s","productCode":"%s"}' "$CALL_ID" "$PRODUCT_CODE")"

echo "BASE_URL=$BASE_URL DOC_ID=$DOC_ID PRODUCT_CODE=$PRODUCT_CODE CALL_ID=$CALL_ID"
echo

# --- GET /health ---
label="GET /health"
if ! code="$(curl -sS -o "$body_file" -w "%{http_code}" -X GET "${BASE_URL}/health")"; then
  echo "FAIL $label — curl error" >&2
  failures=$((failures + 1))
elif [[ "$code" != "200" ]]; then
  echo "FAIL $label — HTTP $code (ожидался 200)" >&2
  head -c 2000 "$body_file" >&2 || true
  echo >&2
  failures=$((failures + 1))
else
  echo "OK   $label — HTTP 200"
fi

# --- POST /api/v1/ff/* ---
paths=(
  "/api/v1/ff/adr01"
  "/api/v1/ff/api01"
  "/api/v1/ff/api02"
  "/api/v1/ff/api03"
  "/api/v1/ff/cnt01"
  "/api/v1/ff/cnt02"
  "/api/v1/ff/cnt03"
  "/api/v1/ff/cpb01"
  "/api/v1/ff/cpb02"
  "/api/v1/ff/cpb03"
  "/api/v1/ff/cpb04"
  "/api/v1/ff/cpb05"
  "/api/v1/ff/ctx01"
  "/api/v1/ff/ctx02"
  "/api/v1/ff/ctx03"
  "/api/v1/ff/dep01"
  "/api/v1/ff/dep02"
  "/api/v1/ff/dep03"
  "/api/v1/ff/dep04"
  "/api/v1/ff/ea0001"
  "/api/v1/ff/git01"
  "/api/v1/ff/sq01"
  "/api/v1/ff/sq02"
  "/api/v1/ff/tech01"
  "/api/v1/ff/tech02"
  "/api/v1/ff/tech03"
  "/api/v1/ff/tech04"
  "/api/v1/ff/tech05"
  "/api/v1/ff/tech06"
)

for p in "${paths[@]}"; do
  label="POST ${p}"
  if ! code="$(curl -sS -o "$body_file" -w "%{http_code}" \
      -X POST \
      "${BASE_URL}${p}?docId=${DOC_ID}" \
      -H "Content-Type: application/json" \
      -d "$json_body")"; then
    echo "FAIL $label — curl error" >&2
    failures=$((failures + 1))
    continue
  fi
  if [[ "$code" != "200" ]]; then
    echo "FAIL $label — HTTP $code (ожидался 200)" >&2
    head -c 2000 "$body_file" >&2 || true
    echo >&2
    failures=$((failures + 1))
  else
    echo "OK   $label — HTTP 200"
  fi
done

echo
if [[ "$failures" -eq 0 ]]; then
  echo "Все проверки прошли (HTTP 200)."
  exit 0
else
  echo "Ошибок: $failures" >&2
  exit 1
fi
