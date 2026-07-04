import asyncio
import os
import sys

# Add backend root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings
from app.models.user import User
from app.models.organization import Organization
from app.models.workspace import Workspace
from app.models.document import DocumentModel
from app.services.pipeline import DocumentPipeline
from app.services.vector_store import VectorStoreService
from app.db.database import database

async def init_db_test():
    await init_beanie(
        database=database,
        document_models=[
            User,
            Organization,
            Workspace,
            DocumentModel
        ]
    )
    print("Beanie DB Initialized!")

async def test_pipeline():
    await init_db_test()
    
    # 1. Ensure we have a workspace
    ws = await Workspace.find_one()
    if not ws:
        print("No workspace found, creating a mock workspace...")
        ws = Workspace(
            organization_id="mock_org",
            name="Test Operations Room",
            description="Mock workspace for pipeline testing",
            workspace_type="Maintenance",
            created_by="mock_user"
        )
        await ws.insert()
    print(f"Using workspace: {ws.name} ({ws.id})")

    # 2. Create a mock document file
    mock_filename = "test_safety_sop.txt"
    workspace_upload_dir = os.path.join("uploads", str(ws.id))
    os.makedirs(workspace_upload_dir, exist_ok=True)
    
    mock_filepath = os.path.join(workspace_upload_dir, mock_filename)
    mock_content = """
    CEREBRO SAFETY REGULATION AND PPE STANDARD OPERATING PROCEDURES
    Version: 2.4
    Department: Safety
    Approved by: Chief Engineer John Doe
    Date: 2026-05-15
    
    Rule 1: All personnel on the manufacturing floor must wear a class-B hard hat and steel-toed boots at all times.
    Rule 2: When working near Compressor C-302 or Pump P-101, double ear protection (earplugs and earmuffs) is mandatory.
    Rule 3: In the event of a hazardous material leak, trigger the evacuation siren immediately and report to Assembly Point 4.
    Rule 4: Do not operate any CNC machines without active certification and a supervisor signature.
    """
    
    with open(mock_filepath, "w", encoding="utf-8") as f:
        f.write(mock_content)
    
    print(f"Created mock document file at: {mock_filepath}")

    # 3. Create DocumentModel in DB
    relative_path = os.path.join("uploads", str(ws.id), mock_filename).replace("\\", "/")
    doc = DocumentModel(
        name=mock_filename,
        workspace_id=str(ws.id),
        uploaded_by="mock_user",
        storage_path=relative_path,
        file_size=len(mock_content),
        status="uploaded",
        version="1.0",
        mime_type="text/plain"
    )
    await doc.insert()
    print(f"Created Beanie DocumentModel entry: {doc.name} (ID: {doc.id})")

    # 4. Trigger Ingestion Pipeline
    print("Triggering document processing pipeline...")
    await DocumentPipeline.process_document(str(doc.id))
    
    # Reload doc and print status
    doc = await DocumentModel.get(str(doc.id))
    print("\n--- Pipeline Ingestion Results ---")
    print(f"Document Status: {doc.status}")
    print(f"Chunks Count: {doc.chunk_count}")
    print(f"Embeddings Count: {doc.embedding_count}")
    print(f"Classified Department: {doc.department}")
    print(f"Extracted Metadata: {doc.extracted_metadata}")
    print(f"Knowledge Score: {doc.knowledge_score}")
    print(f"Error Message: {doc.error_message}")
    
    if doc.status == "ready":
        print("\n--- Testing Semantic Search ---")
        # Generate search and print hits
        from app.services.embedding_service import EmbeddingService
        
        search_query = "What ppe is required for Pump P-101 and Compressor C-302?"
        print(f"Search Query: '{search_query}'")
        
        query_vector = (await EmbeddingService.get_embeddings([search_query]))[0]
        results = await VectorStoreService.search_workspace(
            collection_name=settings.QDRANT_COLLECTION_NAME or "documents_general",
            workspace_id=str(ws.id),
            query_vector=query_vector,
            limit=2
        )
        
        for idx, hit in enumerate(results):
            print(f"\nHit {idx+1} [Score: {hit['score']:.4f} | Source: {hit['title']} (Page {hit['page_number']})]:")
            print(hit['text'])
    else:
        print("\nPipeline failed. Skipping semantic search test.")

    # Cleanup mock doc
    if os.path.exists(mock_filepath):
        os.remove(mock_filepath)
    await doc.delete()
    print("\nTemporary test documents cleaned up.")

if __name__ == "__main__":
    asyncio.run(test_pipeline())
