# backend/routes/communication.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timedelta
from supabase import Client
import uuid

from auth import AuthUser, require_org_member
from database import get_supabase_client

router = APIRouter(prefix="/api/communication", tags=["Communication"])


# ================================
# PYDANTIC MODELS
# ================================

class MessageCreate(BaseModel):
    """Request model for creating a message."""
    receiver_id: str = Field(..., description="ID of the receiver")
    organization_id: str = Field(..., description="Organization ID")
    subject: Optional[str] = Field(None, description="Message subject", max_length=255)
    content: str = Field(..., description="Message content")
    conversation_id: Optional[str] = Field(None, description="Conversation ID if replying")

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        if len(v) > 10000:
            raise ValueError("Content exceeds maximum length of 10000 characters")
        return v.strip()


class ConversationCreate(BaseModel):
    """Request model for creating a conversation."""
    organization_id: str = Field(..., description="Organization ID")
    subject: str = Field(..., description="Conversation subject", max_length=255)
    participant_ids: List[str] = Field(..., description="List of participant user IDs")
    is_urgent: Optional[bool] = Field(False, description="Mark as urgent")
    priority: Optional[str] = Field("normal", description="Priority level")
    initial_message: str = Field(..., description="Initial message content")

    @field_validator('participant_ids')
    @classmethod
    def validate_participants(cls, v: List[str]) -> List[str]:
        if len(v) < 1:
            raise ValueError("At least one participant is required")
        if len(v) > 20:
            raise ValueError("Maximum 20 participants allowed")
        return v


class MessageUpdateReadRequest(BaseModel):
    """Request model for marking messages as read."""
    is_read: bool = Field(True, description="Mark as read or unread")


class MessageResponse(BaseModel):
    """Response model for a message."""
    id: str
    conversation_id: Optional[str]
    sender_id: str
    receiver_id: str
    organization_id: str
    subject: Optional[str]
    content: str
    is_read: bool
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]
    created_at: datetime
    sender_name: Optional[str]
    sender_email: Optional[str]
    receiver_name: Optional[str]
    receiver_email: Optional[str]


class ConversationResponse(BaseModel):
    """Response model for a conversation."""
    id: str
    organization_id: str
    subject: Optional[str]
    status: Optional[str]
    last_message_at: Optional[datetime]
    is_urgent: Optional[bool]
    priority: Optional[str]
    created_at: datetime
    created_by: Optional[str]
    closed_by: Optional[str]
    closed_at: Optional[datetime]
    participants: List[Dict[str, Any]]
    last_message: Optional[MessageResponse]
    unread_count: int
    message_count: int


class NotificationResponse(BaseModel):
    """Response model for a notification."""
    id: str
    user_id: str
    organization_id: Optional[str]
    type: str
    title: str
    message: str
    link: Optional[str]
    is_read: bool
    read_at: Optional[datetime]
    priority: Optional[str]
    created_at: datetime


