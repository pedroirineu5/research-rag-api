# Research RAG API

API FastAPI para conversar em inglês sobre regras e criação de personagens usando o Dungeons & Dragons SRD 5.2.1. O PDF está indexado no File Search da OpenAI; usuários, conversas e mensagens ficam no PostgreSQL.

## Rodar localmente

Requisitos: Python 3.13, `uv` e um daemon Docker ativo.

```bash
uv sync
cp .env.example .env
uv run python -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Preencha `DATABASE_URL`, `JWT_SECRET_KEY` (com o valor gerado) e `OPENAI_API_KEY` no `.env`. Depois:

```bash
docker --context default compose up -d --wait postgres
uv run alembic upgrade head
uv run uvicorn main:app --reload
```

A documentação interativa fica em `http://localhost:8000/docs` e `GET /health` responde `{"status":"ok"}`.

## Autenticação

| Método | Rota | Corpo | Resultado |
|---|---|---|---|
| POST | `/accounts/register` | `{"email":"player@example.com","password":"senha-com-8-ou-mais"}` | Usuário criado (`201`) |
| POST | `/accounts/login` | Email e senha no mesmo formato | `access_token` e `refresh_token` |
| POST | `/accounts/refresh` | `{"refresh_token":"..."}` | Novo `access_token` |
| GET | `/accounts/me` | Header `Authorization: Bearer <access_token>` | Dados do usuário |

O access token dura 15 minutos; o refresh token, 7 dias. O cadastro retorna `409` para email já usado. Tokens inválidos ou com tipo incorreto retornam `401`.

## Base de conhecimento

Antes de enviar livros, confirme que seus termos de uso permitem o armazenamento na OpenAI e configure `OPENAI_API_KEY` no `.env`. Os PDFs ficam fora do Git. Segundo os [controles de dados da OpenAI](https://developers.openai.com/api/docs/guides/your-data), arquivos e Vector Stores permanecem armazenados até a exclusão; dados da API não são usados para treinar modelos por padrão.

```bash
uv run alembic upgrade head
uv run python -m app.knowledge.cli register --slug sistema-a --name "Nome do sistema" --language pt-BR
uv run python -m app.knowledge.cli ingest --slug sistema-a --pdf /caminho/para/livro.pdf
uv run python -m app.knowledge.cli list
```

O SRD 5.2.1 já foi ingerido. Esses comandos servem para adicionar outro sistema no futuro. Cada sistema recebe seu próprio Vector Store. Consulte `list` antes de repetir uma ingestão, pois cada execução pode reenviar o PDF e gerar custo.

O sistema `dnd-srd-5-2-1` usa o SRD 5.2.1 e responde em inglês. Veja a [atribuição exigida pela licença](docs/licencas.md).

## Conversar pela API

Faça login e use o `access_token` no header `Authorization: Bearer <token>`:

| Método | Rota | Corpo | Resultado |
|---|---|---|---|
| GET | `/systems` | — | Sistemas prontos para conversa |
| POST | `/conversations` | `{"system_slug":"dnd-srd-5-2-1"}` | Nova conversa |
| GET | `/conversations` | — | Conversas do usuário |
| GET | `/conversations/{id}` | — | Histórico da conversa |
| POST | `/conversations/{id}/messages` | `{"content":"What is the Longbow's range?"}` | Resposta em inglês com trechos do SRD |

O chat usa `gpt-6-luna` por padrão; `OPENAI_MODEL` permite mudar o modelo. O limite padrão é de 30 perguntas por usuário em uma hora, configurável por `CHAT_REQUESTS_PER_HOUR`. O modelo recebe as últimas 10 mensagens e até 5 trechos recuperados. Se nenhum trecho do SRD sustentar a resposta, a API devolve uma recusa explícita.

## Verificar

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

Os testes usam SQLite em memória; a configuração local usa PostgreSQL. As migrações estão em `alembic/versions/` e os testes de ingestão substituem a OpenAI por um cliente falso.
