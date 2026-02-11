#!/usr/bin/env python
"""Debug script to test the AI service"""

import asyncio
import sys
sys.path.insert(0, '.')

try:
    print("1. Loading config...")
    from app.config import settings
    print(f"   Model: {settings.ollama_model}")
    print(f"   Base URL: {settings.ollama_base_url}")
    print(f"   Use Ollama: {settings.use_ollama}")

    print("\n2. Loading AI Service...")
    from app.services.ai_service import AIService
    ai_service = AIService()
    print("   AI Service loaded OK")

    print("\n3. Loading Tax Calculator...")
    from app.services.tax_calculator import tax_calculator_service
    print("   Tax Calculator loaded OK")

    print("\n4. Loading RAG Service...")
    from app.services.rag_service import RAGService
    rag_service = RAGService()
    print(f"   RAG Available: {rag_service.is_available()}")

    print("\n5. Testing simple LLM call...")
    async def test_llm():
        response = await ai_service.llm.ainvoke("Say hello in Thai")
        print(f"   Response: {response.content[:100]}...")

    asyncio.run(test_llm())
    print("\n✅ All tests passed!")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