class MessagesListResponse(BaseModel):
    """Response model for messages list."""
    messages: List[MessageResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DeleteMessageResponse(BaseModel):
    """Response model for message deletion."""
    success: bool
    message: str
    message_id: str


class MarkAllReadResponse(BaseModel):
    """Response model for marking all notifications as read."""
    success: bool
    message: str
    updated_count: int


# ================================
# MESSAGES ENDPOINTS
# ================================

@router.post("/messages", response_model=MessageResponse)
async def send_message(
    message_data: MessageCreate,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Send a new message."""
    try:
        # Verify user belongs to the organization
        member_check = supabase.from_('organization_members') \
            .select('id') \
            .eq('organization_id', message_data.organization_id) \
            .eq('user_id', current_user.id) \
            .maybe_single() \
            .execute()
        
        if not member_check.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't belong to this organization"
            )
        
        # Verify receiver belongs to the organization
        receiver_check = supabase.from_('organization_members') \
            .select('id') \
            .eq('organization_id', message_data.organization_id) \
            .eq('user_id', message_data.receiver_id) \
            .maybe_single() \
            .execute()
        
        if not receiver_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receiver not found in this organization"
            )
        
        now = datetime.utcnow().isoformat()
        
        # Handle conversation
        conversation_id = message_data.conversation_id
        
        if not conversation_id:
            # Create new conversation
            conv_data = {
                'organization_id': message_data.organization_id,
                'subject': message_data.subject or 'New Conversation',
                'status': 'active',
                'created_by': current_user.id,
                'created_at': now,
                'updated_at': now
            }
            
            conv_result = supabase.from_('conversations') \
                .insert(conv_data) \
                .execute()
            
            if not conv_result.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create conversation"
                )
            
            conversation_id = conv_result.data[0]['id']
        else:
            # Verify conversation exists and belongs to organization
            conv_check = supabase.from_('conversations') \
                .select('id, status') \
                .eq('id', conversation_id) \
                .eq('organization_id', message_data.organization_id) \
                .maybe_single() \
                .execute()
            
            if not conv_check.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
            
            # Check if conversation is closed
            if conv_check.data.get('status') == 'closed':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot send message to a closed conversation"
                )
        
        # Create message
        msg_data = {
            'conversation_id': conversation_id,
            'sender_id': current_user.id,
            'receiver_id': message_data.receiver_id,
            'organization_id': message_data.organization_id,
            'subject': message_data.subject,
            'content': message_data.content,
            'is_read': False,
            'sent_at': now,
            'created_at': now,
            'updated_at': now
        }
        
        result = supabase.from_('messages') \
            .insert(msg_data) \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send message"
            )
        
        message = result.data[0]
        
        # Update conversation last_message_at
        supabase.from_('conversations') \
            .update({
                'last_message_at': now,
                'updated_at': now
            }) \
            .eq('id', conversation_id) \
            .execute()
        
        # Get sender and receiver details for response
        sender_result = supabase.from_('auth.users') \
            .select('email, raw_user_meta_data') \
            .eq('id', current_user.id) \
            .maybe_single() \
            .execute()
        
        receiver_result = supabase.from_('auth.users') \
            .select('email, raw_user_meta_data') \
            .eq('id', message_data.receiver_id) \
            .maybe_single() \
            .execute()
        
        sender_name = None
        if sender_result.data:
            raw_meta = sender_result.data.get('raw_user_meta_data', {})
            sender_name = raw_meta.get('full_name') or raw_meta.get('name') or sender_result.data.get('email')
        
        receiver_name = None
        if receiver_result.data:
            raw_meta = receiver_result.data.get('raw_user_meta_data', {})
            receiver_name = raw_meta.get('full_name') or raw_meta.get('name') or receiver_result.data.get('email')
        
        return MessageResponse(
            id=message['id'],
            conversation_id=message.get('conversation_id'),
            sender_id=message['sender_id'],
            receiver_id=message['receiver_id'],
            organization_id=message['organization_id'],
            subject=message.get('subject'),
            content=message['content'],
            is_read=message.get('is_read', False),
            sent_at=message.get('sent_at'),
            delivered_at=message.get('delivered_at'),
            read_at=message.get('read_at'),
            created_at=message['created_at'],
            sender_name=sender_name,
            sender_email=sender_result.data.get('email') if sender_result.data else None,
            receiver_name=receiver_name,
            receiver_email=receiver_result.data.get('email') if receiver_result.data else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )


@router.get("/messages", response_model=MessagesListResponse)
async def get_messages(
    current_user: AuthUser = Depends(require_org_member()),
    conversation_id: Optional[str] = Query(None, description="Filter by conversation"),
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    supabase: Client = Depends(get_supabase_client)
):
    """Get messages for the current user."""
    try:
        # Build base query
        query = supabase.from_('messages') \
            .select('''
                id, conversation_id, sender_id, receiver_id, organization_id,
                subject, content, is_read, sent_at, delivered_at, read_at,
                created_at
            ''')
        
        # Filter messages where user is sender or receiver
        query = query.or_(f'sender_id.eq.{current_user.id},receiver_id.eq.{current_user.id}')
        
        if conversation_id:
            query = query.eq('conversation_id', conversation_id)
        
        if organization_id:
            query = query.eq('organization_id', organization_id)
        
        if is_read is not None:
            query = query.eq('is_read', is_read)
        
        # Get total count
        count_query = supabase.from_('messages') \
            .select('id', count='exact') \
            .or_(f'sender_id.eq.{current_user.id},receiver_id.eq.{current_user.id}')
        
        if conversation_id:
            count_query = count_query.eq('conversation_id', conversation_id)
        if organization_id:
            count_query = count_query.eq('organization_id', organization_id)
        if is_read is not None:
            count_query = count_query.eq('is_read', is_read)
        
        count_result = count_query.execute()
        total = count_result.count if hasattr(count_result, 'count') else 0
        
        # Get paginated results
        offset = (page - 1) * page_size
        result = query.order('created_at', desc=True) \
            .range(offset, offset + page_size - 1) \
            .execute()
        
        messages = result.data or []
        
        # Get user details for each message
        message_responses = []
        for msg in messages:
            # Get sender details
            sender_result = supabase.from_('auth.users') \
                .select('email, raw_user_meta_data') \
                .eq('id', msg['sender_id']) \
                .maybe_single() \
                .execute()
            
            # Get receiver details
            receiver_result = supabase.from_('auth.users') \
                .select('email, raw_user_meta_data') \
                .eq('id', msg['receiver_id']) \
                .maybe_single() \
                .execute()
            
            sender_name = None
            sender_email = None
            if sender_result.data:
                raw_meta = sender_result.data.get('raw_user_meta_data', {})
                sender_name = raw_meta.get('full_name') or raw_meta.get('name') or sender_result.data.get('email')
                sender_email = sender_result.data.get('email')
            
            receiver_name = None
            receiver_email = None
            if receiver_result.data:
                raw_meta = receiver_result.data.get('raw_user_meta_data', {})
                receiver_name = raw_meta.get('full_name') or raw_meta.get('name') or receiver_result.data.get('email')
                receiver_email = receiver_result.data.get('email')
            
            message_responses.append(MessageResponse(
                id=msg['id'],
                conversation_id=msg.get('conversation_id'),
                sender_id=msg['sender_id'],
                receiver_id=msg['receiver_id'],
                organization_id=msg['organization_id'],
                subject=msg.get('subject'),
                content=msg['content'],
                is_read=msg.get('is_read', False),
                sent_at=msg.get('sent_at'),
                delivered_at=msg.get('delivered_at'),
                read_at=msg.get('read_at'),
                created_at=msg['created_at'],
                sender_name=sender_name,
                sender_email=sender_email,
                receiver_name=receiver_name,
                receiver_email=receiver_email
            ))
        
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        return MessagesListResponse(
            messages=message_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        print(f"❌ Error getting messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get messages: {str(e)}"
        )


@router.get("/messages/{message_id}", response_model=MessageResponse)
async def get_message_detail(
    message_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get a specific message by ID."""
    try:
        # Get message
        result = supabase.from_('messages') \
            .select('''
                id, conversation_id, sender_id, receiver_id, organization_id,
                subject, content, is_read, sent_at, delivered_at, read_at,
                created_at
            ''') \
            .eq('id', message_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        msg = result.data
        
        # Verify user has access (sender or receiver)
        if msg['sender_id'] != current_user.id and msg['receiver_id'] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this message"
            )
        
        # Get sender and receiver details
        sender_result = supabase.from_('auth.users') \
            .select('email, raw_user_meta_data') \
            .eq('id', msg['sender_id']) \
            .maybe_single() \
            .execute()
        
        receiver_result = supabase.from_('auth.users') \
            .select('email, raw_user_meta_data') \
            .eq('id', msg['receiver_id']) \
            .maybe_single() \
            .execute()
        
        sender_name = None
        sender_email = None
        if sender_result.data:
            raw_meta = sender_result.data.get('raw_user_meta_data', {})
            sender_name = raw_meta.get('full_name') or raw_meta.get('name') or sender_result.data.get('email')
            sender_email = sender_result.data.get('email')
        
        receiver_name = None
        receiver_email = None
        if receiver_result.data:
            raw_meta = receiver_result.data.get('raw_user_meta_data', {})
            receiver_name = raw_meta.get('full_name') or raw_meta.get('name') or receiver_result.data.get('email')
            receiver_email = receiver_result.data.get('email')
        
        return MessageResponse(
            id=msg['id'],
            conversation_id=msg.get('conversation_id'),
            sender_id=msg['sender_id'],
            receiver_id=msg['receiver_id'],
            organization_id=msg['organization_id'],
            subject=msg.get('subject'),
            content=msg['content'],
            is_read=msg.get('is_read', False),
            sent_at=msg.get('sent_at'),
            delivered_at=msg.get('delivered_at'),
            read_at=msg.get('read_at'),
            created_at=msg['created_at'],
            sender_name=sender_name,
            sender_email=sender_email,
            receiver_name=receiver_name,
            receiver_email=receiver_email
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting message detail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get message detail: {str(e)}"
        )


@router.put("/messages/{message_id}/read", response_model=MessageResponse)
async def mark_message_read(
    message_id: str,
    read_data: MessageUpdateReadRequest,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Mark a message as read or unread."""
    try:
        # Get message
        result = supabase.from_('messages') \
            .select('id, sender_id, receiver_id, is_read') \
            .eq('id', message_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        msg = result.data
        
        # Verify user is the receiver
        if msg['receiver_id'] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the receiver can mark this message as read"
            )
        
        now = datetime.utcnow().isoformat()
        update_data = {
            'is_read': read_data.is_read,
            'updated_at': now
        }
        
        if read_data.is_read:
            update_data['read_at'] = now
        else:
            update_data['read_at'] = None
        
        # Update message
        update_result = supabase.from_('messages') \
            .update(update_data) \
            .eq('id', message_id) \
            .execute()
        
        if not update_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update message"
            )
        
        # Get full message details
        return await get_message_detail(message_id, current_user, supabase)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error marking message read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark message as read: {str(e)}"
        )


@router.delete("/messages/{message_id}", response_model=DeleteMessageResponse)
async def delete_message(
    message_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Delete a message (soft delete)."""
    try:
        # Get message
        result = supabase.from_('messages') \
            .select('id, sender_id, receiver_id') \
            .eq('id', message_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        msg = result.data
        
        # Verify user is sender or receiver
        if msg['sender_id'] != current_user.id and msg['receiver_id'] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this message"
            )
        
        now = datetime.utcnow().isoformat()
        
        # Soft delete
        update_result = supabase.from_('messages') \
            .update({
                'is_deleted': True,
                'deleted_at': now,
                'updated_at': now
            }) \
            .eq('id', message_id) \
            .execute()
        
        if not update_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete message"
            )
        
        return DeleteMessageResponse(
            success=True,
            message="Message deleted successfully",
            message_id=message_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete message: {str(e)}"
        )


# ================================
# CONVERSATIONS ENDPOINTS
# ================================

@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    current_user: AuthUser = Depends(require_org_member()),
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    status: Optional[str] = Query(None, description="Filter by status (active/closed/archived)"),
    supabase: Client = Depends(get_supabase_client)
):
    """Get all conversations for the current user."""
    try:
        # Get conversations where user is participant
        # First get all messages where user is sender or receiver
        messages_result = supabase.from_('messages') \
            .select('conversation_id') \
            .or_(f'sender_id.eq.{current_user.id},receiver_id.eq.{current_user.id}') \
            .execute()
        
        if not messages_result.data:
            return []
        
        conversation_ids = list(set([m['conversation_id'] for m in messages_result.data if m.get('conversation_id')]))
        
        if not conversation_ids:
            return []
        
        # Get conversations
        query = supabase.from_('conversations') \
            .select('''
                id, organization_id, subject, status, last_message_at,
                is_urgent, priority, created_at, created_by, closed_by, closed_at
            ''') \
            .in_('id', conversation_ids)
        
        if organization_id:
            query = query.eq('organization_id', organization_id)
        
        if status:
            query = query.eq('status', status)
        
        result = query.order('last_message_at', desc=True).execute()
        
        conversations = result.data or []
        
        # Get participants and last message for each conversation
        conversation_responses = []
        for conv in conversations:
            # Get participants (unique users from messages in this conversation)
            participants_result = supabase.from_('messages') \
                .select('sender_id, receiver_id') \
                .eq('conversation_id', conv['id']) \
                .execute()
            
            participant_ids = set()
            for msg in (participants_result.data or []):
                participant_ids.add(msg['sender_id'])
                participant_ids.add(msg['receiver_id'])
            
            participants = []
            for user_id in participant_ids:
                user_result = supabase.from_('auth.users') \
                    .select('email, raw_user_meta_data') \
                    .eq('id', user_id) \
                    .maybe_single() \
                    .execute()
                
                if user_result.data:
                    raw_meta = user_result.data.get('raw_user_meta_data', {})
                    name = raw_meta.get('full_name') or raw_meta.get('name') or user_result.data.get('email')
                    participants.append({
                        'user_id': user_id,
                        'name': name,
                        'email': user_result.data.get('email')
                    })
            
            # Get message count
            count_result = supabase.from_('messages') \
                .select('id', count='exact') \
                .eq('conversation_id', conv['id']) \
                .execute()
            message_count = count_result.count if hasattr(count_result, 'count') else 0
            
            # Get last message
            last_msg_result = supabase.from_('messages') \
                .select('''
                    id, conversation_id, sender_id, receiver_id, organization_id,
                    subject, content, is_read, sent_at, delivered_at, read_at,
                    created_at
                ''') \
                .eq('conversation_id', conv['id']) \
                .order('created_at', desc=True) \
                .limit(1) \
                .execute()
            
            last_message = None
            if last_msg_result.data:
                msg = last_msg_result.data[0]
                # Get sender details
                sender_result = supabase.from_('auth.users') \
                    .select('email, raw_user_meta_data') \
                    .eq('id', msg['sender_id']) \
                    .maybe_single() \
                    .execute()
                
                sender_name = None
                if sender_result.data:
                    raw_meta = sender_result.data.get('raw_user_meta_data', {})
                    sender_name = raw_meta.get('full_name') or raw_meta.get('name') or sender_result.data.get('email')
                
                last_message = MessageResponse(
                    id=msg['id'],
                    conversation_id=msg.get('conversation_id'),
                    sender_id=msg['sender_id'],
                    receiver_id=msg['receiver_id'],
                    organization_id=msg['organization_id'],
                    subject=msg.get('subject'),
                    content=msg['content'],
                    is_read=msg.get('is_read', False),
                    sent_at=msg.get('sent_at'),
                    delivered_at=msg.get('delivered_at'),
                    read_at=msg.get('read_at'),
                    created_at=msg['created_at'],
                    sender_name=sender_name,
                    sender_email=sender_result.data.get('email') if sender_result.data else None,
                    receiver_name=None,
                    receiver_email=None
                )
            
            # Count unread messages for this user
            unread_result = supabase.from_('messages') \
                .select('id', count='exact') \
                .eq('conversation_id', conv['id']) \
                .eq('receiver_id', current_user.id) \
                .eq('is_read', False) \
                .execute()
            
            unread_count = unread_result.count if hasattr(unread_result, 'count') else 0
            
            conversation_responses.append(ConversationResponse(
                id=conv['id'],
                organization_id=conv['organization_id'],
                subject=conv.get('subject'),
                status=conv.get('status', 'active'),
                last_message_at=conv.get('last_message_at'),
                is_urgent=conv.get('is_urgent', False),
                priority=conv.get('priority', 'normal'),
                created_at=conv['created_at'],
                created_by=conv.get('created_by'),
                closed_by=conv.get('closed_by'),
                closed_at=conv.get('closed_at'),
                participants=participants,
                last_message=last_message,
                unread_count=unread_count,
                message_count=message_count
            ))
        
        return conversation_responses
        
    except Exception as e:
        print(f"❌ Error getting conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversations: {str(e)}"
        )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get a specific conversation by ID."""
    try:
        # Check if user is part of this conversation
        msg_check = supabase.from_('messages') \
            .select('id') \
            .eq('conversation_id', conversation_id) \
            .or_(f'sender_id.eq.{current_user.id},receiver_id.eq.{current_user.id}') \
            .limit(1) \
            .execute()
        
        if not msg_check.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this conversation"
            )
        
        # Get conversation details
        result = supabase.from_('conversations') \
            .select('''
                id, organization_id, subject, status, last_message_at,
                is_urgent, priority, created_at, created_by, closed_by, closed_at
            ''') \
            .eq('id', conversation_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        conv = result.data
        
        # Get participants
        participants_result = supabase.from_('messages') \
            .select('sender_id, receiver_id') \
            .eq('conversation_id', conversation_id) \
            .execute()
        
        participant_ids = set()
        for msg in (participants_result.data or []):
            participant_ids.add(msg['sender_id'])
            participant_ids.add(msg['receiver_id'])
        
        participants = []
        for user_id in participant_ids:
            user_result = supabase.from_('auth.users') \
                .select('email, raw_user_meta_data') \
                .eq('id', user_id) \
                .maybe_single() \
                .execute()
            
            if user_result.data:
                raw_meta = user_result.data.get('raw_user_meta_data', {})
                name = raw_meta.get('full_name') or raw_meta.get('name') or user_result.data.get('email')
                participants.append({
                    'user_id': user_id,
                    'name': name,
                    'email': user_result.data.get('email')
                })
        
        # Get message count
        count_result = supabase.from_('messages') \
            .select('id', count='exact') \
            .eq('conversation_id', conversation_id) \
            .execute()
        message_count = count_result.count if hasattr(count_result, 'count') else 0
        
        # Get last message
        last_msg_result = supabase.from_('messages') \
            .select('''
                id, conversation_id, sender_id, receiver_id, organization_id,
                subject, content, is_read, sent_at, delivered_at, read_at,
                created_at
            ''') \
            .eq('conversation_id', conversation_id) \
            .order('created_at', desc=True) \
            .limit(1) \
            .execute()
        
        last_message = None
        if last_msg_result.data:
            msg = last_msg_result.data[0]
            sender_result = supabase.from_('auth.users') \
                .select('email, raw_user_meta_data') \
                .eq('id', msg['sender_id']) \
                .maybe_single() \
                .execute()
            
            sender_name = None
            if sender_result.data:
                raw_meta = sender_result.data.get('raw_user_meta_data', {})
                sender_name = raw_meta.get('full_name') or raw_meta.get('name') or sender_result.data.get('email')
            
            last_message = MessageResponse(
                id=msg['id'],
                conversation_id=msg.get('conversation_id'),
                sender_id=msg['sender_id'],
                receiver_id=msg['receiver_id'],
                organization_id=msg['organization_id'],
                subject=msg.get('subject'),
                content=msg['content'],
                is_read=msg.get('is_read', False),
                sent_at=msg.get('sent_at'),
                delivered_at=msg.get('delivered_at'),
                read_at=msg.get('read_at'),
                created_at=msg['created_at'],
                sender_name=sender_name,
                sender_email=sender_result.data.get('email') if sender_result.data else None,
                receiver_name=None,
                receiver_email=None
            )
        
        # Count unread messages for this user
        unread_result = supabase.from_('messages') \
            .select('id', count='exact') \
            .eq('conversation_id', conversation_id) \
            .eq('receiver_id', current_user.id) \
            .eq('is_read', False) \
            .execute()
        unread_count = unread_result.count if hasattr(unread_result, 'count') else 0
        
        return ConversationResponse(
            id=conv['id'],
            organization_id=conv['organization_id'],
            subject=conv.get('subject'),
            status=conv.get('status', 'active'),
            last_message_at=conv.get('last_message_at'),
            is_urgent=conv.get('is_urgent', False),
            priority=conv.get('priority', 'normal'),
            created_at=conv['created_at'],
            created_by=conv.get('created_by'),
            closed_by=conv.get('closed_by'),
            closed_at=conv.get('closed_at'),
            participants=participants,
            last_message=last_message,
            unread_count=unread_count,
            message_count=message_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation: {str(e)}"
        )


@router.post("/conversations", response_model=ConversationResponse)
async def start_conversation(
    conversation_data: ConversationCreate,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Start a new conversation with multiple participants."""
    try:
        # Verify user belongs to the organization
        member_check = supabase.from_('organization_members') \
            .select('id') \
            .eq('organization_id', conversation_data.organization_id) \
            .eq('user_id', current_user.id) \
            .maybe_single() \
            .execute()
        
        if not member_check.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't belong to this organization"
            )
        
        # Verify all participants belong to the organization
        participant_ids = set(conversation_data.participant_ids)
        participant_ids.add(current_user.id)  # Add current user as participant
        
        for user_id in participant_ids:
            user_check = supabase.from_('organization_members') \
                .select('id') \
                .eq('organization_id', conversation_data.organization_id) \
                .eq('user_id', user_id) \
                .maybe_single() \
                .execute()
            
            if not user_check.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User {user_id} not found in this organization"
                )
        
        now = datetime.utcnow().isoformat()
        
        # Create conversation
        conv_data = {
            'organization_id': conversation_data.organization_id,
            'subject': conversation_data.subject,
            'status': 'active',
            'is_urgent': conversation_data.is_urgent,
            'priority': conversation_data.priority,
            'created_by': current_user.id,
            'created_at': now,
            'updated_at': now
        }
        
        conv_result = supabase.from_('conversations') \
            .insert(conv_data) \
            .execute()
        
        if not conv_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create conversation"
            )
        
        conversation_id = conv_result.data[0]['id']
        
        # Send initial message to all participants
        for receiver_id in participant_ids:
            if receiver_id == current_user.id:
                continue  # Skip sending to self
            
            msg_data = {
                'conversation_id': conversation_id,
                'sender_id': current_user.id,
                'receiver_id': receiver_id,
                'organization_id': conversation_data.organization_id,
                'subject': conversation_data.subject,
                'content': conversation_data.initial_message,
                'is_read': False,
                'sent_at': now,
                'created_at': now,
                'updated_at': now
            }
            
            supabase.from_('messages').insert(msg_data).execute()
        
        # Update conversation last_message_at
        supabase.from_('conversations') \
            .update({
                'last_message_at': now,
                'updated_at': now
            }) \
            .eq('id', conversation_id) \
            .execute()
        
        # Get the full conversation
        return await get_conversation(conversation_id, current_user, supabase)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error starting conversation: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start conversation: {str(e)}"
        )


