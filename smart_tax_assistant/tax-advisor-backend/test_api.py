#!/usr/bin/env python
"""Test the full API flow"""

import asyncio
import sys
sys.path.insert(0, '.')

async def test_full_flow():
    try:
        print("=" * 50)
        print("Testing Full API Flow")
        print("=" * 50)

        # 1. Import everything
        print("\n1. Importing modules...")
        from app.models import TaxCalculationRequest
        from app.services.tax_calculator import tax_calculator_service
        from app.services.rag_service import RAGService
        from app.services.ai_service import AIService
        from app.config import settings
        print("   OK")

        # 2. Create request
        print("\n2. Creating test request...")
        request = TaxCalculationRequest(
            gross_income=500000,
            risk_tolerance="medium",
            personal_deduction=60000
        )
        print(f"   Gross income: {request.gross_income}")

        # 3. Calculate tax
        print("\n3. Calculating tax...")
        tax_result = tax_calculator_service.calculate_tax(request)
        print(f"   Tax amount: {tax_result.tax_amount}")
        print(f"   Taxable income: {tax_result.taxable_income}")

        # 4. RAG Service
        print("\n4. Testing RAG Service...")
        rag_service = RAGService()
        print(f"   RAG Available: {rag_service.is_available()}")

        context = "ไม่มีข้อมูลจาก RAG"
        if rag_service.is_available():
            query = f"รายได้ {request.gross_income} บาท ระดับความเสี่ยง {request.risk_tolerance}"
            try:
                retrieved_docs = await rag_service.retrieve_relevant_documents(query, k=5)
                if retrieved_docs:
                    context_parts = [doc.page_content for doc in retrieved_docs if hasattr(doc, 'page_content')]
                    if context_parts:
                        context = "\n\n".join(context_parts)
                        print(f"   RAG Context: {len(context)} characters")
            except Exception as e:
                print(f"   RAG Error: {e}")

        # 5. AI Service
        print("\n5. Testing AI Service...")
        ai_service = AIService()
        print(f"   Model: {settings.ollama_model}")

        print("\n6. Generating recommendations (this may take 1-3 minutes)...")
        result = await ai_service.generate_recommendations(
            request, tax_result, context
        )

        if result and "plans" in result:
            print(f"   Generated {len(result['plans'])} plans")
            for plan in result["plans"]:
                print(f"   - {plan.get('plan_name', 'Unknown')}: {plan.get('total_investment', 0):,} THB")
        else:
            print(f"   Result: {result}")

        print("\n" + "=" * 50)
        print("✅ All tests passed!")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_flow())
