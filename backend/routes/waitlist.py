from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from datetime import datetime
from database import get_supabase_client

router = APIRouter(prefix="/api/waitlist", tags=["Waitlist"])

class WaitlistRequest(BaseModel):
    email: EmailStr
    full_name: str | None = None
    company_name: str | None = None
    company_size: str | None = None
    interested_in: str | None = None
    source: str = "landing_page"

@router.post("/")
async def add_to_waitlist(request: WaitlistRequest):
    # Your existing waitlist logic here
    pass

@router.get("/")
async def get_waitlist(limit: int = 100):
    # Your existing get waitlist logic here
    pass