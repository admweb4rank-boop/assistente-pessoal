/**
 * TB Personal OS - Enhanced Dashboard Page with Premium Design
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
  Plus,
  Target,
  Activity,
  MessageSquare
} from 'lucide-react';
import { GlassCard, StatCard, Badge, Button } from '../components/ui';
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

export const DashboardPageEnhanced: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [todayTasks, setTodayTasks] = useState<TaskItem[]>([]);
  const [inboxItems, setInboxItems] = useState<InboxItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const currentHour = new Date().getHours();
  const greeting = currentHour < 12 ? 'Bom dia' : currentHour < 18 ? 'Boa tarde' : 'Boa noite';

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setIsLoading(true);
    try {
      const [contextData, tasksData, inboxData] = await Promise.all([
        api.getAssistantContext().catch(() => null),
        api.getTasksToday().catch(() => ({ items: [] })),
        api.getInbox({ status: 'pending', limit: 5 }).catch(() => ({ items: [] })),
      ]);

      setStats(contextData);
      setTodayTasks(tasksData.items || tasksData || []);
      setInboxItems(inboxData.items || inboxData || []);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-dark-bg-primary flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-brand-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-dark-text-secondary">Carregando...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-bg-primary">
      {/* Background Effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-brand-purple-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-brand-blue-500/10 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 p-4 md:p-8 max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-12 animate-slide-down">
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-4xl md:text-5xl font-bold">
              <span className="text-gradient">{greeting}</span>
              <span className="text-white">, Igor</span>
            </h1>
            <Badge variant="green" className="animate-pulse">
              Online
            </Badge>
          </div>
          <p className="text-dark-text-secondary text-lg">
            {new Date().toLocaleDateString('pt-BR', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12 animate-fade-in">
          <StatCard
            label="Tarefas Hoje"
            value={stats?.tasks_today || 0}
            icon={<CheckSquare />}
            trend={{ value: "3 completadas", positive: true }}
          />
          <StatCard
            label="Inbox Pendente"
            value={stats?.inbox_pending || 0}
            icon={<Inbox />}
            trend={{ value: "5 novos", positive: false }}
          />
          <StatCard
            label="Energia"
            value={`${stats?.energy_level || 75}%`}
            icon={<Zap />}
            trend={{ value: "+5%", positive: true }}
          />
          <StatCard
            label="Streak"
            value="12 dias"
            icon={<TrendingUp />}
            trend={{ value: "Recorde!", positive: true }}
          />
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Tasks Column */}
          <div className="lg:col-span-2 space-y-6">
            {/* Quick Actions */}
            <GlassCard className="p-6 animate-scale-in">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-white">Ações Rápidas</h2>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <QuickActionButton
                  icon={<Plus />}
                  label="Nova Tarefa"
                  to="/tasks"
                  gradient="from-brand-purple-500 to-brand-blue-500"
                />
                <QuickActionButton
                  icon={<MessageSquare />}
                  label="Chat IA"
                  to="/chat"
                  gradient="from-brand-blue-500 to-accent-cyan"
                />
                <QuickActionButton
                  icon={<Calendar />}
                  label="Calendário"
                  to="/calendar"
                  gradient="from-accent-green to-accent-cyan"
                />
                <QuickActionButton
                  icon={<Target />}
                  label="Metas"
                  to="/goals"
                  gradient="from-accent-pink to-accent-orange"
                />
              </div>
            </GlassCard>

            {/* Today's Tasks */}
            <GlassCard className="p-6 animate-slide-up">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-brand-purple-500/20 flex items-center justify-center">
                    <CheckSquare className="w-5 h-5 text-brand-purple-400" />
                  </div>
                  <h2 className="text-2xl font-bold text-white">Tarefas de Hoje</h2>
                </div>
                <Link to="/tasks">
                  <Button variant="ghost" size="sm">
                    Ver todas →
                  </Button>
                </Link>
              </div>

              <div className="space-y-3">
                {todayTasks.length > 0 ? (
                  todayTasks.slice(0, 5).map((task) => (
                    <TaskItemCard key={task.id} task={task} />
                  ))
                ) : (
                  <div className="text-center py-12">
                    <div className="text-6xl mb-4">🎉</div>
                    <p className="text-dark-text-secondary">Nenhuma tarefa pendente!</p>
                  </div>
                )}
              </div>
            </GlassCard>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Activity Feed */}
            <GlassCard className="p-6 animate-slide-up" style={{ animationDelay: '0.1s' }}>
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-accent-green/20 flex items-center justify-center">
                  <Activity className="w-5 h-5 text-accent-green" />
                </div>
                <h2 className="text-xl font-bold text-white">Atividade Recente</h2>
              </div>
              <div className="space-y-4">
                <ActivityItem
                  icon="✅"
                  text="Completou 3 tarefas"
                  time="2h atrás"
                />
                <ActivityItem
                  icon="📝"
                  text="Adicionou nota"
                  time="4h atrás"
                />
                <ActivityItem
                  icon="🎯"
                  text="Atingiu meta semanal"
                  time="1d atrás"
                />
              </div>
            </GlassCard>

            {/* Inbox Preview */}
            <GlassCard className="p-6 animate-slide-up" style={{ animationDelay: '0.2s' }}>
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-brand-blue-500/20 flex items-center justify-center">
                    <Inbox className="w-5 h-5 text-brand-blue-400" />
                  </div>
                  <h2 className="text-xl font-bold text-white">Inbox</h2>
                </div>
                <Badge variant="purple">{inboxItems.length}</Badge>
              </div>
              <div className="space-y-3">
                {inboxItems.slice(0, 3).map((item) => (
                  <InboxItemCard key={item.id} item={item} />
                ))}
              </div>
              <Link to="/inbox" className="block mt-4">
                <Button variant="ghost" size="sm" className="w-full">
                  Ver tudo
                </Button>
              </Link>
            </GlassCard>
          </div>
        </div>
      </div>
    </div>
  );
};

