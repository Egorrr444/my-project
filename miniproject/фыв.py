from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from typing import Optional

app = FastAPI()


class Movie(BaseModel):
    id: int
    title: str
    year: int
    genre: str


movies: list[Movie] = []


@app.post("/movies",response_model=Movie)
def add_movie(movie: Movie):
    movies.append(movie)
    return movie 



@app.get("/movies", response_model=list[Movie])
def get_all_movie():
    return movies


@app.get("/movies/{movie_id}", response_model=Movie)
def get_movie_by_id(movie_id: int):
    for movie in movies:
        if movie.id == movie_id:
            return movie
        

@app.get("/movies/filter/{movie_year}", response_model=list[Movie])
def get_movies_by_year(year: Optional[int] = None):
    filtered_movies = movies
    if year is not None:
        filtered_movies = [movie for movie in filtered_movies if movie.year == year]
    if filtered_movies:
        return filtered_movies
    raise HTTPException(status_code=404, detail=" Фильм по этому критерию не найден")



@app.put("/movies", response_model=Movie)
def update_movie(movie_id: int, updated_movie: Movie):
    for movie in movies:
        if movie.id == movie_id:
            movie.title = updated_movie.title
            movie.year = updated_movie.year
            movie.genre = updated_movie.genre
            return movie
        raise HTTPException(status_code=404, detail="фильм не найден")
    

@app.delete("/movies/{movie_id}", response_model=Movie)
def delete_movie(movie_id: int):
    for movie in movies:
        if movie.id == movie_id:
            movies.remove(movie)
        return {"message": "фильм успешно удален"}
    

