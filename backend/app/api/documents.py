from fastapi import APIRouter, Depends, UploadFile, File, Form, status, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.document import DocumentModel
from app.schemas.document import DocumentResponse
from app.services.document_service import DocumentService
from app.services.pipeline import DocumentPipeline

router = APIRouter()

def map_document_to_response(doc: DocumentModel) -> DocumentResponse:
    return DocumentResponse(
        id=str(doc.id),
        name=doc.name,
        workspace_id=doc.workspace_id,
        uploaded_by=doc.uploaded_by,
        storage_path=doc.storage_path,
        file_size=doc.file_size,
        status=doc.status,
        version=doc.version,
        mime_type=doc.mime_type,
        chunk_count=doc.chunk_count,
        embedding_count=doc.embedding_count,
        extracted_metadata=doc.extracted_metadata,
        knowledge_score=doc.knowledge_score,
        learning_progress=doc.learning_progress,
        error_message=doc.error_message,
        department=doc.department,
        created_at=doc.created_at,
        updated_at=doc.updated_at
    )

@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    workspace_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    document = await DocumentService.upload_document(
        file=file,
        workspace_id=workspace_id,
        uploaded_by=str(current_user.id)
    )
    
    # Queue processing pipeline in background
    background_tasks.add_task(DocumentPipeline.process_document, str(document.id))

    return map_document_to_response(document)

@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    workspace_id: str,
    current_user: User = Depends(get_current_user)
):
    documents = await DocumentService.list_documents(workspace_id)
    return [map_document_to_response(doc) for doc in documents]

@router.get("/{id}/download")
async def download_document(
    id: str,
    current_user: User = Depends(get_current_user)
):
    document = await DocumentService.get_document_by_id(id)
    absolute_path = DocumentService.get_absolute_file_path(document.storage_path)
    return FileResponse(
        path=absolute_path,
        filename=document.name,
        media_type=document.mime_type or "application/octet-stream"
    )

@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_document(
    id: str,
    current_user: User = Depends(get_current_user)
):
    await DocumentService.delete_document(id)
    return {"message": "Document deleted successfully"}

# ----------------- Phase 2 Endpoints -----------------

@router.get("/{id}/status")
async def get_document_status(
    id: str,
    current_user: User = Depends(get_current_user)
):
    doc = await DocumentService.get_document_by_id(id)
    return {
        "id": str(doc.id),
        "name": doc.name,
        "status": doc.status,
        "learning_progress": doc.learning_progress,
        "chunk_count": doc.chunk_count,
        "embedding_count": doc.embedding_count,
        "error_message": doc.error_message
    }

