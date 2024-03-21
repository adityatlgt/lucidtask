import os
import re
import uuid
from jose import JWTError, jwt
from typing import List, Union
from typing import List, Optional
from sqlalchemy.orm import Session
from typing_extensions import Annotated
from passlib.context import CryptContext
from fastapi.responses import JSONResponse
from app.database_connections.connection import SessionLocal
from app.helper_functions import authenticate_user, create_access_token
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta, timezone
from fastapi.exceptions import RequestValidationError
from fastapi import Depends, FastAPI, HTTPException, status, Body , Query , Response , Request
from pydantic import BaseModel, ValidationError, validator, EmailStr, root_validator, Extra, Field
from .schemas import User_auth, Token, Posts
from .auth.auth import *
from .database_connections.models import *
from .database_connections.connection import db
from .helper_functions import get_current_user, hash_password
load_dotenv()

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#################################Response caching###############################
# Response caching decorator
def cache_response(duration: int):
    def decorator(func):
        cache = {}

        @wraps(func)
        async def wrapper(*args, **kwargs):
            user_token = kwargs["current_user"]
            if user_token in cache:
                cached_response, expiry_time = cache[user_token]
                if datetime.utcnow() < expiry_time:
                    return cached_response

            response = await func(*args, **kwargs)
            expiry_time = datetime.utcnow() + timedelta(minutes=duration)
            cache[user_token] = (response, expiry_time)
            return response

        return wrapper

    return decorator

########################################################
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = {}
    for error in exc.errors():
        error_message = [msg.strip() for msg in error['msg'].split(',')]
        if error_message[0] == 'Value error':
                if len(error['loc']) > 1:
                    error_message.pop(0)
                    errors[error['loc'][1]] = error_message  
                else:
                    error_message.pop(0)
                    errors[error_message[0]] = error_message[1]
        elif error['type'] == 'extra_forbidden':
            errors[error['loc'][1]] = ["Extra fields are not allowed"]
        elif error['type'] == 'missing':
            errors[error['loc'][1]] = [f"{error['loc'][1]} is required"]
        else:
            errors[error['loc'][1]] = error_message
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"message":"validation_errors",'errors':errors, 'status':False , 'statusCode' : 422}),
    )


"""
Common login Method
"""

def login_details(login_creds):
    authenticate_current_user = authenticate_user(login_creds.email, login_creds.password)
    if not authenticate_current_user:
        return JSONResponse(content={"message":'validation_errors',"errors":["User credentials are incorrect"], 'data':[],'status_code':401 , 'status':False}, status_code=401)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": authenticate_current_user.email}, expires_delta=access_token_expires
    )
    return JSONResponse(content={"message":"Login Success","token":access_token,"token_type":"bearer",  'data':[],'status_code':200 , 'status':True},status_code=200)

"""
This API creates user
Method: POST
"""
@app.post('/api/v1/users')
def register_user(user_credentials: User_auth = Body()):
        user_exists = db.query(User).filter_by(email=user_credentials.email).first()
        if user_exists is None:
            user = User(email=user_credentials.email,password=hash_password(user_credentials.password) ,created_at=datetime.utcnow())
            db.add(user)
            db.commit()
            return login_details(user_credentials)
        else:
            return JSONResponse(content={'message':'validation_errors','errors':{'email':['The email has already been taken']}, 'data':[] , 'status_code':409 , 'status':False}, status_code=409)
"""
This API login user
Method: POST
"""

@app.post('/api/v1/login')
def login_user(login_creds: Annotated[User_auth, Body()]) -> Token:
    return login_details(login_creds)

"""
This API creates posts
Method: POST
"""
@app.post('/api/v1/posts')
def register_user(addpost: Posts = Body(),current_user: str = Depends(get_current_user)):
    max_payload_size = 1024 * 1024 
    request_size = os.environ.get("CONTENT_LENGTH")  
    if request_size and int(request_size) > max_payload_size:
        raise HTTPException(status_code=413, detail="Payload size exceeds the limit of 1 MB")
    post = AddPost(title=addpost.title, description=addpost.description, created_at=datetime.utcnow())
    db.add(post)
    db.commit()
    return JSONResponse(content={'message': 'Post added successfully', 'data': [], 'status_code': 201, 'status': True}, status_code=201)


"""
This API get posts
"""
@app.get('/api/v1/posts')
def get_posts(current_user: str = Depends(get_current_user)):
    data = db.query(AddPost).all()
    all_posts = []
    for vals in data:       
        posts_dict = {
            "id":vals.id,
            "title":vals.title,
            "description":vals.description,
        }
        all_posts.append(posts_dict)
    if len(all_posts) > 0:
        return JSONResponse(content={'message':'data Found','data':all_posts,'status_code':200 , 'status':True}, status_code=200)
    else:
        return JSONResponse(content={"message":"no data found", 'data':[],'status_code':404 , 'status':False}, status_code=404)

"""
This API deletes posts
"""
@app.delete('/api/v1/posts/{id}')
def delete_user(id:int,current_user: str = Depends(get_current_user)):
    post_exists = db.query(AddPost).get(id)
    if post_exists is not None:
        db.delete(post_exists)
        db.commit()
        return JSONResponse(content={'message':'Post deleted successfully', 'data':[],'status_code':200 , 'status':True}, status_code=200)
    else:
        return JSONResponse(content={"message":"validation_errors","errors":{"id":["post not found"]}, 'data':[], 'status_code':404 , 'status':False}, status_code=404)