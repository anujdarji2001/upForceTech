import pytest
from fastapi.testclient import TestClient
from app.tests.test_accounts import get_unique_email
from app.main import app
import uuid

client = TestClient(app)

def get_token(email, password):
    response = client.post("/accounts/login", data={"username": email, "password": password})
    return response.json()["access_token"]

def test_like_unlike():
    # Create two users
    user1 = {"name": "LikeUser1", "email": "likeuser1@example.com", "password": "Valid1!pass"}
    user2 = {"name": "LikeUser2", "email": "likeuser2@example.com", "password": "Valid2!pass"}
    client.post("/accounts/", json=user1)
    client.post("/accounts/", json=user2)
    token1 = get_token(user1["email"], user1["password"])
    token2 = get_token(user2["email"], user2["password"])
    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}
    # User1 creates public and private posts
    pub_post = {"title": "Like Public", "description": "desc", "content": "content", "is_public": True}
    priv_post = {"title": "Like Private", "description": "desc", "content": "content", "is_public": False}
    pub_id = client.post("/blog/", json=pub_post, headers=headers1).json()["id"]
    priv_id = client.post("/blog/", json=priv_post, headers=headers1).json()["id"]
    # User2 can like public post
    resp = client.post(f"/like/{pub_id}", headers=headers2)
    assert resp.status_code == 200
    # User2 cannot like private post of user1
    resp = client.post(f"/like/{priv_id}", headers=headers2)
    assert resp.status_code == 403 or resp.status_code == 404
    # User1 can like own private post
    resp = client.post(f"/like/{priv_id}", headers=headers1)
    assert resp.status_code == 200
    # Unlike
    resp = client.delete(f"/like/{pub_id}", headers=headers2)
    assert resp.status_code == 204
    resp = client.delete(f"/like/{priv_id}", headers=headers1)
    assert resp.status_code == 204
    # Clean up
    client.delete(f"/blog/{pub_id}", headers=headers1)
    client.delete(f"/blog/{priv_id}", headers=headers1)

def test_like_same_post_twice():
    user = {"name": "LikeTwice", "email": "liketwice@example.com", "password": "Valid3!pass"}
    client.post("/accounts/", json=user)
    token = get_token(user["email"], user["password"])
    headers = {"Authorization": f"Bearer {token}"}
    post = {"title": "LikeTwice", "content": "C", "is_public": True}
    post_id = client.post("/blog/", json=post, headers=headers).json()["id"]
    resp = client.post(f"/like/{post_id}", headers=headers)
    assert resp.status_code == 200
    resp = client.post(f"/like/{post_id}", headers=headers)
    assert resp.status_code == 400
    assert "Already liked" in resp.json()["detail"]
    # Clean up
    client.delete(f"/like/{post_id}", headers=headers)
    client.delete(f"/blog/{post_id}", headers=headers)

def test_unlike_not_liked():
    user = {"name": "UnlikeNotLiked", "email": "unlikenotliked@example.com", "password": "Valid4!pass"}
    client.post("/accounts/", json=user)
    token = get_token(user["email"], user["password"])
    headers = {"Authorization": f"Bearer {token}"}
    post = {"title": "UnlikeNotLiked", "content": "C", "is_public": True}
    post_id = client.post("/blog/", json=post, headers=headers).json()["id"]
    resp = client.delete(f"/like/{post_id}", headers=headers)
    assert resp.status_code == 404
    assert "Like not found" in resp.json()["detail"]
    # Clean up
    client.delete(f"/blog/{post_id}", headers=headers)

def test_unauthenticated_like_unlike():
    user = {"name": "UnauthLike", "email": "unauthlike@example.com", "password": "Valid5!pass"}
    client.post("/accounts/", json=user)
    token = get_token(user["email"], user["password"])
    headers = {"Authorization": f"Bearer {token}"}
    post = {"title": "UnauthLike", "content": "C", "is_public": True}
    post_id = client.post("/blog/", json=post, headers=headers).json()["id"]
    resp = client.post(f"/like/{post_id}")
    assert resp.status_code == 401
    resp = client.delete(f"/like/{post_id}")
    assert resp.status_code == 401
    # Clean up
    client.delete(f"/blog/{post_id}", headers=headers)

def test_like_nonexistent_post():
    user = {"name": "Like404", "email": "like404@example.com", "password": "Valid6!pass"}
    client.post("/accounts/", json=user)
    token = get_token(user["email"], user["password"])
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post(f"/like/999999", headers=headers)
    assert resp.status_code == 404

