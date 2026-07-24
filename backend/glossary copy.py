# backend/main.py - Glossary endpoints

from pydantic import BaseModel
from typing import Optional, List

class GlossaryTerm(BaseModel):
    term: str
    definition: str
    category: Optional[str] = None
    related_terms: Optional[List[str]] = None
    example: Optional[str] = None

@app.get("/api/glossary")
async def get_glossary(category: Optional[str] = None, search: Optional[str] = None):
    """Get all glossary terms with optional filtering"""
    try:
        if supabase is None:
            raise HTTPException(status_code=500, detail="Database not available")
        
        query = supabase.table("glossary").select("*").eq("is_active", True)
        
        if category:
            query = query.eq("category", category)
        
        if search:
            query = query.or_(f"term.ilike.%{search}%,definition.ilike.%{search}%")
        
        result = query.order("term", asc=True).execute()
        
        return {
            "success": True,
            "data": result.data,
            "count": len(result.data) if result.data else 0
        }
        
    except Exception as e:
        print(f"❌ Glossary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/glossary/{term_id}")
async def get_glossary_term(term_id: str):
    """Get a single glossary term by ID"""
    try:
        if supabase is None:
            raise HTTPException(status_code=500, detail="Database not available")
        
        result = supabase.table("glossary")\
            .select("*")\
            .eq("id", term_id)\
            .eq("is_active", True)\
            .single()\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Term not found")
        
        return {
            "success": True,
            "data": result.data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Glossary term error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/glossary")
async def create_glossary_term(term: GlossaryTerm):
    """Create a new glossary term (admin only)"""
    try:
        if supabase is None:
            raise HTTPException(status_code=500, detail="Database not available")
        
        # Check if term already exists
        existing = supabase.table("glossary")\
            .select("term")\
            .eq("term", term.term)\
            .maybe_single()\
            .execute()
        
        if existing.data:
            raise HTTPException(status_code=409, detail="Term already exists")
        
        result = supabase.table("glossary").insert({
            "term": term.term,
            "definition": term.definition,
            "category": term.category,
            "related_terms": term.related_terms,
            "example": term.example,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }).execute()
        
        return {
            "success": True,
            "message": "Term created successfully",
            "data": result.data[0] if result.data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Create glossary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/glossary/{term_id}")
async def update_glossary_term(term_id: str, term: GlossaryTerm):
    """Update a glossary term (admin only)"""
    try:
        if supabase is None:
            raise HTTPException(status_code=500, detail="Database not available")
        
        result = supabase.table("glossary")\
            .update({
                "term": term.term,
                "definition": term.definition,
                "category": term.category,
                "related_terms": term.related_terms,
                "example": term.example,
                "updated_at": datetime.now().isoformat()
            })\
            .eq("id", term_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Term not found")
        
        return {
            "success": True,
            "message": "Term updated successfully",
            "data": result.data[0] if result.data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Update glossary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/glossary/{term_id}")
async def delete_glossary_term(term_id: str):
    """Soft delete a glossary term (admin only)"""
    try:
        if supabase is None:
            raise HTTPException(status_code=500, detail="Database not available")
        
        result = supabase.table("glossary")\
            .update({
                "is_active": False,
                "updated_at": datetime.now().isoformat()
            })\
            .eq("id", term_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Term not found")
        
        return {
            "success": True,
            "message": "Term deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Delete glossary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))