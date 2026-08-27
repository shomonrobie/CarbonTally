# backend/routes/organizations/files.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse, FileResponse
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator 
from datetime import datetime, timedelta
import io
import mimetypes
from auth import AuthUser, require_org_member, require_permission, require_org_admin
from supabase import Client
from database import get_supabase_client
from utils import classify_document
router = APIRouter(prefix="/api/organizations/files", tags=["Organization Files"])

# ==========================================
# PYDANTIC MODELS
# ==========================================

class FileResponse(BaseModel):
    """Response model for a file."""
    id: str
    name: str
    path: str
    size_bytes: int
    size_mb: float
    file_type: str  # PDF, CSV, XLSX, IMAGE, etc.
    mime_type: str
    bucket: str
    uploaded_by: Optional[str] = None
    uploaded_by_name: Optional[str] = None
    uploaded_at: datetime
    last_accessed: Optional[datetime] = None
    metadata: Dict[str, Any] = {}
    download_url: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "utility_bill_jan2024.pdf",
                "path": "organizations/2b7a2e09/2024/01/utility_bill.pdf",
                "size_bytes": 245760,
                "size_mb": 0.234,
                "file_type": "PDF",
                "mime_type": "application/pdf",
                "bucket": "documents",
                "uploaded_by": "123e4567-e89b-12d3-a456-426614174000",
                "uploaded_by_name": "John Doe",
                "uploaded_at": "2024-01-15T10:30:00Z",
                "last_accessed": "2024-01-16T14:20:00Z",
                "metadata": {"data_type": "utility", "batch_id": "batch_123"},
                "download_url": "https://storage.supabase.co/..."
            }
        }

class FileListResponse(BaseModel):
    """Response model for file list."""
    files: List[FileResponse]
    total: int
    total_size_mb: float
    total_files: int

class FileUploadResponse(BaseModel):
    """Response model for file upload."""
    success: bool
    file_id: str
    file_name: str
    file_path: str
    size_bytes: int
    size_mb: float
    message: str
    download_url: Optional[str] = None

class FileStatsResponse(BaseModel):
    """Response model for file statistics."""
    organization_id: str
    total_files: int
    total_size_mb: float
    files_by_type: Dict[str, int]
    files_by_month: Dict[str, int]
    storage_used_mb: float
    storage_limit_mb: float = 5000  # 5GB default
    storage_used_percent: float
    oldest_file: Optional[datetime] = None
    newest_file: Optional[datetime] = None

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_file_type(filename: str, mime_type: str) -> str:
    """Determine file type from filename and mime type."""
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    
    if ext in ['pdf'] or 'pdf' in mime_type:
        return 'PDF'
    elif ext in ['csv'] or 'csv' in mime_type:
        return 'CSV'
    elif ext in ['xlsx', 'xls'] or 'spreadsheet' in mime_type:
        return 'EXCEL'
    elif ext in ['jpg', 'jpeg', 'png', 'gif', 'webp'] or 'image' in mime_type:
        return 'IMAGE'
    elif ext in ['doc', 'docx'] or 'word' in mime_type:
        return 'DOCUMENT'
    else:
        return 'OTHER'

async def get_organization_upload_path(supabase_client, org_id: str, filename: str) -> str:
    """Generate an upload path for a file."""
    now = datetime.now()
    year_month = now.strftime('%Y/%m')
    timestamp = now.strftime('%Y%m%d_%H%M%S')
    
    # Clean filename
    clean_name = filename.replace(' ', '_').lower()
    name_parts = clean_name.rsplit('.', 1)
    if len(name_parts) == 2:
        clean_name = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
    else:
        clean_name = f"{clean_name}_{timestamp}"
    
    return f"organizations/{org_id}/{year_month}/{clean_name}"

async def get_user_name(supabase_client, user_id: str) -> Optional[str]:
    """Get user's full name from auth."""
    try:
        result = supabase_client.from_('auth.users') \
            .select('raw_user_meta_data->>full_name as full_name') \
            .eq('id', user_id) \
            .maybe_single() \
            .execute()
        
        if result.data:
            return result.data.get('full_name')
        return None
    except:
        return None

async def get_file_download_url(supabase_client, bucket: str, path: str) -> str:
    """Generate a signed download URL for a file."""
    try:
        # Get signed URL (expires in 1 hour)
        result = supabase_client.storage.from_(bucket).create_signed_url(
            path,
            expires_in=3600  # 1 hour
        )
        
        if result and hasattr(result, 'signed_url'):
            return result.signed_url
        return None
    except Exception as e:
        print(f"⚠️ Error generating signed URL: {e}")
        return None

# ==========================================
# ENDPOINTS
# ==========================================

