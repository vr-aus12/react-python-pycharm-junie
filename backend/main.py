from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./todos.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TodoDB(Base):
    __tablename__ = "todos"
    id = Column(String, primary_key=True, index=True)
    title = Column(String)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=True)
    start_date = Column(DateTime, nullable=True)
    status = Column(String, default="pending")

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Pre-seed some data on startup if database is empty
def pre_seed():
    db = SessionLocal()
    if db.query(TodoDB).count() == 0:
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
                due_date=datetime(now.year, now.month, day + 2, 17, 0)
            )
            db.add(todo)
        db.commit()
    db.close()

pre_seed()

@app.get("/todos", response_model=List[Todo])
def get_todos(db: Session = Depends(get_db)):
    return db.query(TodoDB).all()

@app.post("/seed")
def seed_data(db: Session = Depends(get_db)):
    # Clear existing data
    db.query(TodoDB).delete()
    
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
                due_date=datetime(year, month, day + 2, 17, 0) if day < 25 else None
            )
            db.add(todo)
            count += 1
    db.commit()
    return {"message": f"Seeded {count} tasks"}

@app.post("/todos", response_model=Todo)
def create_todo(todo: Todo, db: Session = Depends(get_db)):
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
        status=todo.status
    )
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

@app.put("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: str, updated_todo: Todo, db: Session = Depends(get_db)):
    db_todo = db.query(TodoDB).filter(TodoDB.id == todo_id).first()
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
def delete_todo(todo_id: str, db: Session = Depends(get_db)):
    db_todo = db.query(TodoDB).filter(TodoDB.id == todo_id).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    db.delete(db_todo)
    db.commit()
    return {"message": "Todo deleted"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
