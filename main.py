from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import List
import uvicorn

#FastAPI app
app= FastAPI(title='User Microservice')

#Database setup (SQLite for simplicity)
Database_URL ="sqlite://./users.db"
engine = create_engine(Database_URL,connect_args={"check_same_thread":False})
SessionaLocal = sessionmaker(autocommit=False, autoflush=False, bind= engine)

#SQLAlchemy User model
class User(Base):
    __tablename__="users"
    id=Column(Integer, primary_key=True,index=True)
    name=Column(String,index=True)
    email =Column(String, unique=True, index=True)
    

#Create Database table
Base.metadata.create_all(bind=engine)

#Pydantic models for request/response validation
class UserCreate(BaseModel):
    name:str
    email:str

class UserResponse(BaseModel):
    id:int
    name:str
    email:str
    
    class Config:
        orm_mode=True

#Dependency to get DB session
def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
#RESTFul Endpoints
@app.post("/users/",response_model=UserResponse)
async def create_user(user:UserCreate, db: SessionLocal = next(get_db())):
    db_user=User(name=user.name,email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/",response_model=List[UserResponse])
async def read_uses(db: SessionLocal= next(get_db())):
    return db.query(User).all()

@app.get("/users/{user_id}",response_model=UserResponse)
async def read_user(user_id: int, db:SessionLocal= next(get_db())):
    user= db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPExceptio(status_code=404, detail="User not found")
    return user

@app.put("/users/{user_id}",response_model= UserResponse)
async def update_user(user_id:int, user:UserCreate,db:SessionLocal= next(get_db())):
    db_user=db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, details="User not found")
    db_user.name= user.name
    db_user.email= user.email
    db.commit()
    db.refresh(db_user)
    return db_user

@app.delete("/users/{user_id}")
async def delete_user(user_id:int, db:SessionLocal = next(get_db())):
    db_user = db.query(User).filter(User.id==user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404,details="User not found")
    db.delete(db_user)
    db.commit()
    return {"detail":"User deleted"}

if __name__ =="__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    