// Quick Action Button Component
interface QuickActionButtonProps {
  icon: React.ReactNode;
  label: string;
  to: string;
  gradient: string;
}

const QuickActionButton: React.FC<QuickActionButtonProps> = ({ icon, label, to, gradient }) => (
  <Link to={to}>
    <button className="w-full p-4 glass-card hover:glass-card-hover group">
      <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${gradient} flex items-center justify-center mx-auto mb-2 group-hover:scale-110 transition-transform`}>
        {icon}
      </div>
      <p className="text-sm font-medium text-dark-text-secondary group-hover:text-white transition-colors">
        {label}
      </p>
    </button>
  </Link>
);

// Task Item Card Component
const TaskItemCard: React.FC<{ task: TaskItem }> = ({ task }) => {
  const priorityColors = {
    urgent: 'bg-accent-pink/20 text-accent-pink border-accent-pink/30',
    high: 'bg-accent-orange/20 text-accent-orange border-accent-orange/30',
    medium: 'bg-brand-blue-500/20 text-brand-blue-300 border-brand-blue-500/30',
    low: 'bg-dark-text-tertiary/20 text-dark-text-tertiary border-dark-text-tertiary/30',
  };

  return (
    <div className="glass-card p-4 hover:bg-dark-bg-tertiary transition-colors group cursor-pointer">
      <div className="flex items-start gap-3">
        <input
          type="checkbox"
          className="mt-1 w-5 h-5 rounded border-2 border-brand-purple-500 bg-transparent checked:bg-brand-purple-500 transition-colors cursor-pointer"
        />
        <div className="flex-1 min-w-0">
          <p className="text-white font-medium group-hover:text-gradient transition-colors">
            {task.title}
          </p>
          {task.due_date && (
            <p className="text-sm text-dark-text-tertiary mt-1 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {new Date(task.due_date).toLocaleDateString('pt-BR')}
            </p>
          )}
        </div>
        <span className={`badge ${priorityColors[task.priority as keyof typeof priorityColors] || priorityColors.low}`}>
          {task.priority}
        </span>
      </div>
    </div>
  );
};

// Activity Item Component
const ActivityItem: React.FC<{ icon: string; text: string; time: string }> = ({ icon, text, time }) => (
  <div className="flex items-center gap-3">
    <div className="w-8 h-8 rounded-lg bg-dark-bg-tertiary flex items-center justify-center text-lg">
      {icon}
    </div>
    <div className="flex-1 min-w-0">
      <p className="text-sm text-white">{text}</p>
      <p className="text-xs text-dark-text-tertiary">{time}</p>
    </div>
  </div>
);

// Inbox Item Card Component
const InboxItemCard: React.FC<{ item: InboxItem }> = ({ item }) => (
  <div className="glass-card p-3 hover:bg-dark-bg-tertiary transition-colors cursor-pointer">
    <p className="text-sm text-white line-clamp-2 mb-1">{item.content}</p>
    <div className="flex items-center gap-2">
      <Badge variant="blue" className="text-xs">{item.source}</Badge>
      <span className="text-xs text-dark-text-tertiary">
        {new Date(item.created_at).toLocaleDateString('pt-BR')}
      </span>
    </div>
  </div>
);
