import os
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = os.getenv("SECRET_KEY", "adpulse_secret_2026")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class AuthService:
    def hash_password(self, password): return pwd_context.hash(password)
    def verify_password(self, plain, hashed): return pwd_context.verify(plain, hashed)
    
    def create_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=20)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    def get_user_merchant_id(self, username):
        """Get merchant_id for a user from database"""
        from services.db_service import db_svc
        db = db_svc.get_data()
        user = db.get("users", {}).get(username, {})
        return user.get("merchant_id")

    async def get_current_user(self, token: str = Depends(oauth2_scheme)):
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except:
            raise HTTPException(status_code=401, detail="Invalid Session")

auth_svc = AuthService()