from typing import List
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

 
# CRUD операции
def get_books(db: Session, sort_by: str = "title", order: str = "asc"):
    books = db.query(Book)
    if sort_by == "title":
        books = books.order_by(Book.title.asc() if order == "asc" else Book.title.desc())
    elif sort_by == "year":
        books = books.order_by(Book.year.asc() if order == "asc" else Book.year.desc())
    elif sort_by == "price":
        books = books.order_by(Book.price.asc() if order == "asc" else Book.price.desc())
    return books.all()
    


def get_book(db: Session, book_id: int):
    return db.query(Book).filter(Book.id == book_id).first()


def create_book(db: Session, book: BookCreate):
    db_book = Book(**book.dict())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book



def update_book(db: Session, book_id: int, book: BookCreate):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if db_book:
        for key, value in book.dict().items():
            setattr(db_book, key, value)
        db.commit()
        db.refresh(db_book)
    return db_book


def delete_book(db: Session, book_id: int):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if db_book:
        db.delete(db_book)
        db.commit()
    return db_book


# Роуты
@app.post("/books", response_model=Book)
def create_book_route(book: BookCreate, db: Session = Depends(get_db)):
    return create_book(db, book)

@app.get("/books", response_model=List[Book])
def read_books(sort_by: str = "title", order: str = "asc", db: Session = Depends(get_db)):
    return get_books(db, sort_by=sort_by, order=order)

@app.get("/books/{book_id}", response_model=Book)
def read_book(book_id: int, db: Session = Depends(get_db)):
    db_book = get_book(db, book_id)
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return db_book

@app.put("/books/{book_id}", response_model=Book)
def update_book_route(book_id: int, book: BookCreate, db: Session = Depends(get_db)):
    return update_book(db, book_id, book)

@app.delete("/books/{book_id}")
def delete_book_route(book_id: int, db: Session = Depends(get_db)):
    return delete_book(db, book_id)
