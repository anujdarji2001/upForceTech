from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from .. import schemas, crud, auth, dependencies

router = APIRouter(prefix="/blog", tags=["blog"])

@router.post("/", response_model=schemas.PostResponse)
def create_blog(post: schemas.PostCreate, current_user: schemas.UserResponse = Depends(auth.get_current_user), db: Session = Depends(dependencies.get_db)):
    return crud.create_post(db, post, current_user.id)

@router.get("/", response_model=List[schemas.PostResponse])
def get_blogs(
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, gt=0), 
    current_user: schemas.UserResponse = Depends(auth.get_current_user), 
    db: Session = Depends(dependencies.get_db)
):
    all_posts = crud.get_posts(db, skip=skip, limit=limit)
    visible_posts = [
        post for post in all_posts
        if post.is_public or post.owner_id == current_user.id
    ]
    return visible_posts

@router.get("/{post_id}", response_model=schemas.PostWithLikes)
def get_blog(post_id: int, current_user: schemas.UserResponse = Depends(auth.get_current_user), db: Session = Depends(dependencies.get_db)):
    post = crud.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if not post.is_public and post.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this post")
    likes = post.likes
    post_data = {k: v for k, v in post.__dict__.items() if k != "likes"}
    return schemas.PostWithLikes(**post_data, likes=likes)

@router.put("/{post_id}", response_model=schemas.PostResponse)
def update_blog(post_id: int, post_update: schemas.PostUpdate, current_user: schemas.UserResponse = Depends(auth.get_current_user), db: Session = Depends(dependencies.get_db)):
    post = crud.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this post")
    return crud.update_post(db, post, post_update)

@router.delete("/{post_id}", status_code=204)
def delete_blog(post_id: int, current_user: schemas.UserResponse = Depends(auth.get_current_user), db: Session = Depends(dependencies.get_db)):
    post = crud.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")
    crud.delete_post(db, post)
    return 