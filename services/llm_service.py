import os
import re
import time
from utils.texto import resumir as _resumir
import streamlit as st
from groq import Groq

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)
else:
    client = None

SYSTEM_PROMPT = '''
Você é um amigo que entende muito de NBA e conversa em português do Brasil de forma natural, direta e com personalidade. Você consulta uma base verificada (bloco [DADOS VERIFICADOS]) e conversa de forma contínua: lembra do que já foi dito.

COMO CONVERSAR
- Responda primeiro o que a pessoa perguntou, logo na primeira frase. Só depois explique, se for útil.
- Fale como numa conversa, não como um relatório. Não use títulos como "Veredito", "Contra-argumento" ou "Conclusão" em toda resposta; use tabela ou tópicos só quando ajudarem (rankings, comparações). Em perguntas de acompanhamento, prefira respostas curtas.
- Entenda perguntas informais, gírias e abreviações. Se algo for ambíguo, escolha a leitura mais provável e responda, em vez de pedir esclarecimento.
- Perguntas como "e se fosse nos playoffs?", "resuma", "explique melhor" ou "estão em ordem?" se referem à sua resposta anterior: use a conversa e o contexto herdado.
- Em perguntas objetivas (ex.: "quem foi MVP em 2005?"), responda direto e acrescente de 2 a 4 detalhes relevantes que estiverem no contexto: time e campanha, estatísticas da temporada regular, desempenho nos playoffs e como o time terminou.
- Se a pessoa apontar uma inconsistência ou um erro, reconheça com naturalidade ("Você tem razão") e corrija de forma clara, sem se justificar em excesso.
- Opinião é bem-vinda em debates (GOAT, melhores da história). Nunca diga que "não há dados oficiais para estabelecer um ranking": assuma um critério, diga qual é e responda.

REGRAS SOBRE DADOS
- Para títulos, prêmios, times e anos, use apenas os [DADOS VERIFICADOS]. Cada jogador tem uma FICHA: só atribua a ele o que está na ficha. Um time campeão não torna campeão todo jogador citado perto dele. Se a ficha diz 0x, o jogador não tem esse feito no período.
- Rankings: se o contexto traz um RANKING CALCULADO, use exatamente essa ordem e esses números. Se discordar da ordem, mantenha a lista como está e dê a sua opinião à parte, dizendo que é opinião. Nunca mostre pontuações que contradigam a ordem apresentada.
- Posições: a base só informa Guard, Forward e Center. Quando o contexto trouxer uma lista já filtrada por posição (ex.: armadores), use somente jogadores dessa lista e não justifique a inclusão de jogadores de outras posições (Michael Jordan e Kobe, por exemplo, não são armadores).
- Playoffs: quando o contexto trouxer as estatísticas de playoffs do jogador e a campanha do time (séries, adversários e placares), use-as e compare com a temporada regular. Se não trouxer, diga que não tem esses números; não os invente nem os recorde de memória. Em rankings "nos playoffs", o critério é títulos e MVP das Finais: diga isso em uma frase.
- Se faltar um dado específico, diga que não tem esse dado, mas continue ajudando com o que existe. Não invente.

FORMATO
- Nunca escreva rótulos internos ("modo fato", "dados verificados") na resposta.
- Não use HTML (nada de <br> ou <b>). Em tabelas, separe itens da mesma célula com " · " ou ";".
- Detalhada: até cerca de 350 palavras. Curta: até 6 linhas.
'''


MODELO = "openai/gpt-oss-120b"
MODELO_RAPIDO = "llama-3.1-8b-instant"
_RE = {"ok": True}


def _montar(pergunta, contexto, modo, historico, detalhado, enxuto):
    """Monta a mensagem dentro do limite de tokens por minuto do plano gratuito da Groq."""
    estilo = "Resposta completa, mas natural e sem enrolação." if detalhado else "Resposta curta: no máximo 6 linhas."
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    if not enxuto:
        msgs += [{"role": m["role"], "content": _resumir(m["content"], 800)} for m in historico[-5:-1]]
    ctx = contexto[: 4000 if enxuto else 8000]
    msgs.append({"role": "user", "content": f"(tipo da pergunta: {modo}; não cite este rótulo) {estilo}\n\n[DADOS VERIFICADOS]\n{ctx}\n\n[PERGUNTA]\n{pergunta}"})
    return msgs, (1000 if enxuto else (1600 if detalhado else 600))


