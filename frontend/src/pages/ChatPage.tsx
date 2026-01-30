/**
 * TB Personal OS - Chat/Assistant Page
 */

import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, Sparkles } from 'lucide-react';
import { GlassCard, Button, Input } from '../components/ui';
import { api } from '../services/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isLoading?: boolean;
}

export const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initial greeting
  useEffect(() => {
    setMessages([{
      id: 'welcome',
      role: 'assistant',
      content: 'Olá! 👋 Sou seu assistente pessoal com IA. Como posso ajudar?\n\nVocê pode me perguntar sobre:\n• Suas tarefas e projetos\n• Agendar compromissos\n• Análise do seu dia/semana\n• Qualquer dúvida ou ideia!',
      timestamp: new Date(),
    }]);
  }, []);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    // Add loading message
    const loadingId = (Date.now() + 1).toString();
    setMessages(prev => [...prev, {
      id: loadingId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isLoading: true,
    }]);

    try {
      const response = await api.askAssistant(input.trim());
      
      // Replace loading message with actual response
      setMessages(prev => prev.map(m => 
        m.id === loadingId 
          ? { ...m, content: response.response || response, isLoading: false }
          : m
      ));
    } catch (err: any) {
      setMessages(prev => prev.map(m => 
        m.id === loadingId 
          ? { ...m, content: 'Desculpe, ocorreu um erro. Tente novamente.', isLoading: false }
          : m
      ));
    } finally {
      setIsLoading(false);
    }
  };

  const quickActions = [
    { label: '📋 Resumo do dia', message: 'Me dê um resumo do meu dia' },
    { label: '✅ Tarefas pendentes', message: 'Quais são minhas tarefas pendentes?' },
    { label: '📅 Agenda de hoje', message: 'O que tenho na agenda hoje?' },
    { label: '💡 Sugestões', message: 'O que você sugere que eu faça agora?' },
  ];

  const handleQuickAction = (message: string) => {
    setInput(message);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] animate-fade-in">
      {/* Header */}
      <div className="mb-4">
        <h1 className="text-3xl font-bold text-gradient flex items-center">
          <Sparkles className="w-6 h-6 mr-2 text-brand-purple-400 animate-pulse" />
          Assistente IA
        </h1>
        <p className="text-dark-text-secondary mt-1">Converse com seu assistente pessoal</p>
      </div>

      {/* Messages */}
      <GlassCard className="flex-1 overflow-hidden flex flex-col shadow-glow-purple">
        <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
          {messages.map((message, index) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-slide-up`}
              style={{ animationDelay: `${index * 50}ms` }}
            >
              <div
                className={`flex items-start max-w-[80%] ${
                  message.role === 'user' ? 'flex-row-reverse' : ''
                }`}
              >
                <div
                  className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                    message.role === 'user' 
                      ? 'bg-gradient-to-br from-brand-purple-500 to-brand-blue-500 ml-2 shadow-glow-purple' 
                      : 'glass-card mr-2'
                  }`}
                >
                  {message.role === 'user' 
                    ? <User className="w-4 h-4 text-white" />
                    : <Bot className="w-4 h-4 text-brand-purple-400" />
                  }
                </div>
                <div
                  className={`px-4 py-3 rounded-2xl transition-all duration-300 ${
                    message.role === 'user'
                      ? 'bg-gradient-to-r from-brand-purple-500 to-brand-blue-500 text-white rounded-br-sm shadow-glow-purple'
                      : 'glass-card text-white rounded-bl-sm border border-dark-border'
                  }`}
                >
                  {message.isLoading ? (
                    <div className="flex items-center space-x-2">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Pensando...</span>
                    </div>
                  ) : (
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  )}
                </div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Actions */}
        {messages.length <= 1 && (
          <div className="px-4 py-3 border-t border-dark-border">
            <p className="text-xs text-dark-text-secondary mb-2">Ações rápidas:</p>
            <div className="flex flex-wrap gap-2">
              {quickActions.map((action) => (
                <button
                  key={action.label}
                  onClick={() => handleQuickAction(action.message)}
                  className="px-3 py-1.5 text-sm glass-card rounded-full text-white hover:border-brand-purple-500/50 transition-all duration-300 hover:shadow-glow-purple"
                >
                  {action.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <form onSubmit={sendMessage} className="p-4 border-t border-dark-border">
          <div className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Digite sua mensagem..."
              disabled={isLoading}
              className="flex-1 glass-input"
            />
            <Button
              type="submit"
              variant="gradient"
              disabled={!input.trim() || isLoading}
              leftIcon={isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              className="shadow-glow-purple"
            >
              Enviar
            </Button>
          </div>
        </form>
      </GlassCard>
    </div>
  );
};

export default ChatPage;
