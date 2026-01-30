/**
 * TB Personal OS - Dashboard Page
 */

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  CheckSquare, 
  Inbox, 
  Calendar, 
  Zap,
  Sun,
  TrendingUp,
  Clock,
  Plus
} from 'lucide-react';
import { Card, CardTitle, CardContent, Badge, Button } from '../components/ui';
import { api } from '../services/api';

interface DashboardStats {
  tasks_today: number;
  tasks_overdue: number;
  inbox_pending: number;
  energy_level?: number;
}

interface TaskItem {
  id: string;
  title: string;
  priority: string;
  due_date?: string;
  status: string;
}

interface InboxItem {
  id: string;
  content: string;
  source: string;
  created_at: string;
}

export const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [todayTasks, setTodayTasks] = useState<TaskItem[]>([]);
  const [inboxItems, setInboxItems] = useState<InboxItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [contextData, tasksData, inboxData] = await Promise.all([
        api.getAssistantContext().catch(() => null),
        api.getTasksToday().catch(() => ({ items: [] })),
        api.getInbox({ status: 'pending', limit: 5 }).catch(() => ({ items: [] })),
      ]);

      setStats(contextData);
      setTodayTasks(tasksData.items || tasksData || []);
      setInboxItems(inboxData.items || inboxData || []);
    } catch (err: any) {
      setError('Erro ao carregar dados');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const getPriorityBadge = (priority: string) => {
    const variants: Record<string, 'danger' | 'warning' | 'info' | 'default'> = {
      urgent: 'danger',
      high: 'warning',
      medium: 'info',
      low: 'default',
    };
    return <Badge variant={variants[priority] || 'default'}>{priority}</Badge>;
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Bom dia';
    if (hour < 18) return 'Boa tarde';
    return 'Boa noite';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="relative">
          <div className="w-16 h-16 rounded-full border-4 border-dark-bg-tertiary border-t-brand-purple-500 animate-spin-slow" />
          <div className="absolute inset-0 w-16 h-16 rounded-full bg-brand-purple-500/20 blur-xl animate-pulse" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-bg-primary pb-24 md:pb-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between animate-slide-down">
          <div>
            <h1 className="text-display-lg font-bold text-white mb-2">
              {getGreeting()}, <span className="text-gradient">Igor</span>! 👋
            </h1>
            <p className="text-xl text-dark-text-secondary">
              {new Date().toLocaleDateString('pt-BR', { 
                weekday: 'long', 
                day: 'numeric', 
                month: 'long' 
              })}
            </p>
          </div>
          <div className="mt-4 sm:mt-0">
            <Button variant="gradient" leftIcon={<Plus className="w-4 h-4" />}>
              Nova Tarefa
            </Button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 animate-fade-in">
          <Card className="glass-card flex items-center p-4 hover:scale-105 transition-transform">
            <div className="p-3 rounded-lg bg-accent-blue-500/10 border border-accent-blue-500/20">
              <CheckSquare className="w-6 h-6 text-accent-blue-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-dark-text-secondary">Tarefas Hoje</p>
              <p className="text-2xl font-bold text-white">
                {stats?.tasks_today || todayTasks.length || 0}
              </p>
            </div>
          </Card>

          <Card className="glass-card flex items-center p-4 hover:scale-105 transition-transform">
            <div className="p-3 rounded-lg bg-status-error/10 border border-status-error/20">
              <Clock className="w-6 h-6 text-status-error" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-dark-text-secondary">Atrasadas</p>
              <p className="text-2xl font-bold text-white">
                {stats?.tasks_overdue || 0}
              </p>
            </div>
          </Card>

          <Card className="glass-card flex items-center p-4 hover:scale-105 transition-transform">
            <div className="p-3 rounded-lg bg-brand-purple-500/10 border border-brand-purple-500/20">
              <Inbox className="w-6 h-6 text-brand-purple-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-dark-text-secondary">Inbox</p>
              <p className="text-2xl font-bold text-white">
                {stats?.inbox_pending || inboxItems.length || 0}
              </p>
            </div>
          </Card>

          <Card className="glass-card flex items-center p-4 hover:scale-105 transition-transform">
            <div className="p-3 rounded-lg bg-accent-yellow-500/10 border border-accent-yellow-500/20">
              <Zap className="w-6 h-6 text-accent-yellow-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-dark-text-secondary">Energia</p>
              <p className="text-2xl font-bold text-white">
                {stats?.energy_level || '-'}/10
              </p>
            </div>
          </Card>
        </div>

        {/* Main Content */}
        <div className="grid lg:grid-cols-2 gap-6 animate-slide-up">
          {/* Today's Tasks */}
          <Card className="glass-card">
            <div className="flex items-center justify-between mb-4">
              <CardTitle className="flex items-center text-white">
                <Sun className="w-5 h-5 mr-2 text-accent-yellow-400" />
                Tarefas de Hoje
              </CardTitle>
              <Link to="/tasks" className="text-sm text-brand-purple-400 hover:text-brand-purple-300 transition-colors">
                Ver todas →
              </Link>
            </div>
            <CardContent>
              {todayTasks.length === 0 ? (
                <div className="text-center py-8 text-dark-text-secondary">
                  <CheckSquare className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>Nenhuma tarefa para hoje!</p>
                  <p className="text-sm mt-1">Aproveite o dia livre 🎉</p>
                </div>
              ) : (
                <ul className="space-y-3">
                  {todayTasks.slice(0, 5).map((task) => (
                    <li 
                      key={task.id} 
                      className="flex items-center justify-between p-3 bg-dark-bg-secondary rounded-lg hover:bg-dark-bg-tertiary transition-colors border border-dark-border"
                    >
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          className="w-4 h-4 text-brand-purple-500 rounded border-dark-border focus:ring-brand-purple-500"
                          checked={task.status === 'completed'}
                          readOnly
                        />
                        <span className={`ml-3 ${task.status === 'completed' ? 'line-through text-dark-text-tertiary' : 'text-white'}`}>
                          {task.title}
                        </span>
                      </div>
                      {getPriorityBadge(task.priority)}
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          {/* Inbox */}
          <Card className="glass-card">
            <div className="flex items-center justify-between mb-4">
              <CardTitle className="flex items-center text-white">
                <Inbox className="w-5 h-5 mr-2 text-brand-purple-400" />
                Inbox Recente
              </CardTitle>
              <Link to="/inbox" className="text-sm text-brand-purple-400 hover:text-brand-purple-300 transition-colors">
                Ver todos →
              </Link>
            </div>
            <CardContent>
              {inboxItems.length === 0 ? (
                <div className="text-center py-8 text-dark-text-secondary">
                  <Inbox className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>Inbox vazio!</p>
                  <p className="text-sm mt-1">Todas as mensagens foram processadas</p>
                </div>
              ) : (
                <ul className="space-y-3">
                  {inboxItems.map((item) => (
                    <li 
                      key={item.id} 
                      className="p-3 bg-dark-bg-secondary rounded-lg hover:bg-dark-bg-tertiary transition-colors border border-dark-border"
                    >
                      <p className="text-white line-clamp-2">{item.content}</p>
                      <div className="flex items-center mt-2 text-xs text-dark-text-secondary">
                        <Badge size="sm">{item.source}</Badge>
                        <span className="ml-2">
                          {new Date(item.created_at).toLocaleDateString('pt-BR')}
                        </span>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <Card className="glass-card animate-slide-up" style={{animationDelay: '0.1s'}}>
          <CardTitle className="flex items-center mb-4 text-white">
            <TrendingUp className="w-5 h-5 mr-2 text-accent-green-400" />
            Ações Rápidas
          </CardTitle>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Button variant="outline" className="h-auto py-4 flex-col border-dark-border hover:border-brand-purple-500 hover:bg-brand-purple-500/10 transition-all">
                <Zap className="w-6 h-6 mb-2 text-accent-yellow-400" />
                <span className="text-white">Check-in Energia</span>
              </Button>
              <Button variant="outline" className="h-auto py-4 flex-col border-dark-border hover:border-accent-blue-500 hover:bg-accent-blue-500/10 transition-all">
                <Calendar className="w-6 h-6 mb-2 text-accent-blue-400" />
                <span className="text-white">Ver Agenda</span>
              </Button>
              <Button variant="outline" className="h-auto py-4 flex-col border-dark-border hover:border-accent-yellow-500 hover:bg-accent-yellow-500/10 transition-all">
                <Sun className="w-6 h-6 mb-2 text-accent-yellow-400" />
                <span className="text-white">Rotina Manhã</span>
              </Button>
              <Link to="/chat" className="w-full">
                <Button variant="outline" className="w-full h-auto py-4 flex-col border-dark-border hover:border-brand-purple-500 hover:bg-brand-purple-500/10 transition-all">
                  <span className="text-2xl mb-2">🤖</span>
                  <span className="text-white">Falar com IA</span>
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default DashboardPage;