@router.put("/conversations/{conversation_id}/close", response_model=Dict[str, Any])
async def close_conversation(
    conversation_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Close a conversation."""
    try:
        # Check if user is part of this conversation
        msg_check = supabase.from_('messages') \
            .select('id') \
            .eq('conversation_id', conversation_id) \
            .or_(f'sender_id.eq.{current_user.id},receiver_id.eq.{current_user.id}') \
            .limit(1) \
            .execute()
        
        if not msg_check.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this conversation"
            )
        
        # Get conversation
        result = supabase.from_('conversations') \
            .select('id, status') \
            .eq('id', conversation_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        if result.data['status'] == 'closed':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conversation is already closed"
            )
        
        now = datetime.utcnow().isoformat()
        
        # Close conversation
        update_result = supabase.from_('conversations') \
            .update({
                'status': 'closed',
                'closed_by': current_user.id,
                'closed_at': now,
                'updated_at': now
            }) \
            .eq('id', conversation_id) \
            .execute()
        
        if not update_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to close conversation"
            )
        
        return {
            "success": True,
            "message": "Conversation closed successfully",
            "conversation_id": conversation_id,
            "closed_by": current_user.id,
            "closed_at": now
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error closing conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to close conversation: {str(e)}"
        )


@router.put("/conversations/{conversation_id}/archive", response_model=Dict[str, Any])
async def archive_conversation(
    conversation_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Archive a conversation."""
    try:
        # Check if user is part of this conversation
        msg_check = supabase.from_('messages') \
            .select('id') \
            .eq('conversation_id', conversation_id) \
            .or_(f'sender_id.eq.{current_user.id},receiver_id.eq.{current_user.id}') \
            .limit(1) \
            .execute()
        
        if not msg_check.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this conversation"
            )
        
        # Get conversation
        result = supabase.from_('conversations') \
            .select('id, status') \
            .eq('id', conversation_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        if result.data['status'] == 'archived':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conversation is already archived"
            )
        
        now = datetime.utcnow().isoformat()
        
        # Archive conversation
        update_result = supabase.from_('conversations') \
            .update({
                'status': 'archived',
                'updated_at': now
            }) \
            .eq('id', conversation_id) \
            .execute()
        
        if not update_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to archive conversation"
            )
        
        return {
            "success": True,
            "message": "Conversation archived successfully",
            "conversation_id": conversation_id,
            "archived_at": now
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error archiving conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to archive conversation: {str(e)}"
        )


