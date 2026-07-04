import os
import shutil
from datetime import datetime, UTC
from fastapi import UploadFile, HTTPException, status
from app.models.document import DocumentModel
from app.models.workspace import Workspace

# Base directory for uploads: backend/uploads
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".xlsx", ".txt"}

class DocumentService:

    @staticmethod
    async def upload_document(file: UploadFile, workspace_id: str, uploaded_by: str) -> DocumentModel:
        # Validate workspace exists
        workspace = await Workspace.get(workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )

        # Validate file extension
        _, ext = os.path.splitext(file.filename or "")
        ext = ext.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Supported types: {', '.join(SUPPORTED_EXTENSIONS)}"
            )

        # Ensure folder exists
        workspace_upload_dir = os.path.join(UPLOAD_DIR, workspace_id)
        os.makedirs(workspace_upload_dir, exist_ok=True)

        # Generate a unique local file path to avoid conflicts
        timestamp = int(datetime.now(UTC).timestamp())
        filename = f"{timestamp}_{file.filename}"
        local_path = os.path.join(workspace_upload_dir, filename)

        # Save file locally
        try:
            with open(local_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to write file to local disk: {str(e)}"
            )

        # Get file size
        file_size = os.path.getsize(local_path)

        # Create Beanie document entry
        # Store storage_path as a relative path to keep it system-agnostic
        relative_path = os.path.join("uploads", workspace_id, filename).replace("\\", "/")

        document = DocumentModel(
            name=file.filename or "unknown",
            workspace_id=workspace_id,
            uploaded_by=uploaded_by,
            storage_path=relative_path,
            file_size=file_size,
            status="uploaded",
            version="1.0",
            mime_type=file.content_type or "application/octet-stream"
        )

        await document.insert()
        return document

    @staticmethod
    async def list_documents(workspace_id: str) -> list[DocumentModel]:
        # Validate workspace exists
        workspace = await Workspace.get(workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )
        return await DocumentModel.find(DocumentModel.workspace_id == workspace_id).to_list()

    @staticmethod
    async def get_document_by_id(document_id: str) -> DocumentModel:
        document = await DocumentModel.get(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        return document

    @staticmethod
    async def delete_document(document_id: str) -> bool:
        document = await DocumentService.get_document_by_id(document_id)

        # Resolve local absolute path
        abs_path = os.path.join(BASE_DIR, document.storage_path)

        # Delete file from local disk if it exists
        if os.path.exists(abs_path):
            try:
                os.remove(abs_path)
            except Exception as e:
                print(f"Warning: Failed to delete local file {abs_path}: {e}")

        # Delete from Qdrant
        from app.services.vector_store import VectorStoreService
        from app.core.config import settings
        try:
            await VectorStoreService.delete_document_vectors(
                settings.QDRANT_COLLECTION_NAME or "documents_general", 
                document_id
            )
        except Exception as e:
            print(f"Warning: Failed to delete document vectors: {e}")

        # Delete Beanie database record
        await document.delete()
        return True

    @staticmethod
    def get_absolute_file_path(storage_path: str) -> str:
        # Resolve path
        return os.path.abspath(os.path.join(BASE_DIR, storage_path))
