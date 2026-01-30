#!/usr/bin/env python3
"""
Script para criar usuário Igor no Supabase
"""

from supabase import create_client
import os
from dotenv import load_dotenv

# Carregar .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

USER_ID = "11111111-1111-1111-1111-111111111111"

# Criar usuário
try:
    user_result = supabase.table("users").upsert({
        "id": USER_ID,
        "email": "igor@tbpersonal.os",
        "full_name": "Igor Bessa"
    }).execute()
    print(f"✅ User created: {user_result.data}")
except Exception as e:
    print(f"User may already exist: {e}")

# Criar profile
try:
    profile_result = supabase.table("profiles").upsert({
        "user_id": USER_ID,
        "timezone": "America/Sao_Paulo",
        "language": "pt-BR",
        "onboarding_completed": True
    }).execute()
    print(f"✅ Profile created: {profile_result.data}")
except Exception as e:
    print(f"Profile may already exist: {e}")

# Criar telegram chat
try:
    telegram_result = supabase.table("telegram_chats").upsert({
        "user_id": USER_ID,
        "chat_id": 8225491023,
        "username": "Igor",
        "first_name": "Igor",
        "last_name": "Bessa",
        "is_active": True
    }).execute()
    print(f"✅ Telegram chat created: {telegram_result.data}")
except Exception as e:
    print(f"Telegram chat may already exist: {e}")

print(f"\n🎉 Igor user setup complete! User ID: {USER_ID}")
