import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import httpx
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

SECRET_KEY = "batpool"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

PROFILE_SERVICE_URL = os.getenv("PROFILE_SERVICE_URL", "http://localhost:8080")


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


security = HTTPBearer()

app = FastAPI(title="Auth Service", description="Authentication service that communicates with profile service", version="1.0.0")


app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


class User(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class Profile(BaseModel):
    id: Optional[int] = None
    name: str
    email: str
    age: int
    location: str


class ProfileCreate(BaseModel):
    name: str
    email: str
    age: int
    location: str


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    age: Optional[int] = None
    location: Optional[str] = None


fake_users_db = {
    "batpool": {
        "username": "batpool",
        "full_name": "Satyabrata",
        "email": "satyabrata@example.com",
        "hashed_password": pwd_context.hash("secret"),
        "disabled": False,
    },
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def get_user(db: Dict[str, Dict[str, Any]], username: str) -> Optional[UserInDB]:
    if username in db:
        user_dict = db[username]
        return UserInDB(
            username=user_dict["username"],
            email=user_dict["email"],
            full_name=user_dict.get("full_name"),
            disabled=user_dict.get("disabled", False),
            hashed_password=user_dict["hashed_password"],
        )


def authenticate_user(fake_db: Dict[str, Dict[str, Any]], username: str, password: str) -> Optional[UserInDB]:
    user = get_user(fake_db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    if token_data.username is None:
        raise credentials_exception
    user = get_user(fake_users_db, token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# HTTP client for profile service
async def get_profile_service_client():
    async with httpx.AsyncClient() as client:
        yield client


# Routes
@app.get("/")
async def root():
    return {"message": "Auth Service is running"}


@app.get("/healthz")
async def health_check():
    return {"status": "healthy", "service": "auth-service", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/token", response_model=Token)
async def login_for_access_token(username: str, password: str) -> Token:
    user = authenticate_user(fake_users_db, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")


@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


# Profile service proxy endpoints
@app.get("/profiles", response_model=dict)
async def get_all_profiles(current_user: User = Depends(get_current_active_user), client: httpx.AsyncClient = Depends(get_profile_service_client)):
    try:
        response = await client.get(f"{PROFILE_SERVICE_URL}/profiles")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to profile service: {str(e)}")


@app.get("/profiles/{profile_id}", response_model=Profile)
async def get_profile(profile_id: int, current_user: User = Depends(get_current_active_user), client: httpx.AsyncClient = Depends(get_profile_service_client)):
    try:
        response = await client.get(f"{PROFILE_SERVICE_URL}/profiles/{profile_id}")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Profile not found")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to profile service: {str(e)}")


@app.post("/profiles", response_model=Profile)
async def create_profile(profile: ProfileCreate, current_user: User = Depends(get_current_active_user), client: httpx.AsyncClient = Depends(get_profile_service_client)):
    try:
        response = await client.post(f"{PROFILE_SERVICE_URL}/profiles", json=profile.model_dump())
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to profile service: {str(e)}")


@app.put("/profiles/{profile_id}", response_model=Profile)
async def update_profile(profile_id: int, profile: ProfileUpdate, current_user: User = Depends(get_current_active_user), client: httpx.AsyncClient = Depends(get_profile_service_client)):
    try:
        # Only send non-None fields
        update_data = {k: v for k, v in profile.model_dump().items() if v is not None}
        response = await client.put(f"{PROFILE_SERVICE_URL}/profiles/{profile_id}", json=update_data)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Profile not found")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to profile service: {str(e)}")


@app.delete("/profiles/{profile_id}")
async def delete_profile(profile_id: int, current_user: User = Depends(get_current_active_user), client: httpx.AsyncClient = Depends(get_profile_service_client)):
    try:
        response = await client.delete(f"{PROFILE_SERVICE_URL}/profiles/{profile_id}")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Profile not found")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to profile service: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)  # type: ignore
