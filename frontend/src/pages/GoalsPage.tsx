import { useState, useEffect } from 'react';
import { api } from '../services/api';

interface Goal {
  id: string;
  title: string;
  description?: string;
  level: 'macro' | 'meso' | 'micro';
  period_type: 'year' | 'quarter' | 'month' | 'week';
  period_label?: string;
  area?: string;
  icon?: string;
  progress_percentage: number;
  status: 'draft' | 'active' | 'paused' | 'completed' | 'abandoned';
  priority: number;
  parent_id?: string;
  children?: Goal[];
  created_at: string;
}

interface GoalSummary {
  total: number;
  active_macro: number;
  active_meso: number;
  active_micro: number;
  avg_progress: number;
  by_level: Record<string, number>;
  by_status: Record<string, number>;
}

interface GoalArea {
  id: string;
  name: string;
  icon: string;
  color: string;
}

const AREAS: GoalArea[] = [
  { id: 'work', name: 'Trabalho & Projetos', icon: '💼', color: '#3b82f6' },
  { id: 'health', name: 'Saúde & Energia', icon: '💪', color: '#22c55e' },
  { id: 'finance', name: 'Finanças', icon: '💰', color: '#f59e0b' },
  { id: 'relationships', name: 'Relacionamentos', icon: '❤️', color: '#ef4444' },
  { id: 'learning', name: 'Aprendizado', icon: '📚', color: '#8b5cf6' },
  { id: 'personal', name: 'Pessoal & Identidade', icon: '✨', color: '#ec4899' },
  { id: 'content', name: 'Conteúdo & Marca', icon: '✍️', color: '#06b6d4' }
];

const LEVELS = [
  { id: 'macro', name: 'Macro (Anual)', period: 'year', color: 'blue' },
  { id: 'meso', name: 'Meso (Trimestral)', period: 'quarter', color: 'green' },
  { id: 'micro', name: 'Micro (Semanal)', period: 'week', color: 'yellow' }
];

