/**
 * TB Personal OS - Inbox Page
 */

import React, { useEffect, useState } from 'react';
import { 
  Inbox, 
  MessageSquare,
  Bot,
  ArrowRight,
  Archive,
  Trash2,
  RefreshCw
} from 'lucide-react';
import { GlassCard, Badge, Button } from '../components/ui';
import { api } from '../services/api';
import type { InboxItem } from '../types';

export const InboxPage: React.FC = () => {
  const [items, setItems] = useState<InboxItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [filter, setFilter] = useState<'pending' | 'processed' | 'all'>('pending');

  useEffect(() => {
    loadInbox();
  }, [filter]);

  const loadInbox = async () => {
    setIsLoading(true);
    try {
      const data = await api.getInbox({ 
        status: filter === 'all' ? undefined : filter,
        limit: 50 
      });
      setItems(data.items || data || []);
    } catch (err) {
      console.error('Failed to load inbox:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleProcess = async (itemId: string) => {
    setProcessingId(itemId);
    try {
      const result = await api.processInboxItem(itemId);
      // Show result somehow
      console.log('Process result:', result);
      loadInbox();
    } catch (err) {
      console.error('Failed to process item:', err);
    } finally {
      setProcessingId(null);
    }
  };

  const handleArchiveAll = async () => {
    if (!confirm('Arquivar todos os itens processados?')) return;
    
    try {
      await api.archiveProcessedInbox();
      loadInbox();
    } catch (err) {
      console.error('Failed to archive:', err);
    }
  };

  const getSourceIcon = (source: string) => {
    switch (source) {
      case 'telegram':
        return <MessageSquare className="w-4 h-4" />;
      case 'web':
        return <Bot className="w-4 h-4" />;
      default:
        return <Inbox className="w-4 h-4" />;
    }
  };

  const getSourceBadge = (source: string) => {
    const config: Record<string, { variant: 'purple' | 'blue' | 'default', label: string }> = {
      telegram: { variant: 'purple', label: '📱 Telegram' },
      web: { variant: 'blue', label: '🌐 Web' },
      voice: { variant: 'default', label: '🎤 Voz' },
    };
    const { variant, label } = config[source] || { variant: 'default', label: source };
    return <Badge variant={variant} size="sm">{label}</Badge>;
  };

  return (
    <div className="min-h-screen bg-dark-bg-primary pb-24 md:pb-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 animate-slide-down">
          <div>
            <h1 className="text-display-lg font-bold text-white mb-2">
              📥 <span className="text-gradient">Inbox</span>
            </h1>
            <p className="text-xl text-dark-text-secondary">Capture rápida de ideias e mensagens</p>
          </div>
          <div className="flex gap-2">
          <Button 
            variant="outline"
            onClick={loadInbox}
            leftIcon={<RefreshCw className="w-4 h-4" />}
          >
            Atualizar
          </Button>
          <Button 
            variant="gradient"
            onClick={handleArchiveAll}
            leftIcon={<Archive className="w-4 h-4" />}
            className="shadow-glow-purple"
          >
            Arquivar Processados
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        {(['pending', 'processed', 'all'] as const).map((f) => (
          <Button
            key={f}
            variant={filter === f ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setFilter(f)}
          >
            {f === 'pending' ? 'Pendentes' : f === 'processed' ? 'Processados' : 'Todos'}
          </Button>
        ))}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <GlassCard className="flex items-center shadow-glow-yellow animate-slide-up">
          <div className="p-3 bg-gradient-to-br from-accent-yellow-500 to-accent-yellow-600 rounded-xl shadow-glow-yellow">
            <Inbox className="w-5 h-5 text-white" />
          </div>
          <div className="ml-3">
            <p className="text-xs text-dark-text-secondary">Pendentes</p>
            <p className="text-2xl font-bold text-white">{items.filter(i => i.status === 'pending').length}</p>
          </div>
        </GlassCard>
        <GlassCard className="flex items-center shadow-glow-green animate-slide-up" style={{ animationDelay: '100ms' }}>
          <div className="p-3 bg-gradient-to-br from-accent-green-500 to-accent-green-600 rounded-xl shadow-glow-green">
            <ArrowRight className="w-5 h-5 text-white" />
          </div>
          <div className="ml-3">
            <p className="text-xs text-dark-text-secondary">Processados</p>
            <p className="text-2xl font-bold text-white">{items.filter(i => i.status === 'processed').length}</p>
          </div>
        </GlassCard>
        <GlassCard className="flex items-center shadow-glow-purple animate-slide-up" style={{ animationDelay: '200ms' }}>
          <div className="p-3 bg-gradient-to-br from-brand-purple-500 to-brand-purple-600 rounded-xl shadow-glow-purple">
            <Archive className="w-5 h-5 text-white" />
          </div>
          <div className="ml-3">
            <p className="text-xs text-dark-text-secondary">Arquivados</p>
            <p className="text-2xl font-bold text-white">{items.filter(i => i.status === 'archived').length}</p>
          </div>
        </GlassCard>
      </div>

      {/* Inbox Items */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      ) : items.length === 0 ? (
        <GlassCard className="text-center py-12 animate-scale-in">
          <Inbox className="w-16 h-16 mx-auto text-brand-purple-400/30 mb-4" />
          <h3 className="text-lg font-medium text-white">Inbox vazio!</h3>
          <p className="text-dark-text-secondary mt-1">
            Envie mensagens pelo Telegram ou adicione itens via API
          </p>
        </GlassCard>
      ) : (
        <div className="space-y-4">
          {items.map((item, index) => (
            <GlassCard 
              key={item.id}
              className={`transition-all hover:border-brand-purple-500/30 animate-slide-up ${
                item.status === 'processed' ? 'opacity-60' : ''
              }`}
              style={{ animationDelay: `${index * 50}ms` }}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    {getSourceBadge(item.source)}
                    <span className="text-xs text-dark-text-secondary">
                      {new Date(item.created_at).toLocaleString('pt-BR')}
                    </span>
                    {item.status === 'processed' && (
                      <Badge variant="green" size="sm">✓ Processado</Badge>
                    )}
                  </div>
                  <p className="text-white whitespace-pre-wrap">{item.content}</p>
                </div>
                
                {item.status === 'pending' && (
                  <div className="ml-4 flex gap-2">
                    <Button
                      size="sm"
                      variant="gradient"
                      onClick={() => handleProcess(item.id)}
                      isLoading={processingId === item.id}
                      leftIcon={<Bot className="w-4 h-4" />}
                      className="shadow-glow-purple"
                    >
                      Processar com IA
                    </Button>
                  </div>
                )}
              </div>
            </GlassCard>
          ))}
        </div>
      )}
      </div>
    </div>
  );
};

export default InboxPage;
