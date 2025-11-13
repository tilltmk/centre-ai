#!/bin/bash
# API Test Script for Centre AI MCP Server

API_KEY="${API_KEY:-dev-api-key-12345}"
BASE_URL="${BASE_URL:-http://localhost:5000}"

echo "======================================"
echo "Centre AI - MCP Server API Test"
echo "======================================"
echo ""
echo "Base URL: $BASE_URL"
echo "API Key: $API_KEY"
echo ""

# Test 1: Health Check
echo "Test 1: Health Check"
echo "------------------------------"
curl -s "$BASE_URL/health" | python3 -m json.tool
echo -e "\n"

# Test 2: Server Status
echo "Test 2: Server Status"
echo "------------------------------"
curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/api/status" | python3 -m json.tool
echo -e "\n"

# Test 3: List Tools
echo "Test 3: List Tools"
echo "------------------------------"
curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/mcp/tools/list" | python3 -m json.tool
echo -e "\n"

# Test 4: Execute Tool (text_length)
echo "Test 4: Execute Tool - text_length"
echo "------------------------------"
curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"tool_name": "text_length", "parameters": {"text": "Hello, Centre AI!"}}' \
  "$BASE_URL/mcp/tools/execute" | python3 -m json.tool
echo -e "\n"

# Test 5: Store Memory
echo "Test 5: Store Memory"
echo "------------------------------"
curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"key": "test_key", "value": "test_value", "tags": ["test"]}' \
  "$BASE_URL/mcp/memory/store" | python3 -m json.tool
echo -e "\n"

# Test 6: Retrieve Memory
echo "Test 6: Retrieve Memory"
echo "------------------------------"
curl -s -H "X-API-Key: $API_KEY" \
  "$BASE_URL/mcp/memory/retrieve?key=test_key" | python3 -m json.tool
echo -e "\n"

echo "======================================"
echo "API Tests Complete"
echo "======================================"
