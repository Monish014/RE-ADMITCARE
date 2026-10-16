"""Authentication utilities module

This module provides comprehensive authentication functionality for the ReadmitCare platform:
- JWT token creation, validation, and refresh
- Password hashing and verification using bcrypt
- User session management
- Role extraction and validation
- FastAPI dependency functions for secure endpoints

Implements requirements:
- Requirements 2.2, 2.3, 2.4, 2.5: User authentication and authorization
- Requirements 2.15, 2.16: Rate limiting for failed login attempts
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .config import settings
from .database import get_db
from .models.user import User

# Password hashing context using bcrypt with cost factor 12
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Bcrypt cost factor of 12 as per requirement 2.2
)

# HTTP Bearer token security
security = HTTPBearer()

# Session store for rate limiting (in production, use Redis or similar)
_login_attempts: Dict[str, list] = {}
_sessions: Dict[str, dict] = {}


# ============================================================================
# Password Hashing and Verification (Requirement 2.2)
# ============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify plain password against bcrypt hash.
    
    Args:
        plain_password: Plain text password from user input
        hashed_password: Bcrypt hashed password from database
        
    Returns:
        bool: True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash plain password using bcrypt with cost factor 12.
    
    Requirement 2.2: Password hashing using bcrypt with cost factor >= 12
    
    Args:
        password: Plain text password to hash
        
    Returns:
        str: Bcrypt hashed password
    """
    return pwd_context.hash(password)


# ============================================================================
# JWT Token Management (Requirements 2.3, 2.4, 2.5)
# ============================================================================

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token with HS256 algorithm.
    
    Requirements:
    - 2.3: JWT token generation with RS256 or HS256
    - 2.4: JWT expiration of 8 hours
    - 2.5: JWT payload includes user_id, email, role, organization_id
    
    Args:
        data: Dictionary with user claims (sub, email, role, ward_id, etc.)
        expires_delta: Optional custom expiration delta (defaults to 8 hours)
        
    Returns:
        str: Encoded JWT access token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT refresh token with longer expiration (7 days).
    
    Requirement 2.4: Token refresh logic
    
    Args:
        data: Dictionary with user claims
        expires_delta: Optional custom expiration delta (defaults to 7 days)
        
    Returns:
        str: Encoded JWT refresh token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode JWT token.
    
    Requirement 2.4: JWT token validation on expiration
    
    Args:
        token: JWT token string to verify
        
    Returns:
        Dict: Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        if "expired" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"}
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )


# ============================================================================
# User Session and Role Management
# ============================================================================

def extract_user_id_from_token(token: str) -> Optional[str]:
    """
    Extract user_id (sub claim) from JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        str: User ID if valid, None otherwise
    """
    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        return user_id
    except HTTPException:
        return None


def extract_role_from_token(token: str) -> Optional[str]:
    """
    Extract role from JWT token payload.
    
    Requirement 6.1: Role extraction from tokens
    
    Args:
        token: JWT token string
        
    Returns:
        str: User role if valid, None otherwise
    """
    try:
        payload = verify_token(token)
        role = payload.get("role")
        return role
    except HTTPException:
        return None


def create_user_session(user_id: str, user_data: Dict[str, Any]) -> str:
    """
    Create and store user session (for rate limiting and tracking).
    
    Args:
        user_id: UUID of the user
        user_data: Dictionary with user metadata
        
    Returns:
        str: Session ID
    """
    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc),
        "data": user_data
    }
    return session_id


