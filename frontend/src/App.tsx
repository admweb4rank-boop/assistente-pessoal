/**
 * TB Personal OS - Main Application Component
 */

import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuthStore } from './hooks/useAuthStore';
import { Layout } from './components/layout';
import { 
  LoginPage, 
  DashboardPage, 
  TasksPage, 
  InboxPage, 
  ChatPage,
  HealthPage,
  InsightsPage,
  CalendarPage,
  ProjectsPage,
  SettingsPage,
  BookmarkletPage,
  ContentPage,
  LearningPage,
  ModesPage,
  FinancesPage,
  GoalsPage
} from './pages';
import PrivacyPage from './pages/PrivacyPage';
import TermsPage from './pages/TermsPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// Protected Route wrapper
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

// Public Route wrapper (redirects to dashboard if authenticated)
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

// App wrapper for auth initialization
const AppContent: React.FC = () => {
  const { initialize } = useAuthStore();

  useEffect(() => {
    initialize();
  }, [initialize]);

  return (
    <Routes>
      {/* Public routes */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        }
      />
      
      {/* Public pages - Privacy & Terms */}
      <Route path="/privacy" element={<PrivacyPage />} />
      <Route path="/terms" element={<TermsPage />} />
      <Route path="/bookmarklet" element={<BookmarkletPage />} />

      {/* Protected routes with layout */}
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<DashboardPage />} />
        <Route path="/tasks" element={<TasksPage />} />
        <Route path="/inbox" element={<InboxPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/health" element={<HealthPage />} />
        <Route path="/insights" element={<InsightsPage />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/calendar" element={<CalendarPage />} />
        <Route path="/content" element={<ContentPage />} />
        <Route path="/learning" element={<LearningPage />} />
        <Route path="/modes" element={<ModesPage />} />
        <Route path="/finances" element={<FinancesPage />} />
        <Route path="/goals" element={<GoalsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>

      {/* Auth callback */}
      <Route path="/auth/callback" element={<AuthCallback />} />

      {/* 404 */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

// Coming Soon placeholder
const ComingSoon: React.FC<{ title: string }> = ({ title }) => (
  <div className="text-center py-12">
    <div className="text-6xl mb-4">🚧</div>
    <h2 className="text-2xl font-bold text-gray-900 mb-2">{title}</h2>
    <p className="text-gray-600">Esta funcionalidade está em desenvolvimento</p>
  </div>
);

// Auth callback handler
const AuthCallback: React.FC = () => {
  const [error, setError] = React.useState<string | null>(null);
  const [debugInfo, setDebugInfo] = React.useState<string[]>([]);
  const { initialize } = useAuthStore();

  useEffect(() => {
    const processCallback = async () => {
      try {
        console.log('[AuthCallback] Iniciando processamento do callback OAuth');
        setDebugInfo(prev => [...prev, 'Iniciando processamento...']);
        
        // Verifica se há hash na URL
        const hash = window.location.hash;
        console.log('[AuthCallback] Hash da URL:', hash ? 'presente' : 'ausente');
        setDebugInfo(prev => [...prev, `Hash: ${hash ? 'presente' : 'ausente'}`]);
        
        if (!hash) {
          throw new Error('Nenhum token encontrado na URL');
        }
        
        // O Supabase processa automaticamente os tokens do hash
        console.log('[AuthCallback] Chamando initialize()');
        setDebugInfo(prev => [...prev, 'Inicializando auth...']);
        await initialize();
        
        console.log('[AuthCallback] Initialize concluído, aguardando 1s...');
        setDebugInfo(prev => [...prev, 'Processando sessão...']);
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        console.log('[AuthCallback] Redirecionando para dashboard');
        setDebugInfo(prev => [...prev, 'Redirecionando...']);
        
        // Redireciona para o dashboard
        window.location.replace('/dashboard');
      } catch (err) {
        console.error('[AuthCallback] Erro:', err);
        const errorMsg = err instanceof Error ? err.message : 'Erro desconhecido';
        setError(`Erro ao processar autenticação: ${errorMsg}`);
        setDebugInfo(prev => [...prev, `ERRO: ${errorMsg}`]);
        
        // Redireciona para login após 5s
        setTimeout(() => {
          window.location.replace('/login');
        }, 5000);
      }
    };

    processCallback();
  }, [initialize]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center max-w-md">
        {error ? (
          <>
            <div className="text-red-500 text-4xl mb-4">⚠️</div>
            <p className="text-red-600 mb-4">{error}</p>
            <div className="text-xs text-left bg-gray-100 p-3 rounded">
              {debugInfo.map((info, i) => (
                <div key={i} className="mb-1">{info}</div>
              ))}
            </div>
          </>
        ) : (
          <>
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
            <p className="text-gray-600 mb-4">Autenticando com Google...</p>
            <div className="text-xs text-left bg-gray-100 p-3 rounded">
              {debugInfo.map((info, i) => (
                <div key={i} className="mb-1">{info}</div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <AppContent />
      </Router>
    </QueryClientProvider>
  );
}

export default App;
