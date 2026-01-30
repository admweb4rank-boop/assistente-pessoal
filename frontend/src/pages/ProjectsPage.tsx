/**
 * TB Personal OS - Projects Page
 */

import React, { useEffect, useState } from 'react';
import { 
  FolderKanban, 
  Plus,
  MoreVertical,
  CheckCircle2,
  Circle,
  Clock,
  AlertCircle,
  Search,
  ChevronRight
} from 'lucide-react';
import { Card, CardContent, Badge, Button, Input } from '../components/ui';
import { api } from '../services/api';
import { Link } from 'react-router-dom';

interface Project {
  id: string;
  name: string;
  description?: string;
  status: 'active' | 'paused' | 'completed' | 'archived';
  priority: 'low' | 'medium' | 'high';
  due_date?: string;
  progress: number;
  tasks_total: number;
  tasks_completed: number;
  created_at: string;
}

export const ProjectsPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await api.get('/projects');
      setProjects(data || []);
    } catch (err: any) {
      setError('Erro ao carregar projetos');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case 'active':
        return <Circle className="w-4 h-4 text-blue-500" />;
      case 'paused':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      default:
        return <Circle className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'success' | 'info' | 'warning' | 'default'> = {
      completed: 'success',
      active: 'info',
      paused: 'warning',
      archived: 'default',
    };
    const labels: Record<string, string> = {
      completed: 'Concluído',
      active: 'Ativo',
      paused: 'Pausado',
      archived: 'Arquivado',
    };
    return <Badge variant={variants[status] || 'default'}>{labels[status] || status}</Badge>;
  };

  const getPriorityBadge = (priority: string) => {
    const variants: Record<string, 'danger' | 'warning' | 'info'> = {
      high: 'danger',
      medium: 'warning',
      low: 'info',
    };
    return <Badge variant={variants[priority] || 'info'}>{priority}</Badge>;
  };

  const filteredProjects = projects.filter(project => {
    const matchesSearch = project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      project.description?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || project.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const projectsByStatus = {
    active: filteredProjects.filter(p => p.status === 'active'),
    paused: filteredProjects.filter(p => p.status === 'paused'),
    completed: filteredProjects.filter(p => p.status === 'completed'),
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="relative">
          <div className="w-16 h-16 rounded-full border-4 border-dark-bg-tertiary border-t-accent-blue-500 animate-spin-slow" />
          <div className="absolute inset-0 w-16 h-16 rounded-full bg-accent-blue-500/20 blur-xl animate-pulse" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-bg-primary pb-24 md:pb-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between animate-slide-down">
          <div>
            <h1 className="text-display-lg font-bold text-white mb-2">
              📁 <span className="text-gradient">Projetos</span>
            </h1>
            <p className="text-xl text-dark-text-secondary">
              Gerencie seus projetos e acompanhe o progresso
            </p>
          </div>
          <Button>
          <Plus className="w-4 h-4 mr-2" />
          Novo Projeto
        </Button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <span className="text-red-700 dark:text-red-400">{error}</span>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            type="text"
            placeholder="Buscar projetos..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm"
        >
          <option value="all">Todos os status</option>
          <option value="active">Ativos</option>
          <option value="paused">Pausados</option>
          <option value="completed">Concluídos</option>
          <option value="archived">Arquivados</option>
        </select>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Total</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {projects.length}
                </p>
              </div>
              <FolderKanban className="w-8 h-8 text-gray-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Ativos</p>
                <p className="text-2xl font-bold text-blue-600">
                  {projectsByStatus.active.length}
                </p>
              </div>
              <Circle className="w-8 h-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Pausados</p>
                <p className="text-2xl font-bold text-yellow-600">
                  {projectsByStatus.paused.length}
                </p>
              </div>
              <Clock className="w-8 h-8 text-yellow-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Concluídos</p>
                <p className="text-2xl font-bold text-green-600">
                  {projectsByStatus.completed.length}
                </p>
              </div>
              <CheckCircle2 className="w-8 h-8 text-green-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Projects List */}
      {filteredProjects.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <FolderKanban className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              Nenhum projeto encontrado
            </h3>
            <p className="text-gray-500 mb-4">
              {searchTerm || statusFilter !== 'all' 
                ? 'Tente ajustar os filtros'
                : 'Crie seu primeiro projeto para começar'
              }
            </p>
            {!searchTerm && statusFilter === 'all' && (
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                Criar Projeto
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredProjects.map(project => (
            <Card key={project.id} className="hover:shadow-lg transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(project.status)}
                    <h3 className="font-medium text-gray-900 dark:text-white">
                      {project.name}
                    </h3>
                  </div>
                  <button className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
                    <MoreVertical className="w-4 h-4 text-gray-400" />
                  </button>
                </div>

                {project.description && (
                  <p className="text-sm text-gray-500 mb-3 line-clamp-2">
                    {project.description}
                  </p>
                )}

                <div className="flex items-center gap-2 mb-3">
                  {getStatusBadge(project.status)}
                  {getPriorityBadge(project.priority)}
                </div>

                {/* Progress Bar */}
                <div className="mb-3">
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-gray-500">Progresso</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {project.progress}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div 
                      className="bg-blue-500 h-2 rounded-full transition-all"
                      style={{ width: `${project.progress}%` }}
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">
                    {project.tasks_completed}/{project.tasks_total} tarefas
                  </span>
                  <Link 
                    to={`/projects/${project.id}`}
                    className="text-blue-500 hover:text-blue-600 flex items-center gap-1"
                  >
                    Ver detalhes
                    <ChevronRight className="w-4 h-4" />
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))}  </div>
      )}
      </div>
    </div>
  );
};

export default ProjectsPage;