def test_like_private_post_owner():
    """Test that post owner can like their own private post"""
    # Create and login user
    email = get_unique_email()
    user = {"name": "Test User", "email": email, "password": "Valid1!pass"}
    client.post("/accounts/", json=user)
    
    login_response = client.post("/accounts/login", data={
        "username": email,
        "password": "Valid1!pass"
    })
    token = login_response.json()["access_token"]
    
    # Create a private post
    post_response = client.post("/blog/", 
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Private Post",
            "description": "Private Description",
            "content": "Private Content",
            "is_public": False
        }
    )
    assert post_response.status_code == 200
    post_id = post_response.json()["id"]
    
    # Like own private post
    like_response = client.post(f"/like/{post_id}", 
        headers={"Authorization": f"Bearer {token}"}
    )
    assert like_response.status_code == 200

def test_like_private_post_non_owner():
    """Test that non-owner cannot like private post"""
    # Create first user
    email1 = get_unique_email()
    user1 = {"name": "Test User 1", "email": email1, "password": "Valid1!pass"}
    client.post("/accounts/", json=user1)
    
    login1_response = client.post("/accounts/login", data={
        "username": email1,
        "password": "Valid1!pass"
    })
    token1 = login1_response.json()["access_token"]
    
    # Create a private post
    post_response = client.post("/blog/", 
        headers={"Authorization": f"Bearer {token1}"},
        json={
            "title": "Private Post",
            "description": "Private Description",
            "content": "Private Content",
            "is_public": False
        }
    )
    assert post_response.status_code == 200
    post_id = post_response.json()["id"]
    
    # Create second user
    email2 = get_unique_email()
    user2 = {"name": "Test User 2", "email": email2, "password": "Valid2!pass"}
    client.post("/accounts/", json=user2)
    
    login2_response = client.post("/accounts/login", data={
        "username": email2,
        "password": "Valid2!pass"
    })
    token2 = login2_response.json()["access_token"]
    
    # Try to like private post as non-owner
    like_response = client.post(f"/like/{post_id}", 
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert like_response.status_code == 403

def test_unlike_others_like():
    """Test that users cannot unlike others' likes"""
    # Create first user
    email1 = get_unique_email()
    user1 = {"name": "Test User 1", "email": email1, "password": "Valid1!pass"}
    client.post("/accounts/", json=user1)
    
    login1_response = client.post("/accounts/login", data={
        "username": email1,
        "password": "Valid1!pass"
    })
    token1 = login1_response.json()["access_token"]
    
    # Create a public post
    post_response = client.post("/blog/", 
        headers={"Authorization": f"Bearer {token1}"},
        json={
            "title": "Public Post",
            "description": "Public Description",
            "content": "Public Content",
            "is_public": True
        }
    )
    assert post_response.status_code == 200
    post_id = post_response.json()["id"]
    
    # Create second user
    email2 = get_unique_email()
    user2 = {"name": "Test User 2", "email": email2, "password": "Valid2!pass"}
    client.post("/accounts/", json=user2)
    
    login2_response = client.post("/accounts/login", data={
        "username": email2,
        "password": "Valid2!pass"
    })
    token2 = login2_response.json()["access_token"]
    
    # User 1 likes the post
    like1_response = client.post(f"/like/{post_id}", 
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert like1_response.status_code == 200
    
    # User 2 tries to unlike user 1's like
    unlike_response = client.delete(f"/like/{post_id}", 
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert unlike_response.status_code == 404

def test_unlike_nonexistent_post():
    """Test that unliking a nonexistent post returns 404"""
    # Create and login user
    email = get_unique_email()
    user = {"name": "Test User", "email": email, "password": "Valid1!pass"}
    client.post("/accounts/", json=user)
    
    login_response = client.post("/accounts/login", data={
        "username": email,
        "password": "Valid1!pass"
    })
    token = login_response.json()["access_token"]
    
    # Try to unlike nonexistent post
    unlike_response = client.delete("/like/99999", 
        headers={"Authorization": f"Bearer {token}"}
    )
    assert unlike_response.status_code == 404

def test_like_without_authentication():
    """Test that liking without authentication returns 401"""
    response = client.post("/like/1")
    assert response.status_code == 401

def test_unlike_without_authentication():
    """Test that unliking without authentication returns 401"""
    response = client.delete("/like/1")
    assert response.status_code == 401 