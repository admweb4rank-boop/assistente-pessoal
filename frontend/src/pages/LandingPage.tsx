import React from 'react';
import { Button, GlassCard, StatCard, Badge } from '../components/ui';
import { useNavigate } from 'react-router-dom';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-animated">
      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center px-4 overflow-hidden">
        {/* Floating Elements */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-20 left-10 w-64 h-64 bg-brand-purple-500/20 rounded-full blur-3xl animate-float" />
          <div className="absolute bottom-20 right-10 w-96 h-96 bg-brand-blue-500/20 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }} />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full bg-gradient-mesh opacity-30" />
        </div>

        <div className="relative z-10 max-w-6xl mx-auto text-center">
          {/* Badge */}
          <Badge variant="purple" className="mb-8 animate-slide-down">
            🚀 Seu assistente pessoal com IA
          </Badge>

          {/* Heading */}
          <h1 className="text-6xl md:text-7xl lg:text-8xl font-bold mb-6 animate-slide-up">
            <span className="text-gradient">Organize sua vida</span>
            <br />
            <span className="text-white">com inteligência</span>
          </h1>

          {/* Subheading */}
          <p className="text-xl md:text-2xl text-dark-text-secondary max-w-3xl mx-auto mb-12 animate-fade-in">
            Seu assistente pessoal completo com IA. Gerencie tarefas, acompanhe metas,
            organize conteúdo e muito mais - tudo em um só lugar.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16 animate-scale-in">
            <Button 
              size="lg" 
              onClick={() => navigate('/login')}
              className="group"
            >
              Começar Agora
              <svg className="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Button>
            <Button 
              variant="outline" 
              size="lg"
              onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}
            >
              Ver Recursos
            </Button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 max-w-4xl mx-auto animate-fade-in">
            <StatCard
              label="Usuários Ativos"
              value="1,234"
              trend={{ value: "+12%", positive: true }}
              icon="👥"
            />
            <StatCard
              label="Tarefas Completadas"
              value="15K+"
              trend={{ value: "+24%", positive: true }}
              icon="✅"
            />
            <StatCard
              label="Horas Economizadas"
              value="2.5K"
              trend={{ value: "+18%", positive: true }}
              icon="⏱️"
            />
          </div>
        </div>

        {/* Scroll Indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
          <svg className="w-6 h-6 text-dark-text-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-32 px-4">
        <div className="max-w-7xl mx-auto">
          {/* Section Header */}
          <div className="text-center mb-20">
            <Badge variant="green" className="mb-6">
              Recursos Poderosos
            </Badge>
            <h2 className="section-heading">
              Tudo que você precisa
              <br />
              <span className="text-white">em um só lugar</span>
            </h2>
            <p className="text-xl text-dark-text-secondary max-w-2xl mx-auto mt-6">
              Ferramentas inteligentes que se adaptam ao seu estilo de trabalho
            </p>
          </div>

          {/* Feature Cards */}
          <div className="card-grid">
            <FeatureCard
              icon="🤖"
              title="IA Personalizada"
              description="Assistente com inteligência artificial que aprende com você e se adapta às suas necessidades"
              gradient="from-brand-purple-500 to-brand-blue-500"
            />
            <FeatureCard
              icon="📝"
              title="Gestão de Tarefas"
              description="Organize, priorize e complete suas tarefas com produtividade máxima"
              gradient="from-brand-blue-500 to-accent-cyan"
            />
            <FeatureCard
              icon="🎯"
              title="Metas e OKRs"
              description="Defina objetivos ambiciosos e acompanhe seu progresso em tempo real"
              gradient="from-accent-green to-accent-cyan"
            />
            <FeatureCard
              icon="📊"
              title="Analytics"
              description="Insights poderosos sobre sua produtividade e padrões de trabalho"
              gradient="from-accent-pink to-accent-orange"
            />
            <FeatureCard
              icon="💬"
              title="Chat Inteligente"
              description="Converse naturalmente com seu assistente e obtenha respostas instantâneas"
              gradient="from-brand-purple-500 to-accent-pink"
            />
            <FeatureCard
              icon="🔗"
              title="Integrações"
              description="Conecte com suas ferramentas favoritas e centralize tudo"
              gradient="from-accent-cyan to-brand-blue-500"
            />
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-32 px-4">
        <div className="max-w-4xl mx-auto">
          <GlassCard className="p-12 text-center relative overflow-hidden">
            {/* Background Glow */}
            <div className="absolute inset-0 bg-gradient-purple opacity-10 blur-3xl" />
            
            <div className="relative z-10">
              <h2 className="text-4xl md:text-5xl font-bold mb-6">
                Pronto para começar?
              </h2>
              <p className="text-xl text-dark-text-secondary mb-8">
                Junte-se a milhares de usuários que já transformaram sua produtividade
              </p>
              <Button size="lg" onClick={() => navigate('/login')}>
                Criar Conta Grátis →
              </Button>
            </div>
          </GlassCard>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-dark-border py-12 px-4">
        <div className="max-w-7xl mx-auto text-center text-dark-text-tertiary">
          <p>&copy; 2026 TB Personal OS. Todos os direitos reservados.</p>
        </div>
      </footer>
    </div>
  );
};

// Feature Card Component
interface FeatureCardProps {
  icon: string;
  title: string;
  description: string;
  gradient: string;
}

const FeatureCard: React.FC<FeatureCardProps> = ({ icon, title, description, gradient }) => {
  return (
    <GlassCard hover className="p-8 group">
      <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${gradient} flex items-center justify-center text-3xl mb-6 group-hover:scale-110 transition-transform`}>
        {icon}
      </div>
      <h3 className="text-2xl font-bold mb-3 text-white">{title}</h3>
      <p className="text-dark-text-secondary leading-relaxed">{description}</p>
    </GlassCard>
  );
};
