from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

class Book(BaseModel):
    id: int
    title: str
    autor: str
    year: int


books: list[Book] = []


 #получить список всех книг 
@app.get("/books")
def get_all_books():
    return books


#получить данные конкретной книги по id 
@app.get("/books/{book_id}")
def get_books_by_id(book_id: int):
    for book in books:
        if book.id == book_id:
            return book
    raise HTTPException(status_code=404, detail="Книга не найдена")


#добавить новую книгу
@app.post("/books")
def add_books(book: Book):
    books.append(book)
    return book


#обновить информацию о книге
@app.put("/books/edit/{book_id}")
def edit_book(book_id: int, book: Book):
    existing_book = next((book for book in books if book.id == book_id), None)
    if existing_book is None:
        raise HTTPException(status_code=404, detail="Книга не найдена")

    # Обновляем данные книги
    existing_book.title = book.title
    existing_book.autor = book.autor
    existing_book.year = book.year
        
   

@app.delete("/book/delete/{book_id}")
def delete_book(book_id: int):
    book_to_delete = next((b for b in books if b.id == book_id), None)
    for book in books:
        if book.id == book_id:
            books.remove(book)
        return{"message": "Book успешно удалена"}