export function GoalsPage() {
  const [goals, setGoals] = useState<Goal[]>([]);
  const [summary, setSummary] = useState<GoalSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedLevel, setSelectedLevel] = useState<string | null>(null);
  const [selectedGoal, setSelectedGoal] = useState<Goal | null>(null);
  
  // Form state
  const [newGoal, setNewGoal] = useState({
    title: '',
    description: '',
    level: 'micro' as 'macro' | 'meso' | 'micro',
    period_type: 'week' as 'year' | 'quarter' | 'month' | 'week',
    area: '',
    priority: 3
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [goalsRes, summaryRes] = await Promise.all([
        api.get('/goals'),
        api.get('/goals/summary')
      ]);
      
      setGoals(goalsRes.data.data || []);
      setSummary(summaryRes.data.data);
    } catch (err) {
      setError('Erro ao carregar objetivos');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const createGoal = async () => {
    try {
      await api.post('/goals', newGoal);
      setShowCreateModal(false);
      setNewGoal({
        title: '',
        description: '',
        level: 'micro',
        period_type: 'week',
        area: '',
        priority: 3
      });
      loadData();
    } catch (err) {
      console.error('Erro ao criar objetivo:', err);
    }
  };

  const updateProgress = async (goalId: string, progress: number) => {
    try {
      await api.patch(`/goals/${goalId}/progress`, {
        progress_percentage: progress
      });
      loadData();
    } catch (err) {
      console.error('Erro ao atualizar progresso:', err);
    }
  };

  const completeGoal = async (goalId: string) => {
    try {
      await api.patch(`/goals/${goalId}`, {
        status: 'completed',
        progress_percentage: 100
      });
      loadData();
    } catch (err) {
      console.error('Erro ao completar objetivo:', err);
    }
  };

  const getAreaInfo = (areaId?: string) => {
    return AREAS.find(a => a.id === areaId) || { icon: '🎯', name: 'Geral', color: '#6b7280' };
  };

  const getLevelInfo = (level: string) => {
    return LEVELS.find(l => l.id === level) || LEVELS[2];
  };

  const filteredGoals = selectedLevel 
    ? goals.filter(g => g.level === selectedLevel)
    : goals;

  const activeGoals = filteredGoals.filter(g => g.status === 'active');

  if (loading) {
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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            🎯 Objetivos
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Sistema Macro/Meso/Micro
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-2"
        >
          <span>+</span>
          Novo Objetivo
        </button>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
            <div className="text-3xl font-bold text-gray-900 dark:text-white">
              {summary.total}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Total de Objetivos
            </div>
          </div>
          
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4">
            <div className="text-2xl font-bold text-blue-600">
              {summary.active_macro}
            </div>
            <div className="text-sm text-blue-600/70">
              🔵 Macro (Anuais)
            </div>
          </div>
          
          <div className="bg-green-50 dark:bg-green-900/20 rounded-xl p-4">
            <div className="text-2xl font-bold text-green-600">
              {summary.active_meso}
            </div>
            <div className="text-sm text-green-600/70">
              🟢 Meso (Trimestrais)
            </div>
          </div>
          
          <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-xl p-4">
            <div className="text-2xl font-bold text-yellow-600">
              {summary.active_micro}
            </div>
            <div className="text-sm text-yellow-600/70">
              🟡 Micro (Semanais)
            </div>
          </div>
        </div>
      )}

      {/* Progress Overview */}
      {summary && summary.avg_progress > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Progresso Médio
            </span>
            <span className="text-lg font-bold text-indigo-600">
              {summary.avg_progress}%
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
            <div 
              className="bg-indigo-600 h-3 rounded-full transition-all duration-500"
              style={{ width: `${summary.avg_progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Level Filter */}
      <div className="flex gap-2 flex-wrap">
        <button
          onClick={() => setSelectedLevel(null)}
          className={`px-4 py-2 rounded-lg transition-colors ${
            !selectedLevel 
              ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900'
              : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200'
          }`}
        >
          Todos
        </button>
        {LEVELS.map(level => (
          <button
            key={level.id}
            onClick={() => setSelectedLevel(level.id)}
            className={`px-4 py-2 rounded-lg transition-colors ${
              selectedLevel === level.id
                ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200'
            }`}
          >
            {level.name}
          </button>
        ))}
      </div>

      {/* Goals List */}
      <div className="space-y-4">
        {activeGoals.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 rounded-xl p-8 text-center">
            <div className="text-4xl mb-4">🎯</div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              Nenhum objetivo {selectedLevel ? `${getLevelInfo(selectedLevel).name.toLowerCase()}` : ''} ainda
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Crie seu primeiro objetivo para começar a acompanhar seu progresso
            </p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Criar Objetivo
            </button>
          </div>
        ) : (
          activeGoals.map(goal => {
            const area = getAreaInfo(goal.area);
            const level = getLevelInfo(goal.level);
            
            return (
              <div 
                key={goal.id}
                className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => setSelectedGoal(goal)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">{goal.icon || area.icon}</span>
                    <div>
                      <h3 className="font-medium text-gray-900 dark:text-white">
                        {goal.title}
                      </h3>
                      {goal.description && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          {goal.description}
                        </p>
                      )}
                      <div className="flex items-center gap-3 mt-2">
                        <span 
                          className={`text-xs px-2 py-1 rounded-full ${
                            level.id === 'macro' ? 'bg-blue-100 text-blue-700' :
                            level.id === 'meso' ? 'bg-green-100 text-green-700' :
                            'bg-yellow-100 text-yellow-700'
                          }`}
                        >
                          {level.name}
                        </span>
                        {goal.period_label && (
                          <span className="text-xs text-gray-500">
                            📅 {goal.period_label}
                          </span>
                        )}
                        <span className="text-xs text-gray-500">
                          {area.name}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <div className="text-lg font-bold text-gray-900 dark:text-white">
                        {goal.progress_percentage}%
                      </div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        completeGoal(goal.id);
                      }}
                      className="p-2 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg transition-colors"
                      title="Marcar como concluído"
                    >
                      ✓
                    </button>
                  </div>
                </div>
                
                {/* Progress Bar */}
                <div className="mt-4">
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full transition-all duration-300 ${
                        goal.progress_percentage >= 100 ? 'bg-green-500' :
                        goal.progress_percentage >= 50 ? 'bg-indigo-500' :
                        'bg-yellow-500'
                      }`}
                      style={{ width: `${goal.progress_percentage}%` }}
                    />
                  </div>
                </div>
                
                {/* Quick Progress Buttons */}
                <div className="mt-3 flex gap-2">
                  {[25, 50, 75, 100].map(pct => (
                    <button
                      key={pct}
                      onClick={(e) => {
                        e.stopPropagation();
                        updateProgress(goal.id, pct);
                      }}
                      className={`px-3 py-1 text-xs rounded-lg transition-colors ${
                        goal.progress_percentage >= pct
                          ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30'
                          : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 hover:bg-gray-200'
                      }`}
                    >
                      {pct}%
                    </button>
                  ))}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Completed Goals Section */}
      {goals.filter(g => g.status === 'completed').length > 0 && (
        <div className="mt-8">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            ✅ Objetivos Concluídos
          </h2>
          <div className="space-y-2">
            {goals.filter(g => g.status === 'completed').map(goal => {
              const area = getAreaInfo(goal.area);
              return (
                <div 
                  key={goal.id}
                  className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4 flex items-center justify-between opacity-75"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xl">{area.icon}</span>
                    <span className="text-gray-700 dark:text-gray-300 line-through">
                      {goal.title}
                    </span>
                  </div>
                  <span className="text-green-600 font-medium">100%</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
              🎯 Novo Objetivo
            </h2>
            
            <div className="space-y-4">
              {/* Title */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Título *
                </label>
                <input
                  type="text"
                  value={newGoal.title}
                  onChange={(e) => setNewGoal({ ...newGoal, title: e.target.value })}
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                  placeholder="Ex: Atingir 100k de receita"
                />
              </div>
              
              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Descrição
                </label>
                <textarea
                  value={newGoal.description}
                  onChange={(e) => setNewGoal({ ...newGoal, description: e.target.value })}
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                  rows={2}
                  placeholder="Detalhes opcionais..."
                />
              </div>
              
              {/* Level */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Nível
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {LEVELS.map(level => (
                    <button
                      key={level.id}
                      onClick={() => setNewGoal({ 
                        ...newGoal, 
                        level: level.id as any,
                        period_type: level.period as any
                      })}
                      className={`p-3 rounded-lg text-center transition-colors ${
                        newGoal.level === level.id
                          ? 'bg-indigo-100 dark:bg-indigo-900/30 border-2 border-indigo-500'
                          : 'bg-gray-100 dark:bg-gray-700 border-2 border-transparent'
                      }`}
                    >
                      <div className="font-medium text-sm">{level.name.split(' ')[0]}</div>
                      <div className="text-xs text-gray-500">{level.name.match(/\(([^)]+)\)/)?.[1]}</div>
                    </button>
                  ))}
                </div>
              </div>
              
              {/* Area */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Área
                </label>
                <div className="grid grid-cols-4 gap-2">
                  {AREAS.map(area => (
                    <button
                      key={area.id}
                      onClick={() => setNewGoal({ ...newGoal, area: area.id })}
                      className={`p-3 rounded-lg text-center transition-colors ${
                        newGoal.area === area.id
                          ? 'bg-indigo-100 dark:bg-indigo-900/30 border-2 border-indigo-500'
                          : 'bg-gray-100 dark:bg-gray-700 border-2 border-transparent'
                      }`}
                    >
                      <div className="text-2xl">{area.icon}</div>
                      <div className="text-xs mt-1 truncate">{area.name.split(' ')[0]}</div>
                    </button>
                  ))}
                </div>
              </div>
              
              {/* Priority */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Prioridade
                </label>
                <div className="flex gap-2">
                  {[1, 2, 3, 4, 5].map(p => (
                    <button
                      key={p}
                      onClick={() => setNewGoal({ ...newGoal, priority: p })}
                      className={`flex-1 py-2 rounded-lg transition-colors ${
                        newGoal.priority === p
                          ? 'bg-indigo-600 text-white'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                      }`}
                    >
                      {p === 1 ? '🔥' : p === 2 ? '⚡' : p === 3 ? '•' : p === 4 ? '↓' : '...'}
                    </button>
                  ))}
                </div>
                <div className="text-xs text-gray-500 mt-1 text-center">
                  1 = Urgente, 5 = Baixa prioridade
                </div>
              </div>
            </div>
            
            {/* Actions */}
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                Cancelar
              </button>
              <button
                onClick={createGoal}
                disabled={!newGoal.title.trim()}
                className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Criar Objetivo
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Goal Detail Modal */}
      {selectedGoal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 max-w-lg w-full">
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center gap-3">
                <span className="text-3xl">{getAreaInfo(selectedGoal.area).icon}</span>
                <div>
                  <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                    {selectedGoal.title}
                  </h2>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    selectedGoal.level === 'macro' ? 'bg-blue-100 text-blue-700' :
                    selectedGoal.level === 'meso' ? 'bg-green-100 text-green-700' :
                    'bg-yellow-100 text-yellow-700'
                  }`}>
                    {getLevelInfo(selectedGoal.level).name}
                  </span>
                </div>
              </div>
              <button
                onClick={() => setSelectedGoal(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            
            {selectedGoal.description && (
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                {selectedGoal.description}
              </p>
            )}
            
            <div className="mb-6">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-gray-600 dark:text-gray-400">Progresso</span>
                <span className="font-bold text-lg">{selectedGoal.progress_percentage}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
                <div 
                  className="bg-indigo-600 h-4 rounded-full transition-all"
                  style={{ width: `${selectedGoal.progress_percentage}%` }}
                />
              </div>
            </div>
            
            {/* Progress Slider */}
            <div className="mb-6">
              <label className="block text-sm text-gray-600 dark:text-gray-400 mb-2">
                Atualizar Progresso
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={selectedGoal.progress_percentage}
                onChange={(e) => {
                  const newProgress = parseInt(e.target.value);
                  setSelectedGoal({ ...selectedGoal, progress_percentage: newProgress });
                }}
                onMouseUp={() => updateProgress(selectedGoal.id, selectedGoal.progress_percentage)}
                onTouchEnd={() => updateProgress(selectedGoal.id, selectedGoal.progress_percentage)}
                className="w-full"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Período</span>
                <p className="font-medium">{selectedGoal.period_label}</p>
              </div>
              <div>
                <span className="text-gray-500">Área</span>
                <p className="font-medium">{getAreaInfo(selectedGoal.area).name}</p>
              </div>
            </div>
            
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  completeGoal(selectedGoal.id);
                  setSelectedGoal(null);
                }}
                className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                ✓ Concluir
              </button>
              <button
                onClick={() => setSelectedGoal(null)}
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 text-red-600 p-4 rounded-lg">
          {error}
        </div>
      )}
    </div>
  );
}
