#!/usr/bin/env python3
"""
Manual test script for the /api/v1/parse endpoint.
Tests the endpoint with real requests to verify everything works.
"""

import asyncio
import json
from httpx import AsyncClient


async def test_parse_endpoint():
    """Test the parse endpoint with various inputs"""
    base_url = "http://localhost:8000"

    test_cases = [
        {
            "name": "Price-based swap",
            "input": "When GAS drops below $5, swap 10 GAS for NEO",
            "expected_success": True
        },
        {
            "name": "Time-based stake",
            "input": "Stake 50% of my NEO every day at 9 AM",
            "expected_success": True
        },
        {
            "name": "Multi-step workflow",
            "input": "Every Monday, swap 30% of my GAS to NEO and stake all of it",
            "expected_success": True
        },
        {
            "name": "Ambiguous input (should error)",
            "input": "Do something with my tokens",
            "expected_success": False
        },
        {
            "name": "Empty input (should error)",
            "input": "",
            "expected_success": False
        },
        {
            "name": "Too long input (should error)",
            "input": "x" * 501,
            "expected_success": False
        }
    ]

    async with AsyncClient(base_url=base_url, timeout=10.0) as client:
        print("Testing /api/v1/parse endpoint...\n")
        print("=" * 80)

        for i, test in enumerate(test_cases, 1):
            print(f"\nTest {i}: {test['name']}")
            print(f"Input: {test['input'][:50]}{'...' if len(test['input']) > 50 else ''}")
            print("-" * 80)

            try:
                response = await client.post(
                    "/api/v1/parse",
                    json={"input": test["input"]}
                )

                print(f"Status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"✓ Success: {data.get('success')}")
                    if data.get('success'):
                        print(f"  Workflow Name: {data['workflow_spec']['name']}")
                        print(f"  Trigger Type: {data['workflow_spec']['trigger']['type']}")
                        print(f"  Steps: {len(data['workflow_spec']['steps'])}")
                        print(f"  Confidence: {data['confidence']:.2f}")
                        print(f"  Parse Time: {data['parse_time_ms']:.2f}ms")
                else:
                    error = response.json()
                    print(f"✗ Error: {error.get('detail', {}).get('error', {}).get('message', 'Unknown error')}")

                # Verify expected result
                is_success = response.status_code == 200
                if is_success == test['expected_success']:
                    print(f"✓ Result matches expected: {'Success' if is_success else 'Error'}")
                else:
                    print(f"✗ UNEXPECTED: Expected {'success' if test['expected_success'] else 'error'}, got {'success' if is_success else 'error'}")

            except Exception as e:
                print(f"✗ Exception: {str(e)}")

        # Test helper endpoints
        print("\n" + "=" * 80)
        print("\nTesting helper endpoints...")
        print("-" * 80)

        # Examples endpoint
        print("\nGET /api/v1/parse/examples")
        response = await client.get("/api/v1/parse/examples")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Examples count: {len(data.get('examples', {}))}")

        # Capabilities endpoint
        print("\nGET /api/v1/parse/capabilities")
        response = await client.get("/api/v1/parse/capabilities")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Supported tokens: {data['capabilities']['tokens']}")
            print(f"✓ Supported actions: {data['capabilities']['actions']}")
            print(f"✓ Supported triggers: {data['capabilities']['triggers']}")
            print(f"✓ Max input length: {data['constraints']['max_input_length']}")
            print(f"✓ Max parse time: {data['constraints']['max_parse_time_ms']}ms")

        print("\n" + "=" * 80)
        print("\n✓ All tests completed!")


if __name__ == "__main__":
    print("Starting manual parse endpoint tests...")
    print("Make sure the backend server is running on http://localhost:8000")
    print()

    try:
        asyncio.run(test_parse_endpoint())
    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
