/**
 * ContentPage.tsx - Página de Content OS
 * Gerencia ideias de conteúdo, calendário editorial, posts
 */

import { useState, useEffect, useCallback } from 'react';
import {
  FileText,
  Plus,
  Calendar,
  Instagram,
  Linkedin,
  Youtube,
  Twitter,
  Globe,
  Edit,
  Trash2,
  Clock,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Sparkles,
  Filter,
  LayoutGrid,
  List
} from 'lucide-react';

interface ContentIdea {
  id: string;
  title: string;
  platform: string;
  status: 'idea' | 'drafting' | 'scheduled' | 'published';
  scheduled_date?: string;
  published_at?: string;
  content_type: string;
  topic?: string;
  notes?: string;
  engagement_score?: number;
  created_at: string;
}

interface ContentStats {
  total_ideas: number;
  published_this_month: number;
  scheduled: number;
  engagement_avg: number;
}

const platformIcons: Record<string, React.ReactNode> = {
  instagram: <Instagram className="w-4 h-4 text-pink-500" />,
  linkedin: <Linkedin className="w-4 h-4 text-blue-600" />,
  youtube: <Youtube className="w-4 h-4 text-red-500" />,
  twitter: <Twitter className="w-4 h-4 text-sky-400" />,
  blog: <Globe className="w-4 h-4 text-green-500" />,
  newsletter: <FileText className="w-4 h-4 text-purple-500" />
};

const statusColors: Record<string, string> = {
  idea: 'bg-gray-100 text-gray-600',
  drafting: 'bg-yellow-100 text-yellow-700',
  scheduled: 'bg-blue-100 text-blue-700',
  published: 'bg-green-100 text-green-700'
};

const statusLabels: Record<string, string> = {
  idea: 'Ideia',
  drafting: 'Rascunho',
  scheduled: 'Agendado',
  published: 'Publicado'
};

