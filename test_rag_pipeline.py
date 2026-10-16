from pathlib import Path
from app.services.pdf_processor import pdf_processor
from app.services.vector_store import vector_store

def test_pipeline():
    sample_pdf = Path("sample_docs/sample_company_policy.pdf")
    assert sample_pdf.exists(), "Sample PDF not found!"

    print("1. Testing PDF text extraction and chunking...")
    chunks = pdf_processor.process_pdf(
        file_path=str(sample_pdf),
        document_id=1,
        document_title="sample_company_policy.pdf"
    )
    print(f"   Extracted {len(chunks)} chunks.")
    assert len(chunks) > 0, "No chunks generated!"
    
    # Verify page numbers in chunk metadata
    for c in chunks:
        print(f"   Chunk ID: {c['id']}, Page: {c['metadata']['page_number']}, Excerpt: {c['text'][:60]}...")

    print("\n2. Testing ChromaDB vector indexing...")
    vector_store.add_chunks(chunks)
    print("   Chunks indexed in ChromaDB successfully.")

    print("\n3. Testing Vector Retrieval with Query: 'How much is the home office stipend and monthly internet subsidy?'...")
    results = vector_store.query_similar(
        query_text="How much is the home office stipend and monthly internet subsidy?",
        n_results=2,
        document_ids=[1]
    )

    print(f"   Retrieved {len(results)} chunks:")
    for r in results:
        print(f"   - [Score: {r['similarity']:.4f}] Page {r['metadata']['page_number']}: {r['text'][:120]}...")

    assert len(results) > 0, "Retrieval returned 0 chunks!"
    top_text = results[0]["text"]
    assert "1,000" in top_text or "stipend" in top_text.lower(), "Top chunk did not contain stipend details!"
    print("\n[SUCCESS] RAG Pipeline (PDF Processing -> ChromaDB Indexing -> Vector Retrieval) verified successfully!")

if __name__ == "__main__":
    test_pipeline()
