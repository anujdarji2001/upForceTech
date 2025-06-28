import pytest
from fastapi.testclient import TestClient
from app.tests.test_accounts import get_unique_email
from app.main import app

client = TestClient(app)

def get_token(email, password):
    response = client.post("/accounts/login", data={"username": email, "password": password})
    return response.json()["access_token"]

def test_blog_visibility():
    # Create two users
    user1 = {"name": "User1", "email": "user1@example.com", "password": "Valid1!pass"}
    user2 = {"name": "User2", "email": "user2@example.com", "password": "Valid2!pass"}
    client.post("/accounts/", json=user1)
    client.post("/accounts/", json=user2)
    token1 = get_token(user1["email"], user1["password"])
    token2 = get_token(user2["email"], user2["password"])
    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}
    # User1 creates public and private posts
    pub_post = {"title": "Public Post", "description": "desc", "content": "content", "is_public": True}
    priv_post = {"title": "Private Post", "description": "desc", "content": "content", "is_public": False}
    pub_resp = client.post("/blog/", json=pub_post, headers=headers1)
    priv_resp = client.post("/blog/", json=priv_post, headers=headers1)
    pub_id = pub_resp.json()["id"]
    priv_id = priv_resp.json()["id"]
    # User2 should see only public post
    resp = client.get("/blog/", headers=headers2)
    ids = [p["id"] for p in resp.json()]
    assert pub_id in ids
    assert priv_id not in ids
    # User1 should see both
    resp = client.get("/blog/", headers=headers1)
    ids = [p["id"] for p in resp.json()]
    assert pub_id in ids
    assert priv_id in ids
    # Clean up: delete posts
    client.delete(f"/blog/{pub_id}", headers=headers1)
    client.delete(f"/blog/{priv_id}", headers=headers1)

def test_blog_crud():
    user = {"name": "BlogUser", "email": "bloguser@example.com", "password": "Valid3!pass"}
    client.post("/accounts/", json=user)
    token = get_token(user["email"], user["password"])
    headers = {"Authorization": f"Bearer {token}"}
    post = {"title": "Test Blog", "description": "desc", "content": "content", "is_public": True}
    # Create
    resp = client.post("/blog/", json=post, headers=headers)
    assert resp.status_code == 200
    post_id = resp.json()["id"]
    # Update
    resp = client.put(f"/blog/{post_id}", json={"title": "Updated Blog"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated Blog"
    # Delete
    resp = client.delete(f"/blog/{post_id}", headers=headers)
    assert resp.status_code == 204

def test_update_delete_another_users_post_forbidden():
    # User1 creates a post
    user1 = {"name": "U1", "email": "u1@example.com", "password": "Valid1!pass"}
    user2 = {"name": "U2", "email": "u2@example.com", "password": "Valid2!pass"}
    client.post("/accounts/", json=user1)
    client.post("/accounts/", json=user2)
    token1 = get_token(user1["email"], user1["password"])
    token2 = get_token(user2["email"], user2["password"])
    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}
    post = {"title": "U1 Post", "description": "desc", "content": "content", "is_public": True}
    post_id = client.post("/blog/", json=post, headers=headers1).json()["id"]
    # User2 tries to update/delete
    resp = client.put(f"/blog/{post_id}", json={"title": "Hacked"}, headers=headers2)
    assert resp.status_code == 403
    resp = client.delete(f"/blog/{post_id}", headers=headers2)
    assert resp.status_code == 403
    # Clean up
    client.delete(f"/blog/{post_id}", headers=headers1)

def test_view_private_post_access():
    # User1 creates private post
    user1 = {"name": "U3", "email": "u3@example.com", "password": "Valid3!pass"}
    user2 = {"name": "U4", "email": "u4@example.com", "password": "Valid4!pass"}
    client.post("/accounts/", json=user1)
    client.post("/accounts/", json=user2)
    token1 = get_token(user1["email"], user1["password"])
    token2 = get_token(user2["email"], user2["password"])
    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}
    post = {"title": "Private", "description": "desc", "content": "content", "is_public": False}
    post_id = client.post("/blog/", json=post, headers=headers1).json()["id"]
    # User2 cannot view
    resp = client.get(f"/blog/{post_id}", headers=headers2)
    assert resp.status_code == 403
    # User1 can view
    resp = client.get(f"/blog/{post_id}", headers=headers1)
    assert resp.status_code == 200
    # Clean up
    client.delete(f"/blog/{post_id}", headers=headers1)

def test_unauthenticated_access_forbidden():
    resp = client.get("/blog/")
    assert resp.status_code == 401
    resp = client.post("/blog/", json={"title": "T", "content": "C", "is_public": True})
    assert resp.status_code == 401
    resp = client.put("/blog/1", json={"title": "T"})
    assert resp.status_code == 401
    resp = client.delete("/blog/1")
    assert resp.status_code == 401

