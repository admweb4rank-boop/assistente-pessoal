"""
Script para resetar usuário e iniciar novo onboarding
"""

import sys
sys.path.insert(0, '/var/www/assistente_igor/backend')

from app.core.config import settings
from supabase import create_client
from datetime import datetime

def reset_user(telegram_user_id: int):
    """Reseta todos os dados do usuário mantendo apenas o registro básico."""
    
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    
    # Buscar user_id
    chat = supabase.table('telegram_chats').select('user_id').eq('chat_id', telegram_user_id).execute()
    
    if not chat.data:
        print(f"❌ Usuário telegram {telegram_user_id} não encontrado")
        return False
    
    user_id = chat.data[0]['user_id']
    
    print(f"🔄 Resetando usuário {user_id}...")
    
    # Tabelas para limpar
    tables_to_clear = [
        'tasks',
        'inbox_items',
        'health_checkins',
        'projects',
        'finance_transactions',
        'memories',
        'achievements',
        'learning_items',
        'routines',
        'goals'
    ]
    
    deleted_counts = {}
    
    for table in tables_to_clear:
        try:
            result = supabase.table(table).delete().eq('user_id', user_id).execute()
            count = len(result.data) if result.data else 0
            deleted_counts[table] = count
            if count > 0:
                print(f"  ✓ {table}: {count} registros deletados")
        except Exception as e:
            print(f"  ⚠️ {table}: {str(e)}")
    
    # Resetar user_profile (mantém o registro mas limpa dados)
    try:
        supabase.table('user_profiles').upsert({
            'user_id': user_id,
            'level': 1,
            'xp': 0,
            'attributes': {
                'energy': 50,
                'focus': 50,
                'productivity': 50,
                'knowledge': 50,
                'social': 50,
                'health': 50
            },
            'onboarding_completed': False,
            'onboarding_answers': {},
            'onboarding_step': 0,
            'personality_type': None,
            'work_style': None,
            'updated_at': datetime.utcnow().isoformat()
        }).execute()
        print(f"  ✓ user_profiles: resetado")
    except Exception as e:
        print(f"  ⚠️ user_profiles: {str(e)}")
    
    # Resetar telegram_chats (atualizar last_interaction)
    try:
        supabase.table('telegram_chats').update({
            'last_interaction_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }).eq('chat_id', telegram_user_id).execute()
        print(f"  ✓ telegram_chats: atualizado")
    except Exception as e:
        print(f"  ⚠️ telegram_chats: {str(e)}")
    
    print(f"\n✅ Reset completo!")
    print(f"📊 Total deletado: {sum(deleted_counts.values())} registros")
    print(f"\n🎮 Use /start no Telegram para começar o onboarding!")
    
    return True


if __name__ == "__main__":
    # ID do Igor no Telegram
    IGOR_TELEGRAM_ID = 8225491023
    
    print("=" * 50)
    print("🔄 TB PERSONAL OS - RESET DE USUÁRIO")
    print("=" * 50)
    print()
    
    confirm = input(f"Confirma reset do usuário {IGOR_TELEGRAM_ID}? (sim/não): ")
    
    if confirm.lower() in ['sim', 's', 'yes', 'y']:
        reset_user(IGOR_TELEGRAM_ID)
    else:
        print("❌ Cancelado")
