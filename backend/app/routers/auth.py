from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from ..database import get_db, User

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "secret"
ALGORITHM = "HS256"

class UserAuth(BaseModel):
    username: str
    password: str

@router.post("/register")
def register(user: UserAuth, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        return {"msg": "User exists (OK)"} 
    hashed = pwd_context.hash(user.password)
    db.add(User(username=user.username, hashed_password=hashed))
    db.commit()
    return {"msg": "Created"}

@router.post("/token")
def login(user: UserAuth, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.username == user.username).first()
    if not u or not pwd_context.verify(user.password, u.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect")
    token = jwt.encode({"sub": u.username, "exp": datetime.utcnow() + timedelta(hours=2)}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}