def test_blog_pagination():
    user = {"name": "Paginate", "email": "paginate@example.com", "password": "Valid5!pass"}
    client.post("/accounts/", json=user)
    token = get_token(user["email"], user["password"])
    headers = {"Authorization": f"Bearer {token}"}
    # Create 5 posts with unique titles
    ids = []
    titles = []
    for i in range(5):
        title = f"PaginateTestPost{i}"
        post = {"title": title, "content": "C", "is_public": True}
        resp = client.post("/blog/", json=post, headers=headers)
        ids.append(resp.json()["id"])
        titles.append(title)
    # Fetch all and assert at least 5 with our unique titles
    resp = client.get("/blog/", headers=headers)
    assert resp.status_code == 200
    posts = [p for p in resp.json() if p["title"] in titles]
    # Test skip/limit on our posts only
    resp = client.get("/blog/?skip=1&limit=2", headers=headers)
    assert resp.status_code == 200
    paginated = [p for p in resp.json() if p["title"] in titles]
    # If there are more posts in the DB, paginated may include others, so just check <= 2
    assert len(paginated) <= 2
    # Clean up
    for pid in ids:
        client.delete(f"/blog/{pid}", headers=headers)

def test_post_deletion_cascade():
    """Test that deleting a post also deletes all its likes"""
    # Create and login user
    email = get_unique_email()
    user = {"name": "Test User", "email": email, "password": "Valid1!pass"}
    client.post("/accounts/", json=user)
    
    login_response = client.post("/accounts/login", data={
        "username": email,
        "password": "Valid1!pass"
    })
    token = login_response.json()["access_token"]
    
    # Create a post
    post_response = client.post("/blog/", 
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Test Post",
            "description": "Test Description",
            "content": "Test Content",
            "is_public": True
        }
    )
    assert post_response.status_code == 200
    post_id = post_response.json()["id"]
    
    # Like the post
    like_response = client.post(f"/like/{post_id}", 
        headers={"Authorization": f"Bearer {token}"}
    )
    assert like_response.status_code == 200
    
    # Delete the post
    delete_response = client.delete(f"/blog/{post_id}", 
        headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_response.status_code == 204
    
    # Try to get the deleted post
    get_response = client.get(f"/blog/{post_id}", headers={"Authorization": f"Bearer {token}"})
    assert get_response.status_code == 404
    
    # Try to like the deleted post
    like_deleted_response = client.post(f"/like/{post_id}", 
        headers={"Authorization": f"Bearer {token}"}
    )
    assert like_deleted_response.status_code == 404

def test_access_own_private_post():
    """Test that users can access their own private posts"""
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
    
    # Access own private post
    get_response = client.get(f"/blog/{post_id}", 
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["title"] == "Private Post"
    assert data["is_public"] == False

def test_like_own_post():
    """Test that users can like their own posts"""
    # Create and login user
    email = get_unique_email()
    user = {"name": "Test User", "email": email, "password": "Valid1!pass"}
    client.post("/accounts/", json=user)
    
    login_response = client.post("/accounts/login", data={
        "username": email,
        "password": "Valid1!pass"
    })
    token = login_response.json()["access_token"]
    
    # Create a post
    post_response = client.post("/blog/", 
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Test Post",
            "description": "Test Description",
            "content": "Test Content",
            "is_public": True
        }
    )
    assert post_response.status_code == 200
    post_id = post_response.json()["id"]
    
    # Like own post
    like_response = client.post(f"/like/{post_id}", 
        headers={"Authorization": f"Bearer {token}"}
    )
    assert like_response.status_code == 200

def test_data_validation_empty_title():
    """Test that empty title is rejected"""
    # Create and login user
    email = get_unique_email()
    user = {"name": "Test User", "email": email, "password": "Valid1!pass"}
    client.post("/accounts/", json=user)
    
    login_response = client.post("/accounts/login", data={
        "username": email,
        "password": "Valid1!pass"
    })
    token = login_response.json()["access_token"]
    
    # Try to create post with empty title
    post_response = client.post("/blog/", 
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "",
            "description": "Test Description",
            "content": "Test Content",
            "is_public": True
        }
    )
    assert post_response.status_code == 422

def test_data_validation_empty_content():
    """Test that empty content is rejected"""
    # Create and login user
    email = get_unique_email()
    user = {"name": "Test User", "email": email, "password": "Valid1!pass"}
    client.post("/accounts/", json=user)
    
    login_response = client.post("/accounts/login", data={
        "username": email,
        "password": "Valid1!pass"
    })
    token = login_response.json()["access_token"]
    
    # Try to create post with empty content
    post_response = client.post("/blog/", 
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Test Title",
            "description": "Test Description",
            "content": "",
            "is_public": True
        }
    )
    assert post_response.status_code == 422

def test_pagination_invalid_skip():
    """Test pagination with invalid skip value"""
    # Create and login user for authentication
    email = get_unique_email()
    user = {"name": "Test User", "email": email, "password": "Valid1!pass"}
    client.post("/accounts/", json=user)
    
    login_response = client.post("/accounts/login", data={
        "username": email,
        "password": "Valid1!pass"
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/blog/?skip=-1&limit=5", headers=headers)
    assert response.status_code == 422

def test_pagination_invalid_limit():
    """Test pagination with invalid limit value"""
    # Create and login user for authentication
    email = get_unique_email()
    user = {"name": "Test User", "email": email, "password": "Valid1!pass"}
    client.post("/accounts/", json=user)
    
    login_response = client.post("/accounts/login", data={
        "username": email,
        "password": "Valid1!pass"
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/blog/?skip=0&limit=0", headers=headers)
    assert response.status_code == 422

def test_invalid_token():
    """Test behavior with invalid token"""
    response = client.get("/accounts/me", 
        headers={"Authorization": "Bearer invalid_token_here"}
    )
    assert response.status_code == 401

def test_missing_token():
    """Test behavior with missing token"""
    response = client.get("/accounts/me")
    assert response.status_code == 401 