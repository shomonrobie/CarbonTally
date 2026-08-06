# backend/routes/admin/document_types.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from auth import AuthUser, require_role
from database import get_supabase_client

router = APIRouter(prefix="/api/admin/document-types", tags=["Admin - Document Types"])

# ==========================================
# PYDANTIC MODELS
# ==========================================

class DocumentTypeCreate(BaseModel):
    code: str = Field(..., description="Unique code")
    name: str = Field(..., description="Display name")
    category: str = Field(..., description="invoice, receipt, log, export, spreadsheet, other")
    description: Optional[str] = None
    file_extensions: List[str] = Field(default=[])
    requires_asset: bool = False
    requires_date_range: bool = False
    requires_facility: bool = False
    priority: int = 0
    metadata: Optional[Dict] = None

class DocumentTypeUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    file_extensions: Optional[List[str]] = None
    requires_asset: Optional[bool] = None
    requires_date_range: Optional[bool] = None
    requires_facility: Optional[bool] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict] = None

class DocumentTypeResponse(BaseModel):
    id: str
    code: str
    name: str
    category: str
    description: Optional[str]
    file_extensions: List[str]
    requires_asset: bool
    requires_date_range: bool
    requires_facility: bool
    priority: int
    is_active: bool
    metadata: Optional[Dict]
    created_at: datetime
    updated_at: datetime

# ==========================================
# ENDPOINTS
# ==========================================

@router.get("/", response_model=List[DocumentTypeResponse])
async def get_document_types(
    category: Optional[str] = Query(None, description="Filter by category"),
    active_only: bool = Query(True, description="Only show active types"),
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """Get all document types."""
    try:
        supabase = get_supabase_client()
        
        query = supabase.from_('document_types') \
            .select('*') \
            .order('priority', desc=True)
        
        if category:
            query = query.eq('category', category)
        if active_only:
            query = query.eq('is_active', True)
        
        result = query.execute()
        return result.data or []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=DocumentTypeResponse)