@router.get("/", response_model=FileListResponse)
async def get_organization_files(
    file_type: Optional[str] = Query(None, description="Filter by file type (PDF, CSV, EXCEL, IMAGE, DOCUMENT, OTHER)"),
    search: Optional[str] = Query(None, description="Search by filename"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Get all files for the organization.
    """
    try:
        supabase = get_supabase_client()
        
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not associated with an organization"
            )
        
        # ✅ Helper function to apply filters
        def apply_filters(query):
            query = query.eq('organization_id', org_id).eq('is_active', True)
            if file_type:
                query = query.eq('file_type', file_type.upper())
            if search:
                query = query.ilike('name', f'%{search}%')
            if start_date:
                query = query.gte('uploaded_at', start_date)
            if end_date:
                query = query.lte('uploaded_at', end_date)
            return query
        
        # ✅ Build main query
        query = supabase.from_('organization_files') \
            .select('''
                id,
                name,
                path,
                size_bytes,
                file_type,
                mime_type,
                bucket,
                uploaded_by,
                uploaded_at,
                last_accessed,
                metadata
            ''')
        query = apply_filters(query)
        
        # ✅ Get total count (separate query - no .clone())
        count_query = supabase.from_('organization_files') \
            .select('id', count='exact')
        count_query = apply_filters(count_query)
        
        count_result = count_query.execute()
        total = count_result.count or 0
        
        # ✅ Get total size (separate query - no .clone())
        size_query = supabase.from_('organization_files') \
            .select('size_bytes')
        size_query = apply_filters(size_query)
        
        size_result = size_query.execute()
        total_size_bytes = sum(f.get('size_bytes', 0) for f in (size_result.data or []))
        
        # ✅ Get paginated results
        result = query.order('uploaded_at', desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        # Transform data and get user names
        files = []
        for file in (result.data or []):
            # Get uploader name
            uploaded_by_name = None
            if file.get('uploaded_by'):
                uploaded_by_name = await get_user_name(supabase, file['uploaded_by'])
            
            # Generate download URL
            download_url = await get_file_download_url(
                supabase, 
                file.get('bucket', 'documents'),
                file.get('path', '')
            )
            
            files.append(FileResponse(
                id=file.get('id'),
                name=file.get('name', ''),
                path=file.get('path', ''),
                size_bytes=file.get('size_bytes', 0),
                size_mb=file.get('size_bytes', 0) / (1024 * 1024),
                file_type=file.get('file_type'),
                mime_type=file.get('mime_type'),
                bucket=file.get('bucket', 'documents'),
                uploaded_by=file.get('uploaded_by'),
                uploaded_by_name=uploaded_by_name,
                uploaded_at=file.get('uploaded_at'),
                last_accessed=file.get('last_accessed'),
                metadata=file.get('metadata', {}),
                download_url=download_url
            ))
        
        return FileListResponse(
            files=files,
            total=total,
            total_size_mb=total_size_bytes / (1024 * 1024),
            total_files=len(files)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting files: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get files: {str(e)}"
        )
    
@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Download a file from the organization's storage.
    """
    try:
        supabase = get_supabase_client()
        
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not associated with an organization"
            )
        
        # Get file metadata
        file_result = supabase.from_('organization_files') \
            .select('name, path, bucket, mime_type, size_bytes') \
            .eq('id', file_id) \
            .eq('organization_id', org_id) \
            .eq('is_active', True) \
            .maybe_single() \
            .execute()
        
        if not file_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        file_data = file_result.data
        
        # Update last accessed timestamp
        supabase.from_('organization_files') \
            .update({
                'last_accessed': datetime.now().isoformat(),
                'access_count': supabase.raw('access_count + 1')
            }) \
            .eq('id', file_id) \
            .execute()
        
        # Get file from storage
        bucket = file_data.get('bucket', 'documents')
        path = file_data['path']
        
        try:
            # Download file from Supabase Storage
            file_bytes = supabase.storage.from_(bucket).download(path)
            
            # Determine content disposition
            filename = file_data['name']
            disposition = f'attachment; filename="{filename}"'
            
            # Return file as streaming response
            return StreamingResponse(
                io.BytesIO(file_bytes),
                media_type=file_data.get('mime_type', 'application/octet-stream'),
                headers={
                    'Content-Disposition': disposition,
                    'Content-Length': str(len(file_bytes))
                }
            )
            
        except Exception as storage_error:
            print(f"❌ Storage download error: {storage_error}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found in storage"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error downloading file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}"
        )

@router.get("/{file_id}/url")
async def get_file_download_url_endpoint(
    file_id: str,
    expires_in: int = Query(3600, ge=60, le=86400, description="URL expiration in seconds"),
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Get a signed download URL for a file.
    """
    try:
        supabase = get_supabase_client()
        
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not associated with an organization"
            )
        
        # Get file metadata
        file_result = supabase.from_('organization_files') \
            .select('path, bucket') \
            .eq('id', file_id) \
            .eq('organization_id', org_id) \
            .eq('is_active', True) \
            .maybe_single() \
            .execute()
        
        if not file_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Generate signed URL
        download_url = await get_file_download_url(
            supabase,
            file_result.data.get('bucket', 'documents'),
            file_result.data['path']
        )
        
        if not download_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate download URL"
            )
        
        return {
            "success": True,
            "file_id": file_id,
            "download_url": download_url,
            "expires_in": expires_in,
            "expires_at": (datetime.now() + timedelta(seconds=expires_in)).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error generating download URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate download URL: {str(e)}"
        )

@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    permanent: bool = Query(False, description="Permanently delete from storage or soft delete"),
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Delete a file from the organization's storage.
    """
    try:
        supabase = get_supabase_client()
        
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not associated with an organization"
            )
        
        # Get file metadata
        file_result = supabase.from_('organization_files') \
            .select('name, path, bucket') \
            .eq('id', file_id) \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        if not file_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        filename = file_result.data['name']
        
        if permanent:
            try:
                # Delete from storage
                supabase.storage.from_(file_result.data['bucket']).remove([file_result.data['path']])
            except Exception as storage_error:
                print(f"⚠️ Storage deletion error: {storage_error}")
                # Continue - we can still delete the record
            
            # Delete from database
            supabase.from_('organization_files') \
                .delete() \
                .eq('id', file_id) \
                .execute()
            
            message = f"File '{filename}' permanently deleted"
        else:
            # Soft delete
            supabase.from_('organization_files') \
                .update({
                    'is_active': False,
                    'deleted_at': datetime.now().isoformat()
                }) \
                .eq('id', file_id) \
                .execute()
            
            message = f"File '{filename}' moved to trash"
        
        return {
            "success": True,
            "message": message,
            "file_id": file_id,
            "file_name": filename,
            "permanent": permanent
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )

