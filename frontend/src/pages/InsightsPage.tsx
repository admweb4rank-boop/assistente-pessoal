/**
 * TB Personal OS - Insights Page
 */

import React, { useEffect, useState } from 'react';
import { 
  Brain, 
  TrendingUp, 
  TrendingDown,
  Target,
  Clock,
  Calendar,
  RefreshCw,
  AlertCircle,
  Lightbulb,
  BarChart3,
  PieChart,
  Sparkles
} from 'lucide-react';
import { Card, CardTitle, CardContent, Badge, Button } from '../components/ui';
import { api } from '../services/api';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart as RechartsPie,
  Pie,
  Cell
} from 'recharts';

interface InsightsSummary {
  productivity_score: number;
  total_tasks_completed: number;
  completion_rate: number;
  average_completion_time_hours?: number;
  insights: string[];
  top_categories: Array<{category: string; count: number}>;
}

interface Pattern {
  pattern_type: string;
  description: string;
  confidence: number;
  data: any;
}

interface Recommendation {
  id: string;
  title: string;
  description: string;
  priority: string;
  category: string;
}

const COLORS = ['#3B82F6', '#8B5CF6', '#EC4899', '#10B981', '#F59E0B', '#EF4444'];

export const InsightsPage: React.FC = () => {
  const [summary, setSummary] = useState<InsightsSummary | null>(null);
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadInsightsData();
  }, []);

  const loadInsightsData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [summaryData, patternsData, recommendationsData] = await Promise.all([
        api.get('/insights/productivity').catch(() => null),
        api.get('/insights/patterns').catch(() => []),
        api.get('/insights/recommendations').catch(() => []),
      ]);

      setSummary(summaryData);
      setPatterns(patternsData || []);
      setRecommendations(recommendationsData || []);
    } catch (err: any) {
      setError('Erro ao carregar insights');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-500';
    if (score >= 60) return 'text-yellow-500';
    if (score >= 40) return 'text-orange-500';
    return 'text-red-500';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 80) return 'Excelente';
    if (score >= 60) return 'Bom';
    if (score >= 40) return 'Regular';
    return 'Precisa Melhorar';
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
        <div className="flex items-center justify-between animate-slide-down">
          <div>
            <h1 className="text-display-lg font-bold text-white mb-2">
              🧠 <span className="text-gradient">Insights</span>
            </h1>
            <p className="text-xl text-dark-text-secondary">
              Análise inteligente da sua produtividade
            </p>
          </div>
          <Button onClick={loadInsightsData} variant="outline" size="sm">
          <RefreshCw className="w-4 h-4 mr-2" />
          Atualizar
        </Button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <span className="text-red-700 dark:text-red-400">{error}</span>
        </div>
      )}

      {/* Score Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Productivity Score */}
        <Card className="bg-gradient-to-br from-purple-500 to-indigo-600 text-white">
          <CardContent className="p-4">
            <div className="text-center">
              <p className="text-white/80 text-sm mb-2">Score de Produtividade</p>
              <div className="relative w-24 h-24 mx-auto">
                <svg className="transform -rotate-90 w-24 h-24">
                  <circle
                    cx="48"
                    cy="48"
                    r="40"
                    stroke="currentColor"
                    strokeWidth="8"
                    fill="transparent"
                    className="text-white/20"
                  />
                  <circle
                    cx="48"
                    cy="48"
                    r="40"
                    stroke="currentColor"
                    strokeWidth="8"
                    fill="transparent"
                    strokeDasharray={251.2}
                    strokeDashoffset={251.2 - (251.2 * (summary?.productivity_score || 0)) / 100}
                    className="text-white"
                  />
                </svg>
                <span className="absolute inset-0 flex items-center justify-center text-2xl font-bold">
                  {summary?.productivity_score || 0}
                </span>
              </div>
              <p className="text-white/90 text-sm mt-2">
                {getScoreLabel(summary?.productivity_score || 0)}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Tasks Completed */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">Tarefas Concluídas</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {summary?.total_tasks_completed || 0}
                </p>
                <p className="text-gray-400 text-xs">nos últimos 7 dias</p>
              </div>
              <Target className="w-8 h-8 text-green-400" />
            </div>
          </CardContent>
        </Card>

        {/* Completion Rate */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">Taxa de Conclusão</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {summary?.completion_rate?.toFixed(0) || 0}%
                </p>
                <p className="text-gray-400 text-xs">das tarefas planejadas</p>
              </div>
              <BarChart3 className="w-8 h-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>

        {/* Avg Time */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">Tempo Médio</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {summary?.average_completion_time_hours?.toFixed(1) || '--'}h
                </p>
                <p className="text-gray-400 text-xs">por tarefa</p>
              </div>
              <Clock className="w-8 h-8 text-orange-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Categories Chart */}
        <Card>
          <CardTitle className="flex items-center gap-2 p-4 border-b dark:border-gray-700">
            <PieChart className="w-5 h-5" />
            Tarefas por Categoria
          </CardTitle>
          <CardContent className="p-4">
            {summary?.top_categories && summary.top_categories.length > 0 ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <RechartsPie>
                    <Pie
                      data={summary.top_categories}
                      dataKey="count"
                      nameKey="category"
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      label={({ category, percent }) => `${category} ${(percent * 100).toFixed(0)}%`}
                    >
                      {summary.top_categories.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </RechartsPie>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">
                Sem dados de categorias
              </p>
            )}
          </CardContent>
        </Card>

        {/* Patterns */}
        <Card>
          <CardTitle className="flex items-center gap-2 p-4 border-b dark:border-gray-700">
            <Sparkles className="w-5 h-5 text-yellow-500" />
            Padrões Identificados
          </CardTitle>
          <CardContent className="p-4">
            {patterns.length === 0 ? (
              <p className="text-gray-500 text-center py-8">
                Continue usando o app para descobrir padrões
              </p>
            ) : (
              <div className="space-y-3">
                {patterns.slice(0, 4).map((pattern, idx) => (
                  <div 
                    key={idx}
                    className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-gray-900 dark:text-white capitalize">
                        {pattern.pattern_type.replace('_', ' ')}
                      </span>
                      <Badge variant={pattern.confidence > 0.7 ? 'success' : 'info'}>
                        {(pattern.confidence * 100).toFixed(0)}% confiança
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-300">
                      {pattern.description}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recommendations */}
      <Card>
        <CardTitle className="flex items-center gap-2 p-4 border-b dark:border-gray-700">
          <Lightbulb className="w-5 h-5 text-yellow-500" />
          Recomendações Personalizadas
        </CardTitle>
        <CardContent className="p-4">
          {recommendations.length === 0 && (!summary?.insights || summary.insights.length === 0) ? (
            <p className="text-gray-500 text-center py-4">
              Sem recomendações no momento
            </p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* API Recommendations */}
              {recommendations.map((rec) => (
                <div 
                  key={rec.id}
                  className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-100 dark:border-blue-800 rounded-lg"
                >
                  <div className="flex items-start gap-3">
                    <div className="p-2 bg-blue-100 dark:bg-blue-800 rounded-lg">
                      <Lightbulb className="w-4 h-4 text-blue-600 dark:text-blue-300" />
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white">
                        {rec.title}
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                        {rec.description}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
              
              {/* Summary Insights */}
              {summary?.insights?.map((insight, idx) => (
                <div 
                  key={`insight-${idx}`}
                  className="p-4 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 border border-purple-100 dark:border-purple-800 rounded-lg"
                >
                  <p className="text-gray-700 dark:text-gray-300">{insight}</p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      </div>
    </div>
  );
};

export default InsightsPage;