def get_user_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve user session by session ID.
    
    Args:
        session_id: Session ID to retrieve
        
    Returns:
        Dict: Session data if valid, None otherwise
    """
    return _sessions.get(session_id)


# ============================================================================
# Rate Limiting (Requirement 2.15, 2.16)
# ============================================================================

def record_login_attempt(email: str) -> int:
    """
    Record a failed login attempt for rate limiting.
    
    Requirement 2.15: Rate limiting of 5 failed login attempts per email within 15 minutes
    
    Args:
        email: Email address of login attempt
        
    Returns:
        int: Total failed attempts in the last 15 minutes
    """
    now = datetime.now(timezone.utc)
    fifteen_minutes_ago = now - timedelta(minutes=15)
    
    if email not in _login_attempts:
        _login_attempts[email] = []
    
    # Remove attempts older than 15 minutes
    _login_attempts[email] = [
        attempt_time for attempt_time in _login_attempts[email]
        if attempt_time > fifteen_minutes_ago
    ]
    
    # Add new attempt
    _login_attempts[email].append(now)
    
    return len(_login_attempts[email])


def get_login_attempts(email: str) -> int:
    """
    Get count of failed login attempts in last 15 minutes.
    
    Args:
        email: Email address to check
        
    Returns:
        int: Number of failed attempts in last 15 minutes
    """
    now = datetime.now(timezone.utc)
    fifteen_minutes_ago = now - timedelta(minutes=15)
    
    if email not in _login_attempts:
        return 0
    
    valid_attempts = [
        attempt_time for attempt_time in _login_attempts[email]
        if attempt_time > fifteen_minutes_ago
    ]
    
    return len(valid_attempts)


def is_account_locked(email: str) -> bool:
    """
    Check if account is locked due to too many failed login attempts.
    
    Requirement 2.16: Temporarily block account for 30 minutes after 5 failed attempts
    
    Args:
        email: Email address to check
        
    Returns:
        bool: True if account is locked, False otherwise
    """
    now = datetime.now(timezone.utc)
    thirty_minutes_ago = now - timedelta(minutes=30)
    
    if email not in _login_attempts:
        return False
    
    # Check if there are 5 attempts within the last 30 minutes
    recent_attempts = [
        attempt_time for attempt_time in _login_attempts[email]
        if attempt_time > thirty_minutes_ago
    ]
    
    return len(recent_attempts) >= 5


def clear_login_attempts(email: str) -> None:
    """
    Clear login attempts for an email (called after successful login).
    
    Args:
        email: Email address to clear attempts for
    """
    if email in _login_attempts:
        _login_attempts[email] = []


# ============================================================================
# FastAPI Dependency Functions
# ============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    FastAPI dependency to extract and validate current user from JWT token.
    
    Requirement 6.1: Create reusable dependency for FastAPI endpoints
    
    Usage:
        @app.get("/api/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            return {"user_id": current_user.id}
    
    Args:
        credentials: HTTP Bearer credentials from request header
        db: Database session
        
    Returns:
        User: Current authenticated user from database
        
    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    try:
        token = credentials.credentials
        payload = verify_token(token)
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type", "access")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Ensure this is an access token, not refresh token
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"}
            )
            
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Fetch user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    FastAPI dependency to ensure current user has admin role.
    
    Usage:
        @app.delete("/api/admin/users/:id")
        async def delete_user(current_user: User = Depends(get_current_admin_user)):
            return {"deleted": True}
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Current user if admin, raises exception otherwise
        
    Raises:
        HTTPException: 403 if user is not admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_current_caregiver_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    FastAPI dependency to ensure current user is a caregiver (nurse, doctor, social_worker, admin).
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Current user if caregiver, raises exception otherwise
        
    Raises:
        HTTPException: 403 if user is not a caregiver
    """
    caregiver_roles = ["admin", "doctor", "nurse", "social_worker"]
    if current_user.role not in caregiver_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Caregiver access required"
        )
    return current_user


# ============================================================================
# User Authorization and Data Access Control
# ============================================================================

def can_access_patient(current_user: User, patient_ward_id: Optional[str]) -> bool:
    """
    Check if user can access patient data based on role and ward.
    
    Requirement 2.13: Care team members can only access patients within their organization
    Requirement 18.2: Enforce that patient role users can only access their own data
    
    Args:
        current_user: Current authenticated user
        patient_ward_id: Ward ID of patient being accessed
        
    Returns:
        bool: True if user can access patient, False otherwise
    """
    # Admin can access all patients
    if current_user.role == "admin":
        return True
    
    # Non-admin users can only access patients in their ward
    if current_user.ward_id is None:
        return False
    
    return str(current_user.ward_id) == str(patient_ward_id)


def can_modify_user_role(current_user: User, target_role: str) -> bool:
    """
    Check if user can modify another user's role (authorization check).
    
    Requirement 18.8: Log all permission changes and role assignments
    
    Args:
        current_user: Current authenticated user
        target_role: Role being assigned
        
    Returns:
        bool: True if user can modify role, False otherwise
    """
    # Only admin can modify roles
    if current_user.role != "admin":
        return False
    
    # Admin cannot create roles beyond admin level
    valid_roles = ["admin", "doctor", "nurse", "social_worker"]
    return target_role in valid_roles
