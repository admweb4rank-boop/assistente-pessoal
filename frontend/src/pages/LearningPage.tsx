/**
 * LearningPage.tsx - Página de Learning OS
 * Gerencia aprendizado, revisão espaçada, trilhas
 */

import { useState, useEffect, useCallback } from 'react';
import {
  BookOpen,
  Plus,
  Brain,
  Clock,
  Target,
  Trophy,
  Play,
  CheckCircle,
  AlertCircle,
  RotateCcw,
  Folder,
  FileText,
  Video,
  Headphones,
  GraduationCap,
  Filter,
  Search
} from 'lucide-react';

interface LearningItem {
  id: string;
  title: string;
  content_type: string;
  status: string;
  topic?: string;
  summary?: string;
  source_url?: string;
  next_review?: string;
  review_count: number;
  ease_factor: number;
  interval_days: number;
  priority: number;
  created_at: string;
}

interface LearningPath {
  id: string;
  title: string;
  description?: string;
  goal?: string;
  status: string;
  total_items: number;
  completed_items: number;
  progress_percentage: number;
}

interface ReviewStats {
  total_reviews: number;
  average_quality: number;
  items_by_status: Record<string, number>;
  total_items: number;
  mastered_items: number;
  items_due_for_review: number;
  retention_rate: number;
}

const contentTypeIcons: Record<string, React.ReactNode> = {
  book: <BookOpen className="w-4 h-4" />,
  article: <FileText className="w-4 h-4" />,
  course: <GraduationCap className="w-4 h-4" />,
  video: <Video className="w-4 h-4" />,
  podcast: <Headphones className="w-4 h-4" />,
  flashcard: <Brain className="w-4 h-4" />,
  note: <FileText className="w-4 h-4" />
};

const statusColors: Record<string, string> = {
  to_learn: 'bg-gray-100 text-gray-600',
  learning: 'bg-blue-100 text-blue-700',
  completed: 'bg-green-100 text-green-700',
  reviewing: 'bg-yellow-100 text-yellow-700',
  mastered: 'bg-purple-100 text-purple-700'
};

const statusLabels: Record<string, string> = {
  to_learn: 'Para Aprender',
  learning: 'Aprendendo',
  completed: 'Completo',
  reviewing: 'Revisando',
  mastered: 'Dominado'
};

