/**
 * TB Personal OS - Finances Page V2
 * Gestão financeira pessoal - Design System V2
 */

import React, { useState, useEffect } from 'react';
import { 
  DollarSign, 
  TrendingUp, 
  TrendingDown, 
  PieChart,
  Plus,
  ArrowUpRight,
  ArrowDownRight,
  Calendar,
  AlertTriangle,
  Target,
  RefreshCw,
  Wallet,
  CreditCard
} from 'lucide-react';
import { ProgressCard } from '../components/ui/ProgressCard';
import { api } from '../services/api';

interface Transaction {
  id: string;
  transaction_type: 'income' | 'expense';
  amount: number;
  description: string;
  category: string;
  transaction_date: string;
}

interface Summary {
  period: { start_date: string; end_date: string };
  total_income: number;
  total_expense: number;
  balance: number;
  transaction_count: number;
  by_category: Record<string, { income: number; expense: number }>;
  status: 'positive' | 'negative';
}

interface Alert {
  type: string;
  severity: 'warning' | 'danger' | 'info';
  title: string;
  message: string;
}

interface CategoryBreakdown {
  category: string;
  amount: number;
  percentage: number;
}

const CATEGORY_ICONS: Record<string, string> = {
  salary: '💼',
  freelance: '💻',
  investments: '📈',
  sales: '🛒',
  housing: '🏠',
  food: '🍽️',
  transport: '🚗',
  health: '🏥',
  education: '📚',
  entertainment: '🎮',
  shopping: '🛍️',
  subscriptions: '📱',
  taxes: '📋',
  other: '💰',
};

