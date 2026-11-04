from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, Float, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List, Optional

# ==========================================
# 1. НАСТРОЙКА БАЗЫ ДАННЫХ (Вместо database.py)
# ==========================================
SQLALCHEMY_DATABASE_URL = "sqlite:///./movies.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==========================================
# 2. МОДЕЛЬ ДАННЫХ (Вместо models.py)
# ==========================================
class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    director = Column(String, nullable=False)
    # Ограничения БД
    year = Column(Integer, CheckConstraint('year > 1888'), nullable=False) 
    rating = Column(Float, CheckConstraint('rating >= 0 AND rating <= 10'), nullable=True)

# Создаем таблицы в БД при запуске
Base.metadata.create_all(bind=engine)

# ==========================================
# 3. СХЕМЫ PYDANTIC ДЛЯ ВАЛИДАЦИИ
# ==========================================
class MovieCreate(BaseModel):
    title: str
    director: str
    year: int
    rating: Optional[float] = None

class MovieResponse(MovieCreate):
    id: int
    class Config:
        orm_mode = True

# ==========================================
# 4. ПРИЛОЖЕНИЕ FASTAPI И ЭНДПОИНТЫ
# ==========================================
app = FastAPI(title="Movie Catalog")

# Зависимость для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Welcome to Movie Catalog API. Go to /docs to test."}

@app.post("/movies/", response_model=MovieResponse)
def create_movie(movie: MovieCreate, db: Session = Depends(get_db)):
    db_movie = Movie(**movie.dict())
    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    return db_movie

@app.get("/movies/", response_model=List[MovieResponse])
def get_movies(
    skip: int = 0, 
    limit: int = 10,
    director: Optional[str] = None,
    sort_by: Optional[str] = "id",
    db: Session = Depends(get_db)
):
    query = db.query(Movie)
    
    # Фильтрация
    if director:
        query = query.filter(Movie.director == director)
        
    # Сортировка
    if sort_by == "year":
        query = query.order_by(Movie.year)
    elif sort_by == "rating":
        query = query.order_by(Movie.rating.desc())
    else:
        query = query.order_by(Movie.id)
        
    return query.offset(skip).limit(limit).all()