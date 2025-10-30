#!/bin/bash

# PDF Processing API Test Script

API_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:8080"

echo "========================================="
echo "PDF Processing Application - API Test"
echo "========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo -e "${YELLOW}Test 1: Health Check${NC}"
echo "GET $API_URL/health"
curl -s "$API_URL/health" | python3 -m json.tool
echo ""
echo ""

# Test 2: API Info
echo -e "${YELLOW}Test 2: API Information${NC}"
echo "GET $API_URL/"
curl -s "$API_URL/" | python3 -m json.tool
echo ""
echo ""

# Test 3: Check if PDF file exists
if [ ! -f "sample_pdfs/sample.pdf" ]; then
    echo -e "${RED}Warning: No sample.pdf found in sample_pdfs/ directory${NC}"
    echo "Please place a PDF file at sample_pdfs/sample.pdf to test upload"
    echo ""
    echo "You can still test other endpoints manually."
    echo ""
else
    # Test 3: Upload PDF with PyPDF parser
    echo -e "${YELLOW}Test 3: Upload PDF (PyPDF parser)${NC}"
    echo "POST $API_URL/api/upload?parser=pypdf"
    RESPONSE=$(curl -s -X POST -F "files=@sample_pdfs/sample.pdf" \
         "$API_URL/api/upload?parser=pypdf")
    echo "$RESPONSE" | python3 -m json.tool

    # Extract job_id from response
    JOB_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['job_id'])" 2>/dev/null)

    if [ -z "$JOB_ID" ]; then
        echo -e "${RED}Failed to extract job_id${NC}"
    else
        echo ""
        echo -e "${GREEN}Job created: $JOB_ID${NC}"
        echo ""
        echo ""

        # Test 4: Check job status
        echo -e "${YELLOW}Test 4: Check Job Status${NC}"
        echo "GET $API_URL/api/status/$JOB_ID"
        curl -s "$API_URL/api/status/$JOB_ID" | python3 -m json.tool
        echo ""
        echo ""

        # Wait a bit for processing
        echo -e "${YELLOW}Waiting 5 seconds for processing...${NC}"
        sleep 5
        echo ""

        # Test 5: Get result
        echo -e "${YELLOW}Test 5: Get Processing Result${NC}"
        echo "GET $API_URL/api/result/$JOB_ID"
        RESULT=$(curl -s "$API_URL/api/result/$JOB_ID")
        echo "$RESULT" | python3 -m json.tool
        echo ""
        echo ""
    fi
fi

# Test 6: List all jobs
echo -e "${YELLOW}Test 6: List All Jobs${NC}"
echo "GET $API_URL/api/jobs"
curl -s "$API_URL/api/jobs" | python3 -m json.tool
echo ""
echo ""

# Summary
echo "========================================="
echo -e "${GREEN}Testing Complete!${NC}"
echo "========================================="
echo ""
echo "API Documentation: $API_URL/docs"
echo "Web UI: $FRONTEND_URL"
echo ""
echo "To test with different parsers:"
echo "  curl -X POST -F \"files=@sample.pdf\" \"$API_URL/api/upload?parser=gemini\""
echo "  curl -X POST -F \"files=@sample.pdf\" \"$API_URL/api/upload?parser=mistral\""
echo ""