def _espera(txt):
    m = re.search(r"try again in (?:(\d+)m)?(\d+(?:\.\d+)?)s", txt)
    return (int(m.group(1) or 0) * 60 + float(m.group(2))) if m else None


def stream_resposta_chat(pergunta, contexto, modo, historico, detalhado=True):
    if not client:
        yield "Erro: chave da API da Groq não configurada."
        return
    enxuto, emitiu = False, False
    for _ in range(4):
        msgs, mt = _montar(pergunta, contexto, modo, historico, detalhado, enxuto)
        extra = {"reasoning_effort": "low"} if _RE["ok"] else {}
        try:
            for ch in client.chat.completions.create(messages=msgs, model=MODELO, temperature=0.4 if modo == "debate" else 0.1,
                                                     max_tokens=mt, stream=True, **extra):
                if ch.choices and ch.choices[0].delta.content:
                    emitiu = True
                    yield ch.choices[0].delta.content
            return
        except Exception as e:
            if emitiu:
                return
            txt, cod = str(e), getattr(e, "status_code", None)
            if "reasoning_effort" in txt and _RE["ok"]:
                _RE["ok"] = False                      # modelo sem esse parâmetro: tenta de novo sem ele
            elif cod == 413 or "too large" in txt.lower():
                enxuto = True                          # pedido grande demais: reduz contexto e histórico
            elif cod == 429 or "rate_limit" in txt:
                espera = _espera(txt)
                if espera is None or espera > 60:
                    yield "Atingi o limite de uso por minuto da Groq. Aguarde cerca de um minuto e pergunte de novo."
                    return
                time.sleep(espera + 1)
            else:
                yield f"Não consegui falar com o modelo agora ({type(e).__name__}). Tente de novo em instantes."
                return
    yield "Não consegui gerar a resposta agora. Aguarde alguns segundos e tente de novo."


def gerar_veredito_comparacao(dados_p1: dict, dados_p2: dict) -> str:
    if not client:
        return "Configure a chave da API para ver a análise."

    prompt = f'''
    Faça uma análise comparativa profunda e definitiva baseada EXCLUSIVAMENTE nos dados abaixo.

    Jogador 1 ({dados_p1['nome']}):
    - Anos de Conquistas: {dados_p1['premios']}
    - Médias da Carreira: {dados_p1['medias']}

    Jogador 2 ({dados_p2['nome']}):
    - Anos de Conquistas: {dados_p2['premios']}
    - Médias da Carreira: {dados_p2['medias']}

    Estrutura obrigatória:
    1. Produção Ofensiva e Volume
    2. Peso das Conquistas (Títulos e MVPs nos anos exatos)
    3. Veredito Final (Conclusão clara sobre quem vence o duelo histórico)
    '''

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Você é um analista estatístico inflexível e detalhista da NBA."},
                {"role": "user", "content": prompt}
            ],
            model="openai/gpt-oss-120b",
            temperature=0.2,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Erro ao gerar o veredito: {str(e)}"

REESCREVER = """Você reescreve a ÚLTIMA mensagem do usuário como uma pergunta completa e autônoma sobre a NBA, em português.
- Resolva referências ("ele", "e o outro?", "nessa época", "e em 2015?") usando a conversa anterior.
- Entenda gírias e abreviações (kd, bron, mj, "o rei") e escreva os nomes completos dos jogadores e times.
- Se o usuário se refere a algo da resposta anterior ("os 5 que você me deu", "essa lista", "eles"), escreva na pergunta os nomes que foram citados.
- Se a pergunta já estiver clara, devolva igual. Não responda e não explique: devolva apenas a pergunta reescrita."""


def reescrever_pergunta(pergunta, historico):
    if not client:
        return pergunta
    recente = [f"{m['role']}: {_resumir(m['content'], 700)}" for m in historico[-5:-1]]
    msgs = [{"role": "system", "content": REESCREVER},
            {"role": "user", "content": "Conversa anterior:\n" + ("\n".join(recente) or "(nenhuma)") + f"\n\nÚltima mensagem: {pergunta}"}]
    # modelo pequeno primeiro: tem limite próprio e não gasta o orçamento do modelo principal
    for modelo, extra in ((MODELO_RAPIDO, {}), (MODELO, {"reasoning_effort": "low"})):
        try:
            r = client.chat.completions.create(messages=msgs, model=modelo, temperature=0, max_tokens=300, **extra)
            t = (r.choices[0].message.content or "").strip()
            return t if 3 < len(t) < 400 else pergunta
        except Exception as e:
            if getattr(e, "status_code", None) not in (400, 404):
                break
    return pergunta
