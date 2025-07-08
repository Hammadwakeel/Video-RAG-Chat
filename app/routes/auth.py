from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from ..models.user import UserCreate, User, Token
from ..services.auth import get_password_hash, authenticate_user, create_access_token
from ..db.mongodb import mongodb

router = APIRouter()

@router.post("/register", response_model=User)
async def register(user: UserCreate):
    if mongodb.users.find_one({"username": user.username}):
        raise HTTPException(400, "Username already registered")
    if mongodb.users.find_one({"email": user.email}):
        raise HTTPException(400, "Email already registered")
    hashed = get_password_hash(user.password)
    user_dict = user.dict(exclude={"password"})
    user_dict["hashed_password"] = hashed
    mongodb.users.insert_one(user_dict)
    return User(**user_dict)

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(401, "Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}