@router.post("/api/organizations/{org_id}/files/upload")
async def upload_file(
    org_id: str,
    file: UploadFile = File(...),
    asset_id: Optional[str] = Form(None),
    document_type_code: Optional[str] = Form(None),
    billing_period_start: Optional[str] = Form(None),
    billing_period_end: Optional[str] = Form(None),
    facility_id: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Upload a file with document type classification.
    """
    try:
        supabase = get_supabase_client()
        
        # Verify user belongs to organization
        if str(org_id) != str(current_user.organization_id):
            raise HTTPException(
                status_code=403,
                detail="You do not have access to this organization"
            )
        
        # ✅ Verify asset belongs to organization if provided
        if asset_id:
            asset_check = supabase.from_('assets') \
                .select('id, name, type, facility_id') \
                .eq('id', asset_id) \
                .eq('facility.organization_id', org_id) \
                .maybe_single() \
                .execute()
            
            if not asset_check.data:
                raise HTTPException(
                    status_code=400,
                    detail="Asset not found or does not belong to your organization"
                )
            
            # Use facility from asset if not provided
            if not facility_id and asset_check.data.get('facility_id'):
                facility_id = asset_check.data['facility_id']
        
        # Validate file size
        content = await file.read()
        file_size = len(content)
        
        if file_size > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="File size exceeds 50MB limit"
            )
        
        # Determine file type
        mime_type = file.content_type or 'application/octet-stream'
        file_type = get_file_type(file.filename, mime_type)
        
        # Generate upload path
        path = await get_organization_upload_path(supabase, org_id, file.filename)
        bucket = 'documents'
        
        # Upload to storage
        try:
            await file.seek(0)
            upload_result = supabase.storage.from_(bucket).upload(
                path,
                content,
                file_options={
                    "content-type": mime_type,
                    "cache-control": "3600"
                }
            )
            public_url = supabase.storage.from_(bucket).get_public_url(path)
        except Exception as storage_error:
            print(f"❌ Storage upload error: {storage_error}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload file: {str(storage_error)}"
            )
        
        now = datetime.now().isoformat()
        
        # ✅ Auto-classify document
        
        classification = await classify_document(
            file.filename,
            content,
            document_type_code
        )
        
        # Create organization_files record
        file_record = {
            'organization_id': org_id,
            'name': file.filename,
            'path': path,
            'size_bytes': file_size,
            'file_type': file_type,
            'mime_type': mime_type,
            'bucket': bucket,
            'uploaded_by': current_user.user_id,
            'uploaded_at': now,
            'metadata': {
                'uploaded_by_email': current_user.email,
                'upload_timestamp': now,
                'file_size_mb': file_size / (1024 * 1024),
                'document_type_code': classification['document_type_code'],
                'asset_id': asset_id
            },
            'is_active': True,
            'access_count': 0,
            'status': 'uploaded',
            'status_updated_at': now
        }
        
        file_result = supabase.from_('organization_files') \
            .insert(file_record) \
            .execute()
        
        if not file_result.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to create file record"
            )
        
        file_record = file_result.data[0]
        
        # ✅ Create customer_document record with type
        customer_doc_data = {
            'organization_id': org_id,
            'organization_member_id': current_user.user_id,
            'asset_id': asset_id,
            'file_name': file.filename,
            'file_url': path,
            'file_type': document_type_code or classification['document_type_code'],
            'document_type_code': classification['document_type_code'],
            'document_type_id': classification['document_type_id'],
            'upload_date': now,
            'status': 'pending',
            'organization_classification': 'staff_assigned' if current_user.is_staff else 'customer_provided',
            'classification_by': current_user.user_id,
            'classification_at': now,
            'confidence_score': classification['confidence'],
            'organization_notes': notes,
            'billing_period_start': billing_period_start,
            'billing_period_end': billing_period_end,
            'metadata': {
                'original_file_id': file_record['id'],
                'classification': classification,
                'user_agent': request.headers.get('user-agent') if hasattr(request, 'headers') else None,
                'ip_address': request.client.host if hasattr(request, 'client') else None
            },
            'created_at': now,
            'updated_at': now
        }
        
        customer_doc_result = supabase.from_('customer_documents') \
            .insert(customer_doc_data) \
            .execute()
        
        # ✅ Create extraction task if document type requires it
        extraction_task = None
        if classification['document_type_code'] != 'other' and classification['confidence'] >= 0.5:
            extraction_task = await create_extraction_task(
                supabase, 
                customer_doc_result.data[0]['id'] if customer_doc_result.data else None,
                current_user
            )
        
        return {
            "success": True,
            "file": file_record,
            "customer_document": customer_doc_result.data[0] if customer_doc_result.data else None,
            "classification": classification,
            "document_type": classification['suggested_type'],
            "extraction_task": extraction_task,
            "download_url": public_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error uploading file: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {str(e)}"
        )

@router.get("/organizations/{org_id}/files/stats", response_model=FileStatsResponse)
async def get_file_stats(
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Get file storage statistics for the organization.
    """
    try:
        supabase = get_supabase_client()
        
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not associated with an organization"
            )
        
        # Get all files
        result = supabase.from_('organization_files') \
            .select('size_bytes, file_type, uploaded_at') \
            .eq('organization_id', org_id) \
            .eq('is_active', True) \
            .execute()
        
        files = result.data or []
        total_files = len(files)
        total_size_bytes = sum(f.get('size_bytes', 0) for f in files)
        total_size_mb = total_size_bytes / (1024 * 1024)
        
        # Files by type
        files_by_type = {}
        for file in files:
            file_type = file.get('file_type', 'OTHER')
            files_by_type[file_type] = files_by_type.get(file_type, 0) + 1
        
        # Files by month
        files_by_month = {}
        for file in files:
            uploaded_at = file.get('uploaded_at')
            if uploaded_at:
                month = uploaded_at[:7]  # YYYY-MM
                files_by_month[month] = files_by_month.get(month, 0) + 1
        
        # Oldest and newest files
        oldest_file = None
        newest_file = None
        if files:
            dates = [f.get('uploaded_at') for f in files if f.get('uploaded_at')]
            if dates:
                oldest_file = min(dates)
                newest_file = max(dates)
        
        # Storage limit (5GB default)
        storage_limit_mb = 5000
        storage_used_percent = (total_size_mb / storage_limit_mb) * 100 if storage_limit_mb > 0 else 0
        
        return FileStatsResponse(
            organization_id=org_id,
            total_files=total_files,
            total_size_mb=total_size_mb,
            files_by_type=files_by_type,
            files_by_month=files_by_month,
            storage_used_mb=total_size_mb,
            storage_limit_mb=storage_limit_mb,
            storage_used_percent=round(storage_used_percent, 2),
            oldest_file=oldest_file,
            newest_file=newest_file
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting file stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get file stats: {str(e)}"
        )

