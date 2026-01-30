#!/usr/bin/env python3
"""
Script para obter o Chat ID do usuário no Telegram
Envie uma mensagem para o bot antes de executar este script
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not BOT_TOKEN:
    print("❌ Erro: TELEGRAM_BOT_TOKEN não encontrado no .env")
    sys.exit(1)

def get_chat_id():
    """Obtém o chat ID do último update"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if not data['ok']:
            print("❌ Erro na API do Telegram")
            return None
        
        updates = data.get('result', [])
        
        if not updates:
            print("⚠️  Nenhuma mensagem encontrada!")
            print("👉 Envie uma mensagem para @Nariscabot no Telegram e tente novamente")
            return None
        
        # Pegar o último update
        last_update = updates[-1]
        
        # Extrair chat_id
        if 'message' in last_update:
            chat_id = last_update['message']['chat']['id']
            user = last_update['message']['from']
            
            print("\n✅ Informações do Chat encontradas!")
            print(f"   Chat ID: {chat_id}")
            print(f"   Nome: {user.get('first_name', '')} {user.get('last_name', '')}")
            print(f"   Username: @{user.get('username', 'N/A')}")
            print(f"\n📝 Adicione no backend/.env:")
            print(f"   OWNER_TELEGRAM_CHAT_ID={chat_id}")
            
            return chat_id
        
        print("❌ Formato de update não reconhecido")
        return None
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

if __name__ == '__main__':
    print("🔍 Buscando seu Chat ID no Telegram...")
    print("   Bot: @Nariscabot")
    print("")
    
    chat_id = get_chat_id()
    
    if chat_id:
        print("\n🎯 Próximo passo: Execute ./scripts/setup.sh")
    else:
        print("\n⚠️  Não foi possível obter o Chat ID")
        print("   1. Envie uma mensagem para @Nariscabot")
        print("   2. Execute este script novamente")
