from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationError

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from fastapi import FastAPI, HTTPException, Depends

import re


# строка подключения
sqlite_url = "sqlite:///pass.db"
# создаем движок SqlAlchemy
engine = create_engine(sqlite_url)


# создаем класс сессии
SessionLocal = sessionmaker(autoflush=False, bind=engine)


#создаем базовый класс для моделей
class Base(DeclarativeBase): 
    pass


class User(Base):
    __tablename__ = "data"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    surname = Column(String, unique=True, nullable=False)
    snils = Column(String, unique=True, nullable= False) 
    inn = Column(String, unique= True, nullable= False)

    Base.metadata.create_all(bind=engine)



class PassportCreate(BaseModel):
    username: str
    surname: str
    snils: str
    inn: str


def validate_snils(snils: str) -> bool:
    # Проверяем формат с помощью regex
    if not re.fullmatch(r'^\d{3}-\d{3}-\d{3} \d{2}$', snils):
        return False
    
    # Удаляем все нецифровые символы
    digits = re.sub(r'\D', '', snils)
    
    # Проверяем длину
    if len(digits) != 11:
        return False
    
    # Проверяем специальный номер
    if digits == "00000000000":
        return True
    
    # Разделяем номер и контрольную сумму
    number = digits[:9]
    checksum = int(digits[9:])
    
    # Вычисляем контрольную сумму
    total = 0
    for i in range(9):
        digit = int(number[i])
        total += digit * (9 - i)
    
    # Проверяем контрольную сумму
    if total < 100:
        return total == checksum
    elif total == 100 or total == 101:
        return checksum == 0
    else:
        return (total % 101) == checksum


def validate_inn(inn: str) -> bool:
    # Очищаем ИНН от лишних символов
    inn_clean = re.sub(r"\D", "", inn)
    
    # Проверяем длину
    if len(inn_clean) not in (10, 12):
        return False
    
    digits = [int(c) for c in inn_clean]
    
    # Проверка для 10-значного ИНН (юрлица)
    if len(digits) == 10:
        weights = [7, 2, 4, 10, 3, 5, 9, 4, 6]
        control_sum = sum(w * d for w, d in zip(weights, digits[:-1])) % 11
        control_digit = 0 if control_sum == 10 else control_sum
        return digits[-1] == control_digit
    
    # Проверка для 12-значного ИНН (физлица и ИП)
    elif len(digits) == 12:
        # Первая контрольная цифра (11-я)
        weights_k1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        control_sum_k1 = sum(w * d for w, d in zip(weights_k1, digits[:-2])) % 11
        control_digit_k1 = 0 if control_sum_k1 == 10 else control_sum_k1
        
        # Вторая контрольная цифра (12-я)
        weights_k2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        control_sum_k2 = sum(w * d for w, d in zip(weights_k2, digits[:-1])) % 11
        control_digit_k2 = 0 if control_sum_k2 == 10 else control_sum_k2
        
        return digits[-2] == control_digit_k1 and digits[-1] == control_digit_k2
    
    return False


class PassportResponse(BaseModel):
    id: int
    username: str
    surname: str
    snils: str
    inn: str


app = FastAPI()


# Зависимость для получения сессии
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/Passport",response_model=PassportResponse)
def add_passport(passport: PassportCreate, db: Session=Depends(get_db)):
    if db.query(User).filter(User.username == passport.username).first():
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    
    if db.query(User).filter(User.snils == passport.snils).first():
        raise HTTPException(status_code=400, detail="СНИЛС уже существует")
    
    if db.query(User).filter(User.inn == passport.inn).first():
        raise HTTPException(status_code=400, detail="ИНН уже существует")
    

    new_passport = User(
        username=passport.username,
        surname=passport.surname,
        snils=passport.snils,
        inn=passport.inn
        
    )
    db.add(new_passport)
    db.commit()
    db.refresh(new_passport)

    return new_passport


@app.get("/Passport", response_model=PassportResponse)
def get_passport(db: Session = Depends(get_db)):
    passport = db.query(User).all()
    return passport


@app.get("/Passport/{passport_id}", response_model=PassportResponse)
def get_passport_by_id(passport_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == passport_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="Паспорт не найден")
    return db_user


@app.delete("/Passport/{user_id}")
def delete_passport(passport_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == passport_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="Паспорт не найден")
    db.delete(db_user)
    db.commit()
    return {"message": "Паспорт удален"}