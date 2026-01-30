#!/usr/bin/env python3
"""
Script para resetar completamente um usuário do sistema
Uso: python3 reset_user.py [user_id ou telegram_id]
"""

import os
import sys
from supabase import create_client, Client

# Configuração do Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def find_user(identifier: str):
    """Encontra usuário por user_id ou telegram_id"""
    print(f"🔍 Procurando usuário: {identifier}")
    
    # Tentar por nome primeiro
    try:
        result = supabase.table('profiles').select('*').ilike('name', f'%{identifier}%').execute()
        if result.data:
            return result.data[0]
    except Exception as e:
        print(f"   ⚠️ Erro buscando por nome: {e}")
    
    # Tentar por telegram_id
    try:
        result = supabase.table('profiles').select('*').eq('telegram_id', identifier).execute()
        if result.data:
            return result.data[0]
    except Exception as e:
        print(f"   ⚠️ Erro buscando por telegram_id: {e}")
    
    # Tentar por user_id (UUID)
    try:
        result = supabase.table('profiles').select('*').eq('user_id', identifier).execute()
        if result.data:
            return result.data[0]
    except Exception as e:
        print(f"   ⚠️ Erro buscando por user_id: {e}")
    
    return None

def reset_user(user_id: str, confirm: bool = False):
    """Reseta completamente um usuário"""
    
    # Buscar perfil
    profile = supabase.table('profiles').select('*').eq('user_id', user_id).execute()
    
    if not profile.data:
        print(f"❌ Usuário {user_id} não encontrado!")
        return False
    
    user = profile.data[0]
    print(f"\n📋 USUÁRIO ENCONTRADO:")
    print(f"   Nome: {user.get('name', 'N/A')}")
    print(f"   User ID: {user_id}")
    print(f"   Telegram ID: {user.get('telegram_id', 'N/A')}")
    print(f"   Nível: {user.get('level', 0)}")
    print(f"   XP: {user.get('xp', 0)}")
    
    if not confirm:
        print("\n⚠️  ATENÇÃO: Esta ação vai DELETAR:")
        print("   • Histórico de conversas (assistant_logs)")
        print("   • Padrões ML (context_patterns)")
        print("   • Tarefas (tasks)")
        print("   • Check-ins (checkins)")
        print("   • Metas (goals)")
        print("   • Conquistas (achievements)")
        print("   • Memórias (memories)")
        print("   • Respostas do quiz (quiz_answers)")
        print("   • XP e nível (reset para 0)")
        print("\n🔄 Para confirmar, execute:")
        print(f"   python3 reset_user.py {user_id} --confirm")
        return False
    
    print("\n🗑️  INICIANDO LIMPEZA...")
    
    try:
        # 1. Deletar assistant_logs
        try:
            result = supabase.table('assistant_logs').delete().eq('user_id', user_id).execute()
            print(f"   ✅ assistant_logs: {len(result.data) if result.data else 0} removidos")
        except Exception as e:
            print(f"   ⚠️  assistant_logs: {str(e)[:80]}")
        
        # 2. Deletar context_patterns
        try:
            result = supabase.table('context_patterns').delete().eq('user_id', user_id).execute()
            print(f"   ✅ context_patterns: {len(result.data) if result.data else 0} removidos")
        except Exception as e:
            print(f"   ⚠️  context_patterns: tabela não existe ou sem dados")
        
        # 3. Deletar tasks
        try:
            result = supabase.table('tasks').delete().eq('user_id', user_id).execute()
            print(f"   ✅ tasks: {len(result.data) if result.data else 0} removidas")
        except Exception as e:
            print(f"   ⚠️  tasks: {str(e)[:80]}")
        
        # 4. Deletar checkins
        try:
            result = supabase.table('checkins').delete().eq('user_id', user_id).execute()
            print(f"   ✅ checkins: {len(result.data) if result.data else 0} removidos")
        except Exception as e:
            print(f"   ⚠️  checkins: {str(e)[:80]}")
        
        # 5. Deletar goals
        try:
            result = supabase.table('goals').delete().eq('user_id', user_id).execute()
            print(f"   ✅ goals: {len(result.data) if result.data else 0} removidas")
        except Exception as e:
            print(f"   ⚠️  goals: {str(e)[:80]}")
        
        # 6. Deletar achievements
        try:
            result = supabase.table('achievements').delete().eq('user_id', user_id).execute()
            print(f"   ✅ achievements: {len(result.data) if result.data else 0} removidas")
        except Exception as e:
            print(f"   ⚠️  achievements: tabela não existe ou sem dados")
        
        # 7. Deletar memories
        try:
            result = supabase.table('memories').delete().eq('user_id', user_id).execute()
            print(f"   ✅ memories: {len(result.data) if result.data else 0} removidas")
        except Exception as e:
            print(f"   ⚠️  memories: tabela não existe ou sem dados")
        
        # 8. Deletar quests
        try:
            result = supabase.table('quests').delete().eq('user_id', user_id).execute()
            print(f"   ✅ quests: {len(result.data) if result.data else 0} removidas")
        except Exception as e:
            print(f"   ⚠️  quests: tabela não existe ou sem dados")
        
        # 9. Deletar daily_quests
        try:
            result = supabase.table('daily_quests').delete().eq('user_id', user_id).execute()
            print(f"   ✅ daily_quests: {len(result.data) if result.data else 0} removidas")
        except Exception as e:
            print(f"   ⚠️  daily_quests: tabela não existe ou sem dados")
        
        # 10. Resetar profile
        try:
            result = supabase.table('profiles').update({
                'quiz_answers': None,
                'personality_profile': None,
                'onboarding_completed': False,
                'level': 1,
                'xp': 0,
                'updated_at': 'now()'
            }).eq('user_id', user_id).execute()
            print(f"   ✅ profile: resetado (nível 1, XP 0)")
        except Exception as e:
            print(f"   ⚠️  profile: {str(e)[:80]}")
        
        print("\n✨ USUÁRIO RESETADO COM SUCESSO!")
        print("\n🔄 Próximos passos:")
        print("   1. Usuário pode enviar /start no Telegram")
        print("   2. Quiz de onboarding será iniciado")
        print("   3. Tudo começa do zero!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO durante reset: {str(e)}")
        return False

def main():
    if len(sys.argv) < 2:
        print("❌ Uso: python3 reset_user.py [user_id ou telegram_id ou nome]")
        print("\nExemplos:")
        print("   python3 reset_user.py 8225491023")
        print("   python3 reset_user.py 'Igor Bessa'")
        print("   python3 reset_user.py UUID-do-usuario")
        sys.exit(1)
    
    identifier = sys.argv[1]
    confirm = '--confirm' in sys.argv or '-y' in sys.argv
    
    # Encontrar usuário
    user = find_user(identifier)
    
    if not user:
        print(f"❌ Usuário '{identifier}' não encontrado!")
        print("\n💡 Dica: Tente buscar por:")
        print("   • Telegram ID (ex: 8225491023)")
        print("   • Nome (ex: 'Igor Bessa')")
        print("   • User ID (UUID)")
        sys.exit(1)
    
    user_id = user['user_id']
    
    # Resetar
    reset_user(user_id, confirm)

if __name__ == "__main__":
    main()
