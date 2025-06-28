import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

@pytest.fixture(scope="module")
def test_user():
    return {"name": "Test User", "email": "test@example.com", "password": "testpass"}

def get_unique_email():
    """Generate a unique email for each test to avoid conflicts"""
    return f"test_{uuid.uuid4().hex[:8]}@example.com"

def test_create_account_valid():
    user = {"name": "Test User", "email": get_unique_email(), "password": "Valid1!pass"}
    response = client.post("/accounts/", json=user)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == user["name"]
    assert data["email"] == user["email"]
    assert "id" in data

def test_create_account_invalid_password():
    user = {"name": "Test User", "email": get_unique_email(), "password": "weak"}
    response = client.post("/accounts/", json=user)
    assert response.status_code == 400
    assert "Password must be at least 8 characters" in response.json()["detail"]

def test_create_account_duplicate_email():
    email = get_unique_email()
    user = {"name": "Test User", "email": email, "password": "Valid1!pass"}
    # Create first user
    client.post("/accounts/", json=user)
    # Try to create second user with same email
    response = client.post("/accounts/", json=user)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

def test_login_valid():
    # First create a user
    email = get_unique_email()
    user = {"name": "Test User", "email": email, "password": "Valid1!pass"}
    client.post("/accounts/", json=user)
    
    # Then login
    response = client.post("/accounts/login", data={
        "username": email,
        "password": "Valid1!pass"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials():
    response = client.post("/accounts/login", data={
        "username": "nonexistent@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 400
    assert "Incorrect email or password" in response.json()["detail"]

def test_update_account_valid():
    # Create and login user
    email = get_unique_email()
    user = {"name": "Test User", "email": email, "password": "Valid1!pass"}
    client.post("/accounts/", json=user)
    
    login_response = client.post("/accounts/login", data={
        "username": email,
        "password": "Valid1!pass"
    })
    token = login_response.json()["access_token"]
    
    # Update account
    update_data = {"name": "Updated User"}
    response = client.put("/accounts/", 
        headers={"Authorization": f"Bearer {token}"},
        json=update_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]

def test_update_account_invalid_password():
    # Create and login user
    email = get_unique_email()
    user = {"name": "Test User", "email": email, "password": "Valid1!pass"}
    client.post("/accounts/", json=user)
    
    login_response = client.post("/accounts/login", data={
        "username": email,
        "password": "Valid1!pass"
    })
    token = login_response.json()["access_token"]
    
    # Try to update with invalid password
    update_data = {"password": "weak"}
    response = client.put("/accounts/", 
        headers={"Authorization": f"Bearer {token}"},
        json=update_data
    )
    assert response.status_code == 400
    assert "Password must be at least 8 characters" in response.json()["detail"]

def test_get_me():
    # Create and login user
    email = get_unique_email()
    user = {"name": "Test User", "email": email, "password": "Valid1!pass"}
    client.post("/accounts/", json=user)
    
    login_response = client.post("/accounts/login", data={
        "username": email,
        "password": "Valid1!pass"
    })
    token = login_response.json()["access_token"]
    
    # Get user info
    response = client.get("/accounts/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == user["name"]
    assert data["email"] == user["email"]

def test_delete_account():
    # Create and login user
    email = get_unique_email()
    user = {"name": "Test User", "email": email, "password": "Valid1!pass"}
    client.post("/accounts/", json=user)
    
    login_response = client.post("/accounts/login", data={
        "username": email,
        "password": "Valid1!pass"
    })
    token = login_response.json()["access_token"]
    
    # Delete account
    response = client.delete("/accounts/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "posts_deleted" in data
    assert "likes_deleted" in data

def test_delete_account_with_cascade():
    """Test that deleting a user also deletes their posts and likes"""
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
    
    # Get user stats before deletion
    stats_response = client.get("/accounts/me/stats", 
        headers={"Authorization": f"Bearer {token}"}
    )
    assert stats_response.status_code == 200
    stats = stats_response.json()
    assert stats["posts_count"] == 1
    assert stats["likes_count"] == 1
    
    # Delete account
    delete_response = client.delete("/accounts/", 
        headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_response.status_code == 200
    delete_data = delete_response.json()
    assert delete_data["posts_deleted"] == 1
    assert delete_data["likes_deleted"] == 1
    
    # Create another user to verify the post is deleted
    email2 = get_unique_email()
    user2 = {"name": "Test User 2", "email": email2, "password": "Valid2!pass"}
    client.post("/accounts/", json=user2)
    
    login_response2 = client.post("/accounts/login", data={
        "username": email2,
        "password": "Valid2!pass"
    })
    token2 = login_response2.json()["access_token"]
    
    # Verify post is deleted by trying to access it with another user
    post_check = client.get(f"/blog/{post_id}", headers={"Authorization": f"Bearer {token2}"})
    assert post_check.status_code == 404

def test_get_my_stats():
    # Create and login user
    email = get_unique_email()
    user = {"name": "Test User", "email": email, "password": "Valid1!pass"}
    client.post("/accounts/", json=user)
    
    login_response = client.post("/accounts/login", data={
        "username": email,
        "password": "Valid1!pass"
    })
    token = login_response.json()["access_token"]
    
    # Get stats
    response = client.get("/accounts/me/stats", 
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "user_name" in data
    assert "user_email" in data
    assert "posts_count" in data
    assert "likes_count" in data
    assert "total_impact" in data
    assert data["posts_count"] == 0
    assert data["likes_count"] == 0
    assert data["total_impact"] == 0 