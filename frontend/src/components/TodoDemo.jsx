// TodoDemo.jsx - Comprehensive Todo Management Component with Full CRUD Operations
import React, { useState, useEffect } from 'react';
import { 
  Plus, 
  Edit3, 
  Trash2, 
  Check, 
  X, 
  Calendar, 
  Tag, 
  User, 
  AlertCircle, 
  Clock, 
  CheckCircle2, 
  Circle,
  Filter,
  Search,
  BarChart3,
  RefreshCw,
  Save
} from 'lucide-react';

const TodoDemo = () => {
  // State management
  const [todos, setTodos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({});
  const [categories, setCategories] = useState([]);
  const [priorities] = useState(['low', 'medium', 'high', 'urgent']);

  // Form and UI state
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingTodo, setEditingTodo] = useState(null);
  const [showStats, setShowStats] = useState(false);
  const [filters, setFilters] = useState({
    search: '',
    completed: null,
    priority: '',
    category: '',
    user_id: ''
  });

  // Form data
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium',
    category: '',
    due_date: '',
    user_id: '',
    tags: [],
    completed: false
  });

  const [newTag, setNewTag] = useState('');

  // API base URL
  const API_BASE = 'http://localhost:8000/api/v1';

  // Load data on component mount
  useEffect(() => {
    loadTodos();
    loadStats();
    loadCategories();
  }, []);

  // Load todos with current filters
  useEffect(() => {
    loadTodos();
  }, [filters]);

  // API functions
  const loadTodos = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = new URLSearchParams();
      if (filters.completed !== null) params.append('completed', filters.completed);
      if (filters.priority) params.append('priority', filters.priority);
      if (filters.category) params.append('category', filters.category);
      if (filters.user_id) params.append('user_id', filters.user_id);

      const response = await fetch(`${API_BASE}/todos?${params}`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      
      let data = await response.json();
      
      // Apply search filter on frontend
      if (filters.search) {
        const searchLower = filters.search.toLowerCase();
        data = data.filter(todo => 
          todo.title.toLowerCase().includes(searchLower) ||
          (todo.description && todo.description.toLowerCase().includes(searchLower)) ||
          (todo.category && todo.category.toLowerCase().includes(searchLower))
        );
      }
      
      setTodos(data);
    } catch (err) {
      console.error('Failed to load todos:', err);
      setError(`Failed to load todos: ${err.message}`);
      setTodos([]);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/todos/stats/summary`);
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  };

  const loadCategories = async () => {
    try {
      const response = await fetch(`${API_BASE}/todos/categories`);
      if (response.ok) {
        const data = await response.json();
        setCategories(data.categories || []);
      }
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  const createTodo = async (todoData) => {
    try {
      const response = await fetch(`${API_BASE}/todos`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(todoData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create todo');
      }

      const newTodo = await response.json();
      setTodos(prevTodos => [newTodo, ...prevTodos]);
      loadStats();
      loadCategories();
      return newTodo;
    } catch (err) {
      console.error('Failed to create todo:', err);
      setError(`Failed to create todo: ${err.message}`);
      throw err;
    }
  };

  const updateTodo = async (todoId, updateData) => {
    try {
      const response = await fetch(`${API_BASE}/todos/${todoId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update todo');
      }

      const updatedTodo = await response.json();
      setTodos(prevTodos => 
        prevTodos.map(todo => todo.id === todoId ? updatedTodo : todo)
      );
      loadStats();
      return updatedTodo;
    } catch (err) {
      console.error('Failed to update todo:', err);
      setError(`Failed to update todo: ${err.message}`);
      throw err;
    }
  };

  const deleteTodo = async (todoId) => {
    try {
      const response = await fetch(`${API_BASE}/todos/${todoId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete todo');
      }

      setTodos(prevTodos => prevTodos.filter(todo => todo.id !== todoId));
      loadStats();
      loadCategories();
    } catch (err) {
      console.error('Failed to delete todo:', err);
      setError(`Failed to delete todo: ${err.message}`);
      throw err;
    }
  };

  const toggleTodoCompletion = async (todoId) => {
    try {
      const response = await fetch(`${API_BASE}/todos/${todoId}/complete`, {
        method: 'PATCH',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to toggle todo');
      }

      const result = await response.json();
      setTodos(prevTodos => 
        prevTodos.map(todo => todo.id === todoId ? result.todo : todo)
      );
      loadStats();
    } catch (err) {
      console.error('Failed to toggle todo:', err);
      setError(`Failed to toggle todo: ${err.message}`);
    }
  };

  // Form handlers
  const handleFormSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.title.trim()) {
      setError('Title is required');
      return;
    }

    try {
      setError(null);
      
      const todoData = {
        ...formData,
        due_date: formData.due_date || null,
        tags: formData.tags.filter(tag => tag.trim() !== '')
      };

      if (editingTodo) {
        await updateTodo(editingTodo.id, todoData);
        setEditingTodo(null);
      } else {
        await createTodo(todoData);
        setShowAddForm(false);
      }

      resetForm();
    } catch (err) {
      // Error is already set in the API functions
    }
  };

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      priority: 'medium',
      category: '',
      due_date: '',
      user_id: '',
      tags: [],
      completed: false
    });
    setNewTag('');
  };

  const handleEditTodo = (todo) => {
    setFormData({
      title: todo.title,
      description: todo.description || '',
      priority: todo.priority || 'medium',
      category: todo.category || '',
      due_date: todo.due_date ? todo.due_date.split('T')[0] : '',
      user_id: todo.user_id || '',
      tags: todo.tags || [],
      completed: todo.completed
    });
    setEditingTodo(todo);
    setShowAddForm(true);
  };

  const handleDeleteTodo = async (todoId, todoTitle) => {
    if (window.confirm(`Are you sure you want to delete "${todoTitle}"?`)) {
      await deleteTodo(todoId);
    }
  };

  const addTag = () => {
    if (newTag.trim() && !formData.tags.includes(newTag.trim())) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, newTag.trim()]
      }));
      setNewTag('');
    }
  };

  const removeTag = (tagToRemove) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  const clearFilters = () => {
    setFilters({
      search: '',
      completed: null,
      priority: '',
      category: '',
      user_id: ''
    });
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'urgent': return 'text-red-400 bg-red-900/20';
      case 'high': return 'text-orange-400 bg-orange-900/20';
      case 'medium': return 'text-yellow-400 bg-yellow-900/20';
      case 'low': return 'text-green-400 bg-green-900/20';
      default: return 'text-neutral-400 bg-neutral-900/20';
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString();
  };

  const isOverdue = (dateString, completed) => {
    if (!dateString || completed) return false;
    return new Date(dateString) < new Date();
  };

  return (
    <div className="min-h-screen bg-neutral-900 text-white">
      {/* Header */}
      <div className="bg-neutral-800 border-b border-neutral-700 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <h1 className="text-3xl font-bold text-blue-400">Todo Demo</h1>
            <div className="flex items-center gap-2 px-3 py-1 rounded-full text-sm border border-neutral-600">
              <CheckCircle2 size={16} />
              <span className="text-green-400">
                {stats.completed || 0} / {stats.total_todos || 0} Complete
              </span>
            </div>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => setShowStats(!showStats)}
              className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
            >
              <BarChart3 size={20} />
              Stats
            </button>
            <button
              onClick={loadTodos}
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-neutral-600 px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
            >
              <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
              Refresh
            </button>
            <button
              onClick={() => {
                resetForm();
                setEditingTodo(null);
                setShowAddForm(true);
              }}
              className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
            >
              <Plus size={20} />
              Add Todo
            </button>
          </div>
        </div>

        {/* Stats Panel */}
        {showStats && (
          <div className="bg-neutral-700 rounded-lg p-4 mb-4">
            <h3 className="text-white font-medium mb-3">Statistics</h3>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
              <div>
                <span className="text-neutral-400">Total:</span>
                <div className="text-blue-400 font-medium text-lg">{stats.total_todos || 0}</div>
              </div>
              <div>
                <span className="text-neutral-400">Completed:</span>
                <div className="text-green-400 font-medium text-lg">{stats.completed || 0}</div>
              </div>
              <div>
                <span className="text-neutral-400">Pending:</span>
                <div className="text-yellow-400 font-medium text-lg">{stats.pending || 0}</div>
              </div>
              <div>
                <span className="text-neutral-400">High Priority:</span>
                <div className="text-red-400 font-medium text-lg">{stats.high_priority || 0}</div>
              </div>
              <div>
                <span className="text-neutral-400">Completion Rate:</span>
                <div className="text-purple-400 font-medium text-lg">{stats.completion_rate || 0}%</div>
              </div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-neutral-400" size={20} />
            <input
              type="text"
              placeholder="Search todos..."
              value={filters.search}
              onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
              className="w-full bg-neutral-700 border border-neutral-600 rounded-lg pl-10 pr-4 py-2 text-white placeholder-neutral-400 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>

          <select
            value={filters.completed === null ? '' : filters.completed}
            onChange={(e) => setFilters(prev => ({ 
              ...prev, 
              completed: e.target.value === '' ? null : e.target.value === 'true' 
            }))}
            className="bg-neutral-700 border border-neutral-600 rounded-lg px-3 py-2 text-white text-sm"
          >
            <option value="">All Status</option>
            <option value="false">Pending</option>
            <option value="true">Completed</option>
          </select>

          <select
            value={filters.priority}
            onChange={(e) => setFilters(prev => ({ ...prev, priority: e.target.value }))}
            className="bg-neutral-700 border border-neutral-600 rounded-lg px-3 py-2 text-white text-sm"
          >
            <option value="">All Priorities</option>
            {priorities.map(priority => (
              <option key={priority} value={priority}>
                {priority.charAt(0).toUpperCase() + priority.slice(1)}
              </option>
            ))}
          </select>

          <select
            value={filters.category}
            onChange={(e) => setFilters(prev => ({ ...prev, category: e.target.value }))}
            className="bg-neutral-700 border border-neutral-600 rounded-lg px-3 py-2 text-white text-sm"
          >
            <option value="">All Categories</option>
            {categories.map(category => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>

          <button
            onClick={clearFilters}
            className="bg-neutral-700 hover:bg-neutral-600 px-3 py-2 rounded-lg text-sm transition-colors"
          >
            Clear Filters
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-900/20 border border-red-700 rounded-lg p-4 m-6 flex items-center gap-3">
          <AlertCircle className="text-red-400 flex-shrink-0" size={20} />
          <div>
            <p className="text-red-400 font-medium">Error</p>
            <p className="text-red-300 text-sm">{error}</p>
          </div>
          <button
            onClick={() => setError(null)}
            className="ml-auto text-red-400 hover:text-red-300"
          >
            <X size={20} />
          </button>
        </div>
      )}

      {/* Add/Edit Form */}
      {showAddForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-white">
                {editingTodo ? 'Edit Todo' : 'Add New Todo'}
              </h2>
              <button
                onClick={() => {
                  setShowAddForm(false);
                  setEditingTodo(null);
                  resetForm();
                }}
                className="text-neutral-400 hover:text-white"
              >
                <X size={24} />
              </button>
            </div>

            <form onSubmit={handleFormSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-2">
                  Title *
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                  className="w-full bg-neutral-700 border border-neutral-600 rounded-lg px-3 py-2 text-white placeholder-neutral-400 focus:outline-none focus:border-blue-500"
                  placeholder="Enter todo title..."
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-2">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full bg-neutral-700 border border-neutral-600 rounded-lg px-3 py-2 text-white placeholder-neutral-400 focus:outline-none focus:border-blue-500"
                  placeholder="Enter description..."
                  rows={3}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-neutral-300 mb-2">
                    Priority
                  </label>
                  <select
                    value={formData.priority}
                    onChange={(e) => setFormData(prev => ({ ...prev, priority: e.target.value }))}
                    className="w-full bg-neutral-700 border border-neutral-600 rounded-lg px-3 py-2 text-white"
                  >
                    {priorities.map(priority => (
                      <option key={priority} value={priority}>
                        {priority.charAt(0).toUpperCase() + priority.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-neutral-300 mb-2">
                    Category
                  </label>
                  <input
                    type="text"
                    value={formData.category}
                    onChange={(e) => setFormData(prev => ({ ...prev, category: e.target.value }))}
                    className="w-full bg-neutral-700 border border-neutral-600 rounded-lg px-3 py-2 text-white placeholder-neutral-400 focus:outline-none focus:border-blue-500"
                    placeholder="Enter category..."
                    list="categories"
                  />
                  <datalist id="categories">
                    {categories.map(category => (
                      <option key={category} value={category} />
                    ))}
                  </datalist>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-neutral-300 mb-2">
                    Due Date
                  </label>
                  <input
                    type="date"
                    value={formData.due_date}
                    onChange={(e) => setFormData(prev => ({ ...prev, due_date: e.target.value }))}
                    className="w-full bg-neutral-700 border border-neutral-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-neutral-300 mb-2">
                    User ID
                  </label>
                  <input
                    type="text"
                    value={formData.user_id}
                    onChange={(e) => setFormData(prev => ({ ...prev, user_id: e.target.value }))}
                    className="w-full bg-neutral-700 border border-neutral-600 rounded-lg px-3 py-2 text-white placeholder-neutral-400 focus:outline-none focus:border-blue-500"
                    placeholder="Enter user ID..."
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-2">
                  Tags
                </label>
                <div className="flex gap-2 mb-2">
                  <input
                    type="text"
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
                    className="flex-1 bg-neutral-700 border border-neutral-600 rounded-lg px-3 py-2 text-white placeholder-neutral-400 focus:outline-none focus:border-blue-500"
                    placeholder="Add tag..."
                  />
                  <button
                    type="button"
                    onClick={addTag}
                    className="bg-blue-600 hover:bg-blue-700 px-3 py-2 rounded-lg transition-colors"
                  >
                    <Plus size={16} />
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {formData.tags.map((tag, index) => (
                    <span
                      key={index}
                      className="bg-blue-600/20 text-blue-400 px-3 py-1 rounded-full text-sm flex items-center gap-2"
                    >
                      {tag}
                      <button
                        type="button"
                        onClick={() => removeTag(tag)}
                        className="text-blue-400 hover:text-blue-300"
                      >
                        <X size={14} />
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              {editingTodo && (
                <div>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={formData.completed}
                      onChange={(e) => setFormData(prev => ({ ...prev, completed: e.target.checked }))}
                      className="text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-neutral-300 text-sm">Mark as completed</span>
                  </label>
                </div>
              )}

              <div className="flex gap-3 pt-4 border-t border-neutral-700">
                <button
                  type="submit"
                  className="bg-green-600 hover:bg-green-700 text-white py-2 px-6 rounded-lg flex items-center gap-2 transition-colors"
                >
                  <Save size={16} />
                  {editingTodo ? 'Update Todo' : 'Create Todo'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowAddForm(false);
                    setEditingTodo(null);
                    resetForm();
                  }}
                  className="bg-neutral-700 hover:bg-neutral-600 text-white py-2 px-4 rounded-lg flex items-center gap-2 transition-colors"
                >
                  <X size={16} />
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Todo List */}
      <div className="p-6">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-neutral-400 text-lg">Loading todos...</div>
          </div>
        ) : (
          <>
            <div className="bg-neutral-800 rounded-lg p-4 mb-6">
              <div className="flex items-center gap-8 text-sm text-neutral-400">
                <span>{todos.length} todos found</span>
                <span>Completed: {todos.filter(t => t.completed).length}</span>
                <span>Pending: {todos.filter(t => !t.completed).length}</span>
                {(filters.search || filters.completed !== null || filters.priority || filters.category || filters.user_id) && (
                  <span className="text-blue-400">Filtered</span>
                )}
              </div>
            </div>

            <div className="space-y-4">
              {todos.map(todo => (
                <div 
                  key={todo.id} 
                  className={`bg-neutral-800 rounded-lg border border-neutral-700 p-4 hover:border-neutral-600 transition-all ${
                    todo.completed ? 'opacity-75' : ''
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3 flex-1">
                      <button
                        onClick={() => toggleTodoCompletion(todo.id)}
                        className={`mt-1 flex-shrink-0 ${
                          todo.completed 
                            ? 'text-green-400 hover:text-green-300' 
                            : 'text-neutral-400 hover:text-green-400'
                        } transition-colors`}
                      >
                        {todo.completed ? <CheckCircle2 size={20} /> : <Circle size={20} />}
                      </button>

                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className={`font-medium ${
                            todo.completed ? 'line-through text-neutral-400' : 'text-white'
                          }`}>
                            {todo.title}
                          </h3>
                          
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(todo.priority)}`}>
                            {todo.priority}
                          </span>

                          {todo.category && (
                            <span className="px-2 py-1 rounded-full text-xs bg-blue-600/20 text-blue-400">
                              {todo.category}
                            </span>
                          )}

                          {todo.due_date && (
                            <span className={`px-2 py-1 rounded-full text-xs flex items-center gap-1 ${
                              isOverdue(todo.due_date, todo.completed)
                                ? 'bg-red-600/20 text-red-400'
                                : 'bg-purple-600/20 text-purple-400'
                            }`}>
                              <Calendar size={12} />
                              {formatDate(todo.due_date)}
                              {isOverdue(todo.due_date, todo.completed) && ' (Overdue)'}
                            </span>
                          )}
                        </div>

                        {todo.description && (
                          <p className={`text-sm mb-2 ${
                            todo.completed ? 'text-neutral-500' : 'text-neutral-300'
                          }`}>
                            {todo.description}
                          </p>
                        )}

                        <div className="flex items-center gap-4 text-xs text-neutral-400">
                          {todo.user_id && (
                            <span className="flex items-center gap-1">
                              <User size={12} />
                              {todo.user_id}
                            </span>
                          )}
                          
                          <span className="flex items-center gap-1">
                            <Clock size={12} />
                            {formatDate(todo.created_at)}
                          </span>

                          {todo.tags && todo.tags.length > 0 && (
                            <div className="flex items-center gap-1">
                              <Tag size={12} />
                              <span>{todo.tags.join(', ')}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 ml-4">
                      <button
                        onClick={() => handleEditTodo(todo)}
                        className="text-neutral-400 hover:text-blue-400 p-2 rounded-lg hover:bg-neutral-700 transition-colors"
                        title="Edit todo"
                      >
                        <Edit3 size={16} />
                      </button>
                      
                      <button
                        onClick={() => handleDeleteTodo(todo.id, todo.title)}
                        className="text-neutral-400 hover:text-red-400 p-2 rounded-lg hover:bg-neutral-700 transition-colors"
                        title="Delete todo"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {todos.length === 0 && !loading && (
              <div className="text-center py-12">
                <div className="text-neutral-400 text-lg mb-2">No todos found</div>
                <div className="text-neutral-500 mb-4">
                  {(filters.search || filters.completed !== null || filters.priority || filters.category || filters.user_id)
                    ? 'Try adjusting your filters'
                    : 'Create your first todo to get started'}
                </div>
                <button
                  onClick={() => {
                    resetForm();
                    setEditingTodo(null);
                    setShowAddForm(true);
                  }}
                  className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg flex items-center gap-2 mx-auto transition-colors"
                >
                  <Plus size={20} />
                  Add Todo
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default TodoDemo;