@router.post("/bulk-upload")
async def bulk_upload_files(
    files: List[UploadFile] = File(..., description="Files to upload"),
    metadata: Optional[str] = Form(None, description="JSON metadata for all files"),
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Upload multiple files to the organization's storage.
    """
    try:
        supabase = get_supabase_client()
        
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not associated with an organization"
            )
        
        # Check total size
        total_size = 0
        for file in files:
            content = await file.read()
            total_size += len(content)
            await file.seek(0)  # Reset for later
        
        if total_size > 100 * 1024 * 1024:  # 100MB total
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Total file size exceeds 100MB limit"
            )
        
        uploaded = []
        failed = []
        
        # Parse metadata
        metadata_dict = {}
        if metadata:
            try:
                import json
                metadata_dict = json.loads(metadata)
            except:
                metadata_dict = {"raw_metadata": metadata}
        
        for file in files:
            try:
                content = await file.read()
                file_size = len(content)
                
                if file_size > 50 * 1024 * 1024:
                    failed.append({
                        "name": file.filename,
                        "error": "File exceeds 50MB limit"
                    })
                    continue
                
                # Determine file type
                mime_type = file.content_type or 'application/octet-stream'
                file_type = get_file_type(file.filename, mime_type)
                
                # Generate upload path
                path = await get_organization_upload_path(supabase, org_id, file.filename)
                bucket = 'documents'
                
                # Upload to storage
                supabase.storage.from_(bucket).upload(
                    path,
                    content,
                    file_options={
                        "content-type": mime_type,
                        "cache-control": "3600"
                    }
                )
                
                # Create database record
                file_metadata = {
                    **metadata_dict,
                    'uploaded_by': current_user.user_id,
                    'uploaded_by_email': current_user.email,
                    'upload_timestamp': datetime.now().isoformat(),
                    'file_size_mb': file_size / (1024 * 1024)
                }
                
                file_record = {
                    'organization_id': org_id,
                    'name': file.filename,
                    'path': path,
                    'size_bytes': file_size,
                    'file_type': file_type,
                    'mime_type': mime_type,
                    'bucket': bucket,
                    'uploaded_by': current_user.user_id,
                    'uploaded_at': datetime.now().isoformat(),
                    'metadata': file_metadata,
                    'is_active': True,
                    'access_count': 0
                }
                
                result = supabase.from_('organization_files') \
                    .insert(file_record) \
                    .execute()
                
                if result.data:
                    uploaded.append({
                        "name": file.filename,
                        "file_id": result.data[0]['id'],
                        "size_mb": file_size / (1024 * 1024)
                    })
                else:
                    failed.append({
                        "name": file.filename,
                        "error": "Failed to create file record"
                    })
                    
            except Exception as file_error:
                failed.append({
                    "name": file.filename,
                    "error": str(file_error)
                })
        
        return {
            "success": True,
            "uploaded": uploaded,
            "failed": failed,
            "total_uploaded": len(uploaded),
            "total_failed": len(failed)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error bulk uploading files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload files: {str(e)}"
        )
# Add to backend/routes/organizations/files.py

# ==========================================
# File Management Endpoints
# ==========================================

@router.post("/{org_id}/files/{file_id}/archive")
async def archive_file(
    org_id: str,
    file_id: str,
    current_user: AuthUser = Depends(require_org_admin())
):
    """Archive a file (soft delete)."""
    try:
        supabase = get_supabase_client()
        
        # Check if file exists
        existing = supabase.from_('organization_files') \
            .select('id') \
            .eq('id', file_id) \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Archive file
        result = supabase.from_('organization_files') \
            .update({
                'is_active': False,
                'deleted_at': datetime.utcnow().isoformat(),
                'status': 'archived'
            }) \
            .eq('id', file_id) \
            .execute()
        
        return {
            "success": True,
            "message": "File archived successfully",
            "data": result.data[0] if result.data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to archive file: {str(e)}"
        )

@router.post("/{org_id}/files/{file_id}/restore")
async def restore_file(
    org_id: str,
    file_id: str,
    current_user: AuthUser = Depends(require_org_admin())
):
    """Restore an archived file."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('organization_files') \
            .update({
                'is_active': True,
                'deleted_at': None,
                'status': 'restored'
            }) \
            .eq('id', file_id) \
            .eq('organization_id', org_id) \
            .execute()
        
        return {
            "success": True,
            "message": "File restored successfully",
            "data": result.data[0] if result.data else None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore file: {str(e)}"
        )

