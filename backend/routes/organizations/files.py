# backend/routes/organizations/files.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse, FileResponse
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import io
import mimetypes
from auth import AuthUser, require_org_member, require_permission
from database import get_supabase_client

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
        
        # Build query
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
            ''') \
            .eq('organization_id', org_id) \
            .eq('is_active', True)
        
        if file_type:
            query = query.eq('file_type', file_type.upper())
        if search:
            query = query.ilike('name', f'%{search}%')
        if start_date:
            query = query.gte('uploaded_at', start_date)
        if end_date:
            query = query.lte('uploaded_at', end_date)
        
        # Get total count
        count_query = query.clone()
        count_result = count_query.select('id', count='exact').execute()
        total = count_result.count or 0
        
        # Get total size
        size_result = query.clone().select('size_bytes').execute()
        total_size_bytes = sum(f.get('size_bytes', 0) for f in size_result.data)
        
        # Get paginated results
        result = query.order('uploaded_at', desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        # Transform data and get user names
        files = []
        for file in result.data:
            # Get uploader name
            uploaded_by_name = None
            if file.get('uploaded_by'):
                uploaded_by_name = await get_user_name(supabase, file['uploaded_by'])
            
            # Generate download URL
            download_url = await get_file_download_url(
                supabase, 
                file.get('bucket', 'documents'),
                file['path']
            )
            
            files.append(FileResponse(
                id=file['id'],
                name=file['name'],
                path=file['path'],
                size_bytes=file['size_bytes'],
                size_mb=file['size_bytes'] / (1024 * 1024),
                file_type=file['file_type'],
                mime_type=file['mime_type'],
                bucket=file.get('bucket', 'documents'),
                uploaded_by=file.get('uploaded_by'),
                uploaded_by_name=uploaded_by_name,
                uploaded_at=file['uploaded_at'],
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

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(..., description="File to upload"),
    metadata: Optional[str] = Form(None, description="JSON metadata for the file"),
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Upload a file to the organization's storage.
    """
    try:
        supabase = get_supabase_client()
        
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not associated with an organization"
            )
        
        # Validate file size (max 50MB)
        content = await file.read()
        file_size = len(content)
        
        if file_size > 50 * 1024 * 1024:  # 50MB
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds 50MB limit"
            )
        
        # Determine file type
        mime_type = file.content_type or 'application/octet-stream'
        file_type = get_file_type(file.filename, mime_type)
        
        # Generate upload path
        path = await get_organization_upload_path(supabase, org_id, file.filename)
        bucket = 'documents'
        
        # Upload to Supabase Storage
        try:
            # Reset file position
            await file.seek(0)
            
            # Upload file
            upload_result = supabase.storage.from_(bucket).upload(
                path,
                content,
                file_options={
                    "content-type": mime_type,
                    "cache-control": "3600"
                }
            )
            
            # Get public URL
            public_url = supabase.storage.from_(bucket).get_public_url(path)
            
        except Exception as storage_error:
            print(f"❌ Storage upload error: {storage_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(storage_error)}"
            )
        
        # Parse metadata
        metadata_dict = {}
        if metadata:
            try:
                import json
                metadata_dict = json.loads(metadata)
            except:
                metadata_dict = {"raw_metadata": metadata}
        
        # Add default metadata
        metadata_dict.update({
            'uploaded_by': current_user.user_id,
            'uploaded_by_email': current_user.email,
            'upload_timestamp': datetime.now().isoformat(),
            'file_size_mb': file_size / (1024 * 1024)
        })
        
        # Create database record
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
            'metadata': metadata_dict,
            'is_active': True,
            'access_count': 0
        }
        
        result = supabase.from_('organization_files') \
            .insert(file_record) \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create file record"
            )
        
        return FileUploadResponse(
            success=True,
            file_id=result.data[0]['id'],
            file_name=file.filename,
            file_path=path,
            size_bytes=file_size,
            size_mb=file_size / (1024 * 1024),
            message="File uploaded successfully",
            download_url=public_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error uploading file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )

@router.get("/stats", response_model=FileStatsResponse)
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