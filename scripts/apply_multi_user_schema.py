"""
Script para aplicar schema de multi-user via Supabase client
"""

import os
from supabase import create_client
from dotenv import load_dotenv

# Carregar .env
load_dotenv(os.path.join(os.path.dirname(__file__), "../backend/.env"))


def apply_multi_user_schema():
    """Aplica mudanças de schema para multi-user."""
    try:
        # Criar cliente Supabase
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not supabase_url or not supabase_key:
            print("❌ SUPABASE_URL e SUPABASE_SERVICE_KEY não encontrados no .env")
            return False
        
        supabase = create_client(supabase_url, supabase_key)
        
        print("🔧 Aplicando schema multi-user...")
        
        # 1. Adicionar coluna gemini_api_key em profiles (se não existir)
        print("📝 Adicionando campo gemini_api_key...")
        try:
            # Testar se coluna existe tentando selecionar
            supabase.table("profiles").select("gemini_api_key").limit(1).execute()
            print("  ✓ Campo gemini_api_key já existe")
        except:
            # Coluna não existe, usar SQL direto via RPC ou adicionar manualmente
            print("  ⚠️  Coluna gemini_api_key precisa ser adicionada manualmente no Supabase Dashboard")
            print("     SQL: ALTER TABLE profiles ADD COLUMN IF NOT EXISTS gemini_api_key TEXT;")
        
        # 2. Adicionar campos de onboarding
        print("📝 Adicionando campos de onboarding...")
        try:
            supabase.table("profiles").select("onboarding_completed").limit(1).execute()
            print("  ✓ Campos de onboarding já existem")
        except:
            print("  ⚠️  Campos de onboarding precisam ser adicionados manualmente no Supabase Dashboard")
            print("     SQL:")
            print("     ALTER TABLE profiles ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN DEFAULT FALSE;")
            print("     ALTER TABLE profiles ADD COLUMN IF NOT EXISTS onboarding_step INTEGER DEFAULT 0;")
            print("     ALTER TABLE profiles ADD COLUMN IF NOT EXISTS onboarded_at TIMESTAMP;")
            print("     ALTER TABLE profiles ADD COLUMN IF NOT EXISTS quiz_answers JSONB DEFAULT '{}'::jsonb;")
            print("     ALTER TABLE profiles ADD COLUMN IF NOT EXISTS personality_profile JSONB DEFAULT '{}'::jsonb;")
            print("     ALTER TABLE profiles ADD COLUMN IF NOT EXISTS autonomy_level TEXT DEFAULT 'confirm';")
        
        # 3. Criar dados de teste
        print("\n🧪 Criando perfil de teste...")
        test_user_id = "test_user_123"
        
        # Criar usuário de teste
        try:
            supabase.table("users").upsert({
                "id": test_user_id,
                "telegram_chat_id": "999999999",
                "telegram_username": "test_user",
                "full_name": "Test User",
                "is_active": True
            }).execute()
            print(f"  ✓ Usuário de teste criado: {test_user_id}")
        except Exception as e:
            print(f"  ⚠️  Erro ao criar usuário teste: {e}")
        
        # Criar profile de teste
        try:
            supabase.table("profiles").upsert({
                "user_id": test_user_id,
                "onboarding_completed": False,
                "onboarding_step": 0,
                "quiz_answers": {},
                "personality_profile": {},
                "autonomy_level": "confirm"
            }).execute()
            print(f"  ✓ Profile de teste criado")
        except Exception as e:
            print(f"  ⚠️  Erro ao criar profile teste: {e}")
        
        print("\n✅ Schema aplicado com sucesso!")
        print("\n📋 Próximos passos:")
        print("1. Se viu avisos acima, execute o SQL manualmente no Supabase Dashboard")
        print("2. Reinicie o bot: sudo systemctl restart assistente-bot")
        print("3. Teste com novo usuário no Telegram")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao aplicar schema: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    apply_multi_user_schema()
