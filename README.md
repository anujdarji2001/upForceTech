# FastAPI CMS - Complete Blog Management System

A comprehensive Content Management System built with FastAPI, SQLite, and JWT authentication. This application provides user management, blog post creation with public/private visibility, like functionality, and full test coverage.

## 🚀 Features

### Core Functionality
- **User Management**: Registration, authentication, profile updates, and account deletion
- **Blog Posts**: Create, read, update, delete posts with public/private visibility
- **Like System**: Users can like posts, with automatic cascade deletion
- **Authorization**: JWT-based authentication with role-based access control
- **Data Validation**: Comprehensive input validation including password strength
- **Cascade Operations**: Automatic cleanup of related data on deletion

### Security Features
- **Password Hashing**: Bcrypt password hashing for secure storage
- **JWT Tokens**: Secure authentication with access tokens
- **Authorization Rules**: Users can only modify their own content
- **Input Validation**: Comprehensive validation for all inputs
- **Environment Variables**: Secure configuration management

## 📋 Prerequisites

- Python 3.8+
- pip (Python package installer)

## 🛠️ Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/anujdarji2001/upForceTech.git
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   DATABASE_URL=sqlite:///./app.db
   ```

5. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

Once the server is running, you can access:
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

## 🔗 API Endpoints

### Authentication & User Management

#### 1. User Registration
```
POST /accounts/
```
**Request Body:**
```json
{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "SecurePass123!"
}
```
**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

#### 2. User Login
```
POST /accounts/login
```
**Request Body (form-data):**
```
username: john@example.com
password: SecurePass123!
```
**Response:**
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer"
}
```

#### 3. Get Current User Info
```
GET /accounts/me
```
**Headers:** `Authorization: Bearer <token>`

#### 4. Update User Profile
```
PUT /accounts/
```
**Headers:** `Authorization: Bearer <token>`
**Request Body:**
```json
{
    "name": "Updated Name",
    "password": "NewSecurePass123!"
}
```

#### 5. Get User Statistics
```
GET /accounts/me/stats
```
**Headers:** `Authorization: Bearer <token>`
**Response:**
```json
{
    "posts_count": 5,
    "likes_count": 12
}
```

#### 6. Delete Account
```
DELETE /accounts/
```
**Headers:** `Authorization: Bearer <token>`
**Response:**
```json
{
    "message": "User deleted successfully. Removed 5 posts and 12 likes.",
    "posts_deleted": 5,
    "likes_deleted": 12
}
```

### Blog Management

#### 1. Create Blog Post
```
POST /blog/
```
**Headers:** `Authorization: Bearer <token>`
**Request Body:**
```json
{
    "title": "My First Blog Post",
    "description": "A brief description",
    "content": "This is the main content of my blog post...",
    "is_public": true
}
```

#### 2. Get All Public Posts (Paginated)
```
GET /blog/?skip=0&limit=10
```
**Query Parameters:**
- `skip`: Number of posts to skip (default: 0)
- `limit`: Maximum number of posts to return (default: 100)

#### 3. Get Specific Post
```
GET /blog/{post_id}
```
**Authorization Logic:**
- Public posts: Accessible to everyone
- Private posts: Only accessible to the owner

#### 4. Update Blog Post
```
PUT /blog/{post_id}
```
**Headers:** `Authorization: Bearer <token>`
**Authorization:** Only the post owner can update
**Request Body:**
```json
{
    "title": "Updated Title",
    "content": "Updated content",
    "is_public": false
}
```

#### 5. Delete Blog Post
```
DELETE /blog/{post_id}
```
**Headers:** `Authorization: Bearer <token>`
**Authorization:** Only the post owner can delete
**Cascade:** Automatically deletes all likes on the post

### Like System

#### 1. Like a Post
```
POST /like/{post_id}
```
**Headers:** `Authorization: Bearer <token>`
**Authorization:** Can only like public posts or own private posts
**Response:**
```json
{
    "id": 1,
    "post_id": 5,
    "user_id": 2,
    "created_at": "2024-01-15T10:30:00Z"
}
```

#### 2. Unlike a Post
```
DELETE /like/{post_id}
```
**Headers:** `Authorization: Bearer <token>`
**Authorization:** Can only unlike own likes

## 🔐 Business Logic & Authorization Rules

### User Management
1. **Email Uniqueness**: Each email can only be registered once
2. **Password Security**: Passwords are hashed using bcrypt before storage
3. **Account Deletion**: When a user is deleted, all their posts and likes are automatically removed (cascade delete)

### Blog Posts
1. **Visibility Control**: Posts can be public (visible to all) or private (visible only to owner)
2. **Ownership**: Only post owners can update or delete their posts
3. **Content Validation**: Title and content cannot be empty
4. **Cascade Deletion**: When a post is deleted, all its likes are automatically removed

### Like System
1. **Unique Likes**: A user can only like a post once
2. **Visibility Rules**: Users can only like posts they can see (public posts or own private posts)
3. **Ownership**: Users can only unlike their own likes
4. **Cascade Cleanup**: Likes are automatically removed when posts or users are deleted

### Authentication & Authorization
1. **JWT Tokens**: Secure token-based authentication
2. **Token Expiration**: Tokens expire after 30 minutes (configurable)
3. **Protected Routes**: Most endpoints require valid authentication
4. **Owner-Only Operations**: Users can only modify their own content

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest app/tests/test_accounts.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app
```

### Test Coverage
The application includes comprehensive tests for:
- User registration and validation
- Authentication and login
- Blog post CRUD operations
- Like functionality
- Authorization rules
- Cascade deletion scenarios
- Data validation edge cases

## 📮 Postman Collection

### Importing the Collection
1. Open Postman
2. Click "Import" button
3. Select the `FastAPI CMS Collection.postman_collection.json` file
4. Import the environment file `Upforce.postman_environment.json`

### Environment Setup
The collection uses the following environment variables:
- `base_url`: API base URL (default: http://localhost:8000)
- `token_user1`: JWT token for User 1
- `token_user2`: JWT token for User 2
- `blog_id_user1`: Blog post ID for User 1's post
- `blog_id_user2`: Blog post ID for User 2's public post
- `blog_id_user2_private`: Blog post ID for User 2's private post


### Test Scenarios Covered
1. **User Management**
   - Registration with valid/invalid data
   - Login and token generation
   - Profile updates
   - Account deletion with cascade

2. **Blog Operations**
   - Creating public and private posts
   - Reading posts with proper authorization
   - Updating own posts
   - Deleting posts with cascade

3. **Like System**
   - Liking public and private posts
   - Preventing duplicate likes
   - Unliking posts
   - Cascade deletion when posts/users are deleted

4. **Authorization Testing**
   - Accessing private posts (should fail for non-owners)
   - Modifying others' posts (should fail)
   - Liking private posts of others (should fail)

5. **Edge Cases**
   - Invalid tokens
   - Missing authentication
   - Data validation errors
   - Pagination edge cases

### Collection Structure
The collection is organized in logical groups:
1. **Setup**: User creation and authentication
2. **Blog Operations**: CRUD operations for blog posts
3. **Like System**: Like/unlike functionality
4. **Authorization Tests**: Security and access control
5. **Edge Cases**: Error scenarios and validation

