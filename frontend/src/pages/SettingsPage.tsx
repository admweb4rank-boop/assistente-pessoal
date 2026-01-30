/**
 * TB Personal OS - Settings Page
 */

import React, { useState } from 'react';
import { 
  Settings as SettingsIcon, 
  User,
  Bell,
  Shield,
  Palette,
  Link2,
  LogOut,
  ChevronRight,
  Check,
  Moon,
  Sun,
  Smartphone,
  Mail,
  Calendar,
  HardDrive,
  Bot
} from 'lucide-react';
import { Card, CardTitle, CardContent, Button } from '../components/ui';
import { useAuthStore } from '../hooks/useAuthStore';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';

interface IntegrationStatus {
  google: boolean;
  telegram: boolean;
}

export const SettingsPage: React.FC = () => {
  const { user, signOut } = useAuthStore();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('profile');
  const [theme, setTheme] = useState<'light' | 'dark' | 'system'>('system');
  const [integrations, setIntegrations] = useState<IntegrationStatus>({
    google: false,
    telegram: false,
  });
  const [notifications, setNotifications] = useState({
    email: true,
    telegram: true,
    morning_routine: true,
    evening_routine: true,
    task_reminders: true,
  });

  React.useEffect(() => {
    checkIntegrations();
  }, []);

  const checkIntegrations = async () => {
    try {
      const status = await api.get('/auth/google/status');
      setIntegrations(prev => ({ ...prev, google: status.connected }));
    } catch {
      // Ignore
    }
  };

  const handleSignOut = async () => {
    await signOut();
    navigate('/login');
  };

  const handleConnectGoogle = async () => {
    try {
      const { auth_url } = await api.get('/auth/google/authorize');
      window.location.href = auth_url;
    } catch (err) {
      console.error('Error connecting Google:', err);
    }
  };

  const tabs = [
    { id: 'profile', label: 'Perfil', icon: User },
    { id: 'notifications', label: 'Notificações', icon: Bell },
    { id: 'integrations', label: 'Integrações', icon: Link2 },
    { id: 'appearance', label: 'Aparência', icon: Palette },
    { id: 'security', label: 'Segurança', icon: Shield },
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'profile':
        return (
          <div className="space-y-6">
            <div className="flex items-center gap-4">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-2xl font-bold">
                {user?.email?.charAt(0).toUpperCase() || 'U'}
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  {user?.user_metadata?.name || 'Usuário'}
                </h3>
                <p className="text-gray-500">{user?.email}</p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Nome
                </label>
                <input
                  type="text"
                  defaultValue={user?.user_metadata?.name || ''}
                  className="w-full px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={user?.email || ''}
                  disabled
                  className="w-full px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-900 text-gray-500"
                />
              </div>
              <Button>Salvar Alterações</Button>
            </div>
          </div>
        );

      case 'notifications':
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="flex items-center gap-3">
                <Mail className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">Notificações por Email</p>
                  <p className="text-sm text-gray-500">Receba resumos e alertas por email</p>
                </div>
              </div>
              <button
                onClick={() => setNotifications(prev => ({ ...prev, email: !prev.email }))}
                className={`w-12 h-6 rounded-full transition-colors ${
                  notifications.email ? 'bg-blue-500' : 'bg-gray-300'
                }`}
              >
                <span className={`block w-5 h-5 bg-white rounded-full shadow transform transition-transform ${
                  notifications.email ? 'translate-x-6' : 'translate-x-0.5'
                }`} />
              </button>
            </div>

            <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="flex items-center gap-3">
                <Smartphone className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">Notificações Telegram</p>
                  <p className="text-sm text-gray-500">Receba mensagens no bot do Telegram</p>
                </div>
              </div>
              <button
                onClick={() => setNotifications(prev => ({ ...prev, telegram: !prev.telegram }))}
                className={`w-12 h-6 rounded-full transition-colors ${
                  notifications.telegram ? 'bg-blue-500' : 'bg-gray-300'
                }`}
              >
                <span className={`block w-5 h-5 bg-white rounded-full shadow transform transition-transform ${
                  notifications.telegram ? 'translate-x-6' : 'translate-x-0.5'
                }`} />
              </button>
            </div>

            <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="flex items-center gap-3">
                <Sun className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">Rotina Matinal</p>
                  <p className="text-sm text-gray-500">Lembrete de check-in matinal às 7h</p>
                </div>
              </div>
              <button
                onClick={() => setNotifications(prev => ({ ...prev, morning_routine: !prev.morning_routine }))}
                className={`w-12 h-6 rounded-full transition-colors ${
                  notifications.morning_routine ? 'bg-blue-500' : 'bg-gray-300'
                }`}
              >
                <span className={`block w-5 h-5 bg-white rounded-full shadow transform transition-transform ${
                  notifications.morning_routine ? 'translate-x-6' : 'translate-x-0.5'
                }`} />
              </button>
            </div>

            <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="flex items-center gap-3">
                <Moon className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">Rotina Noturna</p>
                  <p className="text-sm text-gray-500">Lembrete de reflexão às 21h</p>
                </div>
              </div>
              <button
                onClick={() => setNotifications(prev => ({ ...prev, evening_routine: !prev.evening_routine }))}
                className={`w-12 h-6 rounded-full transition-colors ${
                  notifications.evening_routine ? 'bg-blue-500' : 'bg-gray-300'
                }`}
              >
                <span className={`block w-5 h-5 bg-white rounded-full shadow transform transition-transform ${
                  notifications.evening_routine ? 'translate-x-6' : 'translate-x-0.5'
                }`} />
              </button>
            </div>
          </div>
        );

      case 'integrations':
        return (
          <div className="space-y-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-white rounded-lg shadow flex items-center justify-center">
                      <svg className="w-6 h-6" viewBox="0 0 24 24">
                        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                      </svg>
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white">Google</h4>
                      <p className="text-sm text-gray-500">Calendar, Gmail, Drive</p>
                    </div>
                  </div>
                  {integrations.google ? (
                    <div className="flex items-center gap-2 text-green-600">
                      <Check className="w-5 h-5" />
                      <span>Conectado</span>
                    </div>
                  ) : (
                    <Button onClick={handleConnectGoogle} variant="outline" size="sm">
                      Conectar
                    </Button>
                  )}
                </div>
                {integrations.google && (
                  <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-6 text-sm text-gray-500">
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4" />
                        Calendar
                      </div>
                      <div className="flex items-center gap-2">
                        <Mail className="w-4 h-4" />
                        Gmail
                      </div>
                      <div className="flex items-center gap-2">
                        <HardDrive className="w-4 h-4" />
                        Drive
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-blue-500 rounded-lg flex items-center justify-center">
                      <Bot className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white">Telegram Bot</h4>
                      <p className="text-sm text-gray-500">Assistente via chat</p>
                    </div>
                  </div>
                  {integrations.telegram ? (
                    <div className="flex items-center gap-2 text-green-600">
                      <Check className="w-5 h-5" />
                      <span>Conectado</span>
                    </div>
                  ) : (
                    <Button variant="outline" size="sm">
                      Configurar
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        );

      case 'appearance':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              {[
                { id: 'light', label: 'Claro', icon: Sun },
                { id: 'dark', label: 'Escuro', icon: Moon },
                { id: 'system', label: 'Sistema', icon: Smartphone },
              ].map(option => (
                <button
                  key={option.id}
                  onClick={() => setTheme(option.id as typeof theme)}
                  className={`p-4 rounded-lg border-2 transition-colors ${
                    theme === option.id
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                  }`}
                >
                  <option.icon className={`w-6 h-6 mx-auto mb-2 ${
                    theme === option.id ? 'text-blue-500' : 'text-gray-400'
                  }`} />
                  <span className={`text-sm ${
                    theme === option.id ? 'text-blue-600 font-medium' : 'text-gray-600'
                  }`}>
                    {option.label}
                  </span>
                </button>
              ))}
            </div>
          </div>
        );

      case 'security':
        return (
          <div className="space-y-6">
            <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">Alterar Senha</h4>
              <p className="text-sm text-gray-500 mb-4">
                Atualize sua senha para manter sua conta segura
              </p>
              <Button variant="outline">Alterar Senha</Button>
            </div>

            <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">Sessões Ativas</h4>
              <p className="text-sm text-gray-500 mb-4">
                Gerencie dispositivos conectados à sua conta
              </p>
              <Button variant="outline">Ver Sessões</Button>
            </div>

            <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
              <h4 className="font-medium text-red-700 dark:text-red-400 mb-2">Zona de Perigo</h4>
              <p className="text-sm text-red-600 dark:text-red-300 mb-4">
                Ações irreversíveis para sua conta
              </p>
              <Button 
                variant="outline" 
                className="border-red-500 text-red-500 hover:bg-red-50"
              >
                Excluir Conta
              </Button>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <SettingsIcon className="w-7 h-7 text-gray-500" />
            Configurações
          </h1>
          <p className="text-gray-500 dark:text-gray-400">
            Gerencie sua conta e preferências
          </p>
        </div>

        <div className="flex flex-col md:flex-row gap-6">
          {/* Sidebar */}
          <nav className="w-full md:w-64 space-y-1">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-colors ${
                  activeTab === tab.id
                    ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600'
                    : 'text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800'
                }`}
              >
                <tab.icon className="w-5 h-5" />
                <span>{tab.label}</span>
                <ChevronRight className="w-4 h-4 ml-auto" />
              </button>
            ))}

            <hr className="my-4 border-gray-200 dark:border-gray-700" />

            <button
              onClick={handleSignOut}
              className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
            >
              <LogOut className="w-5 h-5" />
              <span>Sair</span>
            </button>
          </nav>

          {/* Content */}
          <Card className="flex-1">
            <CardTitle className="p-4 border-b dark:border-gray-700 capitalize">
              {tabs.find(t => t.id === activeTab)?.label}
            </CardTitle>
            <CardContent className="p-6">
              {renderContent()}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
