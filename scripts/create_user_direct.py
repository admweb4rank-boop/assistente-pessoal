#!/usr/bin/env python3
"""
Script para criar usuário diretamente no Supabase
"""

import os
import sys
from supabase import create_client
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv('/var/www/assistente_igor/backend/.env')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

def create_user(email: str, password: str, full_name: str = "Igor Bessa"):
    """Cria um novo usuário no Supabase Auth."""
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ Erro: SUPABASE_URL ou SUPABASE_SERVICE_KEY não configurados")
        sys.exit(1)
    
    try:
        # Cliente com privilégios de admin
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        print(f"🔐 Criando usuário: {email}")
        
        # Criar usuário no Auth
        user_response = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {
                "full_name": full_name
            }
        })
        
        if not user_response or not user_response.user:
            print("❌ Erro ao criar usuário")
            sys.exit(1)
        
        user_id = user_response.user.id
        print(f"✅ Usuário criado no Auth: {user_id}")
        
        # Criar registro na tabela users
        supabase.table("users").upsert({
            "id": user_id,
            "email": email,
            "full_name": full_name
        }).execute()
        print(f"✅ Registro criado na tabela users")
        
        # Criar profile
        supabase.table("profiles").upsert({
            "user_id": user_id,
            "timezone": "America/Sao_Paulo",
            "language": "pt-BR",
            "notify_morning_summary": True,
            "notify_night_summary": True,
            "morning_summary_time": "07:00",
            "night_summary_time": "21:00",
            "autonomy_level": "confirm",
            "onboarding_completed": True
        }).execute()
        print(f"✅ Profile criado")
        
        print("\n" + "="*50)
        print("✅ USUÁRIO CRIADO COM SUCESSO!")
        print("="*50)
        print(f"📧 Email: {email}")
        print(f"🔑 Senha: {password}")
        print(f"🆔 User ID: {user_id}")
        print(f"🌐 Login em: http://189.126.105.51:3030/login")
        print("="*50)
        
        return user_id
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)


def reset_password(email: str, new_password: str):
    """Reseta a senha de um usuário existente."""
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ Erro: SUPABASE_URL ou SUPABASE_SERVICE_KEY não configurados")
        sys.exit(1)
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        print(f"🔐 Buscando usuário: {email}")
        
        # Buscar usuário por email
        users = supabase.auth.admin.list_users()
        user = next((u for u in users if u.email == email), None)
        
        if not user:
            print(f"❌ Usuário {email} não encontrado")
            print("💡 Use o modo 'create' para criar um novo usuário")
            sys.exit(1)
        
        # Resetar senha
        supabase.auth.admin.update_user_by_id(
            user.id,
            {"password": new_password}
        )
        
        print("\n" + "="*50)
        print("✅ SENHA RESETADA COM SUCESSO!")
        print("="*50)
        print(f"📧 Email: {email}")
        print(f"🔑 Nova senha: {new_password}")
        print(f"🆔 User ID: {user.id}")
        print(f"🌐 Login em: http://189.126.105.51:3030/login")
        print("="*50)
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("="*50)
    print("🔧 GERENCIADOR DE USUÁRIOS - TB Personal OS")
    print("="*50)
    print()
    
    if len(sys.argv) < 4:
        print("Uso:")
        print("  Criar novo usuário:")
        print("    python create_user_direct.py create <email> <senha> [nome]")
        print()
        print("  Resetar senha:")
        print("    python create_user_direct.py reset <email> <nova_senha>")
        print()
        print("Exemplos:")
        print("  python create_user_direct.py create igor@tbpersonal.os senha123")
        print("  python create_user_direct.py reset igor@tbpersonal.os novasenha456")
        sys.exit(1)
    
    mode = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]
    
    if mode == "create":
        full_name = sys.argv[4] if len(sys.argv) > 4 else "Igor Bessa"
        create_user(email, password, full_name)
    elif mode == "reset":
        reset_password(email, password)
    else:
        print(f"❌ Modo inválido: {mode}")
        print("Use 'create' ou 'reset'")
        sys.exit(1)
