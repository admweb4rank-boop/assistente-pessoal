/**
 * TB Personal OS - Tasks Page
 */

import React, { useEffect, useState } from 'react';
import { 
  Plus, 
  Filter, 
  Search,
  CheckSquare,
  Clock,
  AlertTriangle,
  MoreVertical,
  Trash2,
  Edit,
  Zap
} from 'lucide-react';
import { GlassCard, Badge, Button, Input } from '../components/ui';
import { api } from '../services/api';
import type { Task, Priority, TaskStatus } from '../types';

export const TasksPage: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'pending' | 'completed'>('pending');
  const [searchQuery, setSearchQuery] = useState('');
  const [showNewTaskForm, setShowNewTaskForm] = useState(false);
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [newTaskPriority, setNewTaskPriority] = useState<Priority>('medium');

  useEffect(() => {
    loadTasks();
  }, [filter]);

  const loadTasks = async () => {
    setIsLoading(true);
    try {
      const data = await api.getTasks({ 
        status: filter === 'all' ? undefined : filter,
        limit: 50 
      });
      setTasks(data.items || data || []);
    } catch (err) {
      console.error('Failed to load tasks:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTaskTitle.trim()) return;

    try {
      await api.createTask({
        title: newTaskTitle,
        priority: newTaskPriority,
      });
      setNewTaskTitle('');
      setShowNewTaskForm(false);
      loadTasks();
    } catch (err) {
      console.error('Failed to create task:', err);
    }
  };

  const handleCompleteTask = async (taskId: string) => {
    try {
      await api.completeTask(taskId);
      loadTasks();
    } catch (err) {
      console.error('Failed to complete task:', err);
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    if (!confirm('Tem certeza que deseja excluir esta tarefa?')) return;
    
    try {
      await api.deleteTask(taskId);
      loadTasks();
    } catch (err) {
      console.error('Failed to delete task:', err);
    }
  };

  const getPriorityBadge = (priority: Priority) => {
    const config: Record<Priority, { variant: 'danger' | 'warning' | 'purple' | 'default', label: string }> = {
      urgent: { variant: 'danger', label: '🔥 Urgente' },
      high: { variant: 'warning', label: '⚡ Alta' },
      medium: { variant: 'purple', label: '📌 Média' },
      low: { variant: 'default', label: '💤 Baixa' },
    };
    const { variant, label } = config[priority] || config.medium;
    return <Badge variant={variant}>{label}</Badge>;
  };

  const filteredTasks = tasks.filter(task => 
    task.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const groupedTasks = {
    overdue: filteredTasks.filter(t => 
      t.status !== 'completed' && 
      t.due_date && 
      new Date(t.due_date) < new Date()
    ),
    today: filteredTasks.filter(t => {
      if (t.status === 'completed') return false;
      if (!t.due_date) return false;
      const today = new Date().toDateString();
      return new Date(t.due_date).toDateString() === today;
    }),
    upcoming: filteredTasks.filter(t => {
      if (t.status === 'completed') return false;
      if (!t.due_date) return true; // No date = upcoming
      const taskDate = new Date(t.due_date);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      return taskDate > today;
    }),
    completed: filteredTasks.filter(t => t.status === 'completed'),
  };

  return (
    <div className="min-h-screen bg-dark-bg-primary pb-24 md:pb-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 animate-slide-down">
          <div>
            <h1 className="text-display-lg font-bold text-white mb-2">
              ✅ <span className="text-gradient">Tarefas</span>
            </h1>
            <p className="text-xl text-dark-text-secondary">Organize suas atividades e projetos</p>
          </div>
          <Button 
          variant="gradient"
          leftIcon={<Plus className="w-4 h-4" />}
          onClick={() => setShowNewTaskForm(true)}
          className="shadow-glow-purple"
        >
          Nova Tarefa
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <Input
            placeholder="Buscar tarefas..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            leftIcon={<Search className="w-5 h-5" />}
          />
        </div>
        <div className="flex gap-2">
          {(['pending', 'completed', 'all'] as const).map((f) => (
            <Button
              key={f}
              variant={filter === f ? 'primary' : 'outline'}
              size="sm"
              onClick={() => setFilter(f)}
            >
              {f === 'pending' ? 'Pendentes' : f === 'completed' ? 'Concluídas' : 'Todas'}
            </Button>
          ))}
        </div>
      </div>

      {/* New Task Form */}
      {showNewTaskForm && (
        <GlassCard className="border-2 border-brand-purple-500/30 shadow-glow-purple animate-slide-down">
          <form onSubmit={handleCreateTask} className="space-y-4">
            <Input
              placeholder="O que você precisa fazer?"
              value={newTaskTitle}
              onChange={(e) => setNewTaskTitle(e.target.value)}
              autoFocus
              className="glass-input"
            />
            <div className="flex items-center justify-between">
              <div className="flex gap-2">
                {(['low', 'medium', 'high', 'urgent'] as Priority[]).map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setNewTaskPriority(p)}
                    className={`px-3 py-1 rounded-lg text-sm transition-all duration-300 ${
                      newTaskPriority === p 
                        ? 'bg-brand-purple-500 text-white shadow-glow-purple' 
                        : 'glass-card text-dark-text-secondary hover:border-brand-purple-500/30'
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>
              <div className="flex gap-2">
                <Button variant="ghost" onClick={() => setShowNewTaskForm(false)}>
                  Cancelar
                </Button>
                <Button type="submit" variant="gradient">Criar</Button>
              </div>
            </div>
          </form>
        </GlassCard>
      )}

      {/* Task Lists */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      ) : (
        <div className="space-y-6">
          {/* Overdue */}
          {filter !== 'completed' && groupedTasks.overdue.length > 0 && (
            <GlassCard className="border-l-4 border-l-accent-red-500 shadow-glow-red animate-slide-up">
              <div className="flex items-center text-accent-red-400 mb-4">
                <AlertTriangle className="w-5 h-5 mr-2" />
                <h3 className="text-lg font-semibold">Atrasadas ({groupedTasks.overdue.length})</h3>
              </div>
              <TaskList 
                tasks={groupedTasks.overdue} 
                onComplete={handleCompleteTask}
                onDelete={handleDeleteTask}
                getPriorityBadge={getPriorityBadge}
              />
            </GlassCard>
          )}

          {/* Today */}
          {filter !== 'completed' && groupedTasks.today.length > 0 && (
            <GlassCard className="border-l-4 border-l-accent-yellow-500 shadow-glow-yellow animate-slide-up" style={{ animationDelay: '100ms' }}>
              <div className="flex items-center mb-4">
                <Clock className="w-5 h-5 mr-2 text-accent-yellow-400" />
                <h3 className="text-lg font-semibold text-white">Hoje ({groupedTasks.today.length})</h3>
              </div>
              <TaskList 
                tasks={groupedTasks.today} 
                onComplete={handleCompleteTask}
                onDelete={handleDeleteTask}
                getPriorityBadge={getPriorityBadge}
              />
            </GlassCard>
          )}

          {/* Upcoming */}
          {filter !== 'completed' && groupedTasks.upcoming.length > 0 && (
            <GlassCard className="border-l-4 border-l-brand-purple-500 shadow-glow-purple animate-slide-up" style={{ animationDelay: '200ms' }}>
              <div className="flex items-center mb-4">
                <Zap className="w-5 h-5 mr-2 text-brand-purple-400" />
                <h3 className="text-lg font-semibold text-white">Próximas ({groupedTasks.upcoming.length})</h3>
              </div>
              <TaskList 
                tasks={groupedTasks.upcoming} 
                onComplete={handleCompleteTask}
                onDelete={handleDeleteTask}
                getPriorityBadge={getPriorityBadge}
              />
            </GlassCard>
          )}

          {/* Completed */}
          {(filter === 'completed' || filter === 'all') && groupedTasks.completed.length > 0 && (
            <GlassCard className="opacity-75 animate-slide-up" style={{ animationDelay: '300ms' }}>
              <div className="flex items-center text-dark-text-secondary mb-4">
                <CheckSquare className="w-5 h-5 mr-2" />
                <h3 className="text-lg font-semibold">Concluídas ({groupedTasks.completed.length})</h3>
              </div>
              <TaskList 
                tasks={groupedTasks.completed} 
                onComplete={handleCompleteTask}
                onDelete={handleDeleteTask}
                getPriorityBadge={getPriorityBadge}
                completed
              />
            </GlassCard>
          )}

          {/* Empty State */}
          {filteredTasks.length === 0 && (
            <GlassCard className="text-center py-12 animate-scale-in">
              <CheckSquare className="w-16 h-16 mx-auto text-brand-purple-400/30 mb-4" />
              <h3 className="text-lg font-medium text-white">Nenhuma tarefa encontrada</h3>
              <p className="text-dark-text-secondary mt-1">
                {searchQuery 
                  ? 'Tente ajustar sua busca' 
                  : 'Crie sua primeira tarefa para começar'}
              </p>
              <Button 
                className="mt-4" 
                variant="gradient"
                onClick={() => setShowNewTaskForm(true)}
                leftIcon={<Plus className="w-4 h-4" />}
              >
                Nova Tarefa
              </Button>
            </GlassCard>
          )}
        </div>
      )}
      </div>
    </div>
  );
};

// TaskList Component
interface TaskListProps {
  tasks: Task[];
  onComplete: (id: string) => void;
  onDelete: (id: string) => void;
  getPriorityBadge: (priority: Priority) => React.ReactNode;
  completed?: boolean;
}

const TaskList: React.FC<TaskListProps> = ({ 
  tasks, 
  onComplete, 
  onDelete, 
  getPriorityBadge,
  completed 
}) => (
  <ul className="space-y-2">
    {tasks.map((task) => (
      <li 
        key={task.id}
        className="flex items-center justify-between p-4 glass-card rounded-lg hover:border-brand-purple-500/30 group transition-all duration-300"
      >
        <div className="flex items-center flex-1 min-w-0">
          <input
            type="checkbox"
            checked={task.status === 'completed'}
            onChange={() => onComplete(task.id)}
            className="w-5 h-5 text-brand-purple-500 rounded border-dark-border focus:ring-brand-purple-500 bg-dark-bg-secondary"
          />
          <div className="ml-3 min-w-0">
            <p className={`text-white truncate ${completed ? 'line-through text-dark-text-secondary' : ''}`}>
              {task.title}
            </p>
            {task.due_date && (
              <p className="text-xs text-dark-text-secondary mt-0.5">
                {new Date(task.due_date).toLocaleDateString('pt-BR')}
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2 ml-4">
          {getPriorityBadge(task.priority)}
          <button
            onClick={() => onDelete(task.id)}
            className="p-1.5 text-dark-text-secondary hover:text-accent-red-400 opacity-0 group-hover:opacity-100 transition-all duration-300 hover:scale-110"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </li>
    ))}
  </ul>
);

export default TasksPage;
