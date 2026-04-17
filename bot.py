from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import random
import time
import os
from openai import OpenAI

# Pega variáveis do Railway
TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")

client = OpenAI(api_key=API_KEY)

# MEMÓRIA
historico = []
usuarios = {}
contador_msgs = {}
ultimo_tempo_msg = time.time()
alvo_do_momento = None

# FRASES FIXAS
frases = [
    "Isso aqui devia ser estudado",
    "Eu tô acompanhando essa decadência ao vivo",
    "Ninguém aqui pretende melhorar né",
    "5 minutos fora e já virou isso…",
    "Isso escalou rápido demais",
    "Eu devia ter ficado offline",
    "{nome} claramente comprometido com o caos",
    "{nome} não ajuda em absolutamente nada"
]

def analisar_usuario(nome, texto):
    if nome not in usuarios:
        usuarios[nome] = {
            "msgs": 0,
            "curtas": 0,
            "longas": 0,
            "risada": 0
        }

    usuarios[nome]["msgs"] += 1

    if len(texto) < 10:
        usuarios[nome]["curtas"] += 1
    elif len(texto) > 50:
        usuarios[nome]["longas"] += 1

    if "kkk" in texto or "haha" in texto:
        usuarios[nome]["risada"] += 1

def detectar_treta():
    if len(historico) < 4:
        return False

    ultimas = historico[-4:]
    nomes = [msg.split(":")[0] for msg in ultimas]

    return len(set(nomes)) <= 2

def escolher_alvo():
    if contador_msgs:
        return max(contador_msgs, key=contador_msgs.get)
    return None

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global historico, contador_msgs, ultimo_tempo_msg, alvo_do_momento

    if not update.message or not update.message.text:
        return

    texto = update.message.text
    nome = update.message.from_user.first_name

    agora = time.time()

    # ANALISA USUÁRIO
    analisar_usuario(nome, texto)

    # CONTADOR
    contador_msgs[nome] = contador_msgs.get(nome, 0) + 1

    # HISTÓRICO
    historico.append(f"{nome}: {texto}")
    if len(historico) > 8:
        historico.pop(0)

    # TRETA
    treta = detectar_treta()

    # ALVO DINÂMICO
    if random.random() < 0.2:
        alvo_do_momento = escolher_alvo()

    # SILÊNCIO
    if agora - ultimo_tempo_msg > 120:
        await update.message.reply_text("Silêncio estranho… tava melhor assim")

    ultimo_tempo_msg = agora

    # TIMING
    chance = 0.2
    if treta:
        chance = 0.5

    if random.random() > chance:
        return

    contexto = "\n".join(historico)

    # FRASE RÁPIDA
    if random.random() < 0.3:
        frase = random.choice(frases).replace("{nome}", nome)

        if nome == alvo_do_momento:
            frase += " (protagonista do caos)"

        await update.message.reply_text(frase)
        return

    # RANKING
    if random.random() < 0.1:
        top = escolher_alvo()
        if top:
            await update.message.reply_text(f"Ranking: {top} liderando em caos hoje")
            return

    perfil = usuarios.get(nome, {})

    prompt = f"""
Você é o "Fiscal do Caos".

PERSONALIDADE:
- Sarcástico, ácido, observador
- Age como quem assiste um reality ruim
- Não ajuda, só comenta

REGRAS:
- Respostas curtas
- Zoar situação ou comportamento
- Pode provocar levemente {nome}
- Nunca seja genérico

PERFIL:
Mensagens: {perfil.get("msgs",0)}
Curtas: {perfil.get("curtas",0)}
Longas: {perfil.get("longas",0)}
Risadas: {perfil.get("risada",0)}

CONTEXTO:
{contexto}

MENSAGEM:
{nome}: {texto}
"""

    try:
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=1
        )

        reply = resposta.choices[0].message.content

        if nome == alvo_do_momento:
            reply += " 👁️"

        await update.message.reply_text(reply)

    except Exception as e:
        print("Erro:", e)

# START
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), responder))

print("Fiscal do Caos ATIVO 👁️")
app.run_polling()
