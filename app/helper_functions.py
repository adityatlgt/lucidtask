from datetime import datetime, timedelta, timezone
from typing_extensions import Annotated

from fastapi import Depends, HTTPException, status
from jose import JWTError , jwt
from .auth.auth import ALGORITHM, SECRET_KEY, pwd_context, oauth2_scheme
from typing import List, Union
from .database_connections.models import *
from .database_connections.connection import db

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password):
    return pwd_context.hash(password)

def email_exists(user_email):
    try:
        email_ex = db.query(User).filter_by(email=user_email).first()
        return email_ex
    except:
        return None

def authenticate_user(email,password):
    user_identity = email_exists(email)
    if user_identity is not None:
        if verify_password(password, user_identity.password):
            return user_identity
    return False

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username