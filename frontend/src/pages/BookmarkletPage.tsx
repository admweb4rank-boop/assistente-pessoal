import { useState, useEffect } from 'react';

interface BookmarkletData {
  bookmarklet: string;
  instructions: string[];
  features: string[];
}

export default function BookmarkletPage() {
  const [bookmarkletData, setBookmarkletData] = useState<BookmarkletData | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchBookmarkletData();
  }, []);

  const fetchBookmarkletData = async () => {
    try {
      const response = await fetch('/api/v1/bookmarklet/script');
      const data = await response.json();
      setBookmarkletData(data);
    } catch (error) {
      console.error('Error fetching bookmarklet data:', error);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async () => {
    if (bookmarkletData?.bookmarklet) {
      await navigator.clipboard.writeText(bookmarkletData.bookmarklet);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 to-indigo-700 py-12 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Header Card */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-8 mb-8">
          <div className="text-center mb-8">
            <div className="text-6xl mb-4">📌</div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              Salvar no Igor
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Bookmarklet para capturar links e páginas rapidamente
            </p>
          </div>

          {/* Bookmarklet Button */}
          <div className="bg-gray-100 dark:bg-gray-700 rounded-xl p-8 text-center mb-8">
            <a
              href={bookmarkletData?.bookmarklet || '#'}
              className="inline-block bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-8 py-4 rounded-xl text-lg font-semibold hover:shadow-lg hover:scale-105 transition-all cursor-grab active:cursor-grabbing"
              onClick={(e) => e.preventDefault()}
              draggable="true"
            >
              📌 Salvar no Igor
            </a>
            <p className="text-gray-500 dark:text-gray-400 mt-4 text-sm">
              ⬆️ Arraste este botão para sua barra de favoritos
            </p>
          </div>

          {/* Copy Button */}
          <div className="text-center">
            <button
              onClick={copyToClipboard}
              className={`px-6 py-3 rounded-lg font-medium transition-all ${
                copied
                  ? 'bg-green-500 text-white'
                  : 'bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-500'
              }`}
            >
              {copied ? '✓ Copiado!' : '📋 Copiar Código'}
            </button>
          </div>
        </div>

        {/* Instructions Card */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 mb-8">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <span>📋</span> Como Instalar
          </h2>
          <ol className="space-y-4">
            <li className="flex gap-4">
              <span className="flex-shrink-0 w-8 h-8 bg-purple-100 dark:bg-purple-900 text-purple-600 dark:text-purple-400 rounded-full flex items-center justify-center font-bold">
                1
              </span>
              <div className="text-gray-600 dark:text-gray-300">
                <strong>Arraste o botão</strong> "Salvar no Igor" para sua barra de favoritos
              </div>
            </li>
            <li className="flex gap-4">
              <span className="flex-shrink-0 w-8 h-8 bg-purple-100 dark:bg-purple-900 text-purple-600 dark:text-purple-400 rounded-full flex items-center justify-center font-bold">
                2
              </span>
              <div className="text-gray-600 dark:text-gray-300">
                Se a barra não estiver visível, pressione{' '}
                <kbd className="px-2 py-1 bg-gray-200 dark:bg-gray-700 rounded text-sm">Ctrl+Shift+B</kbd> (Windows) ou{' '}
                <kbd className="px-2 py-1 bg-gray-200 dark:bg-gray-700 rounded text-sm">Cmd+Shift+B</kbd> (Mac)
              </div>
            </li>
            <li className="flex gap-4">
              <span className="flex-shrink-0 w-8 h-8 bg-purple-100 dark:bg-purple-900 text-purple-600 dark:text-purple-400 rounded-full flex items-center justify-center font-bold">
                3
              </span>
              <div className="text-gray-600 dark:text-gray-300">
                <strong>Pronto!</strong> Agora você pode salvar qualquer página com um clique
              </div>
            </li>
          </ol>
        </div>

        {/* Features Card */}
        <div className="bg-green-50 dark:bg-green-900/30 rounded-2xl shadow-xl p-8 mb-8">
          <h2 className="text-xl font-bold text-green-800 dark:text-green-400 mb-4 flex items-center gap-2">
            <span>✨</span> Funcionalidades
          </h2>
          <ul className="space-y-3">
            {[
              'Captura URL, título e descrição automaticamente',
              'Salva texto selecionado na página',
              'Opção de gerar resumo com IA (Gemini)',
              'Opção de criar tarefa de leitura',
              'Adiciona notas personalizadas',
              'Classifica automaticamente por categoria',
            ].map((feature, index) => (
              <li key={index} className="flex items-center gap-3 text-gray-700 dark:text-gray-300">
                <span className="text-green-500 font-bold">✓</span>
                {feature}
              </li>
            ))}
          </ul>
        </div>

        {/* Usage Card */}
        <div className="bg-orange-50 dark:bg-orange-900/30 rounded-2xl shadow-xl p-8">
          <h2 className="text-xl font-bold text-orange-800 dark:text-orange-400 mb-4 flex items-center gap-2">
            <span>🚀</span> Como Usar
          </h2>
          <ol className="space-y-3 text-gray-700 dark:text-gray-300">
            <li>1. Navegue até qualquer página interessante</li>
            <li>2. (Opcional) Selecione um trecho de texto importante</li>
            <li>3. Clique no bookmarklet "Salvar no Igor"</li>
            <li>4. Escolha a ação:
              <ul className="ml-6 mt-2 space-y-1 text-sm">
                <li>• <strong>1 = Salvar:</strong> Apenas salva na Inbox</li>
                <li>• <strong>2 = Resumir:</strong> Salva e gera resumo com IA</li>
                <li>• <strong>3 = Tarefa:</strong> Cria tarefa de leitura</li>
              </ul>
            </li>
            <li>5. Adicione notas se quiser</li>
            <li>6. Pronto! O link está na sua Inbox 📬</li>
          </ol>
        </div>

        {/* Footer */}
        <p className="text-center text-white/70 mt-8">
          TB Personal OS - Seu segundo cérebro 🧠
        </p>
      </div>
    </div>
  );
}
