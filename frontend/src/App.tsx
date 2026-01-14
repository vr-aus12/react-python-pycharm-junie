import { useState, useEffect } from 'react'
import axios from 'axios'
import { 
  PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid
} from 'recharts'
import { LayoutDashboard, ListTodo, PieChart as PieIcon, RefreshCw, LogOut, User as UserIcon } from 'lucide-react'
import { GoogleOAuthProvider, GoogleLogin, googleLogout } from '@react-oauth/google'
import { jwtDecode } from 'jwt-decode'
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

interface User {
  id: string;
  email: string;
  full_name: string;
  picture: string;
}

const API_BASE_URL = 'http://localhost:8000';
const GOOGLE_CLIENT_ID = 'YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com'; // Replace with your real Google Client ID

const COLORS = ['#f59e0b', '#6366f1', '#22c55e']; // Pending, In Progress, Completed

function AppContent() {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [newTodo, setNewTodo] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [startDate, setStartDate] = useState('');
  const [activeTab, setActiveTab] = useState<'tasks' | 'reports'>('tasks');
  const [user, setUser] = useState<User | null>(() => {
    const savedUser = localStorage.getItem('user');
    return savedUser ? JSON.parse(savedUser) : null;
  });
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      fetchTodos();
    }
  }, [token]);

  const fetchTodos = async () => {
    try {
      const response = await axios.get<Todo[]>(`${API_BASE_URL}/todos`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTodos(response.data);
    } catch (error) {
      console.error('Error fetching todos:', error);
      if (axios.isAxiosError(error) && error.response?.status === 401) {
        handleLogout();
      }
    }
  };

  const handleLoginSuccess = async (credentialResponse: any) => {
    try {
      const res = await axios.post(`${API_BASE_URL}/login`, {
        token: credentialResponse.credential
      });
      const { access_token, user: userData } = res.data;
      setToken(access_token);
      setUser(userData);
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(userData));
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  const handleLogout = () => {
    googleLogout();
    setToken(null);
    setUser(null);
    setTodos([]);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  };

  const seedData = async () => {
    try {
      await axios.post(`${API_BASE_URL}/seed`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchTodos();
    } catch (error) {
      console.error('Error seeding data:', error);
    }
  };

  const addTodo = async () => {
    if (!newTodo.trim()) return;
    try {
      const response = await axios.post<Todo>(`${API_BASE_URL}/todos`, {
        title: newTodo,
        completed: false,
        due_date: dueDate || undefined,
        start_date: startDate || undefined,
        status: 'pending'
      }, {
        headers: { Authorization: `Bearer ${token}` }
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
      const nextStatus = todo.status === 'pending' ? 'in-progress' : 
                         todo.status === 'in-progress' ? 'completed' : 'pending';
      const updatedTodo = { 
        ...todo, 
        completed: nextStatus === 'completed',
        status: nextStatus
      };
      await axios.put(`${API_BASE_URL}/todos/${todo.id}`, updatedTodo, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTodos(todos.map(t => t.id === todo.id ? updatedTodo : t));
    } catch (error) {
      console.error('Error updating todo:', error);
    }
  };

  const deleteTodo = async (id: string) => {
    try {
      await axios.delete(`${API_BASE_URL}/todos/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
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

  const getPieData = () => {
    const counts = { pending: 0, 'in-progress': 0, completed: 0 };
    todos.forEach(t => {
      counts[t.status as keyof typeof counts]++;
    });
    return [
      { name: 'Pending', value: counts.pending },
      { name: 'In Progress', value: counts['in-progress'] },
      { name: 'Completed', value: counts.completed },
    ];
  };

  const getMonthlyData = () => {
    const monthlyMap: Record<string, { month: string, opened: number, closed: number }> = {};
    for (let i = 5; i >= 0; i--) {
      const d = new Date();
      d.setMonth(d.getMonth() - i);
      const key = d.toLocaleString('default', { month: 'short', year: 'numeric' });
      monthlyMap[key] = { month: key, opened: 0, closed: 0 };
    }
    todos.forEach(t => {
      if (t.created_at) {
        const date = new Date(t.created_at);
        const key = date.toLocaleString('default', { month: 'short', year: 'numeric' });
        if (monthlyMap[key]) {
          monthlyMap[key].opened++;
          if (t.status === 'completed') {
            monthlyMap[key].closed++;
          }
        }
      }
    });
    return Object.values(monthlyMap);
  };

  if (!user) {
    return (
      <div className="login-container">
        <div className="login-card">
          <h1>Task Master</h1>
          <p>Organize your life, one task at a time.</p>
          <div className="login-button-wrapper">
            <GoogleLogin
              onSuccess={handleLoginSuccess}
              onError={() => console.log('Login Failed')}
              useOneTap
            />
          </div>
          <button className="mock-login-btn" onClick={() => handleLoginSuccess({ credential: 'mock-token' })}>
            Demo Login (No Google Account)
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="todo-container">
      <header className="app-header">
        <div className="user-profile">
          <img src={user.picture} alt={user.full_name} className="user-avatar" />
          <div className="user-info">
            <span className="user-name">{user.full_name}</span>
            <button className="logout-btn" onClick={handleLogout} title="Logout">
              <LogOut size={16} /> Logout
            </button>
          </div>
        </div>
        <h1>Task Master</h1>
        <div className="header-actions">
           <button className={`nav-btn ${activeTab === 'tasks' ? 'active' : ''}`} onClick={() => setActiveTab('tasks')}>
             <ListTodo size={18} /> Tasks
           </button>
           <button className={`nav-btn ${activeTab === 'reports' ? 'active' : ''}`} onClick={() => setActiveTab('reports')}>
             <LayoutDashboard size={18} /> Reports
           </button>
           <button className="seed-btn" onClick={seedData} title="Load Dummy Data">
             <RefreshCw size={18} />
           </button>
        </div>
      </header>
      
      {activeTab === 'tasks' ? (
        <>
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
              {todos.length === 0 && <p className="empty-state">No tasks yet. Add one above or load dummy data!</p>}
              {todos.map((todo) => (
                <li key={todo.id} className={`todo-item ${todo.completed ? 'completed' : ''}`}>
                  <div className="todo-checkbox" onClick={() => toggleTodo(todo)}>
                    <div className={`checkbox-custom ${todo.status}`}>
                      {todo.completed && <span>✓</span>}
                      {todo.status === 'in-progress' && <span className="dot"></span>}
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
        </>
      ) : (
        <div className="reports-container">
          <div className="chart-card">
            <h3><PieIcon size={20} /> Status Distribution</h3>
            <div className="chart-wrapper">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={getPieData()}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {getPieData().map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="chart-card">
            <h3><LayoutDashboard size={20} /> Monthly Report (Opened vs Closed)</h3>
            <div className="chart-wrapper">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={getMonthlyData()}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="opened" fill="#6366f1" name="Tasks Opened" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="closed" fill="#22c55e" name="Tasks Closed" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function App() {
  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <AppContent />
    </GoogleOAuthProvider>
  )
}

export default App
