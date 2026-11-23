"""Verificação antes de publicar no GitHub: python scripts/checar_publicacao.py
Procura no que SERIA publicado (arquivos versionados e os que 'git add .' incluiria) por:
chaves de API, dados baixados, histórico de conversas, imagens e configurações inseguras.
Sai com código 1 se houver ERRO (pode ser usado em CI ou como hook de pre-commit)."""
import os
import re
import subprocess
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PULAR = {".git", ".venv", "venv", "__pycache__", ".idea", ".vscode", "node_modules", ".pytest_cache"}
PROIBIDOS = [(r"(^|/)\.env$", "arquivo .env (contém segredos)"), (r"(^|/)secrets\.toml$", "secrets.toml (contém segredos)"),
             (r"\.csv$", "CSV de dados (não redistribuir)"), (r"conversas\.json$", "histórico pessoal de conversas"),
             (r"\.(rar|zip|7z|sqlite|db)$", "arquivo compactado/banco de dados")]
IMAGENS = re.compile(r"\.(png|jpe?g|gif|svg|webp|ico)$", re.I)
SEGREDOS = [(re.compile(r"gsk_[A-Za-z0-9]{20,}"), "chave da Groq"), (re.compile(r"sk-[A-Za-z0-9_\-]{20,}"), "chave de API (sk-...)"),
            (re.compile(r"AKIA[0-9A-Z]{16}"), "chave da AWS"), (re.compile(r"ghp_[A-Za-z0-9]{30,}"), "token do GitHub"),
            (re.compile(r"(?:API_KEY|SECRET|TOKEN)\s*[=:]\s*[\"']?([A-Za-z0-9_\-]{20,})"), "valor de chave/segredo")]
PLACEHOLDER = re.compile(r"cole_sua|sua_chave|xxxx|exemplo|example|changeme", re.I)
CAMINHOS_PESSOAIS = re.compile(r"[A-Za-z]:\\Users\\|/Users/[a-z]|/home/[a-z]")
TEXTO = {".py", ".md", ".txt", ".toml", ".yml", ".yaml", ".json", ".cfg", ".ini", ".example", ".env", ""}


def listar():
    try:
        run = lambda *a: subprocess.run(["git", *a], cwd=RAIZ, capture_output=True, text=True, check=True).stdout.splitlines()
        arqs = set(run("ls-files")) | set(run("ls-files", "--others", "--exclude-standard"))
        return sorted(a for a in arqs if os.path.isfile(os.path.join(RAIZ, a))), "git (arquivos que seriam publicados)"
    except Exception:
        out = []
        for d, ds, fs in os.walk(RAIZ):
            ds[:] = [x for x in ds if x not in PULAR]
            out += [os.path.relpath(os.path.join(d, f), RAIZ).replace("\\", "/") for f in fs]
        return sorted(out), "pasta inteira (sem repositório git; arquivos ignorados pelo .gitignore também são listados)"


def main():
    erros, avisos = [], []
    arqs, modo = listar()
    print(f"Verificando: {modo}\n{len(arqs)} arquivos\n")
    for a in arqs:
        for padrao, motivo in PROIBIDOS:
            if re.search(padrao, a) and not a.endswith((".example",)):
                erros.append(f"{a}: {motivo}")
        if IMAGENS.search(a):
            (avisos if a.startswith("docs/img/") else erros).append(
                f"{a}: imagem" + (" (confira se o print não mostra logos/fotos da NBA)" if a.startswith("docs/img/") else " fora de docs/img (evite marcas de terceiros)"))
        ext = os.path.splitext(a)[1].lower()
        if ext in TEXTO or os.path.basename(a).startswith(".env"):
            try:
                with open(os.path.join(RAIZ, a), encoding="utf8", errors="ignore") as f:
                    for n, linha in enumerate(f, 1):
                        for rx, nome in SEGREDOS:
                            m = rx.search(linha)
                            if m and not PLACEHOLDER.search(linha):
                                val = m.group(0)
                                erros.append(f"{a}:{n}: possível {nome} ({val[:4]}***)")
                        if CAMINHOS_PESSOAIS.search(linha) and a != "scripts/checar_publicacao.py":
                            avisos.append(f"{a}:{n}: caminho pessoal no texto")
            except OSError:
                pass
    gi = os.path.join(RAIZ, ".gitignore")
    conteudo = open(gi, encoding="utf8").read() if os.path.exists(gi) else ""
    for item in [".env", "secrets.toml", "data/*"]:
        if item not in conteudo:
            erros.append(f".gitignore não protege '{item}'")
    logos = os.path.join(RAIZ, "utils", "logos.py")
    if os.path.exists(logos) and 'flag("EXIBIR_IMAGENS_NBA", "0")' not in open(logos, encoding="utf8").read():
        erros.append("utils/logos.py: as imagens da NBA não estão desligadas por padrão")
    lic = os.path.join(RAIZ, "LICENSE")
    if not os.path.exists(lic):
        erros.append("falta o arquivo LICENSE")
    elif "<SEU NOME>" in open(lic, encoding="utf8").read():
        avisos.append("LICENSE: troque <SEU NOME> pelo seu nome")
    for obrigatorio in ["README.md", "AVISO_LEGAL.md"]:
        if not os.path.exists(os.path.join(RAIZ, obrigatorio)):
            erros.append(f"falta o arquivo {obrigatorio}")
    for t, lista in [("AVISOS (revise)", avisos), ("ERROS (corrija antes de publicar)", erros)]:
        if lista:
            print(f"{t}:")
            print("\n".join(f"  - {x}" for x in lista), "\n")
    if erros:
        print("❌ NÃO publique ainda.")
        sys.exit(1)
    print("✅ Nada de segredo, dado ou imagem encontrado." + (" Resolva os avisos acima." if avisos else " Pode publicar."))


if __name__ == "__main__":
    main()