@router.post("/{id}/reprocess", response_model=DocumentResponse)
async def reprocess_document(
    id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    doc = await DocumentService.get_document_by_id(id)
    
    # Reset processing fields
    doc.status = "uploaded"
    doc.learning_progress = 0.0
    doc.chunk_count = 0
    doc.embedding_count = 0
    doc.error_message = None
    await doc.save()

    # Launch background task
    background_tasks.add_task(DocumentPipeline.process_document, str(doc.id))

    return map_document_to_response(doc)

@router.get("/{id}/metadata")
async def get_document_metadata(
    id: str,
    current_user: User = Depends(get_current_user)
):
    doc = await DocumentService.get_document_by_id(id)
    return doc.extracted_metadata

@router.get("/workspace/{workspace_id}/knowledge-summary")
async def get_workspace_knowledge_summary(
    workspace_id: str,
    current_user: User = Depends(get_current_user)
):
    # Validate workspace
    from app.models.workspace import Workspace
    ws = await Workspace.get(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    docs = await DocumentModel.find(DocumentModel.workspace_id == workspace_id).to_list()
    
    doc_count = len(docs)
    chunk_count = sum(doc.chunk_count for doc in docs)
    embedding_count = sum(doc.embedding_count for doc in docs)
    
    # Calculate average knowledge score
    ready_docs = [d for d in docs if d.status == "ready"]
    avg_score = sum(d.knowledge_score for d in ready_docs) / len(ready_docs) if ready_docs else 0.0
    
    # Calculate progress
    avg_progress = sum(d.learning_progress for d in docs) / doc_count if doc_count else 0.0

    # Required departments check
    existing_depts = {d.department.lower() for d in ready_docs if d.department}
    required_depts = {"safety", "maintenance", "operations"}
    missing_depts = list(required_depts - existing_depts)
    
    missing_docs = []
    for dept in missing_depts:
        if dept == "safety":
            missing_docs.append("PPE & Work Safety HSE Manual")
        elif dept == "maintenance":
            missing_docs.append("Critical Pump/Compressor Maintenance Guide")
        elif dept == "operations":
            missing_docs.append("Standard Operating Procedures (SOP) Checklist")
            
    return {
        "workspace_id": workspace_id,
        "document_count": doc_count,
        "chunk_count": chunk_count,
        "embedding_count": embedding_count,
        "knowledge_score": round(avg_score, 2),
        "processing_progress": round(avg_progress, 2),
        "missing_documents": missing_docs
    }

@router.get("/workspace/{workspace_id}/knowledge-health")
async def get_workspace_knowledge_health(
    workspace_id: str,
    current_user: User = Depends(get_current_user)
):
    # Validate workspace
    from app.models.workspace import Workspace
    ws = await Workspace.get(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    docs = await DocumentModel.find(DocumentModel.workspace_id == workspace_id).to_list()
    ready_docs = [d for d in docs if d.status == "ready"]
    failed_docs = [d for d in docs if d.status == "failed"]

    # Compute department coverage
    coverage = {"Operations": 0, "Maintenance": 0, "Safety": 0, "General": 0}
    for d in ready_docs:
        dept = d.department or "General"
        if dept in coverage:
            coverage[dept] += 1
        else:
            coverage[dept] = 1

    # Base score
    health_score = 50
    distinct_covered = sum(1 for v in coverage.values() if v > 0)
    health_score += distinct_covered * 15
    if failed_docs:
        health_score -= 20
    health_score += min(15, len(ready_docs) * 5)
    health_score = max(5, min(100, health_score))

    if health_score >= 80:
        readiness = "Production Ready"
    elif health_score >= 50:
        readiness = "Operational Standby"
    else:
        readiness = "Needs Data"

    missing_critical = []
    if coverage["Safety"] == 0:
        missing_critical.append("Occupational HSE Plan / Safe Work Procedures")
    if coverage["Maintenance"] == 0:
        missing_critical.append("Equipment Maintenance Manuals / Preventative Tasks")
    if coverage["Operations"] == 0:
        missing_critical.append("Plant Start-up / Shut-down standard SOPs")

    # Document relationships mock mapper
    relationships = []
    if len(ready_docs) >= 2:
        for i in range(len(ready_docs) - 1):
            relationships.append({
                "source_doc_id": str(ready_docs[i].id),
                "source_title": ready_docs[i].name,
                "target_doc_id": str(ready_docs[i+1].id),
                "target_title": ready_docs[i+1].name,
                "relationship_type": "Refers To / Context Link",
                "strength": round(0.85 - (i * 0.1), 2)
            })

    return {
        "health_score": health_score,
        "readiness_indicator": readiness,
        "department_coverage": coverage,
        "missing_critical_documents": missing_critical,
        "document_relationships": relationships
    }

class SearchRequest(BaseModel):
    query: str
    limit: int = 5

@router.post("/workspace/{workspace_id}/search")
async def search_workspace_knowledge(
    workspace_id: str,
    req: SearchRequest,
    current_user: User = Depends(get_current_user)
):
    from app.services.embedding_service import EmbeddingService
    from app.services.vector_store import VectorStoreService
    from app.core.config import settings

    try:
        # Generate search embedding
        query_embeddings = await EmbeddingService.get_embeddings([req.query])
        if not query_embeddings:
            raise HTTPException(status_code=500, detail="Failed to generate search embedding")
        query_vector = query_embeddings[0]

        # Search Qdrant
        collection = settings.QDRANT_COLLECTION_NAME or "documents_general"
        results = await VectorStoreService.search_workspace(
            collection_name=collection,
            workspace_id=workspace_id,
            query_vector=query_vector,
            limit=req.limit
        )
        return {"query": req.query, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
