/**
 * TB Personal OS - Terms of Service Page
 */

export function TermsPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-3xl mx-auto bg-white rounded-lg shadow-md p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">
          Termos de Serviço
        </h1>
        
        <p className="text-gray-600 mb-4">
          <strong>Última atualização:</strong> 20 de Janeiro de 2026
        </p>

        <section className="mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-3">1. Aceitação dos Termos</h2>
          <p className="text-gray-600">
            Ao utilizar o TB Personal OS (disponível em jhypmryyfafwwdkifgcg.supabase.co), você concorda com estes termos de serviço. 
            Este é um aplicativo de uso pessoal para gerenciamento de produtividade.
          </p>
        </section>

        <section className="mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-3">2. Descrição do Serviço</h2>
          <p className="text-gray-600">
            O TB Personal OS é um assistente pessoal que integra:
          </p>
          <ul className="list-disc list-inside text-gray-600 space-y-2 mt-2">
            <li>Gerenciamento de tarefas e projetos</li>
            <li>Sincronização com Google Calendar</li>
            <li>Check-ins de bem-estar</li>
            <li>Bot de Telegram para interação</li>
            <li>Análise de produtividade com IA</li>
          </ul>
        </section>

        <section className="mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-3">3. Uso Aceitável</h2>
          <p className="text-gray-600">
            O serviço deve ser utilizado apenas para fins pessoais de organização e produtividade.
          </p>
        </section>

        <section className="mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-3">4. Integrações de Terceiros</h2>
          <p className="text-gray-600">
            O aplicativo integra com serviços do Google (Calendar, Gmail) e Telegram. 
            O uso dessas integrações está sujeito aos termos de serviço de cada plataforma.
          </p>
        </section>

        <section className="mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-3">5. Limitação de Responsabilidade</h2>
          <p className="text-gray-600">
            O serviço é fornecido "como está". Não nos responsabilizamos por perdas de dados 
            ou interrupções de serviço.
          </p>
        </section>

        <section className="mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-3">6. Contato</h2>
          <p className="text-gray-600">
            Para questões sobre estes termos, entre em contato: adm.web4rank@gmail.com
          </p>
        </section>
      </div>
    </div>
  );
}

export default TermsPage;
