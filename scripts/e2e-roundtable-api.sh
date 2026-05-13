#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://localhost:8000/api}"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

require_command curl
require_command jq

payload='{"decisionPrompt":"E2E: 是否现在把后端部署到 Render 并开放接口？","personaIds":["drucker","munger","socrates"]}'

personas="$(curl -sS "$API_BASE_URL/roundtable/personas")"
persona_count="$(printf '%s' "$personas" | jq 'length')"
if [ "$persona_count" -lt 3 ]; then
  echo "FAIL personas count=$persona_count" >&2
  exit 1
fi

created="$(
  curl -sS -X POST "$API_BASE_URL/roundtable/sessions" \
    -H 'Content-Type: application/json' \
    -d "$payload"
)"
session_id="$(printf '%s' "$created" | jq -r '.session.id')"
session_status="$(printf '%s' "$created" | jq -r '.session.status')"
selected_count="$(printf '%s' "$created" | jq '.session.selectedPersonas | length')"
if [ -z "$session_id" ] || [ "$session_id" = "null" ] || [ "$session_status" != "ready" ] || [ "$selected_count" -ne 3 ]; then
  echo "FAIL create session" >&2
  printf '%s' "$created" | jq . >&2
  exit 1
fi

stream_file="$(mktemp)"
follow_file="$(mktemp)"
trap 'rm -f "$stream_file" "$follow_file"' EXIT

curl -sS -X POST "$API_BASE_URL/roundtable/sessions/$session_id/stream" -o "$stream_file"
stream_size="$(wc -c < "$stream_file" | tr -d ' ')"
if [ "$stream_size" -le 0 ]; then
  echo "FAIL empty discussion stream" >&2
  exit 1
fi

restored="$(curl -sS "$API_BASE_URL/roundtable/sessions/$session_id")"
completed_status="$(printf '%s' "$restored" | jq -r '.status')"
message_count="$(printf '%s' "$restored" | jq '.transcript | length')"
recommendation="$(printf '%s' "$restored" | jq -r '.artifacts.recommendation // empty')"
if [ "$completed_status" != "completed" ] || [ "$message_count" -lt 4 ] || [ -z "$recommendation" ]; then
  echo "FAIL restore after discussion" >&2
  printf '%s' "$restored" | jq '{id,status,messages:(.transcript|length),artifacts}' >&2
  exit 1
fi

curl -sS -X POST "$API_BASE_URL/roundtable/sessions/$session_id/follow-up/stream" \
  -H 'Content-Type: application/json' \
  -d '{"question":"如果只能先做一件事，应该是什么？"}' \
  -o "$follow_file"
follow_size="$(wc -c < "$follow_file" | tr -d ' ')"
if [ "$follow_size" -le 0 ]; then
  echo "FAIL empty follow-up stream" >&2
  exit 1
fi

final="$(curl -sS "$API_BASE_URL/roundtable/sessions/$session_id")"
follow_messages="$(printf '%s' "$final" | jq '[.transcript[] | select(.roundName == "follow_up")] | length')"
if [ "$follow_messages" -lt 1 ]; then
  echo "FAIL follow-up not persisted" >&2
  printf '%s' "$final" | jq '{id,status,messages:(.transcript|length),rounds:[.transcript[].roundName]}' >&2
  exit 1
fi

total_messages="$(printf '%s' "$final" | jq '.transcript | length')"
echo "PASS api-e2e session_id=$session_id personas=$persona_count selected=$selected_count discussion_stream_bytes=$stream_size follow_stream_bytes=$follow_size messages=$total_messages follow_up_messages=$follow_messages"
