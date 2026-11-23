# Aviso legal

## Disclaimer (English)
This is an educational, non-commercial project for portfolio purposes. It is not affiliated with, endorsed or sponsored by the National Basketball Association (NBA), any team, Groq, or any other company mentioned. NBA-related names, data, logos and player images are the property of the NBA and their respective owners. This repository contains source code only: no NBA data, logos or photos are included, and images are disabled by default. Data comes from NBA.com via the third-party `nba_api` library and is subject to the NBA.com Terms of Use; do not redistribute it or use it commercially. If you are a rights holder and want something removed, open an issue. This is not legal advice.

---

## Versão em português

**Hoops StatBot é um projeto pessoal, educacional e sem fins lucrativos.** Não é afiliado, patrocinado nem endossado pela NBA, pelas franquias, pela Groq ou por qualquer outra empresa citada.

## O que este repositório contém (e o que não contém)
- **Contém:** apenas código-fonte e documentação escritos pelo autor, sob a licença MIT (`LICENSE`).
- **Não contém:** dados da NBA, logos, fotos ou outras marcas de terceiros. A pasta `data/` é mantida vazia; cada pessoa gera seus próprios dados localmente.

## Dados
Os dados são obtidos do NBA.com por meio da biblioteca de terceiros [`nba_api`](https://github.com/swar/nba_api) (MIT), que informa que os dados estão sujeitos aos Termos de Uso do NBA.com. Esses termos, em resumo, destinam o conteúdo ao uso pessoal, informativo e educacional e restringem sua reprodução ou reutilização em outros sites para fins públicos ou comerciais.
Por isso:
- os dados baixados **não devem ser publicados nem redistribuídos** (o `.gitignore` os exclui);
- o projeto **não deve ser usado comercialmente** com esses dados;
- leia os termos atuais em <https://www.nba.com/terms> e use por sua conta e risco.

## Marcas, logos e imagens
O nome e o logo da NBA e os nomes e logos dos times pertencem à NBA Properties e às franquias, e as fotos aos seus titulares. Para evitar o uso dessas marcas:
- por padrão o app **não carrega logos nem fotos** (`EXIBIR_IMAGENS_NBA=0`);
- a opção `EXIBIR_IMAGENS_NBA=1` existe apenas para uso pessoal e local, e as imagens são carregadas diretamente dos servidores da NBA, sem serem copiadas para o repositório;
- não publique capturas de tela ou vídeos com essas marcas se quiser manter o repositório neutro.

## Inteligência artificial
As respostas são geradas por um modelo de linguagem (via Groq) com base em dados locais. Podem conter erros ou interpretações subjetivas (rankings e "melhor da história" são análises, não fatos). Não use para apostas, decisões financeiras ou qualquer finalidade que exija precisão garantida.

## Privacidade
O app não coleta dados de usuários. O histórico de conversas fica em `data/conversas.json` (ignorado pelo Git) ou apenas na sessão do navegador (`NBA_HISTORICO=0`). Chaves de API ficam em `.env` ou `.streamlit/secrets.toml`, também ignorados pelo Git.

## Contato e remoção
Se você representa um titular de direitos e deseja a remoção de algum conteúdo, abra uma *issue* neste repositório e o conteúdo será retirado prontamente.

*Este documento é informativo e não constitui aconselhamento jurídico.*
