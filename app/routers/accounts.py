from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from .. import schemas, crud, auth, dependencies
from ..database import SessionLocal
import re

router = APIRouter(prefix="/accounts", tags=["accounts"])

def validate_password(password: str):
    if (len(password) < 8 or
        not re.search(r"[A-Z]", password) or
        not re.search(r"[a-z]", password) or
        not re.search(r"[0-9]", password) or
        not re.search(r"[^A-Za-z0-9]", password)):
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long and include an uppercase letter, a lowercase letter, a digit, and a special character.")

@router.post("/", response_model=schemas.UserResponse)
def create_account(user: schemas.UserCreate, db: Session = Depends(dependencies.get_db)):
    validate_password(user.password)
    db_user = crud.get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db, user)

@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(dependencies.get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = auth.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.put("/", response_model=schemas.UserResponse)
def update_account(user_update: schemas.UserUpdate = Body(...), current_user: schemas.UserResponse = Depends(auth.get_current_user), db: Session = Depends(dependencies.get_db)):
    if user_update.password:
        validate_password(user_update.password)
    user = crud.get_user(db, current_user.id)
    return crud.update_user(db, user, user_update)

@router.delete("/", status_code=200)
def delete_account(current_user: schemas.UserResponse = Depends(auth.get_current_user), db: Session = Depends(dependencies.get_db)):
    user = crud.get_user(db, current_user.id)
    result = crud.delete_user(db, user)
    return result

@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: schemas.UserResponse = Depends(auth.get_current_user)):
    return current_user

@router.get("/me/stats")
def get_my_stats(current_user: schemas.UserResponse = Depends(auth.get_current_user), db: Session = Depends(dependencies.get_db)):
    """Get current user's statistics including posts and likes count"""
    posts_count = crud.get_user_posts_count(db, current_user.id)
    likes_count = crud.get_user_likes_count(db, current_user.id)
    
    return {
        "user_id": current_user.id,
        "user_name": current_user.name,
        "user_email": current_user.email,
        "posts_count": posts_count,
        "likes_count": likes_count,
        "total_impact": posts_count + likes_count
    } 