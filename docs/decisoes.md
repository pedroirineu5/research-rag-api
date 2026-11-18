# Registro de decisões arquiteturais

Formato: ADR simplificado. Status possíveis: **Aceita**, **Substituída por Dxx**, **Descartada**.
Decisões substituídas são mantidas para preservar o histórico do raciocínio.

Sessão de planejamento inicial: **2026-11-16**.

## Resumo

| # | Decisão | Status |
|---|---|---|
| D01 | Chatbot de regras e criação de personagens de RPG, com 2 sistemas | Aceita |
| D02 | Os 2 sistemas são bases independentes; o usuário escolhe o sistema | Aceita |
| D03 | Um sistema com conteúdo aberto + um nacional/comercial; PDFs fora do git | Aceita (nomes pendentes) |
| D04 | Perguntas e respostas em PT; livros no idioma original | Aceita |
| D05 | Provider abstrato (API externa + Ollama depois) | Substituída por D18 |
| D06 | PostgreSQL + pgvector como vector store | Substituída por D18 |
| D07 | Pipeline de RAG próprio | Substituída por D18 |
| D08 | Ingestão por linha de comando, síncrona, sem fila | Aceita (ajustada por D18 e D26) |
| D09 | Chunking fixo como baseline experimental | Substituída por D18 |
| D10 | Criação de personagem apenas conversacional no MVP | Aceita |
| D11 | Histórico salvo no banco; janela das últimas N mensagens | Aceita (detalhada em D21) |
| D12 | Autenticação JWT, isolamento por usuário, throttling | Aceita (ajustada por D26) |
| D13 | Resposta única em JSON com fontes; streaming depois | Aceita (ajustada por D26) |
| D14 | Avaliação técnica com dataset "golden" e métricas de recuperação | Descartada (ver D22) |
| D15 | Apps Django por domínio + camada de serviço | Substituída por D26 |
| D16 | Docker só para o PostgreSQL; uv; .env; pytest; ruff | Aceita (ajustada por D18 e D26) |
| D17 | Grounding estrito, com recusa explícita e prompt versionado | Aceita (citação revista em D20) |
| D18 | RAG gerenciado: OpenAI Responses API + File Search | Aceita |
| D19 | Um Vector Store por sistema de RPG | Aceita |
| D20 | Citação por livro + trecho recuperado, sem página no MVP | Aceita |
| D21 | PostgreSQL como fonte da verdade da conversa; salvar `response_id` | Aceita |
| D22 | Avaliação com jogadores: questionário SUS + feedback 👍/👎 | Aceita |
| D23 | Frontend Next.js mínimo antes da avaliação | Aceita |
| D24 | Deploy simples antes da avaliação (acesso remoto) | Aceita (plataforma pendente) |
| D25 | Estrutura da pasta `/docs` | Aceita |
| D26 | FastAPI como framework do backend | Aceita |

---

## D01 — Propósito do sistema
- **Status:** Aceita
- **Decisão:** chatbot que responde dúvidas de regras e orienta a criação de personagens de RPG de mesa, com base nos livros (PDF) de 2 sistemas.

## D02 — Papel dos 2 sistemas
- **Status:** Aceita
- **Contexto:** os 2 sistemas existem para avaliar melhor os resultados.
- **Decisão:** os 2 livros são bases **independentes**. O usuário escolhe em qual sistema está perguntando e a busca considera só aquele livro.
- **Alternativas:** o bot comparar os sistemas entre si; buscar nos dois livros ao mesmo tempo.
- **Consequências:** as regras dos sistemas não se misturam. Dá para comparar o desempenho entre os sistemas.

## D03 — Sistemas e licenças
- **Status:** Aceita (nomes exatos pendentes)
- **Decisão:** um sistema com conteúdo aberto (ex.: D&D 5e SRD 5.1, CC-BY) e um nacional/comercial que o autor possui (ex.: Tormenta20, Ordem Paranormal).
- **Consequências:** os PDFs **não** vão para o repositório git. Com D18, o livro comercial fica armazenado na OpenAI: é preciso verificar os termos de uso do livro e da OpenAI.

## D04 — Idioma
- **Status:** Aceita
- **Decisão:** o usuário pergunta em português e o bot responde sempre em português. Os livros ficam no idioma original (o sistema aberto provavelmente em EN, o nacional em PT).
- **Consequências:** a busca é cross-lingual. O idioma vira uma variável a observar na avaliação.

## D05 — Provider de LLM/embeddings abstrato
- **Status:** Substituída por D18
- **Decisão original:** interface trocável, começando com API externa e testando Ollama depois.

## D06 — PostgreSQL + pgvector
- **Status:** Substituída por D18
- **Decisão original:** um único banco para os dados do Django e os vetores.
- **Situação atual:** o PostgreSQL armazena os dados da aplicação. Os vetores ficam nos Vector Stores da OpenAI.

