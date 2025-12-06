#!/bin/bash
# Test the POST /api/v1/generate endpoint with curl
# This script demonstrates how to call the generate endpoint

echo "========================================================================"
echo "Story 3.3: Generate API Endpoint - API Test"
echo "========================================================================"
echo ""

# Test payload
PAYLOAD='{
  "workflow_spec": {
    "name": "Auto DCA into NEO",
    "description": "When GAS price falls below $5, automatically swap 10 GAS for NEO",
    "trigger": {
      "type": "price",
      "token": "GAS",
      "operator": "below",
      "value": 5.0
    },
    "steps": [
      {
        "action": {
          "type": "swap",
          "from_token": "GAS",
          "to_token": "NEO",
          "amount": 10.0
        },
        "description": "Swap 10 GAS to NEO"
      }
    ]
  },
  "user_id": "test_user_curl",
  "user_address": "NTestCurl123..."
}'

echo "Sending POST request to http://localhost:8000/api/v1/generate"
echo ""
echo "Request payload:"
echo "$PAYLOAD" | python -m json.tool
echo ""
echo "------------------------------------------------------------------------"
echo ""

# Send request
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

# Check if successful
if echo "$RESPONSE" | grep -q '"success": true'; then
  echo "✓ Request successful!"
  echo ""
  echo "Response:"
  echo "$RESPONSE" | python -m json.tool
  echo ""

  # Extract workflow_id
  WORKFLOW_ID=$(echo "$RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin).get('workflow_id', 'N/A'))")
  echo "Workflow ID: $WORKFLOW_ID"

  # Check if file was created
  if [ -f "data/workflows/${WORKFLOW_ID}.json" ]; then
    echo "✓ Workflow file created: data/workflows/${WORKFLOW_ID}.json"
    FILE_SIZE=$(stat -f%z "data/workflows/${WORKFLOW_ID}.json" 2>/dev/null || stat -c%s "data/workflows/${WORKFLOW_ID}.json" 2>/dev/null)
    echo "  File size: ${FILE_SIZE} bytes"
  else
    echo "✗ Workflow file not found"
  fi
else
  echo "✗ Request failed!"
  echo ""
  echo "Response:"
  echo "$RESPONSE" | python -m json.tool || echo "$RESPONSE"
fi

echo ""
echo "========================================================================"
echo "Test complete"
echo "========================================================================"
