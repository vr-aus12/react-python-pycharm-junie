import { useState, useEffect } from 'react'
import axios from 'axios'
import './App.css'

interface Todo {
  id?: string;
  title: string;
  completed: boolean;
  created_at?: string;
  due_date?: string;
  start_date?: string;
  status: string;
}

const API_URL = 'http://localhost:8000/todos';

function App() {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [newTodo, setNewTodo] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [startDate, setStartDate] = useState('');

  useEffect(() => {
    fetchTodos();
  }, []);

  const fetchTodos = async () => {
    try {
      const response = await axios.get<Todo[]>(API_URL);
      setTodos(response.data);
    } catch (error) {
      console.error('Error fetching todos:', error);
    }
  };

  const addTodo = async () => {
    if (!newTodo.trim()) return;
    try {
      const response = await axios.post<Todo>(API_URL, {
        title: newTodo,
        completed: false,
        due_date: dueDate || undefined,
        start_date: startDate || undefined,
        status: 'pending'
      });
      setTodos([...todos, response.data]);
      setNewTodo('');
      setDueDate('');
      setStartDate('');
    } catch (error) {
      console.error('Error adding todo:', error);
    }
  };

  const toggleTodo = async (todo: Todo) => {
    try {
      const updatedTodo = { 
        ...todo, 
        completed: !todo.completed,
        status: !todo.completed ? 'completed' : 'pending'
      };
      await axios.put(`${API_URL}/${todo.id}`, updatedTodo);
      setTodos(todos.map(t => t.id === todo.id ? updatedTodo : t));
    } catch (error) {
      console.error('Error updating todo:', error);
    }
  };

  const deleteTodo = async (id: string) => {
    try {
      await axios.delete(`${API_URL}/${id}`);
      setTodos(todos.filter(t => t.id !== id));
    } catch (error) {
      console.error('Error deleting todo:', error);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleString([], { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric', 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="todo-container">
      <header className="app-header">
        <h1>Task Master</h1>
        <p>Stay organized and productive</p>
      </header>
      
      <div className="input-form">
        <div className="input-group">
          <input
            type="text"
            className="main-input"
            value={newTodo}
            onChange={(e) => setNewTodo(e.target.value)}
            placeholder="What needs to be done?"
            onKeyPress={(e) => e.key === 'Enter' && addTodo()}
          />
          <button className="add-btn" onClick={addTodo}>Add Task</button>
        </div>
        <div className="date-group">
          <div className="field">
            <label>Start Date & Time</label>
            <input 
              type="datetime-local" 
              value={startDate} 
              onChange={(e) => setStartDate(e.target.value)}
            />
          </div>
          <div className="field">
            <label>Due Date & Time</label>
            <input 
              type="datetime-local" 
              value={dueDate} 
              onChange={(e) => setDueDate(e.target.value)}
            />
          </div>
        </div>
      </div>

      <div className="todo-list-container">
        <ul className="todo-list">
          {todos.length === 0 && <p className="empty-state">No tasks yet. Add one above!</p>}
          {todos.map((todo) => (
            <li key={todo.id} className={`todo-item ${todo.completed ? 'completed' : ''}`}>
              <div className="todo-checkbox" onClick={() => toggleTodo(todo)}>
                <div className={`checkbox-custom ${todo.completed ? 'checked' : ''}`}>
                  {todo.completed && <span>✓</span>}
                </div>
              </div>
              
              <div className="todo-content">
                <div className="todo-header">
                  <span className="todo-title" onClick={() => toggleTodo(todo)}>{todo.title}</span>
                  <span className={`status-badge ${todo.status}`}>
                    {todo.status}
                  </span>
                </div>
                <div className="todo-meta">
                  {todo.start_date && (
                    <div className="meta-item">
                      <span className="label">Start:</span>
                      <span className="value">{formatDate(todo.start_date)}</span>
                    </div>
                  )}
                  {todo.due_date && (
                    <div className="meta-item">
                      <span className="label">Due:</span>
                      <span className="value">{formatDate(todo.due_date)}</span>
                    </div>
                  )}
                  <div className="meta-item created">
                    <span className="label">Created:</span>
                    <span className="value">{formatDate(todo.created_at)}</span>
                  </div>
                </div>
              </div>
              
              <button className="delete-action" onClick={() => todo.id && deleteTodo(todo.id)} title="Delete task">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="3 6 5 6 21 6"></polyline>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

export default App