async def create_document_type(
    data: DocumentTypeCreate,
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """Create a new document type."""
    try:
        supabase = get_supabase_client()
        
        # Check if code exists
        existing = supabase.from_('document_types') \
            .select('id') \
            .eq('code', data.code) \
            .maybe_single() \
            .execute()
        
        if existing.data:
            raise HTTPException(
                status_code=409,
                detail=f"Document type with code '{data.code}' already exists"
            )
        
        now = datetime.now().isoformat()
        result = supabase.from_('document_types') \
            .insert({
                'code': data.code,
                'name': data.name,
                'category': data.category,
                'description': data.description,
                'file_extensions': data.file_extensions,
                'requires_asset': data.requires_asset,
                'requires_date_range': data.requires_date_range,
                'requires_facility': data.requires_facility,
                'priority': data.priority,
                'is_active': True,
                'metadata': data.metadata,
                'created_at': now,
                'updated_at': now
            }) \
            .execute()
        
        return result.data[0] if result.data else None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{type_id}", response_model=DocumentTypeResponse)
async def update_document_type(
    type_id: str,
    data: DocumentTypeUpdate,
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """Update a document type."""
    try:
        supabase = get_supabase_client()
        
        # Check if exists
        existing = supabase.from_('document_types') \
            .select('id') \
            .eq('id', type_id) \
            .maybe_single() \
            .execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Document type not found")
        
        update_data = {}
        if data.name is not None: update_data['name'] = data.name
        if data.category is not None: update_data['category'] = data.category
        if data.description is not None: update_data['description'] = data.description
        if data.file_extensions is not None: update_data['file_extensions'] = data.file_extensions
        if data.requires_asset is not None: update_data['requires_asset'] = data.requires_asset
        if data.requires_date_range is not None: update_data['requires_date_range'] = data.requires_date_range
        if data.requires_facility is not None: update_data['requires_facility'] = data.requires_facility
        if data.priority is not None: update_data['priority'] = data.priority
        if data.is_active is not None: update_data['is_active'] = data.is_active
        if data.metadata is not None: update_data['metadata'] = data.metadata
        
        update_data['updated_at'] = datetime.now().isoformat()
        
        result = supabase.from_('document_types') \
            .update(update_data) \
            .eq('id', type_id) \
            .execute()
        
        return result.data[0] if result.data else None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{type_id}")
async def delete_document_type(
    type_id: str,
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """Soft delete a document type."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('document_types') \
            .update({
                'is_active': False,
                'updated_at': datetime.now().isoformat()
            }) \
            .eq('id', type_id) \
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Document type not found")
        
        return {"success": True, "message": "Document type deactivated"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories")
async def get_document_type_categories(
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """Get all document type categories."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('document_types') \
            .select('category') \
            .eq('is_active', True) \
            .execute()
        
        categories = list(set(r.get('category') for r in (result.data or []) if r.get('category')))
        return {"success": True, "categories": sorted(categories)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/seed-defaults")
async def seed_default_document_types(
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """Seed default document types."""
    try:
        supabase = get_supabase_client()
        
        default_types = [
            # Invoices
            {'code': 'invoice_electricity', 'name': 'Electricity Invoice', 'category': 'invoice', 
             'description': 'Electricity utility bill/invoice', 'file_extensions': ['pdf', 'csv', 'xlsx'],
             'requires_asset': True, 'requires_date_range': True, 'requires_facility': True, 'priority': 1},
            {'code': 'invoice_gas', 'name': 'Gas Invoice', 'category': 'invoice',
             'description': 'Gas utility bill/invoice', 'file_extensions': ['pdf', 'csv', 'xlsx'],
             'requires_asset': True, 'requires_date_range': True, 'requires_facility': True, 'priority': 1},
            {'code': 'invoice_water', 'name': 'Water Invoice', 'category': 'invoice',
             'description': 'Water utility bill/invoice', 'file_extensions': ['pdf', 'csv', 'xlsx'],
             'requires_asset': True, 'requires_date_range': True, 'requires_facility': True, 'priority': 2},
            {'code': 'invoice_fuel', 'name': 'Fuel Invoice', 'category': 'invoice',
             'description': 'Fuel purchase invoice', 'file_extensions': ['pdf', 'csv', 'xlsx'],
             'requires_asset': True, 'requires_date_range': True, 'requires_facility': False, 'priority': 1},
            {'code': 'invoice_services', 'name': 'Services Invoice', 'category': 'invoice',
             'description': 'Services/invoice from suppliers', 'file_extensions': ['pdf', 'csv', 'xlsx'],
             'requires_asset': False, 'requires_date_range': True, 'requires_facility': False, 'priority': 2},
            
            # Receipts
            {'code': 'receipt_fuel', 'name': 'Fuel Receipt', 'category': 'receipt',
             'description': 'Fuel purchase receipt/slip', 'file_extensions': ['pdf', 'jpg', 'png', 'jpeg'],
             'requires_asset': True, 'requires_date_range': True, 'requires_facility': False, 'priority': 1},
            {'code': 'receipt_maintenance', 'name': 'Maintenance Receipt', 'category': 'receipt',
             'description': 'Vehicle/equipment maintenance receipt', 'file_extensions': ['pdf', 'jpg', 'png', 'jpeg'],
             'requires_asset': True, 'requires_date_range': True, 'requires_facility': True, 'priority': 2},
            {'code': 'receipt_supplies', 'name': 'Supplies Receipt', 'category': 'receipt',
             'description': 'Office supplies/equipment receipt', 'file_extensions': ['pdf', 'jpg', 'png', 'jpeg'],
             'requires_asset': False, 'requires_date_range': False, 'requires_facility': False, 'priority': 3},
            
            # Logs
            {'code': 'log_fuel', 'name': 'Fuel Log', 'category': 'log',
             'description': 'Manual fuel consumption log', 'file_extensions': ['csv', 'xlsx', 'xls'],
             'requires_asset': True, 'requires_date_range': True, 'requires_facility': False, 'priority': 1},
            {'code': 'log_mileage', 'name': 'Mileage Log', 'category': 'log',
             'description': 'Vehicle mileage/travel log', 'file_extensions': ['csv', 'xlsx', 'xls'],
             'requires_asset': True, 'requires_date_range': True, 'requires_facility': False, 'priority': 1},
            {'code': 'log_energy', 'name': 'Energy Log', 'category': 'log',
             'description': 'Energy consumption log', 'file_extensions': ['csv', 'xlsx', 'xls'],
             'requires_asset': True, 'requires_date_range': True, 'requires_facility': True, 'priority': 1},
            
            # Exports
            {'code': 'export_erp', 'name': 'ERP Export', 'category': 'export',
             'description': 'Export from ERP system (SAP, Oracle, etc.)', 'file_extensions': ['csv', 'xlsx', 'xml', 'json'],
             'requires_asset': False, 'requires_date_range': True, 'requires_facility': False, 'priority': 1},
            {'code': 'export_accounting', 'name': 'Accounting Export', 'category': 'export',
             'description': 'Export from accounting software (QuickBooks, Xero, etc.)', 'file_extensions': ['csv', 'xlsx', 'xml', 'json'],
             'requires_asset': False, 'requires_date_range': True, 'requires_facility': False, 'priority': 1},
            {'code': 'export_utility', 'name': 'Utility Export', 'category': 'export',
             'description': 'Export from utility management software', 'file_extensions': ['csv', 'xlsx', 'xml', 'json'],
             'requires_asset': True, 'requires_date_range': True, 'requires_facility': True, 'priority': 1},
            
            # Spreadsheets
            {'code': 'spreadsheet_emissions', 'name': 'Emissions Spreadsheet', 'category': 'spreadsheet',
             'description': 'Manual emissions calculation spreadsheet', 'file_extensions': ['xlsx', 'xls', 'csv'],
             'requires_asset': False, 'requires_date_range': True, 'requires_facility': False, 'priority': 2},
            {'code': 'spreadsheet_assets', 'name': 'Asset Spreadsheet', 'category': 'spreadsheet',
             'description': 'Asset inventory spreadsheet', 'file_extensions': ['xlsx', 'xls', 'csv'],
             'requires_asset': False, 'requires_date_range': False, 'requires_facility': False, 'priority': 2},
            {'code': 'spreadsheet_facilities', 'name': 'Facility Spreadsheet', 'category': 'spreadsheet',
             'description': 'Facility data spreadsheet', 'file_extensions': ['xlsx', 'xls', 'csv'],
             'requires_asset': False, 'requires_date_range': False, 'requires_facility': False, 'priority': 2},
            
            # Other
            {'code': 'other', 'name': 'Other Document', 'category': 'other',
             'description': 'Other document types', 'file_extensions': ['*'],
             'requires_asset': False, 'requires_date_range': False, 'requires_facility': False, 'priority': 9},
        ]
        
        now = datetime.now().isoformat()
        inserted = 0
        for doc_type in default_types:
            # Check if exists
            existing = supabase.from_('document_types') \
                .select('id') \
                .eq('code', doc_type['code']) \
                .maybe_single() \
                .execute()
            
            if not existing.data:
                doc_type['created_at'] = now
                doc_type['updated_at'] = now
                doc_type['is_active'] = True
                result = supabase.from_('document_types') \
                    .insert(doc_type) \
                    .execute()
                if result.data:
                    inserted += 1
        
        return {
            "success": True,
            "message": f"Seeded {inserted} default document types",
            "total": len(default_types),
            "inserted": inserted
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# Add these endpoints to the existing backend/routes/admin/document_types.py
# Place them after the existing endpoints and before the router is exported

# ==========================================
# NEW ENDPOINTS TO ADD
# ==========================================

@router.get("/{type_id}", response_model=DocumentTypeResponse)
async def get_document_type_by_id(
    type_id: str,
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """Get a specific document type by ID."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('document_types') \
            .select('*') \
            .eq('id', type_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document type not found"
            )
        
        return result.data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-create")
async def bulk_create_document_types(
    items: List[DocumentTypeCreate],
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """Bulk create document types."""
    try:
        supabase = get_supabase_client()
        now = datetime.now().isoformat()
        
        created = []
        errors = []
        
        for item in items:
            try:
                # Check if code exists
                existing = supabase.from_('document_types') \
                    .select('id') \
                    .eq('code', item.code) \
                    .maybe_single() \
                    .execute()
                
                if existing.data:
                    errors.append({
                        'code': item.code,
                        'error': 'Document type with this code already exists'
                    })
                    continue
                
                data = item.dict()
                data['is_active'] = True
                data['created_at'] = now
                data['updated_at'] = now
                
                result = supabase.from_('document_types') \
                    .insert(data) \
                    .execute()
                
                if result.data:
                    created.append(result.data[0])
                else:
                    errors.append({
                        'code': item.code,
                        'error': 'Failed to create document type'
                    })
                    
            except Exception as e:
                errors.append({
                    'code': item.code,
                    'error': str(e)
                })
        
        return {
            "success": True,
            "created": len(created),
            "failed": len(errors),
            "items": created,
            "errors": errors
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/bulk-update")
async def bulk_update_document_types(
    updates: List[Dict[str, Any]],
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """Bulk update document types."""
    try:
        supabase = get_supabase_client()
        now = datetime.now().isoformat()
        
        updated = []
        errors = []
        
        for update in updates:
            try:
                type_id = update.get('id')
                if not type_id:
                    errors.append({
                        'error': 'Missing id in update'
                    })
                    continue
                
                # Check if exists
                existing = supabase.from_('document_types') \
                    .select('id') \
                    .eq('id', type_id) \
                    .maybe_single() \
                    .execute()
                
                if not existing.data:
                    errors.append({
                        'id': type_id,
                        'error': 'Document type not found'
                    })
                    continue
                
                # Remove id from update data
                update_data = {k: v for k, v in update.items() if k != 'id'}
                update_data['updated_at'] = now
                
                result = supabase.from_('document_types') \
                    .update(update_data) \
                    .eq('id', type_id) \
                    .execute()
                
                if result.data:
                    updated.append(result.data[0])
                else:
                    errors.append({
                        'id': type_id,
                        'error': 'Failed to update document type'
                    })
                    
            except Exception as e:
                errors.append({
                    'id': update.get('id', 'unknown'),
                    'error': str(e)
                })
        
        return {
            "success": True,
            "updated": len(updated),
            "failed": len(errors),
            "items": updated,
            "errors": errors
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mapping")
async def get_document_type_mappings(
    document_type_id: Optional[str] = Query(None, description="Filter by document type"),
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """Get document type mappings from metadata."""
    try:
        supabase = get_supabase_client()
        
        query = supabase.from_('document_types') \
            .select('id, code, name, metadata')
        
        if document_type_id:
            query = query.eq('id', document_type_id)
        
        result = query.execute()
        document_types = result.data or []
        
        mappings = []
        for dt in document_types:
            metadata = dt.get('metadata', {})
            if metadata and 'mappings' in metadata:
                for key, value in metadata['mappings'].items():
                    mappings.append({
                        'document_type_id': dt['id'],
                        'document_type_code': dt['code'],
                        'document_type_name': dt['name'],
                        'mapping_key': key,
                        'mapping_value': value,
                        'metadata': None
                    })
        
        return {
            "success": True,
            "count": len(mappings),
            "mappings": mappings
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/mapping")
async def update_document_type_mappings(
    type_id: str = Query(..., description="Document type ID"),
    mappings: Dict[str, Any] = Field(..., description="Mappings to update"),
    replace: bool = Query(False, description="Replace all existing mappings"),
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """Update document type mappings."""
    try:
        supabase = get_supabase_client()
        
        # Get current document type
        result = supabase.from_('document_types') \
            .select('metadata') \
            .eq('id', type_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document type not found"
            )
        
        metadata = result.data.get('metadata', {})
        
        if replace:
            metadata['mappings'] = mappings
        else:
            if 'mappings' not in metadata:
                metadata['mappings'] = {}
            metadata['mappings'].update(mappings)
        
        update_result = supabase.from_('document_types') \
            .update({
                'metadata': metadata,
                'updated_at': datetime.now().isoformat()
            }) \
            .eq('id', type_id) \
            .execute()
        
        if not update_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update mappings"
            )
        
        return {
            "success": True,
            "message": "Mappings updated successfully",
            "document_type_id": type_id,
            "mappings": metadata.get('mappings', {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/extraction-templates")
async def get_extraction_templates(
    document_type_id: Optional[str] = Query(None, description="Filter by document type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """Get extraction templates from metadata."""
    try:
        supabase = get_supabase_client()
        
        query = supabase.from_('document_types') \
            .select('id, code, name, metadata')
        
        if document_type_id:
            query = query.eq('id', document_type_id)
        
        result = query.execute()
        document_types = result.data or []
        
        templates = []
        for dt in document_types:
            metadata = dt.get('metadata', {})
            if metadata and 'extraction_templates' in metadata:
                for template in metadata['extraction_templates']:
                    if is_active is not None and template.get('is_active', True) != is_active:
                        continue
                    
                    templates.append({
                        'id': template.get('id'),
                        'document_type_id': dt['id'],
                        'document_type_code': dt['code'],
                        'document_type_name': dt['name'],
                        'name': template.get('name', 'Default'),
                        'fields': template.get('fields', []),
                        'rules': template.get('rules'),
                        'is_active': template.get('is_active', True),
                        'version': template.get('version', 1),
                        'created_at': template.get('created_at'),
                        'updated_at': template.get('updated_at'),
                        'created_by': template.get('created_by'),
                        'updated_by': template.get('updated_by')
                    })
        
        return {
            "success": True,
            "count": len(templates),
            "templates": templates
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extraction-templates")
async def create_extraction_template(
    document_type_id: str = Query(..., description="Document type ID"),
    name: str = Query(..., description="Template name"),
    fields: List[Dict[str, Any]] = Field(..., description="Fields to extract"),
    rules: Optional[Dict[str, Any]] = Field(None, description="Extraction rules"),
    is_active: bool = Query(True, description="Whether template is active"),
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """Create an extraction template."""
    try:
        supabase = get_supabase_client()
        
        # Get document type
        result = supabase.from_('document_types') \
            .select('metadata') \
            .eq('id', document_type_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document type not found"
            )
        
        metadata = result.data.get('metadata', {})
        if 'extraction_templates' not in metadata:
            metadata['extraction_templates'] = []
        
        # Create template
        template = {
            'id': str(uuid.uuid4()),
            'name': name,
            'fields': fields,
            'rules': rules,
            'is_active': is_active,
            'version': 1,
            'created_by': current_user.id,
            'created_at': datetime.now().isoformat()
        }
        
        metadata['extraction_templates'].append(template)
        
        # Update document type
        update_result = supabase.from_('document_types') \
            .update({
                'metadata': metadata,
                'updated_at': datetime.now().isoformat()
            }) \
            .eq('id', document_type_id) \
            .execute()
        
        if not update_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create extraction template"
            )
        
        return {
            "success": True,
            "message": "Extraction template created successfully",
            "template": template
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/extraction-templates/{template_id}")
async def update_extraction_template(
    template_id: str,
    name: Optional[str] = Query(None, description="Template name"),
    fields: Optional[List[Dict[str, Any]]] = Field(None, description="Fields to extract"),
    rules: Optional[Dict[str, Any]] = Field(None, description="Extraction rules"),
    is_active: Optional[bool] = Query(None, description="Whether template is active"),
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """Update an extraction template."""
    try:
        supabase = get_supabase_client()
        
        # Find the document type containing this template
        dt_result = supabase.from_('document_types') \
            .select('id, metadata') \
            .execute()
        
        document_types = dt_result.data or []
        found_dt = None
        template_index = -1
        template_data = None
        
        for dt in document_types:
            metadata = dt.get('metadata', {})
            if 'extraction_templates' in metadata:
                for idx, template in enumerate(metadata['extraction_templates']):
                    if template.get('id') == template_id:
                        found_dt = dt
                        template_index = idx
                        template_data = template
                        break
                if found_dt:
                    break
        
        if not found_dt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Extraction template not found"
            )
        
        # Update template
        if name is not None:
            template_data['name'] = name
        if fields is not None:
            template_data['fields'] = fields
        if rules is not None:
            template_data['rules'] = rules
        if is_active is not None:
            template_data['is_active'] = is_active
        
        template_data['version'] = template_data.get('version', 0) + 1
        template_data['updated_by'] = current_user.id
        template_data['updated_at'] = datetime.now().isoformat()
        
        # Update document type
        metadata = found_dt['metadata']
        metadata['extraction_templates'][template_index] = template_data
        
        update_result = supabase.from_('document_types') \
            .update({
                'metadata': metadata,
                'updated_at': datetime.now().isoformat()
            }) \
            .eq('id', found_dt['id']) \
            .execute()
        
        if not update_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update extraction template"
            )
        
        return {
            "success": True,
            "message": "Extraction template updated successfully",
            "template": template_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))