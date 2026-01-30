/**
 * TB Personal OS - Privacy Policy Page
 */

export function PrivacyPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-3xl mx-auto bg-white rounded-lg shadow-md p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">
          Política de Privacidade
        </h1>
        
        <p className="text-gray-600 mb-4">
          <strong>Última atualização:</strong> 20 de Janeiro de 2026
        </p>

        <section className="mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-3">1. Introdução</h2>
          <p className="text-gray-600">
            O TB Personal OS (disponível em jhypmryyfafwwdkifgcg.supabase.co) é um assistente pessoal de produtividade 
            desenvolvido para uso individual. Esta política descreve como coletamos, usamos e protegemos suas informações.
          </p>
        </section>

        <section className="mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-3">2. Dados Coletados</h2>
          <ul className="list-disc list-inside text-gray-600 space-y-2">
            <li>Informações de autenticação do Google (Calendar, Gmail)</li>
            <li>Tarefas e notas criadas pelo usuário</li>
            <li>Check-ins de bem-estar (energia, humor, sono)</li>
            <li>Mensagens enviadas ao assistente via Telegram</li>
          </ul>
        </section>

        <section className="mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-3">3. Uso dos Dados</h2>
          <p className="text-gray-600">
            Os dados são utilizados exclusivamente para fornecer as funcionalidades do assistente pessoal, 
            incluindo sincronização de calendário, gerenciamento de tarefas e análise de produtividade.
          </p>
        </section>

        <section className="mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-3">4. Armazenamento</h2>
          <p className="text-gray-600">
            Todos os dados são armazenados de forma segura no Supabase com criptografia em repouso e em trânsito. 
            Os tokens de acesso do Google são criptografados antes do armazenamento.
          </p>
        </section>

        <section className="mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-3">5. Compartilhamento</h2>
          <p className="text-gray-600">
            Não compartilhamos seus dados com terceiros. Este é um aplicativo de uso pessoal.
          </p>
        </section>

        <section className="mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-3">6. Contato</h2>
          <p className="text-gray-600">
            Para questões sobre privacidade, entre em contato: adm.web4rank@gmail.com
          </p>
        </section>
      </div>
    </div>
  );
}

export default PrivacyPage;
