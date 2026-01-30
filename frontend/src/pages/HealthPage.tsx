/**
 * TB Personal OS - Health Dashboard Page V2
 * Fitness app style with circular progress gauges
 */

import React, { useEffect, useState } from 'react';
import { 
  Activity, 
  Heart, 
  Moon, 
  Zap, 
  TrendingUp, 
  TrendingDown,
  Target,
  Calendar,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Flame
} from 'lucide-react';
import { ProgressCard } from '../components/ui/ProgressCard';
import { api } from '../services/api';

interface HealthSummary {
  period_days: number;
  total_checkins: number;
  streak: {
    current_streak: number;
    max_streak: number;
  };
  averages: {
    sleep_hours?: number;
    energy?: number;
    mood?: number;
    productivity?: number;
  };
  insights: string[];
}

interface HealthGoal {
  id: string;
  goal_type: string;
  target_value: number;
  unit: string;
  description?: string;
}

interface Correlation {
  metric_1: string;
  metric_2: string;
  correlation_value: number;
}

export const HealthPage: React.FC = () => {
  const [summary, setSummary] = useState<HealthSummary | null>(null);
  const [goals, setGoals] = useState<HealthGoal[]>([]);
  const [correlations, setCorrelations] = useState<Correlation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadHealthData();
  }, []);

  const loadHealthData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [summaryData, goalsData, correlationsData] = await Promise.all([
        api.get('/health/summary').catch(() => null),
        api.get('/health/goals').catch(() => []),
        api.get('/health/correlations').catch(() => []),
      ]);

      setSummary(summaryData);
      setGoals(goalsData || []);
      setCorrelations(correlationsData || []);
    } catch (err: any) {
      setError('Erro ao carregar dados de saúde');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const formatMetricName = (name: string) => {
    const names: Record<string, string> = {
      'sleep_hours': 'Sono',
      'sleep_quality': 'Qualidade do Sono',
      'energy': 'Energia',
      'mood': 'Humor',
      'productivity': 'Produtividade',
      'exercise_minutes': 'Exercício',
      'water_ml': 'Hidratação',
    };
    return names[name] || name;
  };

  const getMetricIcon = (metric: string) => {
    const icons: Record<string, React.ReactNode> = {
      'sleep_hours': <Moon className="w-5 h-5 text-brand-purple-400" />,
      'energy': <Zap className="w-5 h-5 text-accent-yellow-400" />,
      'mood': <Heart className="w-5 h-5 text-accent-pink-400" />,
      'productivity': <TrendingUp className="w-5 h-5 text-accent-green-400" />,
    };
    return icons[metric] || <Activity className="w-5 h-5 text-accent-blue-400" />;
  };

  const getGoalIcon = (type: string) => {
    const icons: Record<string, string> = {
      'sleep': '💤',
      'steps': '👟',
      'water': '💧',
      'exercise': '🏃',
      'meditation': '🧘',
    };
    return icons[type] || '📌';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="relative">
          <div className="w-16 h-16 rounded-full border-4 border-dark-bg-tertiary border-t-accent-lime-500 animate-spin-slow" />
          <div className="absolute inset-0 w-16 h-16 rounded-full bg-accent-lime-500/20 blur-xl animate-pulse" />
        </div>
      </div>
    );
  }

  const sleepHours = summary?.averages.sleep_hours || 0;
  const energyLevel = summary?.averages.energy || 0;
  const moodLevel = summary?.averages.mood || 0;
  const productivityLevel = summary?.averages.productivity || 0;
  const currentStreak = summary?.streak.current_streak || 0;
  const maxStreak = summary?.streak.max_streak || 0;

  return (
    <div className="min-h-screen bg-dark-bg-primary pb-24 md:pb-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        
        {/* Header */}
        <div className="flex items-center justify-between animate-slide-down">
          <div>
            <h1 className="text-display-lg font-bold text-white mb-2">
              Saúde & <span className="text-gradient">Bem-estar</span>
            </h1>
            <p className="text-xl text-dark-text-secondary">
              Acompanhe suas métricas e descubra padrões
            </p>
          </div>
          <button 
            onClick={loadHealthData}
            className="btn-gradient px-6 py-3 rounded-xl font-semibold text-white shadow-glow-lime hover:shadow-glow-lime/50 transition-all hover:scale-[1.02] active:scale-[0.98] flex items-center"
          >
            <RefreshCw className="w-5 h-5 mr-2" />
            Atualizar
          </button>
        </div>

        {error && (
          <div className="glass-card p-4 border-l-4 border-l-accent-red-500 flex items-center gap-3 shadow-glow-red animate-shake">
            <AlertCircle className="w-5 h-5 text-accent-red-400" />
            <span className="text-accent-red-400">{error}</span>
          </div>
        )}

        {/* Circular Progress Gauges - Easy·A Style */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Streak Card */}
          <div className="glass-card p-6 bg-gradient-to-br from-accent-red-500/20 to-accent-red-600/10 border border-accent-red-500/30 shadow-glow-red animate-scale-in">
            <div className="flex flex-col items-center">
              <div className="relative mb-4">
                <Flame className="w-16 h-16 text-accent-red-400 animate-float" />
                <div className="absolute -top-2 -right-2 w-8 h-8 bg-accent-red-500 rounded-full flex items-center justify-center text-white text-xs font-bold shadow-glow-red">
                  {currentStreak}
                </div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-white mb-1">{currentStreak} dias</div>
                <div className="text-sm text-dark-text-secondary">Streak Atual</div>
                <div className="text-xs text-accent-red-400 mt-1">Recorde: {maxStreak}</div>
              </div>
            </div>
          </div>

          {/* Sleep Progress */}
          <ProgressCard
            label="Sono"
            value={sleepHours}
            maxValue={10}
            unit="h"
            type="circular"
            color="purple"
            size="md"
            icon={<Moon className="w-6 h-6" />}
            subtitle={`Meta: 8h`}
          />

          {/* Energy Progress */}
          <ProgressCard
            label="Energia"
            value={energyLevel}
            maxValue={10}
            type="circular"
            color="yellow"
            size="md"
            icon={<Zap className="w-6 h-6" />}
            subtitle="Nível atual"
          />

          {/* Mood Progress */}
          <ProgressCard
            label="Humor"
            value={moodLevel}
            maxValue={10}
            type="circular"
            color="pink"
            size="md"
            icon={<Heart className="w-6 h-6" />}
            subtitle="Média semanal"
          />
        </div>

        {/* Productivity Linear */}
        <div className="glass-card p-6 shadow-glass-lg animate-slide-up">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <TrendingUp className="w-6 h-6 text-accent-green-400 mr-3" />
              <div>
                <h3 className="text-xl font-bold text-white">Produtividade</h3>
                <p className="text-sm text-dark-text-secondary">Média dos últimos 7 dias</p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-display-lg font-bold text-accent-green-400">{productivityLevel.toFixed(1)}</div>
              <div className="text-sm text-dark-text-secondary">de 10</div>
            </div>
          </div>
          <ProgressCard
            label=""
            value={productivityLevel}
            maxValue={10}
            type="linear"
            color="green"
            showPercentage={false}
            className="mt-0"
          />
        </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Goals */}
        <div className="glass-card p-6 shadow-glass-lg animate-slide-up">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-xl bg-brand-purple-500/20">
              <Target className="w-6 h-6 text-brand-purple-400" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white">Metas de Saúde</h3>
              <p className="text-sm text-dark-text-secondary">Objetivos personalizados</p>
            </div>
          </div>
          {goals.length === 0 ? (
            <div className="text-center py-12">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-brand-purple-500/10 mb-4">
                <Target className="w-8 h-8 text-brand-purple-400" />
              </div>
              <p className="text-white font-medium mb-1">Nenhuma meta definida</p>
              <p className="text-sm text-dark-text-secondary">Crie suas primeiras metas</p>
            </div>
          ) : (
            <div className="space-y-3">
              {goals.map((goal, index) => (
                <div 
                  key={goal.id}
                  className="p-4 bg-dark-bg-tertiary/30 border border-white/5 rounded-xl hover:bg-dark-bg-elevated hover:border-brand-purple-500/30 transition-all animate-slide-up"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-3xl">{getGoalIcon(goal.goal_type)}</span>
                      <div>
                        <p className="font-semibold text-white capitalize">
                          {goal.goal_type}
                        </p>
                        <p className="text-sm text-dark-text-secondary">
                          {goal.description || `Meta: ${goal.target_value} ${goal.unit}`}
                        </p>
                      </div>
                    </div>
                    <div className="px-3 py-1 rounded-lg bg-brand-purple-500/20 border border-brand-purple-500/30 text-brand-purple-400 font-semibold text-sm">
                      {goal.target_value} {goal.unit}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Correlations */}
        <div className="glass-card p-6 shadow-glass-lg animate-slide-up" style={{ animationDelay: '100ms' }}>
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-xl bg-accent-blue-500/20">
              <Activity className="w-6 h-6 text-accent-blue-400" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white">Correlações</h3>
              <p className="text-sm text-dark-text-secondary">Padrões descobertos</p>
            </div>
          </div>
          {correlations.length === 0 ? (
            <div className="text-center py-12">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-accent-blue-500/10 mb-4">
                <Activity className="w-8 h-8 text-accent-blue-400" />
              </div>
              <p className="text-white font-medium mb-1">Ainda não há correlações</p>
              <p className="text-sm text-dark-text-secondary">Continue fazendo check-ins</p>
            </div>
          ) : (
            <div className="space-y-3">
              {correlations.slice(0, 5).map((corr, idx) => (
                <div 
                  key={idx}
                  className="p-4 bg-dark-bg-tertiary/30 border border-white/5 rounded-xl hover:bg-dark-bg-elevated hover:border-accent-blue-500/30 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-2">
                        {getMetricIcon(corr.metric_1)}
                        <span className="text-dark-text-secondary">×</span>
                        {getMetricIcon(corr.metric_2)}
                      </div>
                      <div>
                        <span className="text-sm text-white font-medium block">
                          {formatMetricName(corr.metric_1)} × {formatMetricName(corr.metric_2)}
                        </span>
                        <span className="text-xs text-dark-text-secondary">
                          {corr.correlation_value > 0 ? 'Correlação positiva' : 'Correlação negativa'}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {corr.correlation_value > 0 ? (
                        <TrendingUp className="w-5 h-5 text-accent-green-400" />
                      ) : (
                        <TrendingDown className="w-5 h-5 text-accent-red-400" />
                      )}
                      <span className={`font-bold text-lg ${
                        corr.correlation_value > 0 ? 'text-accent-green-400' : 'text-accent-red-400'
                      }`}>
                        {(corr.correlation_value * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Insights */}
      {summary?.insights && summary.insights.length > 0 && (
        <div className="glass-card p-6 shadow-glass-lg animate-slide-up">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-xl bg-accent-green-500/20">
              <CheckCircle className="w-6 h-6 text-accent-green-400" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white">Insights Personalizados</h3>
              <p className="text-sm text-dark-text-secondary">Descobertas baseadas em seus dados</p>
            </div>
          </div>
          <div className="space-y-3">
            {summary.insights.map((insight, idx) => (
              <div 
                key={idx}
                className="p-4 bg-dark-bg-tertiary/30 border border-white/5 border-l-4 border-l-accent-green-500 rounded-xl hover:bg-dark-bg-elevated hover:border-accent-green-400 transition-all animate-slide-up"
                style={{ animationDelay: `${idx * 50}ms` }}
              >
                <p className="text-white leading-relaxed">{insight}</p>
              </div>
            ))}
          </div>
        </div>
      )}
      </div>
    </div>
  );
};

export default HealthPage;
