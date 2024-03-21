from pydantic import BaseModel, EmailStr, validator, Extra, constr
import re

from app.helper_functions import hash_password

email_pattern = re.compile(r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$')

class User_auth(BaseModel):
    email: EmailStr
    password: str

    @validator("email", pre=True)
    def validate_email(cls, v):
        if not v:
            raise ValueError("Email cannot be empty")
        if not email_pattern.match(v):
            raise ValueError("Email format is invalid.")
        return v

    @validator("password")
    def validate_password(cls, v):
        if not v.strip():
            raise ValueError("Password is required")
        if ' ' in v:
            raise ValueError("Password cannot contain spaces")
        if len(v) > 15:
             raise ValueError("Password length must not exceed 15 characters")
        return v
    
    class Config:
        extra = Extra.forbid

class Posts(BaseModel):
    title: constr(max_length=100)
    description: constr(max_length=1000)

    @validator("title", pre=True)
    def validate_title(cls, v):
        if not v:
            raise ValueError("Title cannot be empty")
        return v

    @validator("description", pre=True)
    def validate_description(cls, v):
        if not v:
            raise ValueError("Description cannot be empty")
        return v
    
    class Config:
        extra = Extra.forbid

class Token(BaseModel):
    access_token: str
    token_type: str
    
    class Config:
        extra = Extra.forbid
