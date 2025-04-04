from sqlalchemy import Boolean, Column, Integer, String, create_engine, Float
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, validator
import re


# строка подключения
SQLALCHEMY_DATABASE_URL = "sqlite:///./bookstore.db"

# создаем движок SqlAlchemy
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
# создаем сессию подключения к бд
SessionLocal = sessionmaker(autoflush=True, bind=engine)

# базовый класс для декларативного определения моделей
Base = declarative_base()

# создаем модель, объекты которой будут храниться в бд
class Tasks(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(50), nullable=False)
    author = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    price = Column(Float)
    is_available = Column(Boolean, default=True)


class BookBase(BaseModel):
        title: str
        author: str
        year: int
        price: float
        is_available: bool

class BookCreate(BookBase):
    pass

class Book(BookBase):
    id: int


    class Config:
        orm_mode = True


app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()