export function ContentPage() {
  const [ideas, setIdeas] = useState<ContentIdea[]>([]);
  const [stats, setStats] = useState<ContentStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingIdea, setEditingIdea] = useState<ContentIdea | null>(null);
  const [filter, setFilter] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  
  // Form state
  const [formData, setFormData] = useState({
    title: '',
    platform: 'instagram',
    content_type: 'post',
    topic: '',
    notes: '',
    scheduled_date: ''
  });

  const fetchIdeas = useCallback(async () => {
    try {
      const token = localStorage.getItem('api_key');
      const response = await fetch('/api/v1/content/ideas', {
        headers: { 'X-API-Key': token || '' }
      });
      if (response.ok) {
        const data = await response.json();
        setIdeas(data.ideas || []);
      }
    } catch (error) {
      console.error('Erro ao carregar ideias:', error);
    }
  }, []);

  const fetchStats = useCallback(async () => {
    try {
      const token = localStorage.getItem('api_key');
      const response = await fetch('/api/v1/content/stats', {
        headers: { 'X-API-Key': token || '' }
      });
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Erro ao carregar stats:', error);
    }
  }, []);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchIdeas(), fetchStats()]);
      setLoading(false);
    };
    loadData();
  }, [fetchIdeas, fetchStats]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('api_key');
      const url = editingIdea
        ? `/api/v1/content/ideas/${editingIdea.id}`
        : '/api/v1/content/ideas';
      
      const response = await fetch(url, {
        method: editingIdea ? 'PATCH' : 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': token || ''
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        setShowModal(false);
        setEditingIdea(null);
        setFormData({
          title: '',
          platform: 'instagram',
          content_type: 'post',
          topic: '',
          notes: '',
          scheduled_date: ''
        });
        fetchIdeas();
        fetchStats();
      }
    } catch (error) {
      console.error('Erro ao salvar:', error);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Excluir esta ideia?')) return;
    
    try {
      const token = localStorage.getItem('api_key');
      await fetch(`/api/v1/content/ideas/${id}`, {
        method: 'DELETE',
        headers: { 'X-API-Key': token || '' }
      });
      fetchIdeas();
      fetchStats();
    } catch (error) {
      console.error('Erro ao excluir:', error);
    }
  };

  const handleEdit = (idea: ContentIdea) => {
    setEditingIdea(idea);
    setFormData({
      title: idea.title,
      platform: idea.platform,
      content_type: idea.content_type,
      topic: idea.topic || '',
      notes: idea.notes || '',
      scheduled_date: idea.scheduled_date || ''
    });
    setShowModal(true);
  };

  const handleGenerateIdeas = async () => {
    try {
      const token = localStorage.getItem('api_key');
      const response = await fetch('/api/v1/content/generate-ideas', {
        method: 'POST',
        headers: { 'X-API-Key': token || '' }
      });
      if (response.ok) {
        fetchIdeas();
      }
    } catch (error) {
      console.error('Erro ao gerar ideias:', error);
    }
  };

  const filteredIdeas = ideas.filter(idea => {
    if (filter === 'all') return true;
    return idea.status === filter;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <FileText className="w-7 h-7 text-purple-600" />
            Content OS
          </h1>
          <p className="text-gray-500 mt-1">
            Gerencie suas ideias e calendário de conteúdo
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleGenerateIdeas}
            className="flex items-center gap-2 px-4 py-2 border border-purple-300 text-purple-700 rounded-lg hover:bg-purple-50 transition"
          >
            <Sparkles className="w-4 h-4" />
            Gerar Ideias com IA
          </button>
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
          >
            <Plus className="w-4 h-4" />
            Nova Ideia
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-4 rounded-xl border shadow-sm">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <FileText className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total de Ideias</p>
                <p className="text-xl font-semibold">{stats.total_ideas}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-xl border shadow-sm">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <CheckCircle className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Publicados (mês)</p>
                <p className="text-xl font-semibold">{stats.published_this_month}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-xl border shadow-sm">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Clock className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Agendados</p>
                <p className="text-xl font-semibold">{stats.scheduled}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-xl border shadow-sm">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-100 rounded-lg">
                <TrendingUp className="w-5 h-5 text-orange-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Engajamento Médio</p>
                <p className="text-xl font-semibold">{stats.engagement_avg?.toFixed(1) || '-'}%</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters & View Toggle */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-400" />
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="border rounded-lg px-3 py-2 text-sm"
          >
            <option value="all">Todos os Status</option>
            <option value="idea">Ideias</option>
            <option value="drafting">Rascunhos</option>
            <option value="scheduled">Agendados</option>
            <option value="published">Publicados</option>
          </select>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('grid')}
            className={`p-2 rounded-lg ${viewMode === 'grid' ? 'bg-purple-100 text-purple-600' : 'text-gray-400'}`}
          >
            <LayoutGrid className="w-5 h-5" />
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`p-2 rounded-lg ${viewMode === 'list' ? 'bg-purple-100 text-purple-600' : 'text-gray-400'}`}
          >
            <List className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Content Grid/List */}
      {filteredIdeas.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border">
          <AlertCircle className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">Nenhuma ideia encontrada</p>
          <button
            onClick={() => setShowModal(true)}
            className="mt-4 text-purple-600 hover:underline"
          >
            Criar primeira ideia
          </button>
        </div>
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-3 gap-4">
          {filteredIdeas.map((idea) => (
            <div
              key={idea.id}
              className="bg-white p-5 rounded-xl border shadow-sm hover:shadow-md transition"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  {platformIcons[idea.platform] || <Globe className="w-4 h-4" />}
                  <span className={`text-xs px-2 py-1 rounded-full ${statusColors[idea.status]}`}>
                    {statusLabels[idea.status]}
                  </span>
                </div>
                <div className="flex gap-1">
                  <button
                    onClick={() => handleEdit(idea)}
                    className="p-1 text-gray-400 hover:text-gray-600"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(idea.id)}
                    className="p-1 text-gray-400 hover:text-red-500"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
              
              <h3 className="font-medium text-gray-900 mb-2 line-clamp-2">
                {idea.title}
              </h3>
              
              {idea.topic && (
                <span className="text-xs text-purple-600 bg-purple-50 px-2 py-1 rounded">
                  {idea.topic}
                </span>
              )}
              
              {idea.scheduled_date && (
                <div className="flex items-center gap-1 mt-3 text-sm text-gray-500">
                  <Calendar className="w-4 h-4" />
                  {new Date(idea.scheduled_date).toLocaleDateString('pt-BR')}
                </div>
              )}
              
              {idea.notes && (
                <p className="text-sm text-gray-500 mt-2 line-clamp-2">
                  {idea.notes}
                </p>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-xl border overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left p-4 text-sm font-medium text-gray-500">Título</th>
                <th className="text-left p-4 text-sm font-medium text-gray-500">Plataforma</th>
                <th className="text-left p-4 text-sm font-medium text-gray-500">Status</th>
                <th className="text-left p-4 text-sm font-medium text-gray-500">Data</th>
                <th className="text-right p-4 text-sm font-medium text-gray-500">Ações</th>
              </tr>
            </thead>
            <tbody>
              {filteredIdeas.map((idea) => (
                <tr key={idea.id} className="border-t hover:bg-gray-50">
                  <td className="p-4">
                    <span className="font-medium">{idea.title}</span>
                  </td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      {platformIcons[idea.platform]}
                      <span className="capitalize">{idea.platform}</span>
                    </div>
                  </td>
                  <td className="p-4">
                    <span className={`text-xs px-2 py-1 rounded-full ${statusColors[idea.status]}`}>
                      {statusLabels[idea.status]}
                    </span>
                  </td>
                  <td className="p-4 text-sm text-gray-500">
                    {idea.scheduled_date
                      ? new Date(idea.scheduled_date).toLocaleDateString('pt-BR')
                      : '-'}
                  </td>
                  <td className="p-4 text-right">
                    <button
                      onClick={() => handleEdit(idea)}
                      className="p-1 text-gray-400 hover:text-gray-600"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(idea.id)}
                      className="p-1 text-gray-400 hover:text-red-500 ml-2"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-lg">
            <h2 className="text-lg font-semibold mb-4">
              {editingIdea ? 'Editar Ideia' : 'Nova Ideia de Conteúdo'}
            </h2>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Título
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                  placeholder="Título da ideia"
                  required
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Plataforma
                  </label>
                  <select
                    value={formData.platform}
                    onChange={(e) => setFormData({ ...formData, platform: e.target.value })}
                    className="w-full border rounded-lg px-3 py-2"
                  >
                    <option value="instagram">Instagram</option>
                    <option value="linkedin">LinkedIn</option>
                    <option value="youtube">YouTube</option>
                    <option value="twitter">Twitter/X</option>
                    <option value="blog">Blog</option>
                    <option value="newsletter">Newsletter</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Tipo
                  </label>
                  <select
                    value={formData.content_type}
                    onChange={(e) => setFormData({ ...formData, content_type: e.target.value })}
                    className="w-full border rounded-lg px-3 py-2"
                  >
                    <option value="post">Post</option>
                    <option value="reel">Reel/Short</option>
                    <option value="story">Story</option>
                    <option value="carousel">Carrossel</option>
                    <option value="video">Vídeo</option>
                    <option value="article">Artigo</option>
                  </select>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tópico
                </label>
                <input
                  type="text"
                  value={formData.topic}
                  onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                  placeholder="Ex: Produtividade, Tech, Negócios"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Data Agendada (opcional)
                </label>
                <input
                  type="date"
                  value={formData.scheduled_date}
                  onChange={(e) => setFormData({ ...formData, scheduled_date: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notas
                </label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                  rows={3}
                  placeholder="Detalhes, referências, ideias..."
                />
              </div>
              
              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowModal(false);
                    setEditingIdea(null);
                  }}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                >
                  {editingIdea ? 'Salvar' : 'Criar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default ContentPage;
