import streamlit as st

CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif}
.stApp{background:radial-gradient(1200px 500px at 10% -10%,#1b2a4a55,transparent),#0E1117}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#121722,#0E1117);border-right:1px solid #232b38}
.card{background:linear-gradient(145deg,#1E2430,#171c26);border:1px solid #2b3442;border-radius:16px;padding:16px 18px;
 transition:transform .2s,border-color .2s,box-shadow .2s;animation:fade .5s ease}
.card:hover{transform:translateY(-4px);border-color:#E56020;box-shadow:0 8px 24px #E5602033}
.card .t{font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:#8b96a8}
.card .v{font-size:1.25rem;font-weight:800;margin-top:4px;color:#f4f6fa}
.card .s{font-size:.8rem;color:#E56020;margin-top:2px}
.podio{text-align:center;padding:18px 10px}.podio .m{font-size:2.2rem}
.ouro{border-color:#F5C542}.prata{border-color:#C0C7D1}.bronze{border-color:#CD7F32}
.stTabs [data-baseweb="tab"]{border-radius:10px 10px 0 0;padding:8px 18px}
.stTabs [aria-selected="true"]{background:#E5602022;color:#E56020}
[data-testid="stChatMessage"]{animation:fade .4s ease}
[data-testid="stChatInput"]{border-radius:16px;border:1px solid #2b3442}
.stButton>button{transition:all .2s;border-radius:12px}
.stButton>button:hover{transform:translateY(-2px);box-shadow:0 6px 16px #E5602033}

.chip{display:inline-block;margin:3px 6px 3px 0;padding:4px 12px;border-radius:20px;background:#1E2430;border:1px solid #2b3442;font-size:.85rem;transition:all .2s}
.chip:hover{border-color:#E56020;color:#E56020}
.card img{height:44px;float:right;margin-left:8px}
h1{background:none!important;-webkit-text-fill-color:initial!important}
.hero{display:flex;align-items:center;gap:18px;padding:18px 24px;margin-bottom:16px;border-radius:18px;
 background:linear-gradient(120deg,#1b2a4a,#171c26 65%);border:1px solid #2b3442;animation:fade .5s ease}
.hero-i{font-size:2.5rem;line-height:1}
.hero-t{font-size:1.9rem;font-weight:800;line-height:1.15;background:linear-gradient(90deg,#fff,#F2A65A);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hero-s{color:#8b96a8;font-size:.92rem;margin-top:2px}
[data-testid="stSidebar"] [role="radiogroup"]{gap:6px}
[data-testid="stSidebar"] [role="radiogroup"] label{background:#171c26;border:1px solid #232b38;border-radius:12px;padding:10px 14px;width:100%;transition:all .2s;cursor:pointer}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{border-color:#E56020;transform:translateX(4px)}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:linear-gradient(90deg,#E5602040,#E5602008);border-color:#E56020;font-weight:600}
[data-testid="stSidebar"] [role="radiogroup"] label>div:first-child{display:none}
[data-testid="stSidebar"] .stButton>button{justify-content:flex-start;text-align:left;font-size:.85rem;padding:6px 12px}
.stTabs [data-baseweb="tab-list"]{gap:6px}
.stTabs [data-baseweb="tab"]{background:#171c26;border:1px solid #232b38;border-bottom:none;font-weight:600}
.pl-card{display:flex;align-items:center;gap:16px;padding:14px 18px;border-radius:16px;background:linear-gradient(145deg,#1E2430,#171c26);border:2px solid #E56020;margin-bottom:10px;animation:fade .5s ease}
.pl-foto{height:96px;width:96px;object-fit:cover;object-position:top center;border-radius:50%;background:#0E1117;flex:none}
.pl-nome{font-size:1.25rem;font-weight:800}
.pl-sub{font-size:.7rem;letter-spacing:.08em;color:#8b96a8;text-transform:uppercase;margin-top:6px}
.pl-times{display:flex;flex-wrap:wrap;gap:8px;margin-top:6px}.pl-times img{height:34px}
::-webkit-scrollbar{width:8px;height:8px}::-webkit-scrollbar-thumb{background:#2b3442;border-radius:8px}::-webkit-scrollbar-thumb:hover{background:#E56020}
.block-container{animation:fade .4s ease}
.boasvindas{text-align:center;color:#8b96a8;margin:6px 0 18px}
.grupo-t{font-weight:700;margin:4px 0 8px;color:#F2A65A}
.pensando{color:#8b96a8}.pensando i{font-style:normal;animation:blink 1.2s infinite}
.pensando i:nth-child(2){animation-delay:.2s}.pensando i:nth-child(3){animation-delay:.4s}
@keyframes blink{0%,80%,100%{opacity:.2}40%{opacity:1}}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]){border-left:3px solid #1D428A}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]){border-left:3px solid #E56020}
[data-testid="stChatInput"]:focus-within{border-color:#E56020;box-shadow:0 0 0 3px #E5602033}
[data-testid="stDataFrame"],[data-testid="stPlotlyChart"]{border:1px solid #232b38;border-radius:14px;overflow:hidden}
.stButton>button[kind="primary"]{background:linear-gradient(90deg,#E56020,#F2A65A);border:none;font-weight:700}
[data-testid="stExpander"]{border:1px solid #232b38;border-radius:12px}
[data-testid="stChatMessage"] table{border-collapse:collapse;width:100%}
[data-testid="stChatMessage"] th{background:#1E2430;color:#F2A65A}
[data-testid="stChatMessage"] td,[data-testid="stChatMessage"] th{padding:8px 10px;border:1px solid #2b3442}
[data-testid="stChatMessage"] tr:hover td{background:#1b2230}
.marca{display:flex;align-items:center;gap:10px;font-size:1.5rem;font-weight:800}
.marca-t{background:linear-gradient(90deg,#fff,#F2A65A);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
@keyframes fade{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
</style>"""


def aplicar_tema():
    st.markdown(CSS, unsafe_allow_html=True)


def card(titulo, valor, sub="", classe="", img=""):
    return f'<div class="card {classe}">{img}<div class="t">{titulo}</div><div class="v">{valor}</div><div class="s">{sub}</div></div>'


def chips(nomes):
    nomes = list(nomes)
    return "".join(f'<span class="chip">{n}</span>' for n in nomes) if nomes else "<i>—</i>"


def cabecalho(icone, titulo, sub=""):
    st.markdown(f'<div class="hero"><div class="hero-i">{icone}</div><div><div class="hero-t">{titulo}</div><div class="hero-s">{sub}</div></div></div>',
                unsafe_allow_html=True)


def card_jogador(nome, pid, times, cor="#E56020"):
    from utils.logos import foto_url, logo_url, IMAGENS_ATIVAS
    if not IMAGENS_ATIVAS:
        return f'<div class="pl-card" style="border-color:{cor}"><div><div class="pl-nome">{nome}</div></div></div>'
    logos = "".join(f'<img src="{logo_url(t)}">' for t in times)
    sub = '<div class="pl-sub">Times da carreira</div>' if logos else ""
    return (f'<div class="pl-card" style="border-color:{cor}"><img class="pl-foto" src="{foto_url(pid)}">'
            f'<div><div class="pl-nome">{nome}</div>{sub}<div class="pl-times">{logos}</div></div></div>')