## D07 — Pipeline de RAG próprio
- **Status:** Substituída por D18
- **Decisão original:** serviços próprios de extração, chunking, embeddings e busca, sem LangChain/LlamaIndex.

## D08 — Ingestão por linha de comando
- **Status:** Aceita (ajustada por D18 e D26)
- **Decisão:** comando local em Python, síncrono e sem fila. O comando **envia o PDF ao Vector Store** do sistema e salva no banco os IDs (`file_id`, `vector_store_id`), o status e a estratégia de chunking usada.
- **Plano anterior:** usar um management command do Django.
- **Alternativas:** upload via endpoint com Celery; upload pelo Django Admin.
- **Consequências:** é reprodutível e não expõe upload de arquivo na API.

## D09 — Chunking fixo como baseline experimental
- **Status:** Substituída por D18
- **Situação atual:** usa a `chunking_strategy` da OpenAI (padrão `auto`: 800 tokens, overlap 400), registrada no banco a cada ingestão.

## D10 — Escopo da criação de personagens
- **Status:** Aceita
- **Decisão:** no MVP, apenas conversa (perguntas de regras e orientação da criação em texto). A ficha estruturada e salva fica no backlog.
- **Consequências:** não precisamos de modelo de dados de ficha por sistema nem de validação de regras.

## D11 — Memória da conversa
- **Status:** Aceita (detalhada em D21)
- **Decisão:** salvar `Conversation` e `Message` no banco e enviar as últimas N mensagens ao LLM. A reescrita da pergunta com base no histórico fica como melhoria futura.

## D12 — Autenticação e controle de uso
- **Status:** Aceita (ajustada por D26)
- **Decisão:** login com emissão e renovação de JWT. Cada usuário só acessa as próprias conversas. Limite de requisições por usuário para controlar o custo da API.
- **Plano anterior:** usar Simple JWT e o throttling do DRF.
- **Alternativas consideradas no plano inicial:** TokenAuthentication do DRF, sessão ou acesso sem autenticação.
- **Consequências:** funciona bem com um frontend separado (D23).

## D13 — Entrega da resposta
- **Status:** Aceita (ajustada por D26)
- **Decisão:** o cliente faz um `POST` e recebe uma única resposta JSON, com o texto e as fontes. Avaliar streaming (SSE) na Fase 4.
- **Consequências:** o FastAPI roda em um servidor ASGI. A resposta única em JSON funciona tanto com `def` quanto com `async def`.

## D14 — Avaliação técnica (dataset "golden")
- **Status:** Descartada (ver D22)
- **Motivo:** com D18 a recuperação é caixa-preta, e o foco passou a ser a utilidade para os jogadores.

## D15 — Organização do projeto Django
- **Status:** Substituída por D26
- **Decisão original:** apps por domínio:
  - `accounts`: usuários.
  - `knowledge`: `RpgSystem` (com `vector_store_id`), `Document`, registro de ingestões.
  - `chat`: `Conversation`, `Message`, citações, feedback.
  - Camada de serviço para a integração com a OpenAI (ingestão e consulta), sem depender de views.
- **Consequências:** as views do DRF ficam finas (validar → chamar serviço → serializar). O serviço é reutilizado pelo endpoint, pelos commands e pelos testes (com a OpenAI mockada).

## D16 — Ambiente e ferramentas
- **Status:** Aceita (ajustada por D18 e D26)
- **Decisão:** Docker Compose **apenas para o PostgreSQL** (com D18, o pgvector deixou de ser necessário). FastAPI roda local com `uv` (lockfile). Configuração por variáveis de ambiente (`.env` fora do git). Testes de API com `pytest` e `TestClient`, lint e formatação com `ruff`.
- **Plano anterior:** executar Django localmente e usar `pytest-django` nos testes.

## D17 — Comportamento da resposta (grounding)
- **Status:** Aceita (a forma de citação foi revista em D20)
- **Decisão:** responder só com base nos trechos recuperados. Se o contexto não bastar, dizer que não encontrou nas regras, sem inventar. O prompt fica **versionado no código**.
- **Motivo:** o LLM já conhece sistemas populares de memória e poderia responder fora do livro.

## D18 — RAG gerenciado com OpenAI File Search
- **Status:** Aceita
- **Contexto:** o objetivo do artigo é resolver o problema o mais rápido possível com a tecnologia disponível, não comparar técnicas de RAG.
- **Decisão:** usar a **OpenAI Responses API** com a ferramenta **File Search** e Vector Stores hospedados. A OpenAI faz extração, chunking, embeddings, busca e geração.
- **Alternativas:** pipeline próprio com pgvector (D06/D07); LangChain/LlamaIndex.
- **Consequências:**
  - ✅ MVP muito mais rápido, com menos código.
  - ❌ Dependência de um único fornecedor (lock-in). A recuperação é caixa-preta.
  - ❌ Sem número de página nativo (ver D20). O chunking só permite ajustar tamanho e overlap.
  - ❌ Custo de armazenamento dos Vector Stores, além do custo por uso. O livro comercial fica nos servidores da OpenAI.

