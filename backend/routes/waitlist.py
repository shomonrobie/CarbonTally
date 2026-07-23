# backend/routes/waitlist.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from ..services.email_service import send_beta_confirmation_email
from ..services.supabase_client import get_supabase_client

router = APIRouter()

class WaitlistRequest(BaseModel):
    email: str
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    company_size: Optional[str] = None
    interested_in: Optional[str] = None
    source: Optional[str] = "landing_page"

@router.post("/api/waitlist")
async def add_to_waitlist(request: WaitlistRequest):
    try:
        supabase = get_supabase_client()
        
        # Check if email already exists
        existing = supabase.from_('waitlist')\
            .select('email, status')\
            .eq('email', request.email)\
            .execute()
        
        if existing.data:
            return {
                "success": False,
                "error": "Already on waitlist",
                "status": existing.data[0]['status']
            }
        
        # Add to waitlist
        result = supabase.from_('waitlist').insert({
            'email': request.email.strip(),
            'full_name': request.full_name,
            'company_name': request.company_name,
            'company_size': request.company_size,
            'interested_in': request.interested_in,
            'source': request.source,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }).execute()
        
        # Send confirmation email
        email_sent = send_beta_confirmation_email(
            request.email.strip(),
            request.full_name
        )
        
        return {
            "success": True,
            "message": "Added to waitlist",
            "data": result.data[0] if result.data else None,
            "email_sent": email_sent
        }
        
    except Exception as e:
        print(f"Waitlist error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/waitlist/invite")
async def invite_beta_user(email: str, beta_code: str):
    try:
        supabase = get_supabase_client()
        
        # Get waitlist entry
        waitlist_entry = supabase.from_('waitlist')\
            .select('*')\
            .eq('email', email)\
            .execute()
        
        if not waitlist_entry.data:
            raise HTTPException(status_code=404, detail="Email not found in waitlist")
        
        # Update waitlist status
        supabase.from_('waitlist')\
            .update({
                'status': 'invited',
                'invited_at': datetime.now().isoformat()
            })\
            .eq('email', email)\
            .execute()
        
        # Send beta invite email
        email_sent = send_beta_invite_email(
            email,
            beta_code,
            waitlist_entry.data[0].get('full_name')
        )
        
        return {
            "success": True,
            "message": "Beta invite sent",
            "email_sent": email_sent
        }
        
    except Exception as e:
        print(f"Invite error: {e}")
        raise HTTPException(status_code=500, detail=str(e))