@router.get("/{org_id}/files/archived")
async def get_archived_files(
    org_id: str,
    current_user: AuthUser = Depends(require_org_admin()),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get archived files for an organization."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('organization_files') \
            .select('*') \
            .eq('organization_id', org_id) \
            .eq('is_active', False) \
            .order('deleted_at', desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        return {
            "success": True,
            "data": result.data,
            "total": len(result.data)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get archived files: {str(e)}"
        )

@router.delete("/{org_id}/files/{file_id}/permanent")
async def permanent_delete_file(
    org_id: str,
    file_id: str,
    current_user: AuthUser = Depends(require_org_admin())
):
    """Permanently delete a file."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('organization_files') \
            .delete() \
            .eq('id', file_id) \
            .eq('organization_id', org_id) \
            .execute()
        
        return {
            "success": True,
            "message": "File permanently deleted"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )
# ================================
# PYDANTIC MODELS
# ================================

class FileVersionResponse(BaseModel):
    """Response model for file version."""
    id: str
    file_id: str
    version_number: int
    file_url: str
    file_name: str
    file_size: Optional[int]
    mime_type: Optional[str]
    changes: Optional[str]
    created_by: Optional[str]
    created_by_name: Optional[str]
    created_at: datetime
    is_current: bool


class FileVersionCreate(BaseModel):
    """Request model for creating a file version."""
    file_url: str = Field(..., description="URL to the new version file")
    file_name: str = Field(..., description="Name of the new version file")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type of the file")
    changes: Optional[str] = Field(None, description="Description of changes")


class FileCommentCreate(BaseModel):
    """Request model for creating a file comment."""
    content: str = Field(..., description="Comment content")
    parent_comment_id: Optional[str] = Field(None, description="Parent comment ID for replies")

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Comment content cannot be empty")
        if len(v) > 5000:
            raise ValueError("Comment exceeds maximum length of 5000 characters")
        return v.strip()


class FileCommentUpdate(BaseModel):
    """Request model for updating a file comment."""
    content: str = Field(..., description="Updated comment content")

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Comment content cannot be empty")
        if len(v) > 5000:
            raise ValueError("Comment exceeds maximum length of 5000 characters")
        return v.strip()


class FileCommentResponse(BaseModel):
    """Response model for file comment."""
    id: str
    file_id: str
    user_id: str
    user_name: Optional[str]
    user_email: Optional[str]
    content: str
    parent_comment_id: Optional[str]
    replies: Optional[List['FileCommentResponse']]
    created_at: datetime
    updated_at: Optional[datetime]
    is_edited: bool


class FileVersionDetailResponse(BaseModel):
    """Response model for file version detail."""
    id: str
    file_id: str
    version_number: int
    file_url: str
    file_name: str
    file_size: Optional[int]
    mime_type: Optional[str]
    changes: Optional[str]
    created_by: Optional[str]
    created_by_name: Optional[str]
    created_at: datetime
    file_metadata: Optional[Dict[str, Any]]
    organization_id: str
    organization_name: Optional[str]


# ================================
# HELPER FUNCTIONS
# ================================

async def verify_file_access(
    org_id: str,
    file_id: str,
    current_user: AuthUser,
    supabase: Client
) -> Dict[str, Any]:
    """
    Verify user has access to a file.
    Returns the file data if access is granted.
    """
    # Verify user belongs to organization
    member_check = supabase.from_('organization_members') \
        .select('id') \
        .eq('organization_id', org_id) \
        .eq('user_id', current_user.user_id) \
        .maybe_single() \
        .execute()
    
    if not member_check.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't belong to this organization"
        )
    
    # Get file
    file_result = supabase.from_('organization_files') \
        .select('''
            id, name, path, size_bytes, file_type, mime_type,
            bucket, uploaded_by, uploaded_at, metadata,
            created_at, updated_at, status,
            organizations(name)
        ''') \
        .eq('id', file_id) \
        .eq('organization_id', org_id) \
        .maybe_single() \
        .execute()
    
    if not file_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return file_result.data


# ================================
# FILE VERSIONS ENDPOINTS
# ================================

@router.get("/{org_id}/files/{file_id}/versions", response_model=List[FileVersionResponse])
async def get_file_versions(
    org_id: str,
    file_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get all versions of a file."""
    try:
        # Verify access
        file_data = await verify_file_access(org_id, file_id, current_user, supabase)
        
        # Get versions from metadata
        metadata = file_data.get('metadata', {})
        versions = metadata.get('versions', [])
        
        # Include current version as first entry
        current_version = {
            'id': str(uuid.uuid4()),
            'version_number': len(versions) + 1,
            'file_url': file_data.get('path'),
            'file_name': file_data.get('name'),
            'file_size': file_data.get('size_bytes'),
            'mime_type': file_data.get('mime_type'),
            'changes': 'Current version',
            'created_by': file_data.get('uploaded_by'),
            'created_at': file_data.get('created_at')
        }
        
        # Add current version first, then historical versions
        all_versions = [current_version] + versions
        
        # Enrich with user details
        response_versions = []
        for v in all_versions:
            created_by_name = None
            if v.get('created_by'):
                user_result = supabase.from_('auth.users') \
                    .select('email, raw_user_meta_data') \
                    .eq('id', v['created_by']) \
                    .maybe_single() \
                    .execute()
                
                if user_result.data:
                    raw_meta = user_result.data.get('raw_user_meta_data', {})
                    created_by_name = raw_meta.get('full_name') or raw_meta.get('name') or user_result.data.get('email')
            
            response_versions.append(FileVersionResponse(
                id=v.get('id', str(uuid.uuid4())),
                file_id=file_id,
                version_number=v.get('version_number', 1),
                file_url=v.get('file_url', ''),
                file_name=v.get('file_name', ''),
                file_size=v.get('file_size'),
                mime_type=v.get('mime_type'),
                changes=v.get('changes'),
                created_by=v.get('created_by'),
                created_by_name=created_by_name,
                created_at=datetime.fromisoformat(v['created_at']) if isinstance(v.get('created_at'), str) else v.get('created_at', datetime.utcnow()),
                is_current=(v == current_version)
            ))
        
        # Sort by version number descending
        response_versions.sort(key=lambda x: x.version_number, reverse=True)
        
        return response_versions
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting file versions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get file versions: {str(e)}"
        )


