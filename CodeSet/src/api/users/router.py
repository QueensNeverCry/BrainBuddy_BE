from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter()

@router.post("/sign-up")
def 