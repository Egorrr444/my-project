from sqlalchemy import Boolean, Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, validator
import re


# строка подключения
SQLALCHEMY_DATABASE_URL = "sqlite:///./library.db"

# создаем движок SqlAlchemy
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
# создаем сессию подключения к бд
SessionLocal = sessionmaker(autoflush=True, bind=engine)

# базовый класс для декларативного определения моделей
Base = declarative_base()

# создаем модель, объекты которой будут храниться в бд
class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(50), nullable=False)
    author = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    is_available = Column(Boolean, default=True)


# создаем таблицы
Base.metadata.create_all(bind=engine)


app = FastAPI()


# валидация входных данных
class BookCreate(BaseModel):
    title: str
    author: str
    year: int
    is_available: bool


    @validator('year')
    def validate_year(cls, value):
        if not re.match(r'^\d{4}$', str(value)):
            raise ValueError('Год должен быть числом из 4 цифр')
        return int(value)


    @validator("title")
    def validate_title(cls, value):
        if not re.match(r'[A-Za-z0-9\s\-,\.]+$', value):
            raise ValueError('Название книги может содержать только буквы, цифры, пробелы и символы -, .')
        return value


    @validator("author")
    def validate_author(cls, value):
        # Проверяем, что имя автора содержит только буквы и пробелы
        if not re.match(r'^[A-Za-z\s\']+$', value):
            raise ValueError('Имя автора может содержать только буквы, пробелы и апострофы')
        return value


# Модель для возврата данных
class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    year: int
    is_available: bool    

    class Config:
        from_attributes = True

# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



# Добавление книги
@app.post("/books/", response_model=BookResponse)
def create_book(book: BookCreate, db: Session = Depends(get_db)):
    db_book = Book(**book.dict())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


# Получение списка всех книг
@app.get("/books/", response_model=list[BookResponse])
def get_books(db: Session = Depends(get_db)):
    return db.query(Book).all()
    

# Получение информации о конкретной книге
@app.get("/books/{book_id}", response_model=BookResponse)
def get_book_by_id(book_id: int, db: Session = Depends(get_db)):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    return db_book


# Обновление информации о книге
@app.put("/books/{book_id}", response_model=BookResponse)
def update_book(book_id: int, book: BookCreate, db: Session = Depends(get_db)):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Книга не найдаена")
    for key, value in book.dict().items():
        setattr(db_book, key, value)
    db.commit()
    db.refresh(db_book)
    return db_book    


# Удаление книги
@app.delete("/books/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db)):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(db_book)
    db.commit()
    return {"message": "Книга удалена"}