# ================================
# NOTIFICATIONS ENDPOINTS
# ================================

@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    current_user: AuthUser = Depends(require_org_member()),
    include_read: bool = Query(False, description="Include read notifications"),
    limit: int = Query(20, ge=1, le=100, description="Number of notifications to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    supabase: Client = Depends(get_supabase_client)
):
    """Get notifications for the current user."""
    try:
        # Build query
        query = supabase.from_('notifications') \
            .select('''
                id, user_id, organization_id, type, title, message,
                link, is_read, read_at, priority, created_at
            ''') \
            .eq('user_id', current_user.id)
        
        if not include_read:
            query = query.eq('is_read', False)
        
        result = query.order('created_at', desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        notifications = result.data or []
        
        return [
            NotificationResponse(
                id=n['id'],
                user_id=n['user_id'],
                organization_id=n.get('organization_id'),
                type=n.get('type', 'info'),
                title=n['title'],
                message=n['message'],
                link=n.get('link'),
                is_read=n.get('is_read', False),
                read_at=n.get('read_at'),
                priority=n.get('priority', 'normal'),
                created_at=n['created_at']
            )
            for n in notifications
        ]
        
    except Exception as e:
        print(f"❌ Error getting notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notifications: {str(e)}"
        )


@router.get("/notifications/unread")
async def get_unread_notification_count(
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get count of unread notifications for the current user."""
    try:
        result = supabase.from_('notifications') \
            .select('id', count='exact') \
            .eq('user_id', current_user.id) \
            .eq('is_read', False) \
            .execute()
        
        unread_count = result.count if hasattr(result, 'count') else 0
        
        return {
            "unread_count": unread_count,
            "user_id": current_user.id
        }
        
    except Exception as e:
        print(f"❌ Error getting unread notification count: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get unread notification count: {str(e)}"
        )


@router.put("/notifications/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Mark a notification as read."""
    try:
        # Get notification
        result = supabase.from_('notifications') \
            .select('id, user_id, is_read') \
            .eq('id', notification_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        notif = result.data
        
        # Verify user owns the notification
        if notif['user_id'] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to mark this notification as read"
            )
        
        if notif['is_read']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Notification is already read"
            )
        
        now = datetime.utcnow().isoformat()
        
        # Update notification
        update_result = supabase.from_('notifications') \
            .update({
                'is_read': True,
                'read_at': now,
                'updated_at': now
            }) \
            .eq('id', notification_id) \
            .execute()
        
        if not update_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to mark notification as read"
            )
        
        # Get updated notification
        return (await get_notifications(current_user, False, 1, 0, supabase))[0]
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error marking notification read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark notification as read: {str(e)}"
        )


