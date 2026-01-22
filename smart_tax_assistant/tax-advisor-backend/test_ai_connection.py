"""
Test script to verify OpenAI API connection
"""
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_connection():
    print("=" * 60)
    print("Testing OpenAI API Connection")
    print("=" * 60)

    # Check if API key is loaded
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment!")
        return False

    # Mask the key for display
    masked_key = api_key[:10] + "..." + api_key[-4:]
    print(f"✅ API Key found: {masked_key}")

    # Try to import and initialize OpenAI
    try:
        from openai import AsyncOpenAI
        print("✅ OpenAI package imported successfully")

        client = AsyncOpenAI(api_key=api_key)
        print("✅ OpenAI client created")

        # Try a simple API call
        print("\n🔄 Testing API call (simple completion)...")

        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # Use cheaper model for test
            messages=[
                {"role": "user", "content": "Say 'Hello, AI Tax Advisor is working!' in Thai"}
            ],
            max_tokens=50
        )

        result = response.choices[0].message.content
        print(f"✅ API Response: {result}")

        print("\n" + "=" * 60)
        print("🎉 All tests passed! OpenAI connection is working!")
        print("=" * 60)
        return True

    except ImportError as e:
        print(f"❌ Failed to import OpenAI: {e}")
        print("   Run: pip install openai")
        return False

    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())
