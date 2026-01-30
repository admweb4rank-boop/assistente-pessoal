#!/bin/bash
# Script para reiniciar o bot com as melhorias

echo "🔄 Reiniciando Bot com Melhorias..."
echo ""

# Ir para diretório do backend
cd /var/www/assistente_igor/backend || {
    echo "❌ Erro: Diretório não encontrado"
    exit 1
}

# Parar bot se estiver rodando
echo "⏹️  Parando bot atual..."
pkill -f run_bot.py
sleep 2

# Verificar se parou
if pgrep -f run_bot.py > /dev/null; then
    echo "⚠️  Bot ainda rodando. Forçando parada..."
    pkill -9 -f run_bot.py
    sleep 2
fi

echo "✅ Bot parado"
echo ""

# Verificar se arquivo existe
if [ ! -f "run_bot.py" ]; then
    echo "❌ Erro: run_bot.py não encontrado"
    exit 1
fi

# Iniciar bot em background
echo "🚀 Iniciando bot melhorado..."
nohup python3 run_bot.py > logs/bot.log 2>&1 &
BOT_PID=$!

sleep 3

# Verificar se iniciou
if pgrep -f run_bot.py > /dev/null; then
    echo "✅ Bot iniciado com sucesso!"
    echo "📝 PID: $(pgrep -f run_bot.py)"
    echo ""
    echo "📊 Status:"
    ps aux | grep run_bot.py | grep -v grep
    echo ""
    echo "📄 Ver logs:"
    echo "   tail -f logs/bot.log"
    echo ""
    echo "🧪 Testar agora:"
    echo "   1. Abra Telegram"
    echo "   2. Envie: Oi"
    echo "   3. Verifique resposta natural"
    echo ""
    echo "✅ Bot rodando com melhorias!"
else
    echo "❌ Erro ao iniciar bot"
    echo ""
    echo "Ver logs de erro:"
    tail -20 logs/bot.log
    exit 1
fi