@router.put("/notifications/mark-all-read", response_model=MarkAllReadResponse)
async def mark_all_notifications_read(
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Mark all notifications as read for the current user."""
    try:
        now = datetime.utcnow().isoformat()
        
        # Update all unread notifications
        result = supabase.from_('notifications') \
            .update({
                'is_read': True,
                'read_at': now,
                'updated_at': now
            }) \
            .eq('user_id', current_user.id) \
            .eq('is_read', False) \
            .execute()
        
        updated_count = len(result.data) if result.data else 0
        
        return MarkAllReadResponse(
            success=True,
            message=f"Marked {updated_count} notifications as read",
            updated_count=updated_count
        )
        
    except Exception as e:
        print(f"❌ Error marking all notifications read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark all notifications as read: {str(e)}"
        )


# ================================
# ADDITIONAL HELPER ENDPOINTS
# ================================

@router.get("/unread/messages")
async def get_unread_message_count(
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get count of unread messages for the current user."""
    try:
        result = supabase.from_('messages') \
            .select('id', count='exact') \
            .eq('receiver_id', current_user.id) \
            .eq('is_read', False) \
            .execute()
        
        unread_count = result.count if hasattr(result, 'count') else 0
        
        return {
            "unread_count": unread_count,
            "user_id": current_user.id
        }
        
    except Exception as e:
        print(f"❌ Error getting unread message count: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get unread message count: {str(e)}"
        )
# ================================
# ADDITIONAL PYDANTIC MODELS
# ================================

class AttachmentCreate(BaseModel):
    """Request model for creating a message attachment."""
    file_url: str = Field(..., description="URL to the attached file")
    file_name: str = Field(..., description="Name of the attached file")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type of the file")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class AttachmentResponse(BaseModel):
    """Response model for message attachment."""
    id: str
    message_id: str
    file_url: str
    file_name: str
    file_size: Optional[int]
    mime_type: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    created_by: Optional[str]
    created_by_name: Optional[str]


class ParticipantCreate(BaseModel):
    """Request model for adding conversation participants."""
    user_ids: List[str] = Field(..., description="List of user IDs to add")


class ParticipantRemove(BaseModel):
    """Request model for removing conversation participants."""
    user_ids: List[str] = Field(..., description="List of user IDs to remove")


class ParticipantResponse(BaseModel):
    """Response model for conversation participant."""
    user_id: str
    user_name: Optional[str]
    user_email: Optional[str]
    role: Optional[str]
    joined_at: Optional[datetime]


class MessageSearchResponse(BaseModel):
    """Response model for message search."""
    messages: List[MessageResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ReplyCreate(BaseModel):
    """Request model for creating a reply."""
    content: str = Field(..., description="Reply content")
    receiver_id: str = Field(..., description="ID of the receiver")

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        if len(v) > 10000:
            raise ValueError("Content exceeds maximum length of 10000 characters")
        return v.strip()


# ================================
# ATTACHMENTS ENDPOINTS
# ================================

@router.post("/messages/{message_id}/attachments", response_model=AttachmentResponse)
async def add_message_attachment(
    message_id: str,
    attachment_data: AttachmentCreate,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Add an attachment to a message."""
    try:
        # Get message and verify access
        msg_result = supabase.from_('messages') \
            .select('id, sender_id, receiver_id, organization_id') \
            .eq('id', message_id) \
            .maybe_single() \
            .execute()
        
        if not msg_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        msg = msg_result.data
        
        # Verify user is sender or receiver
        if msg['sender_id'] != current_user.id and msg['receiver_id'] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this message"
            )
        
        now = datetime.utcnow().isoformat()
        
        # Get current message metadata
        metadata_result = supabase.from_('messages') \
            .select('metadata') \
            .eq('id', message_id) \
            .maybe_single() \
            .execute()
        
        metadata = metadata_result.data.get('metadata', {}) if metadata_result.data else {}
        
        if 'attachments' not in metadata:
            metadata['attachments'] = []
        
        # Create attachment
        attachment = {
            'id': str(uuid.uuid4()),
            'file_url': attachment_data.file_url,
            'file_name': attachment_data.file_name,
            'file_size': attachment_data.file_size,
            'mime_type': attachment_data.mime_type,
            'metadata': attachment_data.metadata,
            'created_by': current_user.id,
            'created_at': now
        }
        
        metadata['attachments'].append(attachment)
        
        # Update message
        update_result = supabase.from_('messages') \
            .update({
                'metadata': metadata,
                'updated_at': now
            }) \
            .eq('id', message_id) \
            .execute()
        
        if not update_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add attachment"
            )
        
        # Get user details
        created_by_name = None
        user_result = supabase.from_('auth.users') \
            .select('email, raw_user_meta_data') \
            .eq('id', current_user.id) \
            .maybe_single() \
            .execute()
        
        if user_result.data:
            raw_meta = user_result.data.get('raw_user_meta_data', {})
            created_by_name = raw_meta.get('full_name') or raw_meta.get('name') or user_result.data.get('email')
        
        return AttachmentResponse(
            id=attachment['id'],
            message_id=message_id,
            file_url=attachment['file_url'],
            file_name=attachment['file_name'],
            file_size=attachment.get('file_size'),
            mime_type=attachment.get('mime_type'),
            metadata=attachment.get('metadata'),
            created_at=datetime.fromisoformat(attachment['created_at']),
            created_by=current_user.id,
            created_by_name=created_by_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error adding attachment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add attachment: {str(e)}"
        )


@router.get("/messages/{message_id}/attachments", response_model=List[AttachmentResponse])
async def get_message_attachments(
    message_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get all attachments for a message."""
    try:
        # Get message and verify access
        msg_result = supabase.from_('messages') \
            .select('id, sender_id, receiver_id, metadata') \
            .eq('id', message_id) \
            .maybe_single() \
            .execute()
        
        if not msg_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        msg = msg_result.data
        
        # Verify user is sender or receiver
        if msg['sender_id'] != current_user.id and msg['receiver_id'] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this message"
            )
        
        metadata = msg.get('metadata', {})
        attachments = metadata.get('attachments', [])
        
        # Enrich with user details
        enriched_attachments = []
        for att in attachments:
            created_by_name = None
            if att.get('created_by'):
                user_result = supabase.from_('auth.users') \
                    .select('email, raw_user_meta_data') \
                    .eq('id', att['created_by']) \
                    .maybe_single() \
                    .execute()
                
                if user_result.data:
                    raw_meta = user_result.data.get('raw_user_meta_data', {})
                    created_by_name = raw_meta.get('full_name') or raw_meta.get('name') or user_result.data.get('email')
            
            enriched_attachments.append(AttachmentResponse(
                id=att['id'],
                message_id=message_id,
                file_url=att['file_url'],
                file_name=att['file_name'],
                file_size=att.get('file_size'),
                mime_type=att.get('mime_type'),
                metadata=att.get('metadata'),
                created_at=datetime.fromisoformat(att['created_at']) if att.get('created_at') else datetime.utcnow(),
                created_by=att.get('created_by'),
                created_by_name=created_by_name
            ))
        
        return enriched_attachments
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting attachments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get attachments: {str(e)}"
        )


# ================================
# CONVERSATION PARTICIPANTS ENDPOINTS
# ================================

@router.get("/conversations/{conversation_id}/participants", response_model=List[ParticipantResponse])
async def get_conversation_participants(
    conversation_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get all participants in a conversation."""
    try:
        # Verify user has access to conversation
        msg_check = supabase.from_('messages') \
            .select('id') \
            .eq('conversation_id', conversation_id) \
            .or_(f'sender_id.eq.{current_user.id},receiver_id.eq.{current_user.id}') \
            .limit(1) \
            .execute()
        
        if not msg_check.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this conversation"
            )
        
        # Get all messages in conversation to find participants
        messages_result = supabase.from_('messages') \
            .select('sender_id, receiver_id, created_at') \
            .eq('conversation_id', conversation_id) \
            .order('created_at', asc=True) \
            .execute()
        
        if not messages_result.data:
            return []
        
        # Build unique participant list with join times
        participants = {}
        for msg in messages_result.data:
            # Add sender
            if msg['sender_id'] not in participants:
                participants[msg['sender_id']] = {
                    'user_id': msg['sender_id'],
                    'joined_at': msg['created_at']
                }
            
            # Add receiver
            if msg['receiver_id'] not in participants:
                participants[msg['receiver_id']] = {
                    'user_id': msg['receiver_id'],
                    'joined_at': msg['created_at']
                }
        
        # Enrich with user details
        enriched_participants = []
        for user_id, data in participants.items():
            user_result = supabase.from_('auth.users') \
                .select('email, raw_user_meta_data') \
                .eq('id', user_id) \
                .maybe_single() \
                .execute()
            
            user_name = None
            user_email = None
            if user_result.data:
                user_email = user_result.data.get('email')
                raw_meta = user_result.data.get('raw_user_meta_data', {})
                user_name = raw_meta.get('full_name') or raw_meta.get('name') or user_email
            
            # Check if user is staff
            role = 'member'
            staff_check = supabase.from_('staff_profiles') \
                .select('id') \
                .eq('user_id', user_id) \
                .maybe_single() \
                .execute()
            
            if staff_check.data:
                role = 'staff'
            
            enriched_participants.append(ParticipantResponse(
                user_id=user_id,
                user_name=user_name,
                user_email=user_email,
                role=role,
                joined_at=data['joined_at']
            ))
        
        return enriched_participants
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting participants: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get participants: {str(e)}"
        )


@router.put("/conversations/{conversation_id}/participants")
async def update_conversation_participants(
    conversation_id: str,
    add_participants: Optional[ParticipantCreate] = None,
    remove_participants: Optional[ParticipantRemove] = None,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Add or remove participants from a conversation."""
    try:
        # Verify user has access to conversation
        msg_check = supabase.from_('messages') \
            .select('id') \
            .eq('conversation_id', conversation_id) \
            .eq('sender_id', current_user.id) \
            .limit(1) \
            .execute()
        
        if not msg_check.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the conversation creator can manage participants"
            )
        
        # Get conversation details
        conv_result = supabase.from_('conversations') \
            .select('organization_id') \
            .eq('id', conversation_id) \
            .maybe_single() \
            .execute()
        
        if not conv_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        org_id = conv_result.data['organization_id']
        now = datetime.utcnow().isoformat()
        
        added = []
        removed = []
        errors = []
        
        # Add participants
        if add_participants:
            for user_id in add_participants.user_ids:
                # Verify user belongs to organization
                member_check = supabase.from_('organization_members') \
                    .select('id') \
                    .eq('organization_id', org_id) \
                    .eq('user_id', user_id) \
                    .maybe_single() \
                    .execute()
                
                if not member_check.data:
                    errors.append({
                        'user_id': user_id,
                        'error': 'User not found in organization'
                    })
                    continue
                
                # Create a system message for adding participant
                msg_data = {
                    'conversation_id': conversation_id,
                    'sender_id': current_user.id,
                    'receiver_id': user_id,
                    'organization_id': org_id,
                    'subject': 'Added to conversation',
                    'content': f"Added to conversation: {conv_result.data.get('subject', 'Untitled')}",
                    'is_read': False,
                    'sent_at': now,
                    'created_at': now,
                    'updated_at': now
                }
                
                result = supabase.from_('messages') \
                    .insert(msg_data) \
                    .execute()
                
                if result.data:
                    added.append(user_id)
                else:
                    errors.append({
                        'user_id': user_id,
                        'error': 'Failed to add participant'
                    })
        
        # Remove participants
        if remove_participants:
            for user_id in remove_participants.user_ids:
                # Don't remove the creator
                if user_id == current_user.id:
                    errors.append({
                        'user_id': user_id,
                        'error': 'Cannot remove conversation creator'
                    })
                    continue
                
                # Soft delete messages for this participant
                # Mark messages as archived for this user
                result = supabase.from_('messages') \
                    .update({
                        'is_archived': True,
                        'archived_at': now,
                        'updated_at': now
                    }) \
                    .eq('conversation_id', conversation_id) \
                    .eq('receiver_id', user_id) \
                    .execute()
                
                removed.append(user_id)
        
        return {
            "success": True,
            "message": "Participants updated successfully",
            "conversation_id": conversation_id,
            "added": added,
            "removed": removed,
            "errors": errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating participants: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update participants: {str(e)}"
        )


# ================================
# MESSAGE SEARCH ENDPOINT
# ================================

@router.get("/messages/search", response_model=MessageSearchResponse)
async def search_messages(
    q: str = Query(..., description="Search query"),
    conversation_id: Optional[str] = Query(None, description="Filter by conversation"),
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Search messages by content or subject."""
    try:
        # Build query
        query = supabase.from_('messages') \
            .select('''
                id, conversation_id, sender_id, receiver_id, organization_id,
                subject, content, is_read, sent_at, delivered_at, read_at,
                created_at
            ''') \
            .or_(f'sender_id.eq.{current_user.id},receiver_id.eq.{current_user.id}')
        
        # Search in content or subject
        query = query.ilike('content', f'%{q}%')
        
        if conversation_id:
            query = query.eq('conversation_id', conversation_id)
        
        if organization_id:
            query = query.eq('organization_id', organization_id)
        
        if start_date:
            query = query.gte('created_at', start_date.isoformat())
        
        if end_date:
            query = query.lte('created_at', end_date.isoformat())
        
        # Get total count
        count_query = supabase.from_('messages') \
            .select('id', count='exact') \
            .or_(f'sender_id.eq.{current_user.id},receiver_id.eq.{current_user.id}') \
            .ilike('content', f'%{q}%')
        
        if conversation_id:
            count_query = count_query.eq('conversation_id', conversation_id)
        if organization_id:
            count_query = count_query.eq('organization_id', organization_id)
        if start_date:
            count_query = count_query.gte('created_at', start_date.isoformat())
        if end_date:
            count_query = count_query.lte('created_at', end_date.isoformat())
        
        count_result = count_query.execute()
        total = count_result.count if hasattr(count_result, 'count') else 0
        
        # Get paginated results
        offset = (page - 1) * page_size
        result = query.order('created_at', desc=True) \
            .range(offset, offset + page_size - 1) \
            .execute()
        
        messages = result.data or []
        
        # Enrich with user details
        message_responses = []
        for msg in messages:
            # Get sender details
            sender_result = supabase.from_('auth.users') \
                .select('email, raw_user_meta_data') \
                .eq('id', msg['sender_id']) \
                .maybe_single() \
                .execute()
            
            # Get receiver details
            receiver_result = supabase.from_('auth.users') \
                .select('email, raw_user_meta_data') \
                .eq('id', msg['receiver_id']) \
                .maybe_single() \
                .execute()
            
            sender_name = None
            sender_email = None
            if sender_result.data:
                raw_meta = sender_result.data.get('raw_user_meta_data', {})
                sender_name = raw_meta.get('full_name') or raw_meta.get('name') or sender_result.data.get('email')
                sender_email = sender_result.data.get('email')
            
            receiver_name = None
            receiver_email = None
            if receiver_result.data:
                raw_meta = receiver_result.data.get('raw_user_meta_data', {})
                receiver_name = raw_meta.get('full_name') or raw_meta.get('name') or receiver_result.data.get('email')
                receiver_email = receiver_result.data.get('email')
            
            message_responses.append(MessageResponse(
                id=msg['id'],
                conversation_id=msg.get('conversation_id'),
                sender_id=msg['sender_id'],
                receiver_id=msg['receiver_id'],
                organization_id=msg['organization_id'],
                subject=msg.get('subject'),
                content=msg['content'],
                is_read=msg.get('is_read', False),
                sent_at=msg.get('sent_at'),
                delivered_at=msg.get('delivered_at'),
                read_at=msg.get('read_at'),
                created_at=msg['created_at'],
                sender_name=sender_name,
                sender_email=sender_email,
                receiver_name=receiver_name,
                receiver_email=receiver_email
            ))
        
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        return MessageSearchResponse(
            messages=message_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        print(f"❌ Error searching messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search messages: {str(e)}"
        )


# ================================
# MESSAGE REPLIES ENDPOINTS
# ================================

@router.get("/messages/{message_id}/replies", response_model=List[MessageResponse])
async def get_message_replies(
    message_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get all replies to a message."""
    try:
        # Get parent message and verify access
        parent_result = supabase.from_('messages') \
            .select('id, sender_id, receiver_id, conversation_id') \
            .eq('id', message_id) \
            .maybe_single() \
            .execute()
        
        if not parent_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        parent = parent_result.data
        
        # Verify user has access to parent message
        if parent['sender_id'] != current_user.id and parent['receiver_id'] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this message"
            )
        
        # Get replies (messages with parent_message_id)
        result = supabase.from_('messages') \
            .select('''
                id, conversation_id, sender_id, receiver_id, organization_id,
                subject, content, is_read, sent_at, delivered_at, read_at,
                created_at
            ''') \
            .eq('parent_message_id', message_id) \
            .order('created_at', asc=True) \
            .execute()
        
        replies = result.data or []
        
        # Enrich with user details
        reply_responses = []
        for msg in replies:
            sender_result = supabase.from_('auth.users') \
                .select('email, raw_user_meta_data') \
                .eq('id', msg['sender_id']) \
                .maybe_single() \
                .execute()
            
            receiver_result = supabase.from_('auth.users') \
                .select('email, raw_user_meta_data') \
                .eq('id', msg['receiver_id']) \
                .maybe_single() \
                .execute()
            
            sender_name = None
            sender_email = None
            if sender_result.data:
                raw_meta = sender_result.data.get('raw_user_meta_data', {})
                sender_name = raw_meta.get('full_name') or raw_meta.get('name') or sender_result.data.get('email')
                sender_email = sender_result.data.get('email')
            
            receiver_name = None
            receiver_email = None
            if receiver_result.data:
                raw_meta = receiver_result.data.get('raw_user_meta_data', {})
                receiver_name = raw_meta.get('full_name') or raw_meta.get('name') or receiver_result.data.get('email')
                receiver_email = receiver_result.data.get('email')
            
            reply_responses.append(MessageResponse(
                id=msg['id'],
                conversation_id=msg.get('conversation_id'),
                sender_id=msg['sender_id'],
                receiver_id=msg['receiver_id'],
                organization_id=msg['organization_id'],
                subject=msg.get('subject'),
                content=msg['content'],
                is_read=msg.get('is_read', False),
                sent_at=msg.get('sent_at'),
                delivered_at=msg.get('delivered_at'),
                read_at=msg.get('read_at'),
                created_at=msg['created_at'],
                sender_name=sender_name,
                sender_email=sender_email,
                receiver_name=receiver_name,
                receiver_email=receiver_email
            ))
        
        return reply_responses
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting replies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get replies: {str(e)}"
        )


