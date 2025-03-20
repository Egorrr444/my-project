import datetime
from pydantic import BaseModel, validator

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from fastapi import FastAPI, HTTPException, Depends

import re


# строка подключения
sqlite_url = "sqlite:///User.db"
# создаем движок SqlAlchemy
engine = create_engine(sqlite_url)


# создаем класс сессии
SessionLocal = sessionmaker(autoflush=False, bind=engine)


#создаем базовый класс для моделей
class Base(DeclarativeBase): 
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


Base.metadata.create_all(bind=engine)


class UserCreate(BaseModel):
    username:str
    email: str
    phone: str


    @validator("email")
    def validate_email(cls, value):
        email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_pattern, value):
            raise ValueError("Некоректный email")
        return value


    @validator("phone")
    def validate_phone(cls, value):
        phone_pattern = r'^((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}$'
        if not re.match(phone_pattern, value):
            raise ValueError("Некоректный номер телефона")
        return value


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    phone: str
    created_at: datetime.datetime



app = FastAPI()


# Зависимость для получения сессии
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/users", response_model= UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username уже существует")
    
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email уже существует")
    
    if db.query(User).filter(User.phone == user.phone).first():
        raise HTTPException(status_code=400, detail="Phone уже существует")
    

    new_user = User(
        username=user.username,
        email=user.email,
        phone=user.phone
        
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.get("/users", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users