export default function FinancesPage() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [breakdown, setBreakdown] = useState<CategoryBreakdown[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [transactionType, setTransactionType] = useState<'income' | 'expense'>('expense');

  // Form state
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [summaryRes, transactionsRes, breakdownRes, alertsRes] = await Promise.all([
        api.get('/finance/summary'),
        api.get('/finance/transactions?limit=10'),
        api.get('/finance/breakdown?transaction_type=expense'),
        api.get('/finance/alerts'),
      ]);

      setSummary(summaryRes.data);
      setTransactions(transactionsRes.data.transactions || []);
      setBreakdown(breakdownRes.data.breakdown || []);
      setAlerts(alertsRes.data.alerts || []);
    } catch (error) {
      console.error('Erro ao carregar dados financeiros:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddTransaction = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      await api.post('/finance/transactions', {
        transaction_type: transactionType,
        amount: parseFloat(amount),
        description,
        category: category || undefined,
      });

      setShowAddModal(false);
      setAmount('');
      setDescription('');
      setCategory('');
      loadData();
    } catch (error) {
      console.error('Erro ao adicionar transação:', error);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(value);
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('pt-BR');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="relative">
          <div className="w-16 h-16 rounded-full border-4 border-dark-bg-tertiary border-t-accent-green-500 animate-spin-slow" />
          <div className="absolute inset-0 w-16 h-16 rounded-full bg-accent-green-500/20 blur-xl animate-pulse" />
        </div>
      </div>
    );
  }

  const savingsRate = summary?.total_income 
    ? ((summary.balance / summary.total_income) * 100) 
    : 0;

  return (
    <div className="min-h-screen bg-dark-bg-primary pb-24 md:pb-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        
        {/* Header */}
        <div className="flex items-center justify-between animate-slide-down">
          <div>
            <h1 className="text-display-lg font-bold text-white mb-2">
              💰 <span className="text-gradient">Finanças</span>
            </h1>
            <p className="text-xl text-dark-text-secondary">
              {summary?.period.start_date && formatDate(summary.period.start_date)} até {summary?.period.end_date && formatDate(summary.period.end_date)}
            </p>
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="btn-gradient px-6 py-3 rounded-xl font-semibold text-white shadow-glow-green hover:shadow-glow-green/50 transition-all hover:scale-[1.02] active:scale-[0.98] flex items-center"
          >
            <Plus className="w-5 h-5 mr-2" />
            Adicionar
          </button>
        </div>

        {/* Financial Stats - Circular Progress */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Receitas */}
          <div className="glass-card p-6 border border-accent-green-500/30 shadow-glow-green animate-scale-in">
            <div className="flex flex-col items-center">
              <div className="mb-4 p-3 rounded-xl bg-accent-green-500/20">
                <TrendingUp className="w-8 h-8 text-accent-green-400" />
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-white mb-1">
                  {formatCurrency(summary?.total_income || 0)}
                </div>
                <div className="text-sm text-dark-text-secondary">Receitas</div>
                <div className="text-xs text-accent-green-400 mt-1">
                  Mês atual
                </div>
              </div>
            </div>
          </div>

          {/* Despesas */}
          <div className="glass-card p-6 border border-accent-red-500/30 shadow-glow-red animate-scale-in" style={{ animationDelay: '100ms' }}>
            <div className="flex flex-col items-center">
              <div className="mb-4 p-3 rounded-xl bg-accent-red-500/20">
                <TrendingDown className="w-8 h-8 text-accent-red-400" />
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-white mb-1">
                  {formatCurrency(summary?.total_expense || 0)}
                </div>
                <div className="text-sm text-dark-text-secondary">Despesas</div>
              </div>
            </div>
          </div>

          {/* Saldo */}
          <div className={`glass-card p-6 border animate-scale-in ${
            (summary?.balance || 0) >= 0 
              ? 'border-accent-green-500/30 shadow-glow-green' 
              : 'border-accent-red-500/30 shadow-glow-red'
          }`} style={{ animationDelay: '200ms' }}>
            <div className="flex flex-col items-center">
              <div className={`mb-4 p-3 rounded-xl ${
                (summary?.balance || 0) >= 0 
                  ? 'bg-accent-green-500/20' 
                  : 'bg-accent-red-500/20'
              }`}>
                <Wallet className={`w-8 h-8 ${
                  (summary?.balance || 0) >= 0 
                    ? 'text-accent-green-400' 
                    : 'text-accent-red-400'
                }`} />
              </div>
              <div className="text-center">
                <div className={`text-2xl font-bold mb-1 ${
                  (summary?.balance || 0) >= 0 
                    ? 'text-accent-green-400' 
                    : 'text-accent-red-400'
                }`}>
                  {formatCurrency(summary?.balance || 0)}
                </div>
                <div className="text-sm text-dark-text-secondary">Saldo</div>
              </div>
            </div>
          </div>

          {/* Taxa de Poupança - Progress Circle */}
          <ProgressCard
            label="Taxa de Poupança"
            value={Math.max(0, savingsRate)}
            maxValue={100}
            unit="%"
            type="circular"
            color="blue"
            size="md"
            icon={<Target className="w-6 h-6" />}
            subtitle={savingsRate >= 20 ? 'Excelente!' : 'Pode melhorar'}
            className="animate-scale-in"
          />
        </div>

        {/* Alerts */}
        {alerts.length > 0 && (
          <div className="space-y-3 animate-slide-up">
            {alerts.map((alert, index) => (
              <div
                key={index}
                className={`glass-card p-4 flex items-start border-l-4 ${
                  alert.severity === 'danger' 
                    ? 'border-l-accent-red-500 bg-accent-red-500/5' :
                  alert.severity === 'warning' 
                    ? 'border-l-accent-yellow-500 bg-accent-yellow-500/5' :
                    'border-l-accent-blue-500 bg-accent-blue-500/5'
                }`}
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <AlertTriangle className={`w-5 h-5 mr-3 flex-shrink-0 ${
                  alert.severity === 'danger' ? 'text-accent-red-400' :
                  alert.severity === 'warning' ? 'text-accent-yellow-400' :
                  'text-accent-blue-400'
                }`} />
                <div>
                  <p className="font-semibold text-white mb-1">
                    {alert.title}
                  </p>
                  <p className="text-sm text-dark-text-secondary">
                    {alert.message}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Breakdown por Categoria */}
          <div className="glass-card p-6 shadow-glass-lg animate-slide-up">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 rounded-xl bg-brand-purple-500/20">
                <PieChart className="w-6 h-6 text-brand-purple-400" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">Despesas por Categoria</h2>
                <p className="text-sm text-dark-text-secondary">Distribuição mensal</p>
              </div>
            </div>
            
            {breakdown.length > 0 ? (
              <div className="space-y-4">
                {breakdown.slice(0, 6).map((item, index) => (
                  <div key={item.category} className="animate-slide-up" style={{ animationDelay: `${index * 50}ms` }}>
                    <div className="flex items-center mb-2">
                      <span className="text-2xl mr-3">
                        {CATEGORY_ICONS[item.category] || '💰'}
                      </span>
                      <div className="flex-1">
                        <div className="flex justify-between mb-2">
                          <span className="text-sm font-semibold text-white capitalize">
                            {item.category.replace('_', ' ')}
                          </span>
                          <span className="text-sm text-dark-text-secondary">
                            {formatCurrency(item.amount)} ({item.percentage}%)
                          </span>
                        </div>
                        <div className="h-2 bg-dark-bg-tertiary rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-brand-purple-500 to-accent-green-500"
                            style={{ width: `${item.percentage}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-brand-purple-500/10 mb-4">
                  <PieChart className="w-8 h-8 text-brand-purple-400" />
                </div>
                <p className="text-white font-medium mb-1">Nenhuma despesa</p>
                <p className="text-sm text-dark-text-secondary">Registre suas transações</p>
              </div>
            )}
          </div>

          {/* Últimas Transações */}
          <div className="glass-card p-6 shadow-glass-lg animate-slide-up" style={{ animationDelay: '100ms' }}>
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 rounded-xl bg-accent-blue-500/20">
                <Calendar className="w-6 h-6 text-accent-blue-400" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">Últimas Transações</h2>
                <p className="text-sm text-dark-text-secondary">Histórico recente</p>
              </div>
            </div>
            
            {transactions.length > 0 ? (
              <div className="space-y-3">
                {transactions.map((tx, index) => (
                  <div
                    key={tx.id}
                    className="p-4 bg-dark-bg-tertiary/30 border border-white/5 rounded-xl hover:bg-dark-bg-elevated hover:border-white/10 transition-all animate-slide-up"
                    style={{ animationDelay: `${index * 50}ms` }}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${
                          tx.transaction_type === 'income' 
                            ? 'bg-accent-green-500/20' 
                            : 'bg-accent-red-500/20'
                        }`}>
                          {tx.transaction_type === 'income' ? (
                            <ArrowUpRight className="w-5 h-5 text-accent-green-400" />
                          ) : (
                            <ArrowDownRight className="w-5 h-5 text-accent-red-400" />
                          )}
                        </div>
                        <div>
                          <p className="text-white font-medium">{tx.description}</p>
                          <p className="text-sm text-dark-text-secondary">
                            {formatDate(tx.transaction_date)} • {tx.category}
                          </p>
                        </div>
                      </div>
                      <div className={`text-lg font-bold ${
                        tx.transaction_type === 'income' 
                          ? 'text-accent-green-400' 
                          : 'text-accent-red-400'
                      }`}>
                        {tx.transaction_type === 'income' ? '+' : '-'}{formatCurrency(tx.amount)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-accent-blue-500/10 mb-4">
                  <Calendar className="w-8 h-8 text-accent-blue-400" />
                </div>
                <p className="text-white font-medium mb-1">Nenhuma transação</p>
                <p className="text-sm text-dark-text-secondary">Comece registrando</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Add Transaction Modal - Placeholder */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="glass-card p-6 max-w-md w-full">
            <h3 className="text-xl font-bold text-white mb-4">Adicionar Transação</h3>
            <form onSubmit={handleAddTransaction} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-dark-text-secondary mb-2">
                  Tipo
                </label>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setTransactionType('income')}
                    className={`flex-1 py-2 rounded-lg transition-all ${
                      transactionType === 'income'
                        ? 'bg-accent-green-500 text-white'
                        : 'bg-dark-bg-tertiary text-dark-text-secondary'
                    }`}
                  >
                    Receita
                  </button>
                  <button
                    type="button"
                    onClick={() => setTransactionType('expense')}
                    className={`flex-1 py-2 rounded-lg transition-all ${
                      transactionType === 'expense'
                        ? 'bg-accent-red-500 text-white'
                        : 'bg-dark-bg-tertiary text-dark-text-secondary'
                    }`}
                  >
                    Despesa
                  </button>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-dark-text-secondary mb-2">
                  Valor
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="w-full px-4 py-3 bg-dark-bg-tertiary border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-brand-purple-500/50"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-dark-text-secondary mb-2">
                  Descrição
                </label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-4 py-3 bg-dark-bg-tertiary border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-brand-purple-500/50"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-dark-text-secondary mb-2">
                  Categoria
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-4 py-3 bg-dark-bg-tertiary border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-brand-purple-500/50"
                >
                  <option value="">Selecione...</option>
                  {Object.keys(CATEGORY_ICONS).map((cat) => (
                    <option key={cat} value={cat}>
                      {CATEGORY_ICONS[cat]} {cat}
                    </option>
                  ))}
                </select>
              </div>
              
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 py-3 bg-dark-bg-tertiary text-white rounded-xl hover:bg-dark-bg-elevated transition-all"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="flex-1 btn-gradient py-3 rounded-xl font-semibold text-white shadow-glow-green"
                >
                  Salvar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