@router.post("/{org_id}/files/{file_id}/versions", response_model=FileVersionResponse)
async def create_file_version(
    org_id: str,
    file_id: str,
    version_data: FileVersionCreate,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Create a new version of a file."""
    try:
        # Verify access
        file_data = await verify_file_access(org_id, file_id, current_user, supabase)
        
        now = datetime.utcnow().isoformat()
        
        # Get current versions
        metadata = file_data.get('metadata', {})
        versions = metadata.get('versions', [])
        
        # Save current version to history
        current_version = {
            'id': str(uuid.uuid4()),
            'version_number': len(versions) + 1,
            'file_url': file_data.get('path'),
            'file_name': file_data.get('name'),
            'file_size': file_data.get('size_bytes'),
            'mime_type': file_data.get('mime_type'),
            'changes': 'Previous version',
            'created_by': file_data.get('uploaded_by') or file_data.get('created_by'),
            'created_at': file_data.get('created_at') or now
        }
        versions.append(current_version)
        
        # Update file with new version
        update_data = {
            'path': version_data.file_url,
            'name': version_data.file_name,
            'size_bytes': version_data.file_size,
            'mime_type': version_data.mime_type,
            'updated_at': now
        }
        
        # Update metadata
        metadata['versions'] = versions
        metadata['version_history'] = metadata.get('version_history', []) + [{
            'version': len(versions),
            'timestamp': now,
            'changes': version_data.changes,
            'created_by': current_user.user_id
        }]
        update_data['metadata'] = metadata
        
        result = supabase.from_('organization_files') \
            .update(update_data) \
            .eq('id', file_id) \
            .eq('organization_id', org_id) \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create new version"
            )
        
        # Create audit log
        try:
            audit_data = {
                'user_id': current_user.user_id,
                'organization_id': org_id,
                'action_type': 'file_version_created',
                'resource_type': 'organization_file',
                'resource_id': file_id,
                'action': 'create_version',
                'description': f"Created new version of file: {version_data.file_name}",
                'new_data': {'version': len(versions), 'changes': version_data.changes},
                'created_at': now
            }
            supabase.from_('audit_logs').insert(audit_data).execute()
        except Exception as audit_error:
            print(f"⚠️ Error creating audit log: {audit_error}")
        
        # Get user details
        created_by_name = None
        user_result = supabase.from_('auth.users') \
            .select('email, raw_user_meta_data') \
            .eq('id', current_user.user_id) \
            .maybe_single() \
            .execute()
        
        if user_result.data:
            raw_meta = user_result.data.get('raw_user_meta_data', {})
            created_by_name = raw_meta.get('full_name') or raw_meta.get('name') or user_result.data.get('email')
        
        return FileVersionResponse(
            id=str(uuid.uuid4()),
            file_id=file_id,
            version_number=len(versions) + 1,
            file_url=version_data.file_url,
            file_name=version_data.file_name,
            file_size=version_data.file_size,
            mime_type=version_data.mime_type,
            changes=version_data.changes or 'New version',
            created_by=current_user.user_id,
            created_by_name=created_by_name,
            created_at=datetime.utcnow(),
            is_current=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating file version: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create file version: {str(e)}"
        )


@router.get("/{org_id}/files/{file_id}/versions/{version_id}", response_model=FileVersionDetailResponse)
async def get_file_version_detail(
    org_id: str,
    file_id: str,
    version_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get details of a specific file version."""
    try:
        # Verify access
        file_data = await verify_file_access(org_id, file_id, current_user, supabase)
        
        # Get versions from metadata
        metadata = file_data.get('metadata', {})
        versions = metadata.get('versions', [])
        
        # Check if version exists
        version = None
        for v in versions:
            if v.get('id') == version_id:
                version = v
                break
        
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found"
            )
        
        # Get user details
        created_by_name = None
        if version.get('created_by'):
            user_result = supabase.from_('auth.users') \
                .select('email, raw_user_meta_data') \
                .eq('id', version['created_by']) \
                .maybe_single() \
                .execute()
            
            if user_result.data:
                raw_meta = user_result.data.get('raw_user_meta_data', {})
                created_by_name = raw_meta.get('full_name') or raw_meta.get('name') or user_result.data.get('email')
        
        # Get organization name
        org_name = file_data.get('organizations', {}).get('name') if file_data.get('organizations') else None
        
        return FileVersionDetailResponse(
            id=version['id'],
            file_id=file_id,
            version_number=version.get('version_number', 1),
            file_url=version.get('file_url', ''),
            file_name=version.get('file_name', ''),
            file_size=version.get('file_size'),
            mime_type=version.get('mime_type'),
            changes=version.get('changes'),
            created_by=version.get('created_by'),
            created_by_name=created_by_name,
            created_at=datetime.fromisoformat(version['created_at']) if isinstance(version.get('created_at'), str) else version.get('created_at', datetime.utcnow()),
            file_metadata=version.get('metadata'),
            organization_id=org_id,
            organization_name=org_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting file version detail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get file version detail: {str(e)}"
        )


