from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from google.oauth2 import id_token
from google.auth.transport import requests
import jwt

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./todos.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Constants
GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com"
JWT_SECRET = "your-very-secret-key"
JWT_ALGORITHM = "HS256"

class UserDB(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    picture = Column(String)
    todos = relationship("TodoDB", back_populates="owner")

class TodoDB(Base):
    __tablename__ = "todos"
    id = Column(String, primary_key=True, index=True)
    title = Column(String)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=True)
    start_date = Column(DateTime, nullable=True)
    status = Column(String, default="pending")
    owner_id = Column(String, ForeignKey("users.id"))
    owner = relationship("UserDB", back_populates="todos")

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = db.query(UserDB).filter(UserDB.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class User(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    picture: Optional[str] = None

    class Config:
        orm_mode = True

class Todo(BaseModel):
    id: Optional[str] = None
    title: str
    completed: bool = False
    created_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    status: str = "pending" # pending, in-progress, completed

    class Config:
        orm_mode = True

@app.post("/login")
async def login(token_data: dict, db: Session = Depends(get_db)):
    token = token_data.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Token missing")
    
    try:
        # In a real app, verify with GOOGLE_CLIENT_ID
        # idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)
        
        # For demonstration purposes, we'll assume the token is valid if it's "mock-token"
        # or we try to verify it and catch the error if it's not a real token
        try:
             idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)
        except Exception:
             # Fallback for mock/invalid tokens during testing if needed, 
             # but better to handle it properly.
             # Let's assume frontend sends a JSON with user info for mock login if real one fails
             if token == "mock-token":
                 idinfo = {
                     "sub": "mock-user-id",
                     "email": "mock@example.com",
                     "name": "Mock User",
                     "picture": "https://via.placeholder.com/150"
                 }
             else:
                 raise HTTPException(status_code=401, detail="Invalid Google token")

        user_id = idinfo['sub']
        user = db.query(UserDB).filter(UserDB.id == user_id).first()
        
        if not user:
            user = UserDB(
                id=user_id,
                email=idinfo['email'],
                full_name=idinfo.get('name'),
                picture=idinfo.get('picture')
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Create JWT token
        access_token_expires = timedelta(minutes=60)
        expire = datetime.utcnow() + access_token_expires
        to_encode = {"sub": user.id, "exp": expire}
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        return {
            "access_token": encoded_jwt,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "picture": user.picture
            }
        }
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Pre-seed some data on startup if database is empty
def pre_seed():
    db = SessionLocal()
    if db.query(UserDB).count() == 0:
        # Create a mock user for pre-seeded tasks
        mock_user = UserDB(
            id="mock-user-id",
            email="mock@example.com",
            full_name="Mock User",
            picture="https://via.placeholder.com/150"
        )
        db.add(mock_user)
        db.commit()
        db.refresh(mock_user)

        statuses = ["pending", "in-progress", "completed"]
        now = datetime.now()
        for i in range(5):
            day = (i * 5) + 1
            created_at = datetime(now.year, now.month, day, 10, 0)
            status = statuses[i % 3]
            todo = TodoDB(
                id=str(uuid.uuid4()),
                title=f"Preloaded Task {i+1}",
                completed=status == "completed",
                created_at=created_at,
                status=status,
                due_date=datetime(now.year, now.month, day + 2, 17, 0),
                owner_id=mock_user.id
            )
            db.add(todo)
        db.commit()
    db.close()

pre_seed()

@app.get("/todos", response_model=List[Todo])
def get_todos(db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    return db.query(TodoDB).filter(TodoDB.owner_id == current_user.id).all()

@app.post("/seed")
def seed_data(db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    # Clear existing data for this user
    db.query(TodoDB).filter(TodoDB.owner_id == current_user.id).delete()
    
    statuses = ["pending", "in-progress", "completed"]
    now = datetime.now()
    
    # Generate data for the last 6 months
    count = 0
    for month_offset in range(6):
        month = now.month - month_offset
        year = now.year
        if month <= 0:
            month += 12
            year -= 1
        
        # Create some tasks for each month
        for i in range(5):
            day = (i * 5) + 1
            created_at = datetime(year, month, day, 10, 0)
            status = statuses[i % 3]
            completed = status == "completed"
            
            todo = TodoDB(
                id=str(uuid.uuid4()),
                title=f"Task {month}-{i}",
                completed=completed,
                created_at=created_at,
                status=status,
                due_date=datetime(year, month, day + 2, 17, 0) if day < 25 else None,
                owner_id=current_user.id
            )
            db.add(todo)
            count += 1
    db.commit()
    return {"message": f"Seeded {count} tasks"}

@app.post("/todos", response_model=Todo)
def create_todo(todo: Todo, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    todo_id = str(uuid.uuid4())
    created_at = datetime.now()
    if not todo.status:
        todo.status = "pending"
    
    db_todo = TodoDB(
        id=todo_id,
        title=todo.title,
        completed=todo.completed,
        created_at=created_at,
        due_date=todo.due_date,
        start_date=todo.start_date,
        status=todo.status,
        owner_id=current_user.id
    )
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

@app.put("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: str, updated_todo: Todo, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    db_todo = db.query(TodoDB).filter(TodoDB.id == todo_id, TodoDB.owner_id == current_user.id).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    db_todo.title = updated_todo.title
    db_todo.completed = updated_todo.completed
    db_todo.due_date = updated_todo.due_date
    db_todo.start_date = updated_todo.start_date
    db_todo.status = updated_todo.status
    
    db.commit()
    db.refresh(db_todo)
    return db_todo

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: str, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    db_todo = db.query(TodoDB).filter(TodoDB.id == todo_id, TodoDB.owner_id == current_user.id).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    db.delete(db_todo)
    db.commit()
    return {"message": "Todo deleted"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
