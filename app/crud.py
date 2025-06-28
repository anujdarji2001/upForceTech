from sqlalchemy.orm import Session
from . import models, schemas
from passlib.context import CryptContext
from typing import Optional

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(name=user.name, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()

def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()

def update_user(db: Session, user: models.User, user_update: schemas.UserUpdate):
    if user_update.name:
        user.name = user_update.name
    if user_update.password:
        user.hashed_password = get_password_hash(user_update.password)
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user: models.User):
    # Get count of likes before deletion for logging/debugging
    likes_count = len(user.likes)
    posts_count = len(user.posts)
    
    # Delete user (cascade will handle posts and likes automatically)
    db.delete(user)
    db.commit()
    
    return {
        "message": f"User deleted successfully. Removed {posts_count} posts and {likes_count} likes.",
        "posts_deleted": posts_count,
        "likes_deleted": likes_count
    }

def get_user_likes_count(db: Session, user_id: int) -> int:
    """Get the number of likes given by a user"""
    return db.query(models.Like).filter(models.Like.user_id == user_id).count()

def get_user_posts_count(db: Session, user_id: int) -> int:
    """Get the number of posts created by a user"""
    return db.query(models.Post).filter(models.Post.owner_id == user_id).count()

def create_post(db: Session, post: schemas.PostCreate, user_id: int):
    db_post = models.Post(**post.model_dump(), owner_id=user_id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

def get_post(db: Session, post_id: int) -> Optional[models.Post]:
    return db.query(models.Post).filter(models.Post.id == post_id).first()

def get_posts(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Post).offset(skip).limit(limit).all()

def update_post(db: Session, post: models.Post, post_update: schemas.PostUpdate):
    for field, value in post_update.model_dump(exclude_unset=True).items():
        setattr(post, field, value)
    db.commit()
    db.refresh(post)
    return post

def delete_post(db: Session, post: models.Post):
    db.delete(post)
    db.commit()

def create_like(db: Session, user_id: int, post_id: int):
    db_like = models.Like(user_id=user_id, post_id=post_id)
    db.add(db_like)
    db.commit()
    db.refresh(db_like)
    return db_like

def get_like(db: Session, user_id: int, post_id: int):
    return db.query(models.Like).filter(models.Like.user_id == user_id, models.Like.post_id == post_id).first()

def delete_like(db: Session, like: models.Like):
    db.delete(like)
    db.commit() 