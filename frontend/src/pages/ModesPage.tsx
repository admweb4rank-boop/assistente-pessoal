/**
 * ModesPage.tsx - Página de Modos/Identidades
 * Gerencia os modos operacionais do assistente
 */

import { useState, useEffect, useCallback } from 'react';
import {
  Zap,
  Pen,
  Heart,
  BookOpen,
  Sparkles,
  Bot,
  Check,
  Clock,
  BarChart3,
  Settings2
} from 'lucide-react';

interface Mode {
  mode_name: string;
  display_name: string;
  icon: string;
  description: string;
  system_prompt?: string;
  greeting?: string;
}

interface ModeStats {
  active_mode: string;
  mode_usage: Record<string, { count: number; total_minutes: number }>;
  total_sessions: number;
  most_used_mode: string;
}

const modeIcons: Record<string, React.ReactNode> = {
  default: <Bot className="w-6 h-6" />,
  execution: <Zap className="w-6 h-6" />,
  content: <Pen className="w-6 h-6" />,
  health: <Heart className="w-6 h-6" />,
  learning: <BookOpen className="w-6 h-6" />,
  presence: <Sparkles className="w-6 h-6" />
};

const modeColors: Record<string, string> = {
  default: 'bg-gray-100 text-gray-600 border-gray-300',
  execution: 'bg-yellow-100 text-yellow-700 border-yellow-400',
  content: 'bg-purple-100 text-purple-700 border-purple-400',
  health: 'bg-green-100 text-green-700 border-green-400',
  learning: 'bg-blue-100 text-blue-700 border-blue-400',
  presence: 'bg-pink-100 text-pink-700 border-pink-400'
};

const modeActiveColors: Record<string, string> = {
  default: 'bg-gray-600 text-white',
  execution: 'bg-yellow-500 text-white',
  content: 'bg-purple-600 text-white',
  health: 'bg-green-600 text-white',
  learning: 'bg-blue-600 text-white',
  presence: 'bg-pink-600 text-white'
};

