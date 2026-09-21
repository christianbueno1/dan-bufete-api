#!/usr/bin/env bash

set -euo pipefail

BASE_URL="http://localhost:8000"

CASE_ID=""
DOCUMENT_ID=""
UPLOAD_DOCUMENT_ID=""

print_section() {
    echo
    echo "============================================================"
    echo "$1"
    echo "============================================================"
}

request() {
    local method="$1"
    local endpoint="$2"
    local expected_status="$3"
    local data="${4:-}"

    local response_file
    local status

    response_file="$(mktemp)"

    if [[ -n "$data" ]]; then
        status="$(
            curl -sS \
                -X "$method" \
                "$BASE_URL$endpoint" \
                -H "Content-Type: application/json" \
                -d "$data" \
                -o "$response_file" \
                -w "%{http_code}"
        )"
    else
        status="$(
            curl -sS \
                -X "$method" \
                "$BASE_URL$endpoint" \
                -o "$response_file" \
                -w "%{http_code}"
        )"
    fi

    echo "HTTP $status" >&2
    echo >&2

    if [[ -s "$response_file" ]]; then
        jq . "$response_file" >&2
    else
        echo "(empty response body)" >&2
    fi

    if [[ "$status" != "$expected_status" ]]; then
        echo >&2
        echo "ERROR: expected HTTP $expected_status, got HTTP $status" >&2
        rm -f "$response_file"
        return 1
    fi

    cat "$response_file"
    rm -f "$response_file"
}

cleanup() {
    local exit_code=$?

    echo
    print_section "CLEANUP"

    if [[ -n "$UPLOAD_DOCUMENT_ID" ]]; then
        echo "Deleting uploaded document $UPLOAD_DOCUMENT_ID..."

        request \
            "DELETE" \
            "/cases/$CASE_ID/documents/$UPLOAD_DOCUMENT_ID" \
            "204" \
            || true

        UPLOAD_DOCUMENT_ID=""
    fi

    if [[ -n "$DOCUMENT_ID" ]]; then
        echo "Deleting document $DOCUMENT_ID..."

        request \
            "DELETE" \
            "/cases/$CASE_ID/documents/$DOCUMENT_ID" \
            "204" \
            || true

        DOCUMENT_ID=""
    fi

    if [[ -n "$CASE_ID" ]]; then
        echo "Deleting case $CASE_ID..."

        request \
            "DELETE" \
            "/cases/$CASE_ID" \
            "204" \
            || true

        CASE_ID=""
    fi

    echo "Cleanup completed."

    exit "$exit_code"
}

trap cleanup EXIT

create_case() {
    print_section "POST /cases"

    local response

    response="$(
        request \
            "POST" \
            "/cases" \
            "201" \
            '{
              "practice_area": "COMMERCIAL",
              "title": "Smoke test case",
              "description": "Caso creado automáticamente por api-smoke-test.sh",
              "client_name": "Smoke Test Client",
              "lawyer_name": "Smoke Test Lawyer",
              "opened_at": "2026-09-20T10:00:00Z"
            }'
    )"

    CASE_ID="$(jq -r '.id' <<< "$response")"

    echo
    echo "Created CASE_ID=$CASE_ID"
}

list_cases() {
    print_section "GET /cases"

    request "GET" "/cases" "200"
}

get_case() {
    print_section "GET /cases/$CASE_ID"

    request "GET" "/cases/$CASE_ID" "200"
}

create_document() {
    print_section "POST /cases/$CASE_ID/documents"

    local response

    response="$(
        request \
            "POST" \
            "/cases/$CASE_ID/documents" \
            "201" \
            '{
                "name": "Smoke test document.pdf",
                "document_type": "contract",
                "file_url": "https://example.com/smoke-test.pdf",
                "uploaded_by": "smoke-test"
            }'
    )"

    DOCUMENT_ID="$(jq -r '.id' <<< "$response")"

    echo
    echo "Created DOCUMENT_ID=$DOCUMENT_ID"
}

get_documents() {
    print_section "GET /cases/$CASE_ID/documents"

    request "GET" "/cases/$CASE_ID/documents" "200"
}

upload_document() {
    print_section "POST /cases/$CASE_ID/documents/upload"

    local test_file="/tmp/api-smoke-test.pdf"
    local response_file
    local status

    printf 'Smoke test PDF content\n' > "$test_file"

    response_file="$(mktemp)"

    status="$(
        curl -sS \
            -X POST \
            "$BASE_URL/cases/$CASE_ID/documents/upload" \
            -F "file=@$test_file" \
            -F "document_type=evidence" \
            -F "uploaded_by=smoke-test" \
            -F "name=Uploaded smoke test document" \
            -o "$response_file" \
            -w "%{http_code}"
    )"

    echo "HTTP $status"
    echo

    jq . "$response_file"

    if [[ "$status" != "201" ]]; then
        echo
        echo "ERROR: expected HTTP 201, got HTTP $status"
        rm -f "$response_file" "$test_file"
        return 1
    fi

    UPLOAD_DOCUMENT_ID="$(jq -r '.id' "$response_file")"

    echo
    echo "Created UPLOAD_DOCUMENT_ID=$UPLOAD_DOCUMENT_ID"

    rm -f "$response_file" "$test_file"
}

delete_document() {
    print_section "DELETE /cases/$CASE_ID/documents/$DOCUMENT_ID"

    request \
        "DELETE" \
        "/cases/$CASE_ID/documents/$DOCUMENT_ID" \
        "204"
}

delete_uploaded_document() {
    print_section "DELETE /cases/$CASE_ID/documents/$UPLOAD_DOCUMENT_ID"

    request \
        "DELETE" \
        "/cases/$CASE_ID/documents/$UPLOAD_DOCUMENT_ID" \
        "204"
}

delete_case() {
    print_section "DELETE /cases/$CASE_ID"

    request \
        "DELETE" \
        "/cases/$CASE_ID" \
        "204"
}

verify_deleted_case() {
    print_section "GET /cases/$CASE_ID after DELETE"

    request \
        "GET" \
        "/cases/$CASE_ID" \
        "404"
}

test_validation() {
    print_section "POST /cases — validation test"

    request \
        "POST" \
        "/cases" \
        "422" \
        '{
          "practice_area": "COMMERCIAL",
          "title": "Invalid future date test",
          "description": "This request should be rejected",
          "client_name": "Validation Test",
          "lawyer_name": "Validation Test",
          "filing_date": "2099-01-01"
        }'
}

main() {
    echo "Dan Bufete API smoke test"
    echo "Base URL: $BASE_URL"

    create_case
    list_cases
    get_case

    create_document
    get_documents
    get_case

    upload_document
    get_documents
    get_case


    test_validation


    echo
    echo "============================================================"
    echo "SMOKE TEST PASSED"
    echo "============================================================"
}

main "$@"
