# Roadmap por fases

Legenda de status: ⬜ Não iniciada · 🟨 Em andamento · ✅ Concluída

| Fase | Nome | Status |
|---|---|---|
| — | Planejamento inicial | ✅ (2026-11-16) |
| 0 | Fundação | ⬜ |
| 1 | Base de conhecimento | ⬜ |
| 2 | API de Chat | ⬜ |
| 3 | Feedback | ⬜ |
| 4 | Frontend Next.js mínimo | ⬜ |
| 5 | Deploy | ⬜ |
| 6 | Avaliação com jogadores | ⬜ |

---

## Fase 0 — Fundação ⬜
**Objetivo:** projeto rodando localmente, com banco, testes e autenticação.
Decisões: D12, D16, D26.

- [ ] Projeto FastAPI criado com `uv` (lockfile versionado)
- [ ] Primeira rota em `main.py`: `GET /health` responde `200` com `{"status": "ok"}` no `/docs`
- [ ] Praticar validação de entrada com anotações de tipo e Pydantic
- [ ] Configurar `pytest` e `ruff` e testar a primeira rota com `TestClient`
- [ ] `docker-compose.yml` com PostgreSQL
- [ ] Escolher a camada de persistência e a ferramenta de migrações e conectar a aplicação ao PostgreSQL
- [ ] Configuração por variáveis de ambiente com `.env.example` versionado e `.env` ignorado
- [ ] PDFs e pasta de dados no `.gitignore`
- [ ] Módulo `accounts` com usuários e autenticação JWT para obter e renovar tokens

**Pronto quando:** a API roda localmente conectada ao PostgreSQL, a rota `/health` responde `200`, os testes de emissão e renovação de JWT passam com `pytest` e `ruff check` não aponta erros.

## Fase 1 — Base de conhecimento ⬜
**Objetivo:** os 2 livros indexados na OpenAI e registrados no banco.
Decisões: D03, D08, D18, D19.

- [ ] Resolver as pendências: nomes dos sistemas e termos de uso
- [ ] Módulo `knowledge`: persistir `RpgSystem` (`slug`, `name`, `language`, `vector_store_id`) e `Document` (`file_id`, status, `chunking_strategy`, data)
- [ ] Serviço de ingestão: criar o Vector Store do sistema e enviar o PDF
- [ ] Comando Python de ingestão que recebe o slug do sistema e o caminho do PDF
- [ ] Testes do serviço com a OpenAI mockada

**Pronto quando:** os 2 sistemas aparecem no banco com Vector Stores prontos (status `completed`), e o teste mockado da ingestão passa.

## Fase 2 — API de Chat ⬜
**Objetivo:** conversar com o bot via API, com respostas fundamentadas e citadas.
Decisões: D10, D11, D12, D13, D17, D20, D21.

- [ ] Módulo `chat`: persistir `Conversation` (usuário, sistema) e `Message` (papel, conteúdo, `response_id`, citações)
- [ ] Serviço de chat: Responses API + `file_search` com o `vector_store_id` do sistema e as últimas N mensagens
- [ ] Prompt de grounding versionado (responder só com base nos trechos e recusar quando não encontrar)
- [ ] Citações (livro + trecho) via `include=["file_search_call.results"]`
- [ ] Endpoints: criar/listar conversas, enviar mensagem, ver histórico
- [ ] Permissão: o usuário só acessa as próprias conversas
- [ ] Definir e aplicar limite de requisições por usuário no chat
- [ ] Testes com a OpenAI mockada (inclusive o isolamento entre usuários)

**Pronto quando:** um usuário autenticado envia uma pergunta e recebe JSON com resposta e fontes. Outro usuário recebe 404 ao tentar acessar a conversa, e os testes passam.

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
- [ ] Roteiro de tarefas para os participantes (ex.: tirar uma dúvida e criar um personagem em cada sistema)
- [ ] Questionário SUS e perguntas abertas
- [ ] Coleta, exportação e análise (SUS, taxa de 👍 por sistema, comentários)

**Pronto quando:** os dados foram coletados e analisados para o artigo.

---

## Backlog (sem fase definida)
- Marcadores de página no pré-processamento dos PDFs (revisaria D20)
- Streaming SSE (se não entrar na Fase 4)
- Ficha de personagem estruturada e salva (revisaria D10)
- Reescrita da pergunta com base no histórico (query rewriting)
- Integração com Discord