# ================================
# FILE COMMENTS ENDPOINTS
# ================================

@router.post("/{org_id}/files/{file_id}/comments", response_model=FileCommentResponse)
async def add_file_comment(
    org_id: str,
    file_id: str,
    comment_data: FileCommentCreate,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Add a comment to a file."""
    try:
        # Verify access
        file_data = await verify_file_access(org_id, file_id, current_user, supabase)
        
        now = datetime.utcnow().isoformat()
        
        # Get current metadata
        metadata = file_data.get('metadata', {})
        if 'comments' not in metadata:
            metadata['comments'] = []
        
        # Create comment
        comment = {
            'id': str(uuid.uuid4()),
            'user_id': current_user.user_id,
            'content': comment_data.content,
            'parent_comment_id': comment_data.parent_comment_id,
            'created_at': now,
            'updated_at': now,
            'is_edited': False
        }
        
        metadata['comments'].append(comment)
        
        # Update file
        update_result = supabase.from_('organization_files') \
            .update({
                'metadata': metadata,
                'updated_at': now
            }) \
            .eq('id', file_id) \
            .eq('organization_id', org_id) \
            .execute()
        
        if not update_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add comment"
            )
        
        # Get user details
        user_name = None
        user_email = None
        user_result = supabase.from_('auth.users') \
            .select('email, raw_user_meta_data') \
            .eq('id', current_user.user_id) \
            .maybe_single() \
            .execute()
        
        if user_result.data:
            user_email = user_result.data.get('email')
            raw_meta = user_result.data.get('raw_user_meta_data', {})
            user_name = raw_meta.get('full_name') or raw_meta.get('name') or user_email
        
        return FileCommentResponse(
            id=comment['id'],
            file_id=file_id,
            user_id=current_user.user_id,
            user_name=user_name,
            user_email=user_email,
            content=comment['content'],
            parent_comment_id=comment.get('parent_comment_id'),
            replies=[],
            created_at=datetime.fromisoformat(comment['created_at']),
            updated_at=datetime.fromisoformat(comment['updated_at']),
            is_edited=comment.get('is_edited', False)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error adding comment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add comment: {str(e)}"
        )


@router.get("/{org_id}/files/{file_id}/comments", response_model=List[FileCommentResponse])
async def get_file_comments(
    org_id: str,
    file_id: str,
    include_replies: bool = Query(True, description="Include replies to comments"),
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get all comments for a file."""
    try:
        # Verify access
        file_data = await verify_file_access(org_id, file_id, current_user, supabase)
        
        # Get comments from metadata
        metadata = file_data.get('metadata', {})
        comments_data = metadata.get('comments', [])
        
        # Build comment tree
        comment_map = {}
        root_comments = []
        
        for comment_data in comments_data:
            # Get user details
            user_name = None
            user_email = None
            if comment_data.get('user_id'):
                user_result = supabase.from_('auth.users') \
                    .select('email, raw_user_meta_data') \
                    .eq('id', comment_data['user_id']) \
                    .maybe_single() \
                    .execute()
                
                if user_result.data:
                    user_email = user_result.data.get('email')
                    raw_meta = user_result.data.get('raw_user_meta_data', {})
                    user_name = raw_meta.get('full_name') or raw_meta.get('name') or user_email
            
            comment_response = FileCommentResponse(
                id=comment_data['id'],
                file_id=file_id,
                user_id=comment_data.get('user_id', ''),
                user_name=user_name,
                user_email=user_email,
                content=comment_data.get('content', ''),
                parent_comment_id=comment_data.get('parent_comment_id'),
                replies=[],
                created_at=datetime.fromisoformat(comment_data['created_at']) if comment_data.get('created_at') else datetime.utcnow(),
                updated_at=datetime.fromisoformat(comment_data['updated_at']) if comment_data.get('updated_at') else None,
                is_edited=comment_data.get('is_edited', False)
            )
            
            comment_map[comment_data['id']] = comment_response
            
            if comment_data.get('parent_comment_id'):
                # This is a reply
                if comment_data['parent_comment_id'] in comment_map:
                    # Add to parent's replies
                    if include_replies:
                        comment_map[comment_data['parent_comment_id']].replies.append(comment_response)
                else:
                    # Parent not found, add as root
                    root_comments.append(comment_response)
            else:
                # Root comment
                root_comments.append(comment_response)
        
        # Sort by created_at descending for root comments
        root_comments.sort(key=lambda x: x.created_at, reverse=True)
        
        # Sort replies by created_at ascending
        for comment in root_comments:
            if comment.replies:
                comment.replies.sort(key=lambda x: x.created_at, ascending=True)
        
        return root_comments
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting comments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get comments: {str(e)}"
        )


