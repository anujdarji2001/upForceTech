from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import schemas, crud, auth, dependencies

router = APIRouter(prefix="/like", tags=["like"])

@router.post("/{post_id}", response_model=schemas.LikeResponse)
def like_blog(post_id: int, current_user: schemas.UserResponse = Depends(auth.get_current_user), db: Session = Depends(dependencies.get_db)):
    post = crud.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    # Only allow like if post is public or owned by current user
    if not post.is_public and post.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to like this post")
    like = crud.get_like(db, current_user.id, post_id)
    if like:
        raise HTTPException(status_code=400, detail="Already liked")
    return crud.create_like(db, current_user.id, post_id)

@router.delete("/{post_id}", status_code=204)
def unlike_blog(post_id: int, current_user: schemas.UserResponse = Depends(auth.get_current_user), db: Session = Depends(dependencies.get_db)):
    like = crud.get_like(db, current_user.id, post_id)
    if not like:
        raise HTTPException(status_code=404, detail="Like not found")
    crud.delete_like(db, like)
    return 