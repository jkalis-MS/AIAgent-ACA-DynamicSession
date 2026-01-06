"""Test script for sandbox implementations."""
import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging to see all logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

# Load environment variables
load_dotenv()

# Test imports
print("Testing imports...")
from tools.weather_sandbox_local import research_weather_local
from tools.weather_sandbox_e2b import research_weather_e2b
from tools.weather_sandbox_aca import research_weather_aca
from tools.weather_sandbox_daytona import research_weather_daytona

print("✓ All imports successful\n")

# Test parameters
destination = "New York"
dates = "February 2026"

# Test Local sandbox
print("="*60)
print("Testing Local Sandbox - New York, February 2026")
print("="*60)
print("\n--- Starting Local Execution ---")
local_result = research_weather_local(destination, dates)
print("\n--- Tool Output ---")
print(local_result)
print("\n")

# # Test E2B sandbox
# print("="*60)
# print("Testing E2B Sandbox - New York, February 2026")
# print("="*60)
# e2b_key = os.getenv('E2B_API_KEY')
# if e2b_key:
#     print(f"E2B API Key found: {e2b_key[:10]}...")
#     print("\n--- Starting E2B Execution ---")
#     e2b_result = research_weather_e2b(destination, dates)
#     print("\n--- Tool Output ---")
#     print(e2b_result)
# else:
#     print("⚠️ E2B_API_KEY not found")

# print("\n")

# # Test ACA sandbox
print("="*60)
print("Testing ACA Sandbox - New York, February 2026")
print("="*60)
aca_endpoint = os.getenv('ACA_POOL_MANAGEMENT_ENDPOINT')
if aca_endpoint:
    print(f"ACA Pool Management Endpoint found: {aca_endpoint[:50]}...")
    print("\n--- Starting ACA Execution ---")
    aca_result = research_weather_aca(destination, dates)
    print("\n--- Tool Output ---")
    print(aca_result)
else:
    print("⚠️ ACA_POOL_MANAGEMENT_ENDPOINT not found")
    print("To test ACA sandbox, set ACA_POOL_MANAGEMENT_ENDPOINT in your .env file")

print("\n")

# Test Daytona sandbox
# print("="*60)
# print("Testing Daytona Sandbox - New York, February 2026")
# print("="*60)
# daytona_key = os.getenv('DAYTONA_API_KEY')
# if daytona_key:
#     print(f"Daytona API Key found: {daytona_key[:10]}...")
#     print("\n--- Starting Daytona Execution ---")
#     daytona_result = research_weather_daytona(destination, dates)
#     print("\n--- Tool Output ---")
#     print(daytona_result)
# else:
#     print("⚠️ DAYTONA_API_KEY not found")
#     print("To test Daytona sandbox:")
#     print("  1. Get your API key from https://app.daytona.io/dashboard/keys")
#     print("  2. Set DAYTONA_API_KEY in your .env file")
#     print("  3. Install the SDK: pip install daytona")

# print("\n" + "="*60)
# print("✅ All tests completed!")
# print("="*60)
