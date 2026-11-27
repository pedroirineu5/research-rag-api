# Roadmap por fases

Legenda de status: ⬜ Não iniciada · 🟨 Em andamento · ✅ Concluída

| Fase | Nome | Status |
|---|---|---|
| — | Planejamento inicial | ✅ (2026-11-16) |
| 0 | Fundação | ✅ Concluída (2026-11-26) |
| 1 | Base de conhecimento | ✅ Concluída (2026-11-26, um PDF) |
| 2 | API de Chat | ✅ Concluída (2026-11-26) |
| 3 | Feedback | ⬜ |
| 4 | Frontend Next.js mínimo | ⬜ |
| 5 | Deploy | ⬜ |
| 6 | Avaliação com jogadores | ⬜ |

---

## Fase 0 — Fundação ✅
**Objetivo:** projeto rodando localmente, com banco, testes e autenticação.
Decisões: D12, D16, D26.

- [x] Projeto FastAPI criado com `uv` (lockfile versionado)
- [x] Primeira rota em `main.py`: `GET /health` responde `200` com `{"status": "ok"}` no `/docs`
- [x] Validação de entrada com anotações de tipo e Pydantic
- [x] `pytest` e `ruff` configurados; rota testada com `TestClient`
- [x] `docker-compose.yml` com PostgreSQL (configuração validada)
- [x] SQLAlchemy e Alembic configurados; migração, cadastro e login validados no PostgreSQL em execução
- [x] Configuração por variáveis de ambiente com `.env.example` versionado e `.env` ignorado
- [x] PDFs e pasta de dados no `.gitignore`
- [x] Módulo `accounts` com usuários e autenticação JWT para obter e renovar tokens

**Pronto quando:** a API roda localmente conectada ao PostgreSQL, a rota `/health` responde `200`, os testes de emissão e renovação de JWT passam com `pytest` e `ruff check` não aponta erros.

## Fase 1 — Base de conhecimento ✅
**Objetivo:** o SRD 5.2.1 indexado na OpenAI e registrado no banco.
Decisões: D08, D18, D19, D29, D30.

- [x] Definir o SRD 5.2.1 e verificar a licença CC BY 4.0
- [x] Módulo `knowledge`: persistir `RpgSystem` (`slug`, `name`, `language`, `vector_store_id`) e `Document` (`file_id`, status, `chunking_strategy`, data)
- [x] Serviço de ingestão: criar o Vector Store do sistema e enviar o PDF
- [x] Comando Python de ingestão que recebe o slug do sistema e o caminho do PDF
- [x] Testes do serviço com a OpenAI mockada

**Resultado:** Dungeons & Dragons SRD 5.2.1 foi indexado; o Vector Store e o arquivo estão com status `completed`. Idioma do livro e das respostas: inglês.

**Pronto quando:** o sistema aparece no banco com Vector Store pronto (status `completed`), e o teste mockado da ingestão passa.

## Fase 2 — API de Chat ✅
**Objetivo:** conversar com o bot via API, com respostas fundamentadas e citadas.
Decisões: D10, D11, D12, D13, D17, D20, D21, D29, D31.

- [x] Módulo `chat`: persistir `Conversation` (usuário, sistema) e `Message` (papel, conteúdo, `response_id`, citações)
- [x] Serviço de chat: Responses API + `file_search` com o `vector_store_id` do sistema e as últimas 10 mensagens
- [x] Prompt de grounding versionado (responder só com base nos trechos e recusar quando não encontrar)
- [x] Responder no idioma configurado em `RpgSystem.response_language` (inglês para D&D SRD 5.2.1)
- [x] Citações (livro + trecho) via `include=["file_search_call.results"]`
- [x] Endpoints: listar sistemas prontos, criar/listar conversas, enviar mensagem, ver histórico
- [x] Permissão: o usuário só acessa as próprias conversas
- [x] Limite de 30 perguntas por usuário em uma janela de uma hora (configurável)
- [x] Testes com a OpenAI mockada (inclusive o isolamento entre usuários)

**Pronto quando:** um usuário autenticado envia uma pergunta e recebe JSON com resposta e fontes. Outro usuário recebe 404 ao tentar acessar a conversa, e os testes passam. Validado também com uma pergunta real ao SRD.

## Fase 3 — Feedback ⬜
**Objetivo:** coletar a avaliação de cada resposta.
Decisões: D22.

- [ ] Persistência e endpoint de feedback 👍/👎 (com comentário opcional) por mensagem do bot
- [ ] Exportação dos dados (comando Python para CSV) para a análise do artigo

**Pronto quando:** o feedback é salvo, apenas para mensagens do próprio usuário, e o CSV é gerado.

## Fase 4 — Frontend Next.js mínimo ⬜
**Objetivo:** interface usável pelos jogadores.
Decisões: D23, D13.

- [ ] Login (JWT), escolha do sistema, conversa, feedback e exibição das fontes
- [ ] Exibir a atribuição CC BY 4.0 do SRD 5.2.1 na interface pública
- [ ] CORS configurado na API
- [ ] Avaliar se o streaming (SSE) entra aqui

**Pronto quando:** um usuário faz uma conversa completa pelo navegador e dá feedback.

## Fase 5 — Deploy ⬜
**Objetivo:** acesso remoto para os participantes.
Decisões: D24.

- [ ] Escolher a plataforma
- [ ] Configuração de produção (servidor ASGI, modo de depuração desativado, hosts permitidos, HTTPS e segredos)
- [ ] Limites de custo na OpenAI e throttling revisados

**Pronto quando:** os participantes acessam por URL pública com HTTPS.

## Fase 6 — Avaliação com jogadores ⬜
**Objetivo:** evidência de que o problema foi resolvido.
Decisões: D22.

- [ ] Alinhar com o orientador: TCLE, comitê de ética e LGPD
- [ ] Roteiro de tarefas para os participantes (ex.: tirar uma dúvida e criar um personagem usando o SRD)
- [ ] Questionário SUS e perguntas abertas
- [ ] Coleta, exportação e análise (SUS, taxa de 👍, comentários)

**Pronto quando:** os dados foram coletados e analisados para o artigo.

---

## Backlog (sem fase definida)
- Marcadores de página no pré-processamento dos PDFs (revisaria D20)
- Streaming SSE (se não entrar na Fase 4)
- Ficha de personagem estruturada e salva (revisaria D10)
- Reescrita da pergunta com base no histórico (query rewriting)
- Integração com Discord
