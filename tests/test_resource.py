#!/usr/bin/env python3
"""Test script to verify the usage guidelines resource using FastMCP client"""

import asyncio
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


async def test_resource():
    """Test that the usage guidelines resource can be read"""
    print("Testing memory://usage-guidelines resource...\n")

    try:
        # Start the MCP server as a subprocess
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "agentmemory"],
        )

        print("=== Starting MCP Server ===")
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                print("Initializing session...")
                await session.initialize()
                print("✅ Session initialized\n")

                # List all available resources
                print("=== Listing Resources ===")
                resources_result = await session.list_resources()
                resources = resources_result.resources
                print(f"Found {len(resources)} resource(s):")
                for resource in resources:
                    print(f"  - URI: {resource.uri}")
                    print(f"    Name: {resource.name}")
                    print(f"    Description: {resource.description[:80]}...")

                # Try to read the usage guidelines resource
                print("\n=== Reading memory://usage-guidelines ===")
                content_result = await session.read_resource(
                    "memory://usage-guidelines"
                )

                if content_result.contents:
                    text = content_result.contents[0].text
                    print(f"✅ Resource read successfully!")
                    print(f"✅ Content length: {len(text)} characters")
                    print(f"\n✅ First 300 chars:")
                    print(f"{text[:300]}...")

                    # Check for expected sections
                    print("\n=== Checking Content ===")
                    expected_sections = [
                        "When to Save Memories",
                        "How to Structure Memories",
                        "How to Query Memories",
                        "Best Practices",
                        "category",
                        "topic",
                        "content",
                    ]

                    all_found = True
                    for section in expected_sections:
                        if section in text:
                            print(f"✅ Contains: '{section}'")
                        else:
                            print(f"❌ Missing: '{section}'")
                            all_found = False

                    if all_found:
                        print("\n✅ All tests passed! Resource is working correctly.")
                    else:
                        print("\n⚠️  Some sections missing but resource is readable.")
                else:
                    print("❌ No content returned")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("FastMCP Resource Test\n" + "=" * 50 + "\n")
    asyncio.run(test_resource())