## D19 — Um Vector Store por sistema
- **Status:** Aceita
- **Decisão:** cada `RpgSystem` tem seu próprio Vector Store. O backend passa ao File Search apenas o `vector_store_id` do sistema escolhido na conversa.
- **Alternativas:** um Vector Store único com filtro por atributo; um único store sem filtro.
- **Consequências:** isolamento garantido entre os sistemas. Dá para reingerir um livro sem afetar o outro.

## D20 — Citações
- **Status:** Aceita
- **Decisão:** citar **livro + trecho recuperado**, usando `include=["file_search_call.results"]` da Responses API. Sem número de página no MVP.
- **Alternativas:** pré-processar o PDF com marcadores `[Página N]` (fica no backlog).

## D21 — Estado da conversa
- **Status:** Aceita
- **Decisão:** o PostgreSQL armazena `Conversation` e `Message` como fonte da verdade. O backend envia as últimas N mensagens como input e salva o `response_id` da OpenAI na mensagem para depuração.
- **Alternativas:** estado na OpenAI (`previous_response_id` / Conversations API).
- **Consequências:** controle do custo pela janela de mensagens, sem depender da retenção da OpenAI. O frontend lista as conversas pela API.

## D22 — Avaliação com jogadores
- **Status:** Aceita
- **Decisão:** avaliação de usabilidade e satisfação com jogadores reais:
  - Questionário externo padronizado, com a escala **SUS** (ex.: Google Forms).
  - Feedback 👍/👎 por resposta, salvo pela API e exportável para análise.
- **Consequências:** exige um frontend usável (D23) e deploy (D24). Por ser pesquisa com pessoas, é preciso alinhar consentimento e ética com o orientador (ver pendências).

## D23 — Frontend antes da avaliação
- **Status:** Aceita
- **Decisão:** frontend mínimo em Next.js (login, escolha do sistema, conversa, feedback) construído antes da avaliação.
- **Alternativas:** templates do Django temporários; bot no Discord.

## D24 — Deploy antes da avaliação
- **Status:** Aceita (plataforma pendente)
- **Decisão:** deploy simples da API e do frontend para que os jogadores acessem remotamente.

## D25 — Estrutura da documentação
- **Status:** Aceita
- **Decisão:** `docs/README.md` (visão geral), `docs/decisoes.md` (este registro) e `docs/fases.md` (roadmap).

## D26 — FastAPI no backend
- **Status:** Aceita em 2026-11-18
- **Contexto:** o backend está em planejamento. O projeto também servirá para aprender FastAPI desde a primeira rota.
- **Decisão:** usar FastAPI para as rotas HTTP e Pydantic para os contratos de entrada e saída. Organizar o código por domínio (`accounts`, `knowledge`, `chat`) conforme as funcionalidades forem implementadas. Manter a integração com a OpenAI em serviços que possam ser chamados pelas rotas e pela linha de comando.
- **Alternativa considerada:** seguir o plano inicial com Django e DRF.
- **Consequências:** a primeira etapa é uma API local com uma rota simples. A escolha da camada de persistência, da ferramenta de migrações e das bibliotecas de autenticação fica para a Fase 0, depois da primeira rota. O mecanismo de limitação de requisições será definido na Fase 2.

---

## Pendências

| Pendência | Impacta | Quando resolver |
|---|---|---|
| Nomes exatos dos 2 sistemas e versão dos livros | D03, D04 | Antes da Fase 1 |
| Camada de persistência, ferramenta de migrações e bibliotecas de autenticação | D12, D26 | Fase 0, depois da primeira rota |
| Verificar os termos de uso do livro comercial e da OpenAI (armazenamento e retenção de dados) | D03, D18 | Antes da Fase 1 |
| Qual modelo da OpenAI usar e o orçamento mensal | D18, D12 | Antes da Fase 2 |
| Valores de N (janela de mensagens) e `max_num_results` | D18, D21 | Fase 2 |
| Mecanismo de throttling e limite de requisições por usuário | D12, D26 | Fase 2 |
| Alinhar o método de avaliação com o orientador: consentimento (TCLE), necessidade de comitê de ética e LGPD dos dados dos participantes | D22 | Antes da Fase 6 |
| Plataforma de deploy | D24 | Antes da Fase 5 |
| Adicionar PDFs e a pasta de dados ao `.gitignore` (hoje não estão ignorados) | D03 | Fase 0 |