export function LearningPage() {
  const [items, setItems] = useState<LearningItem[]>([]);
  const [paths, setPaths] = useState<LearningPath[]>([]);
  const [stats, setStats] = useState<ReviewStats | null>(null);
  const [reviewItems, setReviewItems] = useState<LearningItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'items' | 'review' | 'paths'>('items');
  const [showModal, setShowModal] = useState(false);
  const [filter, setFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  
  // Review mode state
  const [reviewMode, setReviewMode] = useState(false);
  const [currentReviewItem, setCurrentReviewItem] = useState<LearningItem | null>(null);
  const [showAnswer, setShowAnswer] = useState(false);
  
  // Form state
  const [formData, setFormData] = useState({
    title: '',
    content_type: 'article',
    source_url: '',
    summary: '',
    topic: '',
    priority: 5
  });

  const fetchItems = useCallback(async () => {
    try {
      const token = localStorage.getItem('api_key');
      const response = await fetch('/api/v1/learning/items', {
        headers: { 'X-API-Key': token || '' }
      });
      if (response.ok) {
        const data = await response.json();
        setItems(data.items || []);
      }
    } catch (error) {
      console.error('Erro ao carregar itens:', error);
    }
  }, []);

  const fetchPaths = useCallback(async () => {
    try {
      const token = localStorage.getItem('api_key');
      const response = await fetch('/api/v1/learning/paths', {
        headers: { 'X-API-Key': token || '' }
      });
      if (response.ok) {
        const data = await response.json();
        setPaths(data.paths || []);
      }
    } catch (error) {
      console.error('Erro ao carregar trilhas:', error);
    }
  }, []);

  const fetchStats = useCallback(async () => {
    try {
      const token = localStorage.getItem('api_key');
      const response = await fetch('/api/v1/learning/review/stats', {
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

  const fetchReviewItems = useCallback(async () => {
    try {
      const token = localStorage.getItem('api_key');
      const response = await fetch('/api/v1/learning/review', {
        headers: { 'X-API-Key': token || '' }
      });
      if (response.ok) {
        const data = await response.json();
        setReviewItems(data.items || []);
      }
    } catch (error) {
      console.error('Erro ao carregar revisões:', error);
    }
  }, []);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchItems(), fetchPaths(), fetchStats(), fetchReviewItems()]);
      setLoading(false);
    };
    loadData();
  }, [fetchItems, fetchPaths, fetchStats, fetchReviewItems]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('api_key');
      const response = await fetch('/api/v1/learning/items', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': token || ''
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        setShowModal(false);
        setFormData({
          title: '',
          content_type: 'article',
          source_url: '',
          summary: '',
          topic: '',
          priority: 5
        });
        fetchItems();
        fetchStats();
      }
    } catch (error) {
      console.error('Erro ao salvar:', error);
    }
  };

  const startReview = () => {
    if (reviewItems.length > 0) {
      setCurrentReviewItem(reviewItems[0]);
      setShowAnswer(false);
      setReviewMode(true);
    }
  };

  const submitReview = async (quality: number) => {
    if (!currentReviewItem) return;
    
    try {
      const token = localStorage.getItem('api_key');
      await fetch(`/api/v1/learning/review/${currentReviewItem.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': token || ''
        },
        body: JSON.stringify({ quality })
      });

      // Move to next item
      const currentIndex = reviewItems.findIndex(i => i.id === currentReviewItem.id);
      if (currentIndex < reviewItems.length - 1) {
        setCurrentReviewItem(reviewItems[currentIndex + 1]);
        setShowAnswer(false);
      } else {
        setReviewMode(false);
        setCurrentReviewItem(null);
        fetchReviewItems();
        fetchStats();
      }
    } catch (error) {
      console.error('Erro ao submeter revisão:', error);
    }
  };

  const filteredItems = items.filter(item => {
    const matchesFilter = filter === 'all' || item.status === filter;
    const matchesSearch = item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (item.topic && item.topic.toLowerCase().includes(searchTerm.toLowerCase()));
    return matchesFilter && matchesSearch;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  // Review Mode UI
  if (reviewMode && currentReviewItem) {
    return (
      <div className="p-6 max-w-2xl mx-auto">
        <div className="bg-white rounded-xl border shadow-lg p-8">
          <div className="text-center mb-6">
            <span className="text-sm text-gray-500">
              Revisão {reviewItems.findIndex(i => i.id === currentReviewItem.id) + 1} de {reviewItems.length}
            </span>
          </div>
          
          <div className="min-h-[200px] flex items-center justify-center">
            <div className="text-center">
              <div className="flex items-center justify-center gap-2 mb-4">
                {contentTypeIcons[currentReviewItem.content_type]}
                <span className="text-sm text-gray-500">{currentReviewItem.topic || 'Geral'}</span>
              </div>
              
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">
                {currentReviewItem.title}
              </h2>
              
              {showAnswer && currentReviewItem.summary && (
                <div className="mt-6 p-4 bg-gray-50 rounded-lg text-left">
                  <p className="text-gray-700">{currentReviewItem.summary}</p>
                </div>
              )}
            </div>
          </div>
          
          {!showAnswer ? (
            <div className="text-center mt-8">
              <button
                onClick={() => setShowAnswer(true)}
                className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
              >
                Mostrar Resposta
              </button>
            </div>
          ) : (
            <div className="mt-8">
              <p className="text-center text-sm text-gray-500 mb-4">
                Como foi a sua recordação?
              </p>
              <div className="flex justify-center gap-2">
                <button
                  onClick={() => submitReview(0)}
                  className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
                >
                  Esqueci
                </button>
                <button
                  onClick={() => submitReview(2)}
                  className="px-4 py-2 bg-orange-100 text-orange-700 rounded-lg hover:bg-orange-200"
                >
                  Difícil
                </button>
                <button
                  onClick={() => submitReview(3)}
                  className="px-4 py-2 bg-yellow-100 text-yellow-700 rounded-lg hover:bg-yellow-200"
                >
                  Ok
                </button>
                <button
                  onClick={() => submitReview(4)}
                  className="px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200"
                >
                  Bom
                </button>
                <button
                  onClick={() => submitReview(5)}
                  className="px-4 py-2 bg-indigo-100 text-indigo-700 rounded-lg hover:bg-indigo-200"
                >
                  Fácil
                </button>
              </div>
            </div>
          )}
          
          <div className="mt-8 text-center">
            <button
              onClick={() => setReviewMode(false)}
              className="text-gray-500 hover:text-gray-700"
            >
              Sair da Revisão
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <BookOpen className="w-7 h-7 text-indigo-600" />
            Learning OS
          </h1>
          <p className="text-gray-500 mt-1">
            Aprenda de forma estruturada com revisão espaçada
          </p>
        </div>
        <div className="flex gap-3">
          {reviewItems.length > 0 && (
            <button
              onClick={startReview}
              className="flex items-center gap-2 px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition"
            >
              <RotateCcw className="w-4 h-4" />
              Revisar ({reviewItems.length})
            </button>
          )}
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
          >
            <Plus className="w-4 h-4" />
            Novo Item
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-5 gap-4 mb-8">
          <div className="bg-white p-4 rounded-xl border shadow-sm">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-indigo-100 rounded-lg">
                <BookOpen className="w-5 h-5 text-indigo-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total</p>
                <p className="text-xl font-semibold">{stats.total_items}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-xl border shadow-sm">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Trophy className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Dominados</p>
                <p className="text-xl font-semibold">{stats.mastered_items}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-xl border shadow-sm">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <Clock className="w-5 h-5 text-yellow-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Para Revisar</p>
                <p className="text-xl font-semibold">{stats.items_due_for_review}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-xl border shadow-sm">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <Brain className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Revisões</p>
                <p className="text-xl font-semibold">{stats.total_reviews}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-xl border shadow-sm">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Target className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Retenção</p>
                <p className="text-xl font-semibold">{stats.retention_rate}%</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-4 mb-6 border-b">
        <button
          onClick={() => setActiveTab('items')}
          className={`pb-3 px-2 font-medium ${
            activeTab === 'items'
              ? 'text-indigo-600 border-b-2 border-indigo-600'
              : 'text-gray-500'
          }`}
        >
          Itens de Aprendizado
        </button>
        <button
          onClick={() => setActiveTab('review')}
          className={`pb-3 px-2 font-medium flex items-center gap-2 ${
            activeTab === 'review'
              ? 'text-indigo-600 border-b-2 border-indigo-600'
              : 'text-gray-500'
          }`}
        >
          Revisão
          {reviewItems.length > 0 && (
            <span className="bg-yellow-100 text-yellow-700 text-xs px-2 py-0.5 rounded-full">
              {reviewItems.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('paths')}
          className={`pb-3 px-2 font-medium ${
            activeTab === 'paths'
              ? 'text-indigo-600 border-b-2 border-indigo-600'
              : 'text-gray-500'
          }`}
        >
          Trilhas
        </button>
      </div>

      {/* Content based on tab */}
      {activeTab === 'items' && (
        <>
          {/* Filters */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4">
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Buscar..."
                  className="pl-10 pr-4 py-2 border rounded-lg text-sm w-64"
                />
              </div>
              <div className="flex items-center gap-2">
                <Filter className="w-4 h-4 text-gray-400" />
                <select
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                  className="border rounded-lg px-3 py-2 text-sm"
                >
                  <option value="all">Todos</option>
                  <option value="to_learn">Para Aprender</option>
                  <option value="learning">Aprendendo</option>
                  <option value="completed">Completos</option>
                  <option value="reviewing">Revisando</option>
                  <option value="mastered">Dominados</option>
                </select>
              </div>
            </div>
          </div>

          {/* Items Grid */}
          {filteredItems.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-xl border">
              <AlertCircle className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">Nenhum item encontrado</p>
              <button
                onClick={() => setShowModal(true)}
                className="mt-4 text-indigo-600 hover:underline"
              >
                Adicionar primeiro item
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-3 gap-4">
              {filteredItems.map((item) => (
                <div
                  key={item.id}
                  className="bg-white p-5 rounded-xl border shadow-sm hover:shadow-md transition"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      {contentTypeIcons[item.content_type] || <FileText className="w-4 h-4" />}
                      <span className={`text-xs px-2 py-1 rounded-full ${statusColors[item.status]}`}>
                        {statusLabels[item.status]}
                      </span>
                    </div>
                    <span className="text-xs text-gray-400">
                      P{item.priority}
                    </span>
                  </div>
                  
                  <h3 className="font-medium text-gray-900 mb-2 line-clamp-2">
                    {item.title}
                  </h3>
                  
                  {item.topic && (
                    <span className="text-xs text-indigo-600 bg-indigo-50 px-2 py-1 rounded">
                      {item.topic}
                    </span>
                  )}
                  
                  <div className="flex items-center justify-between mt-4 text-xs text-gray-500">
                    <span>Revisões: {item.review_count}</span>
                    {item.next_review && (
                      <span>
                        Próxima: {new Date(item.next_review).toLocaleDateString('pt-BR')}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {activeTab === 'review' && (
        <div className="bg-white rounded-xl border p-8 text-center">
          <Brain className="w-16 h-16 text-indigo-200 mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">Sessão de Revisão</h3>
          <p className="text-gray-500 mb-6">
            Você tem {reviewItems.length} itens para revisar
          </p>
          {reviewItems.length > 0 ? (
            <button
              onClick={startReview}
              className="flex items-center gap-2 mx-auto px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              <Play className="w-5 h-5" />
              Iniciar Revisão
            </button>
          ) : (
            <p className="text-green-600 flex items-center justify-center gap-2">
              <CheckCircle className="w-5 h-5" />
              Todas as revisões em dia!
            </p>
          )}
        </div>
      )}

      {activeTab === 'paths' && (
        <div className="grid grid-cols-2 gap-6">
          {paths.length === 0 ? (
            <div className="col-span-2 text-center py-12 bg-white rounded-xl border">
              <Folder className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">Nenhuma trilha criada</p>
            </div>
          ) : (
            paths.map((path) => (
              <div
                key={path.id}
                className="bg-white p-6 rounded-xl border shadow-sm"
              >
                <div className="flex items-start justify-between mb-4">
                  <h3 className="font-semibold text-lg">{path.title}</h3>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    path.status === 'completed' ? 'bg-green-100 text-green-700' :
                    path.status === 'active' ? 'bg-blue-100 text-blue-700' :
                    'bg-gray-100 text-gray-600'
                  }`}>
                    {path.status === 'completed' ? 'Completa' :
                     path.status === 'active' ? 'Ativa' : 'Planejada'}
                  </span>
                </div>
                
                {path.description && (
                  <p className="text-sm text-gray-500 mb-4">{path.description}</p>
                )}
                
                <div className="mb-4">
                  <div className="flex justify-between text-sm text-gray-500 mb-1">
                    <span>Progresso</span>
                    <span>{path.completed_items}/{path.total_items}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-indigo-600 h-2 rounded-full transition-all"
                      style={{ width: `${path.progress_percentage}%` }}
                    />
                  </div>
                </div>
                
                {path.goal && (
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Target className="w-4 h-4" />
                    {path.goal}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-lg">
            <h2 className="text-lg font-semibold mb-4">
              Novo Item de Aprendizado
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
                  placeholder="Nome do conteúdo"
                  required
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Tipo
                  </label>
                  <select
                    value={formData.content_type}
                    onChange={(e) => setFormData({ ...formData, content_type: e.target.value })}
                    className="w-full border rounded-lg px-3 py-2"
                  >
                    <option value="book">Livro</option>
                    <option value="article">Artigo</option>
                    <option value="course">Curso</option>
                    <option value="video">Vídeo</option>
                    <option value="podcast">Podcast</option>
                    <option value="flashcard">Flashcard</option>
                    <option value="note">Nota</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Prioridade (1-10)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) })}
                    className="w-full border rounded-lg px-3 py-2"
                  />
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
                  placeholder="Ex: Programação, Negócios, Produtividade"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  URL (opcional)
                </label>
                <input
                  type="url"
                  value={formData.source_url}
                  onChange={(e) => setFormData({ ...formData, source_url: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                  placeholder="https://..."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Resumo/Notas
                </label>
                <textarea
                  value={formData.summary}
                  onChange={(e) => setFormData({ ...formData, summary: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                  rows={3}
                  placeholder="Resumo ou pontos principais..."
                />
              </div>
              
              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                >
                  Adicionar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default LearningPage;