@router.put("/{org_id}/files/{file_id}/comments/{comment_id}", response_model=FileCommentResponse)
async def update_file_comment(
    org_id: str,
    file_id: str,
    comment_id: str,
    comment_data: FileCommentUpdate,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Update a file comment."""
    try:
        # Verify access
        file_data = await verify_file_access(org_id, file_id, current_user, supabase)
        
        # Get comments from metadata
        metadata = file_data.get('metadata', {})
        comments = metadata.get('comments', [])
        
        # Find comment
        comment_index = -1
        comment = None
        for idx, c in enumerate(comments):
            if c.get('id') == comment_id:
                comment_index = idx
                comment = c
                break
        
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )
        
        # Verify user owns the comment
        if comment.get('user_id') != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this comment"
            )
        
        now = datetime.utcnow().isoformat()
        
        # Update comment
        comment['content'] = comment_data.content
        comment['updated_at'] = now
        comment['is_edited'] = True
        
        comments[comment_index] = comment
        
        # Update file
        metadata['comments'] = comments
        update_result = supabase.from_('organization_files') \
            .update({
                'metadata': metadata,
                'updated_at': now
            }) \
            .eq('id', file_id) \
            .eq('organization_id', org_id) \
            .execute()
        
        if not update_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update comment"
            )
        
        # Get user details
        user_name = None
        user_email = None
        user_result = supabase.from_('auth.users') \
            .select('email, raw_user_meta_data') \
            .eq('id', current_user.user_id) \
            .maybe_single() \
            .execute()
        
        if user_result.data:
            user_email = user_result.data.get('email')
            raw_meta = user_result.data.get('raw_user_meta_data', {})
            user_name = raw_meta.get('full_name') or raw_meta.get('name') or user_email
        
        return FileCommentResponse(
            id=comment['id'],
            file_id=file_id,
            user_id=current_user.user_id,
            user_name=user_name,
            user_email=user_email,
            content=comment['content'],
            parent_comment_id=comment.get('parent_comment_id'),
            replies=[],
            created_at=datetime.fromisoformat(comment['created_at']) if comment.get('created_at') else datetime.utcnow(),
            updated_at=datetime.fromisoformat(comment['updated_at']) if comment.get('updated_at') else None,
            is_edited=comment.get('is_edited', False)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating comment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update comment: {str(e)}"
        )


# ================================
# ADDITIONAL HELPER ENDPOINTS
# ================================

@router.delete("/{org_id}/files/{file_id}/comments/{comment_id}")
async def delete_file_comment(
    org_id: str,
    file_id: str,
    comment_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Delete a file comment (soft delete)."""
    try:
        # Verify access
        file_data = await verify_file_access(org_id, file_id, current_user, supabase)
        
        # Get comments from metadata
        metadata = file_data.get('metadata', {})
        comments = metadata.get('comments', [])
        
        # Find comment
        comment = None
        comment_index = -1
        for idx, c in enumerate(comments):
            if c.get('id') == comment_id:
                comment = c
                comment_index = idx
                break
        
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )
        
        # Verify user owns the comment or is admin
        if comment.get('user_id') != current_user.user_id:
            # Check if user is staff/admin
            staff_check = supabase.from_('staff_profiles') \
                .select('id') \
                .eq('user_id', current_user.user_id) \
                .eq('role', 'admin') \
                .maybe_single() \
                .execute()
            
            if not staff_check.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to delete this comment"
                )
        
        now = datetime.utcnow().isoformat()
        
        # Soft delete (mark as deleted)
        comments[comment_index]['deleted_at'] = now
        comments[comment_index]['is_deleted'] = True
        
        # Update file
        metadata['comments'] = comments
        update_result = supabase.from_('organization_files') \
            .update({
                'metadata': metadata,
                'updated_at': now
            }) \
            .eq('id', file_id) \
            .eq('organization_id', org_id) \
            .execute()
        
        if not update_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete comment"
            )
        
        return {
            "success": True,
            "message": "Comment deleted successfully",
            "comment_id": comment_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting comment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete comment: {str(e)}"
        )
