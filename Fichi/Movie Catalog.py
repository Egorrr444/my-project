from typing import Generic, List, Optional, TypeVar
from sqlalchemy import Boolean, Column, Integer, String, create_engine, Float
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel, validator


T = TypeVar("T")


class PaginatedResponce(BaseModel, Generic[T]):
    items: List[T]
    total: int # Кол-во элементов
    page: int # Текуш. стр.
    size: int # Кол-во элементов на стр.
    pages: int # Всего стр.

# строка подключения
SQLALCHEMY_DATABASE_URL = "sqlite:///./MovieCatalog.db"

# создаем движок SqlAlchemy
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
# создаем сессию подключения к бд
SessionLocal = sessionmaker(autoflush=True, bind=engine)

# базовый класс для декларативного определения моделей
Base = declarative_base()

# создаем модель, объекты которой будут храниться в бд
class Movie(Base):
    __tablename__ = "Movie"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(50), nullable=False)
    genre = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    rating = Column(Float)
    is_available = Column(Boolean, default=True)

# создаем таблицы
Base.metadata.create_all(bind=engine)


app = FastAPI()


# валидация входных данных
class MovieCreate(BaseModel):
    id: int
    title: str
    genre: str
    year: int
    rating: float
    is_available: bool


# Модель для возврата данных
class MovieResponse(BaseModel):
    title: str
    genre: str
    year: int
    rating: float
    is_available: bool    

    
    class Config:
        from_attributes  = True


# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_movies(
    db: Session,
    skip: int,
    limit: int,
    genre: Optional[str],
    min_rating: Optional[float],
    year: Optional[int],
    is_available: Optional[bool],
    
):
    query = db.query(Movie)

    #Фильтрация
    if genre:
        query = query.filter(Movie.genre == genre)
    if min_rating is not None:
        query = query.filter(Movie.rating >= min_rating)
    if year:
        query = query.filter(Movie.year == year)
    if is_available is not None:
        query = query.filter(Movie.is_available == is_available)
    
    return query.offset(skip).limit(limit).all()#сколько записей пропустить/сколько записей показать


def get_movie(db: Session, movie_id: int):
    return db.query(Movie).filter(Movie.id == movie_id).first()
    
    
def create_movie(db: Session, movie: MovieCreate):
    db_movie = Movie(**movie.dict())
    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    return db_movie


def update_movie(db: Session, movie_id: int, movie: MovieCreate):
    db_movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if db_movie:
        for key, value in movie.dict().items():
            setattr(db_movie, key, value)
        db.commit()
        db.refresh(db_movie)
    return db_movie


def delete_movie(db: Session, movie_id: int):
    db_movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if db_movie:
        db.delete(db_movie)
        db.commit()
    return db_movie


@app.post("/movies", response_model=MovieResponse)
def create_movie_route(movie: MovieCreate, db: Session = Depends(get_db)):
    return create_movie(db, movie)

@app.get("/movies/all", response_model=List[MovieResponse])
def read_all_movies(db: Session = Depends(get_db)):
    return db.query(Movie).all()

@app.get("/movies", response_model=PaginatedResponce[MovieResponse])
def read_movies(
    genre: Optional[str] = Query(None),
    min_rating: Optional[float] = Query(None, ge=0, le=10),
    year: Optional[int] = Query(None),
    is_available: Optional[bool] = Query(None),

    page: int = Query(1, gt = 0, description="Номер страницы"),
    size: int = Query(10, gt = 0, le = 100, description= "Количество элементов" ),

    db: Session = Depends(get_db)
):

    skip = (page - 1) * size # Формула расчета смещения
   
    items = get_movies(
        db,
        skip=skip,
        limit=size,
        genre=genre,
        min_rating=min_rating,
        year=year,
        is_available=is_available
    )


    #подсчет общего количества с учетом фильтров
    total_query = db.query(Movie)
    if genre:
        total_query = total_query.filter(Movie.genre == genre)
    if min_rating is not None:
        total_query = total_query.filter(Movie.rating >= min_rating)
    if year:
        total_query = total_query.filter(Movie.year == year)
    if is_available is not None:
        total_query = total_query.filter(Movie.is_available == is_available)
        
    total = total_query.count()

    #расчет общего количества страниц
    pages = (total + size - 1) // size  # Округление вверх
    
    return PaginatedResponce[MovieResponse](
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )



@app.get("/movies/{movie_id}", response_model=MovieResponse)
def read_movie(movie_id: int, db: Session = Depends(get_db)):
    db_movie = get_movie(db, movie_id)
    if db_movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")
    return db_movie

@app.put("/movies/{movie_id}", response_model=MovieResponse)
def update_movie_route(movie_id: int, movie: MovieCreate, db: Session = Depends(get_db)):
    return update_movie(db, movie_id, movie)

@app.delete("/movies/{movie_id}")
def delete_movie_route(movie_id: int, db: Session = Depends(get_db)):
    return delete_movie(db, movie_id)