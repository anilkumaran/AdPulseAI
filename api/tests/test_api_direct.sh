#!/bin/bash

echo "Testing AdPulseAI API Endpoints"
echo "================================"

# Test 1: Health check
echo -e "\n1. Testing health check..."
curl -s http://localhost:8000/api/healthcheck | python -m json.tool 2>/dev/null || echo "❌ Server not responding"

# Test 2: Login
echo -e "\n2. Testing login..."
TOKEN=$(curl -s -X POST http://localhost:8000/token \
  -d "username=merchant1" \
  -d "password=user123" | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo "❌ Login failed"
  exit 1
fi

echo "✅ Login successful"
echo "Token: ${TOKEN:0:20}..."

# Test 3: Generate ads
echo -e "\n3. Testing ad generation..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product_info": "Test Product - ₹999", "voice": "Professional"}')

echo "$RESPONSE" | python -m json.tool 2>/dev/null || echo "Response: $RESPONSE"

# Check if response contains platforms
if echo "$RESPONSE" | grep -q "FACEBOOK"; then
  echo "✅ Ad generation successful - contains platform content"
else
  echo "❌ Ad generation failed or missing platform content"
fi

echo -e "\nDone!"
