from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
import uuid

from datetime import datetime

app = FastAPI()

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

todos = []

# Pre-seed some data on startup
def pre_seed():
    statuses = ["pending", "in-progress", "completed"]
    now = datetime.now()
    for i in range(5):
        day = (i * 5) + 1
        created_at = datetime(now.year, now.month, day, 10, 0)
        status = statuses[i % 3]
        todo = Todo(
            id=str(uuid.uuid4()),
            title=f"Preloaded Task {i+1}",
            completed=status == "completed",
            created_at=created_at,
            status=status,
            due_date=datetime(now.year, now.month, day + 2, 17, 0)
        )
        todos.append(todo)

pre_seed()

@app.get("/todos", response_model=List[Todo])
def get_todos():
    return todos

@app.post("/seed")
def seed_data():
    global todos
    todos = []
    statuses = ["pending", "in-progress", "completed"]
    now = datetime.now()
    
    # Generate data for the last 6 months
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
            
            todo = Todo(
                id=str(uuid.uuid4()),
                title=f"Task {month}-{i}",
                completed=completed,
                created_at=created_at,
                status=status,
                due_date=datetime(year, month, day + 2, 17, 0) if day < 25 else None
            )
            todos.append(todo)
    return {"message": f"Seeded {len(todos)} tasks"}

@app.post("/todos", response_model=Todo)
def create_todo(todo: Todo):
    todo.id = str(uuid.uuid4())
    todo.created_at = datetime.now()
    if not todo.status:
        todo.status = "pending"
    todos.append(todo)
    return todo

@app.put("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: str, updated_todo: Todo):
    for index, todo in enumerate(todos):
        if todo.id == todo_id:
            todos[index] = updated_todo
            todos[index].id = todo_id
            return todos[index]
    raise HTTPException(status_code=404, detail="Todo not found")

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: str):
    for index, todo in enumerate(todos):
        if todo.id == todo_id:
            del todos[index]
            return {"message": "Todo deleted"}
    raise HTTPException(status_code=404, detail="Todo not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