@router.post("/messages/{message_id}/reply", response_model=MessageResponse)
async def reply_to_message(
    message_id: str,
    reply_data: ReplyCreate,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Reply to a message."""
    try:
        # Get parent message
        parent_result = supabase.from_('messages') \
            .select('id, sender_id, receiver_id, conversation_id, organization_id, subject') \
            .eq('id', message_id) \
            .maybe_single() \
            .execute()
        
        if not parent_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        parent = parent_result.data
        
        # Verify user has access to parent message
        if parent['sender_id'] != current_user.id and parent['receiver_id'] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this message"
            )
        
        # Verify receiver is valid
        if reply_data.receiver_id != parent['sender_id'] and reply_data.receiver_id != parent['receiver_id']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reply receiver must be one of the original participants"
            )
        
        now = datetime.utcnow().isoformat()
        
        # Create reply
        msg_data = {
            'conversation_id': parent['conversation_id'],
            'sender_id': current_user.id,
            'receiver_id': reply_data.receiver_id,
            'organization_id': parent['organization_id'],
            'subject': f"Re: {parent.get('subject', 'Message')}",
            'content': reply_data.content,
            'parent_message_id': message_id,
            'is_read': False,
            'sent_at': now,
            'created_at': now,
            'updated_at': now
        }
        
        result = supabase.from_('messages') \
            .insert(msg_data) \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send reply"
            )
        
        reply = result.data[0]
        
        # Update conversation last_message_at
        supabase.from_('conversations') \
            .update({
                'last_message_at': now,
                'updated_at': now
            }) \
            .eq('id', parent['conversation_id']) \
            .execute()
        
        # Get sender and receiver details
        sender_result = supabase.from_('auth.users') \
            .select('email, raw_user_meta_data') \
            .eq('id', current_user.id) \
            .maybe_single() \
            .execute()
        
        receiver_result = supabase.from_('auth.users') \
            .select('email, raw_user_meta_data') \
            .eq('id', reply_data.receiver_id) \
            .maybe_single() \
            .execute()
        
        sender_name = None
        sender_email = None
        if sender_result.data:
            raw_meta = sender_result.data.get('raw_user_meta_data', {})
            sender_name = raw_meta.get('full_name') or raw_meta.get('name') or sender_result.data.get('email')
            sender_email = sender_result.data.get('email')
        
        receiver_name = None
        receiver_email = None
        if receiver_result.data:
            raw_meta = receiver_result.data.get('raw_user_meta_data', {})
            receiver_name = raw_meta.get('full_name') or raw_meta.get('name') or receiver_result.data.get('email')
            receiver_email = receiver_result.data.get('email')
        
        return MessageResponse(
            id=reply['id'],
            conversation_id=reply.get('conversation_id'),
            sender_id=reply['sender_id'],
            receiver_id=reply['receiver_id'],
            organization_id=reply['organization_id'],
            subject=reply.get('subject'),
            content=reply['content'],
            is_read=reply.get('is_read', False),
            sent_at=reply.get('sent_at'),
            delivered_at=reply.get('delivered_at'),
            read_at=reply.get('read_at'),
            created_at=reply['created_at'],
            sender_name=sender_name,
            sender_email=sender_email,
            receiver_name=receiver_name,
            receiver_email=receiver_email
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error sending reply: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send reply: {str(e)}"
        )