export function ModesPage() {
  const [modes, setModes] = useState<Mode[]>([]);
  const [activeMode, setActiveMode] = useState<string>('default');
  const [stats, setStats] = useState<ModeStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [activating, setActivating] = useState<string | null>(null);
  const [showDetails, setShowDetails] = useState<string | null>(null);

  const fetchModes = useCallback(async () => {
    try {
      const token = localStorage.getItem('api_key');
      const response = await fetch('/api/v1/modes', {
        headers: { 'X-API-Key': token || '' }
      });
      if (response.ok) {
        const data = await response.json();
        setModes(data.modes || []);
      }
    } catch (error) {
      console.error('Erro ao carregar modos:', error);
    }
  }, []);

  const fetchActiveMode = useCallback(async () => {
    try {
      const token = localStorage.getItem('api_key');
      const response = await fetch('/api/v1/modes/active', {
        headers: { 'X-API-Key': token || '' }
      });
      if (response.ok) {
        const data = await response.json();
        setActiveMode(data.mode_name || 'default');
      }
    } catch (error) {
      console.error('Erro ao carregar modo ativo:', error);
    }
  }, []);

  const fetchStats = useCallback(async () => {
    try {
      const token = localStorage.getItem('api_key');
      const response = await fetch('/api/v1/modes/stats/usage', {
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
      await Promise.all([fetchModes(), fetchActiveMode(), fetchStats()]);
      setLoading(false);
    };
    loadData();
  }, [fetchModes, fetchActiveMode, fetchStats]);

  const activateMode = async (modeName: string) => {
    setActivating(modeName);
    try {
      const token = localStorage.getItem('api_key');
      const response = await fetch('/api/v1/modes/activate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': token || ''
        },
        body: JSON.stringify({ mode_name: modeName })
      });

      if (response.ok) {
        setActiveMode(modeName);
        fetchStats();
      }
    } catch (error) {
      console.error('Erro ao ativar modo:', error);
    } finally {
      setActivating(null);
    }
  };

  const fetchModeDetails = async (modeName: string) => {
    try {
      const token = localStorage.getItem('api_key');
      const response = await fetch(`/api/v1/modes/${modeName}`, {
        headers: { 'X-API-Key': token || '' }
      });
      if (response.ok) {
        const data = await response.json();
        // Atualiza o modo com detalhes completos
        setModes(prev => prev.map(m => 
          m.mode_name === modeName ? { ...m, ...data } : m
        ));
        setShowDetails(modeName);
      }
    } catch (error) {
      console.error('Erro ao carregar detalhes:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="relative">
          <div className="w-16 h-16 rounded-full border-4 border-dark-bg-tertiary border-t-accent-pink-500 animate-spin-slow" />
          <div className="absolute inset-0 w-16 h-16 rounded-full bg-accent-pink-500/20 blur-xl animate-pulse" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-bg-primary pb-24 md:pb-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Header */}
        <div className="mb-8 animate-slide-down">
          <h1 className="text-display-lg font-bold text-white mb-2">
            ✨ <span className="text-gradient">Modos</span>
          </h1>
          <p className="text-xl text-dark-text-secondary">
            Escolha um modo para adaptar o comportamento do assistente
          </p>
        </div>

        {/* Modo Ativo Destaque */}
      <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-2xl p-6 mb-8 text-white">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-indigo-200 text-sm mb-1">Modo Ativo</p>
            <h2 className="text-2xl font-bold flex items-center gap-3">
              <span className="text-3xl">
                {modes.find(m => m.mode_name === activeMode)?.icon || '🤖'}
              </span>
              {modes.find(m => m.mode_name === activeMode)?.display_name || 'Assistente Geral'}
            </h2>
          </div>
          <div className="text-right">
            <p className="text-indigo-200 text-sm">Sessões totais</p>
            <p className="text-2xl font-bold">{stats?.total_sessions || 0}</p>
          </div>
        </div>
      </div>

      {/* Grid de Modos */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">
        {modes.map((mode) => {
          const isActive = mode.mode_name === activeMode;
          const isActivating = activating === mode.mode_name;
          
          return (
            <div
              key={mode.mode_name}
              className={`relative rounded-xl border-2 p-5 transition-all cursor-pointer ${
                isActive 
                  ? modeActiveColors[mode.mode_name] || 'bg-indigo-600 text-white'
                  : modeColors[mode.mode_name] || 'bg-gray-100 text-gray-600 border-gray-300'
              } hover:shadow-lg`}
              onClick={() => !isActive && activateMode(mode.mode_name)}
            >
              {isActive && (
                <div className="absolute top-2 right-2">
                  <Check className="w-5 h-5" />
                </div>
              )}
              
              <div className="flex items-center gap-3 mb-3">
                <span className="text-2xl">{mode.icon}</span>
                <span className="font-semibold">{mode.display_name}</span>
              </div>
              
              <p className={`text-sm ${isActive ? 'text-white/80' : 'text-gray-500'}`}>
                {mode.description}
              </p>
              
              {isActivating && (
                <div className="absolute inset-0 bg-white/50 rounded-xl flex items-center justify-center">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600"></div>
                </div>
              )}
              
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  fetchModeDetails(mode.mode_name);
                }}
                className={`mt-3 text-xs underline ${isActive ? 'text-white/70' : 'text-gray-400'}`}
              >
                Ver detalhes
              </button>
            </div>
          );
        })}
      </div>

      {/* Stats de Uso */}
      {stats && stats.mode_usage && Object.keys(stats.mode_usage).length > 0 && (
        <div className="bg-white rounded-xl border p-6">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Uso dos Modos (últimos 30 dias)
          </h3>
          
          <div className="space-y-3">
            {Object.entries(stats.mode_usage).map(([modeName, usage]) => {
              const mode = modes.find(m => m.mode_name === modeName);
              const maxCount = Math.max(...Object.values(stats.mode_usage).map(u => u.count));
              const percentage = (usage.count / maxCount) * 100;
              
              return (
                <div key={modeName} className="flex items-center gap-4">
                  <span className="w-8 text-center">{mode?.icon || '🤖'}</span>
                  <span className="w-32 text-sm text-gray-600">
                    {mode?.display_name || modeName}
                  </span>
                  <div className="flex-1 bg-gray-100 rounded-full h-3">
                    <div
                      className="bg-indigo-500 h-3 rounded-full transition-all"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                  <span className="text-sm text-gray-500 w-24 text-right">
                    {usage.count} sessões
                  </span>
                  <span className="text-sm text-gray-400 w-20 text-right flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {usage.total_minutes}min
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Modal de Detalhes */}
      {showDetails && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
            {(() => {
              const mode = modes.find(m => m.mode_name === showDetails);
              if (!mode) return null;
              
              return (
                <>
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-bold flex items-center gap-2">
                      <span className="text-2xl">{mode.icon}</span>
                      {mode.display_name}
                    </h2>
                    <button
                      onClick={() => setShowDetails(null)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      ✕
                    </button>
                  </div>
                  
                  <p className="text-gray-600 mb-4">{mode.description}</p>
                  
                  {mode.greeting && (
                    <div className="mb-4">
                      <h4 className="font-medium text-gray-700 mb-2">Saudação</h4>
                      <div className="bg-gray-50 p-3 rounded-lg text-sm">
                        {mode.greeting}
                      </div>
                    </div>
                  )}
                  
                  {mode.system_prompt && (
                    <div className="mb-4">
                      <h4 className="font-medium text-gray-700 mb-2">Prompt do Sistema</h4>
                      <div className="bg-gray-50 p-3 rounded-lg text-sm whitespace-pre-wrap max-h-60 overflow-y-auto">
                        {mode.system_prompt}
                      </div>
                    </div>
                  )}
                  
                  <div className="flex justify-end gap-3 mt-6">
                    <button
                      onClick={() => setShowDetails(null)}
                      className="px-4 py-2 text-gray-600"
                    >
                      Fechar
                    </button>
                    {mode.mode_name !== activeMode && (
                      <button
                        onClick={() => {
                          activateMode(mode.mode_name);
                          setShowDetails(null);
                        }}
                        className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                      >
                        Ativar este modo
                      </button>
                    )}
                  </div>
                </>
              );
            })()}
          </div>
        </div>
      )}
      </div>
    </div>
  );
}

export default ModesPage;
