# Checklist de publicação

Siga esta ordem para publicar o projeto no GitHub sem expor segredos, dados ou marcas de terceiros.
*(Informativo; não é aconselhamento jurídico.)*

## 1. Antes do primeiro commit
- [ ] Troque `<SEU NOME>` na `LICENSE`.
- [ ] Gere uma **chave nova** da Groq e apague as antigas (chaves já enviadas em arquivos ou conversas devem ser consideradas expostas).
- [ ] Confirme que suas chaves estão só em `.env` ou `.streamlit/secrets.toml` (ambos ignorados pelo Git).
- [ ] Rode `python scripts/checar_publicacao.py`. Deve terminar com ✅.
- [ ] Rode `pytest` (opcional, mas recomendado).

## 2. Criar o repositório (novo, sem histórico)
```bash
git init
git add .
git status                      # confira: NÃO podem aparecer .env, secrets.toml, data/*.csv
python scripts/checar_publicacao.py
git commit -m "Primeira versão do Hoops StatBot"
git branch -M main
git remote add origin https://github.com/<seu-usuario>/hoops-statbot.git
git push -u origin main
```
- Crie o repositório vazio no GitHub (sem README automático) antes do `git remote add`.
- Nunca reaproveite a pasta de um projeto antigo que já teve `.env` ou dados commitados: o histórico do Git guarda tudo.

## 3. Depois de publicar
- [ ] Ative **Secret scanning** e **Push protection** (Settings → Code security).
- [ ] Ative a autenticação em dois fatores na sua conta.
- [ ] Descrição do repositório neutra, por exemplo: "Chatbot de estatísticas de basquete com RAG (projeto educacional)".
- [ ] Prints/GIF em `docs/img/`, gravados com as imagens desligadas (`EXIBIR_IMAGENS_NBA=0`), sem logos nem fotos.
- [ ] Veja a aba **Actions**: os testes e a verificação de publicação devem passar.

## 4. Se uma chave vazar
Apagar o commit **não basta**. Revogue a chave imediatamente no painel da Groq e gere outra. Só depois limpe o histórico, se quiser.

## 5. Se alguém pedir a remoção de conteúdo
O `AVISO_LEGAL.md` prevê o contato por *issue*. Responda, remova o conteúdo apontado e agradeça.

## 6. Se ainda assim quiser hospedar o app online
Não é recomendado (a API da NBA costuma bloquear provedores de nuvem e os Termos de Uso restringem a exibição pública do conteúdo; sem a pasta `data/` o app abre vazio). Se decidir fazer mesmo assim:
- [ ] Mantenha `EXIBIR_IMAGENS_NBA = "0"` e `NBA_HISTORICO = "0"` nos *Secrets* da plataforma.
- [ ] Coloque a chave da Groq apenas nos *Secrets* da plataforma, com limite de gastos/uso na conta da Groq.
- [ ] Sem anúncios, links de afiliados, doações ou cobrança.
- [ ] Mantenha o aviso legal visível no app e leia os Termos de Uso atuais do NBA.com.
- [ ] Prefira acesso restrito (link privado) a um app público aberto.
