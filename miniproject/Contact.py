from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()


class ContactСreate(BaseModel):
    id: int
    name: str
    phone: int
    email: str
    address: str


class ContactResponce(BaseModel):
    id: int
    name: str
    phone: int
    email: str

cont: List[ContactСreate] = []



@app.post("/contacts",response_model=ContactСreate)
def add_contacts(contact: ContactСreate):
    cont.append(contact)
    return contact 



@app.get("/contacts", response_model=List[ContactResponce])
def get_contacts():
    return cont # Вернутся объекты без емайла



@app.get("/contacts/{contact_id}", response_model=ContactResponce)
def get_contacts_by_id(contact_id: int):
    for contact in cont:
        if contact.id == contact_id:
            return contact
        


app.delete("/contacts/{contact_id}", response_model=ContactСreate)
def delete_contact(contact_id: int):
    for contact in cont:
        if contact.id == contact_id:
            cont.remove(contact)
        return {"message": "Контакт успешно удален"}  



