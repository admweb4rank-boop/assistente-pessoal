"""
Teste de Qualidade do Bot - Conversação Natural
Simula conversas reais para avaliar qualidade do assistente
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict
import sys
sys.path.insert(0, '/var/www/assistente_igor/backend')

from app.services.conversation_service import ConversationService
from app.services.gemini_service import gemini_service

# Cores para output
class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'


class ConversationQualityTester:
    """Testa qualidade das conversas com o bot."""
    
    def __init__(self):
        self.conversation_service = ConversationService()
        self.test_results = []
        
    def print_header(self, title: str):
        """Imprime cabeçalho formatado."""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{title:^70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")
    
    def print_message(self, role: str, content: str, metadata: Dict = None):
        """Imprime mensagem formatada."""
        if role == "user":
            print(f"{Colors.BOLD}{Colors.GREEN}👤 Igor:{Colors.END} {content}")
        else:
            print(f"{Colors.BOLD}{Colors.BLUE}🤖 Bot:{Colors.END} {content}")
            
        if metadata:
            print(f"{Colors.YELLOW}   📊 Análise: {json.dumps(metadata, indent=2, ensure_ascii=False)}{Colors.END}")
        print()
    
    def evaluate_response(
        self, 
        user_message: str, 
        bot_response: str, 
        context: Dict,
        scenario: str
    ) -> Dict:
        """
        Avalia a qualidade da resposta do bot.
        
        Critérios:
        1. Naturalidade (0-10): Resposta soa natural e humana?
        2. Contexto (0-10): Bot entendeu e usou o contexto?
        3. Ação (0-10): Bot propôs ação apropriada?
        4. Progressão (0-10): Conversa avançou naturalmente?
        5. Empatia (0-10): Bot demonstrou compreensão emocional?
        """
        
        # Análise automática simples
        scores = {
            "naturalidade": 0,
            "contexto": 0,
            "acao": 0,
            "progressao": 0,
            "empatia": 0
        }
        
        response_lower = bot_response.lower()
        
        # Naturalidade: resposta não muito formal ou robotizada
        if not any(word in response_lower for word in ["processado", "registro", "item #", "id:"]):
            scores["naturalidade"] += 5
        if any(emoji in bot_response for emoji in ["✅", "📌", "🏷", "⚡️", "💡", "🎯"]):
            scores["naturalidade"] -= 2  # Excesso de emojis = menos natural
        if len(bot_response) > 50 and len(bot_response) < 300:
            scores["naturalidade"] += 3
        else:
            scores["naturalidade"] += 1
            
        # Contexto: menção a informações anteriores
        if context.get("previous_topic") and any(word in response_lower for word in context.get("keywords", [])):
            scores["contexto"] += 5
        
        # Ação: proposta de próximos passos
        if any(word in response_lower for word in ["vamos", "quer", "posso", "vou", "fazer", "criar", "começar"]):
            scores["acao"] += 5
        if "?" in bot_response:  # Faz perguntas para progredir
            scores["progressao"] += 4
        
        # Progressão: avança a conversa
        if any(word in response_lower for word in ["primeiro", "depois", "próximo", "agora", "etapa"]):
            scores["progressao"] += 3
            
        # Empatia: responde ao tom emocional
        if any(word in user_message.lower() for word in ["ajuda", "preciso", "quero", "difícil"]):
            if any(word in response_lower for word in ["claro", "certeza", "vou te ajudar", "beleza", "ótimo"]):
                scores["empatia"] += 5
        
        # Normalizar scores
        for key in scores:
            scores[key] = min(10, max(0, scores[key]))
        
        # Score total
        total = sum(scores.values())
        avg = total / len(scores)
        
        evaluation = {
            "scenario": scenario,
            "user_message": user_message,
            "bot_response": bot_response,
            "scores": scores,
            "total_score": total,
            "avg_score": round(avg, 2),
            "grade": self._get_grade(avg),
            "issues": self._identify_issues(bot_response, scores)
        }
        
        return evaluation
    
    def _get_grade(self, avg_score: float) -> str:
        """Converte score em nota."""
        if avg_score >= 9:
            return "A+ (Excelente)"
        elif avg_score >= 8:
            return "A (Muito Bom)"
        elif avg_score >= 7:
            return "B (Bom)"
        elif avg_score >= 6:
            return "C (Regular)"
        elif avg_score >= 5:
            return "D (Fraco)"
        else:
            return "F (Insuficiente)"
    
    def _identify_issues(self, response: str, scores: Dict) -> List[str]:
        """Identifica problemas específicos na resposta."""
        issues = []
        
        if scores["naturalidade"] < 5:
            issues.append("❌ Resposta muito robotizada ou formal")
        
        if scores["contexto"] < 5:
            issues.append("❌ Não usou contexto anterior")
        
        if scores["acao"] < 5:
            issues.append("❌ Não propôs ação ou próximos passos")
        
        if scores["progressao"] < 5:
            issues.append("❌ Não fez perguntas para avançar a conversa")
        
        if scores["empatia"] < 5:
            issues.append("❌ Faltou empatia ou compreensão emocional")
        
        # Problemas específicos
        if "Item #" in response or "ID:" in response:
            issues.append("🔧 Mostra IDs técnicos para usuário")
        
        if response.count("✅") > 2 or response.count("•") > 5:
            issues.append("🔧 Excesso de formatação/emojis")
        
        if "processado" in response.lower() or "registrado" in response.lower():
            issues.append("🔧 Linguagem muito técnica/sistemática")
        
        return issues
    
    async def simulate_conversation(
        self, 
        scenario: str, 
        messages: List[Dict[str, str]], 
        user_id: str = "test-user-123"
    ):
        """
        Simula uma conversa completa.
        
        Args:
            scenario: Nome do cenário
            messages: Lista de {"user": "...", "context": {...}}
            user_id: ID do usuário de teste
        """
        self.print_header(f"CENÁRIO: {scenario}")
        
        conversation_results = []
        
        for i, msg_data in enumerate(messages, 1):
            user_msg = msg_data["user"]
            context = msg_data.get("context", {})
            
            print(f"{Colors.BOLD}Turno {i}/{len(messages)}{Colors.END}")
            self.print_message("user", user_msg)
            
            try:
                # Processar mensagem
                result = await self.conversation_service.process_message(
                    user_id=user_id,
                    message=user_msg,
                    source="test"
                )
                
                bot_response = result.get("response", "")
                
                self.print_message("bot", bot_response, {
                    "intent": result.get("intent"),
                    "actions": result.get("actions", [])
                })
                
                # Avaliar resposta
                evaluation = self.evaluate_response(
                    user_msg, 
                    bot_response, 
                    context,
                    scenario
                )
                conversation_results.append(evaluation)
                
                # Delay para simular conversa real
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"{Colors.RED}❌ Erro ao processar: {str(e)}{Colors.END}\n")
                conversation_results.append({
                    "scenario": scenario,
                    "error": str(e),
                    "avg_score": 0,
                    "grade": "F (Erro)"
                })
        
        # Resumo do cenário
        self._print_scenario_summary(scenario, conversation_results)
        self.test_results.extend(conversation_results)
        
        return conversation_results
    
    def _print_scenario_summary(self, scenario: str, results: List[Dict]):
        """Imprime resumo de um cenário."""
        print(f"\n{Colors.BOLD}{Colors.PURPLE}📊 RESUMO - {scenario}{Colors.END}")
        
        avg_scores = [r["avg_score"] for r in results if "avg_score" in r]
        if avg_scores:
            overall_avg = sum(avg_scores) / len(avg_scores)
            print(f"   Média Geral: {overall_avg:.2f}/10 - {self._get_grade(overall_avg)}")
        
        # Problemas encontrados
        all_issues = []
        for r in results:
            all_issues.extend(r.get("issues", []))
        
        if all_issues:
            print(f"\n   {Colors.YELLOW}Problemas Identificados:{Colors.END}")
            unique_issues = list(set(all_issues))
            for issue in unique_issues[:5]:  # Top 5
                print(f"   {issue}")
        
        print()
    
    def print_final_report(self):
        """Imprime relatório final de todos os testes."""
        self.print_header("RELATÓRIO FINAL - QUALIDADE DO BOT")
        
        if not self.test_results:
            print(f"{Colors.RED}Nenhum teste executado.{Colors.END}")
            return
        
        # Estatísticas gerais
        all_scores = [r["avg_score"] for r in self.test_results if "avg_score" in r and r["avg_score"] > 0]
        
        if all_scores:
            overall_avg = sum(all_scores) / len(all_scores)
            
            print(f"{Colors.BOLD}📈 Estatísticas Gerais:{Colors.END}")
            print(f"   Total de turnos testados: {len(all_scores)}")
            print(f"   Média geral: {overall_avg:.2f}/10")
            print(f"   Nota: {self._get_grade(overall_avg)}")
            print(f"   Melhor: {max(all_scores):.2f}/10")
            print(f"   Pior: {min(all_scores):.2f}/10")
            
            # Distribuição de scores por categoria
            print(f"\n{Colors.BOLD}📊 Scores por Categoria:{Colors.END}")
            categories = ["naturalidade", "contexto", "acao", "progressao", "empatia"]
            for cat in categories:
                cat_scores = [r["scores"][cat] for r in self.test_results if "scores" in r]
                if cat_scores:
                    avg_cat = sum(cat_scores) / len(cat_scores)
                    print(f"   {cat.capitalize()}: {avg_cat:.2f}/10")
            
            # Problemas mais frequentes
            print(f"\n{Colors.BOLD}⚠️  Problemas Mais Frequentes:{Colors.END}")
            all_issues = []
            for r in self.test_results:
                all_issues.extend(r.get("issues", []))
            
            from collections import Counter
            issue_counts = Counter(all_issues)
            for issue, count in issue_counts.most_common(5):
                print(f"   [{count}x] {issue}")
            
            # Recomendações
            print(f"\n{Colors.BOLD}💡 Recomendações:{Colors.END}")
            if overall_avg < 7:
                print(f"   1. Bot precisa de melhorias significativas")
                print(f"   2. Foco em conversação mais natural e menos robotizada")
                print(f"   3. Melhorar uso de contexto e memória")
            elif overall_avg < 8:
                print(f"   1. Bot está razoável mas pode melhorar")
                print(f"   2. Trabalhar progressão e fluidez da conversa")
            else:
                print(f"   1. Bot está em bom nível!")
                print(f"   2. Ajustes finos para excelência")


async def main():
    """Executa testes de qualidade."""
    tester = ConversationQualityTester()
    
    # CENÁRIO 1: Pedido de ajuda com dieta (baseado na imagem)
    await tester.simulate_conversation(
        scenario="Planejamento de Dieta",
        messages=[
            {
                "user": "Quero ajuda para criar uma dieta para o mês de fevereiro... A ideia é secar barriga, tirar gordura ruim do corpo, e construir massa magra, músculo e definição, além de aumento na disposição e energia.",
                "context": {
                    "previous_topic": None,
                    "keywords": ["dieta", "fevereiro", "secar", "massa magra"]
                }
            },
            {
                "user": "Beleza, vamos conversar, faça perguntas específicas e eu responderei",
                "context": {
                    "previous_topic": "dieta",
                    "keywords": ["perguntas", "conversar"]
                }
            },
            {
                "user": "Sim, tenho algumas preferências. Gosto de frango, ovos, batata doce, mas não curto muito peixe.",
                "context": {
                    "previous_topic": "dieta",
                    "keywords": ["frango", "ovos", "batata doce", "peixe"]
                }
            }
        ]
    )
    
    # CENÁRIO 2: Salvar item na inbox (baseado na imagem)
    await tester.simulate_conversation(
        scenario="Salvar na Inbox",
        messages=[
            {
                "user": "Oi",
                "context": {}
            },
            {
                "user": "Beleza",
                "context": {}
            },
            {
                "user": "E vc ?",
                "context": {}
            }
        ]
    )
    
    # CENÁRIO 3: Conversa sobre projeto (progressiva)
    await tester.simulate_conversation(
        scenario="Discussão de Projeto",
        messages=[
            {
                "user": "Preciso organizar o projeto do app de finanças",
                "context": {}
            },
            {
                "user": "É um app para controle pessoal, com categorias e gráficos",
                "context": {
                    "previous_topic": "projeto app",
                    "keywords": ["app", "finanças"]
                }
            },
            {
                "user": "Sim, vou precisar de backend, frontend e banco de dados",
                "context": {
                    "previous_topic": "projeto app",
                    "keywords": ["backend", "frontend", "banco"]
                }
            }
        ]
    )
    
    # CENÁRIO 4: Conversa casual que vira tarefa
    await tester.simulate_conversation(
        scenario="Conversa Natural → Tarefa",
        messages=[
            {
                "user": "Nossa, lembrei que tenho que ligar pro dentista amanhã",
                "context": {}
            },
            {
                "user": "É pra marcar uma limpeza, já tá atrasado",
                "context": {
                    "previous_topic": "dentista",
                    "keywords": ["ligar", "dentista", "amanhã"]
                }
            }
        ]
    )
    
    # CENÁRIO 5: Pergunta sobre dados pessoais
    await tester.simulate_conversation(
        scenario="Consulta de Informações",
        messages=[
            {
                "user": "Quais são minhas tarefas pra hoje?",
                "context": {}
            },
            {
                "user": "E as de alta prioridade?",
                "context": {
                    "previous_topic": "tarefas",
                    "keywords": ["tarefas", "hoje"]
                }
            }
        ]
    )
    
    # Relatório final
    tester.print_final_report()
    
    # Salvar resultados em JSON
    with open("/var/www/assistente_igor/test_results_bot_quality.json", "w", encoding="utf-8") as f:
        json.dump(tester.test_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{Colors.GREEN}✅ Resultados salvos em: test_results_bot_quality.json{Colors.END}\n")


if __name__ == "__main__":
    asyncio.run(main())
