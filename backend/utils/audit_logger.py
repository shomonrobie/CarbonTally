# backend/utils/audit_logger.py
from typing import Optional, Dict, Any
from datetime import datetime
from database import get_supabase_client

async def log_audit(
    user_id: Optional[str] = None,
    staff_id: Optional[str] = None,
    organization_member_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    action_type: str = None,
    resource_type: str = None,
    resource_id: Optional[str] = None,
    action: str = None,
    description: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    old_data: Optional[Dict] = None,
    new_data: Optional[Dict] = None,
    metadata: Optional[Dict] = None
):
    """Log an audit event."""
    try:
        supabase = get_supabase_client()
        
        # Calculate changes if both old and new data provided
        changes = None
        if old_data and new_data:
            changes = {}
            for key in set(old_data.keys()) | set(new_data.keys()):
                if key in old_data and key in new_data and old_data[key] != new_data[key]:
                    changes[key] = {
                        'old': old_data.get(key),
                        'new': new_data.get(key)
                    }
        
        audit_data = {
            'user_id': user_id,
            'staff_id': staff_id,
            'organization_member_id': organization_member_id,
            'organization_id': organization_id,
            'action_type': action_type,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'action': action,
            'description': description,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'old_data': old_data,
            'new_data': new_data,
            'changes': changes,
            'metadata': metadata,
            'created_at': datetime.now().isoformat()
        }
        
        result = supabase.from_('audit_logs') \
            .insert(audit_data) \
            .execute()
        
        return result.data[0] if result.data else None
        
    except Exception as e:
        print(f"⚠️ Error logging audit: {e}")
        return None

# Logging helpers for specific actions
async def log_document_action(
    document_id: str,
    organization_id: str,
    user_id: str,
    action: str,
    old_data: Optional[Dict] = None,
    new_data: Optional[Dict] = None,
    **kwargs
):
    """Log document-related actions."""
    return await log_audit(
        user_id=user_id,
        organization_id=organization_id,
        action_type='document_uploaded' if action == 'uploaded' else 'document_updated',
        resource_type='document',
        resource_id=document_id,
        action=action,
        old_data=old_data,
        new_data=new_data,
        **kwargs
    )

async def log_verification_action(
    verification_id: str,
    organization_id: str,
    user_id: str,
    action: str,
    status: str,
    **kwargs
):
    """Log verification actions."""
    action_type_map = {
        'submitted': 'verification_submitted',
        'verified': 'verification_approved',
        'rejected': 'verification_rejected',
        'needs_revision': 'verification_needs_revision'
    }
    
    return await log_audit(
        user_id=user_id,
        organization_id=organization_id,
        action_type=action_type_map.get(action, 'verification_submitted'),
        resource_type='verification',
        resource_id=verification_id,
        action=action,
        metadata={'status': status},
        **kwargs
    )

async def log_message_action(
    message_id: str,
    conversation_id: str,
    user_id: str,
    action: str,
    **kwargs
):
    """Log message actions."""
    return await log_audit(
        user_id=user_id,
        action_type='message_sent' if action == 'sent' else 'message_read',
        resource_type='message',
        resource_id=message_id,
        action=action,
        metadata={'conversation_id': conversation_id},
        **kwargs
    )

async def log_notification_action(
    notification_id: str,
    user_id: str,
    action: str,
    **kwargs
):
    """Log notification actions."""
    return await log_audit(
        user_id=user_id,
        action_type='notification_sent' if action == 'sent' else 'notification_read',
        resource_type='notification',
        resource_id=notification_id,
        action=action,
        **kwargs
    )