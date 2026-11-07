# Banco Solidário SCS

MVP acadêmico (disciplina Projeto de Software – Cruzeiro do Sul Virtual) para apoiar a gestão de doações do
Banco de Alimentos do Fundo Social de Solidariedade de São Caetano do Sul: registro de doações (inclusive sem
internet), estoque com alerta de validade e retiradas por entidade assistencial.

> Projeto acadêmico. O diagnóstico do problema foi feito por pesquisa documental e ainda precisa ser validado
> com o parceiro. Todos os dados de exemplo são fictícios.

## Funcionalidades (requisitos)

| Requisito | Descrição | Onde |
|---|---|---|
| RF01 | Registrar doação (canal, categoria, quantidade, validade), com fila offline e sem duplicidade | `POST /doacoes`, tela *Nova doação* |
| RF02 | Estoque por categoria e lotes ordenados por validade, com alerta de até 7 dias | `GET /estoque`, tela *Estoque* |
| RF03 | Cadastro de entidades beneficiárias (CNPJ válido e único) | `/entidades` |
| RF04 | Retirada com baixa atômica do estoque, sem saldo negativo | `POST /retiradas` |
| RNF01 | Senhas com Argon2id, JWT de 30 min, logout com revogação, bloqueio após 5 tentativas | `app/security.py` |
| RNF02 | Validação no servidor, ORM com parâmetros, cabeçalhos de segurança, erros genéricos | `app/schemas.py`, `app/main.py` |
| RNF04 | Áreas de toque ≥ 48 px, contraste AA, alertas com texto + ícone + cor | `frontend/src/styles.css` |

## Arquitetura

Cliente-servidor com back-end monolítico em camadas:

```
frontend/  Angular 22 (PWA, service worker, fila offline com Dexie/IndexedDB)
backend/   Python 3.12 + FastAPI
  app/routers/   camada de API (rotas, autenticação e autorização por perfil)
  app/services/  regras de negócio (testáveis sem banco)
  app/models.py  entidades SQLAlchemy (Usuario, EntidadeBeneficiaria, Doacao, ItemDoado, Retirada, ItemRetirada)
PostgreSQL 16 (SQLite apenas em desenvolvimento rápido e nos testes)
```

Decisões registradas em [`docs/adr`](docs/adr) e regras de negócio em [`docs/regras-de-negocio.md`](docs/regras-de-negocio.md).

## Como rodar localmente

### Back-end
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env            # ajuste a chave JWT; sem .env usa SQLite local
python -m app.seed --email coordenacao@exemplo.org --senha "<senha-forte>" --demo
uvicorn app.main:app --reload   # documentação da API em http://localhost:8000/docs
```

Ou, com Docker: `docker compose up --build` (API + PostgreSQL).

### Front-end
```bash
cd frontend
npm ci
npx ng serve                    # http://localhost:4200
```

## Testes e qualidade

```bash
cd backend && pytest --cov=app        # 37 testes (unitários + integração), cobertura ≥ 80%
cd frontend && npx ng test --watch=false
```

A pipeline de integração contínua (`.github/workflows/ci.yml`) roda a cada push e pull request: lint (ruff),
testes com cobertura mínima, smoke test com PostgreSQL real, build de produção do PWA, testes do front-end e
auditoria de dependências (pip-audit e npm audit).

## Publicação e monitoramento

O app está publicado na Vercel (PWA + API serverless + PostgreSQL Neon) e é verificado a cada 30 minutos por um
workflow do GitHub Actions. Detalhes em [`docs/deploy-e-monitoramento.md`](docs/deploy-e-monitoramento.md).

## Fluxo de trabalho no Git

- `main` protegida; cada história de usuário em uma branch `feat/...` ou `fix/...`.
- Commits no padrão Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`, `ci:`).
- Toda mudança entra por Pull Request com o checklist de auto-revisão (`.github/pull_request_template.md`)
  e só é integrada com a CI verde.

## Evidências

Capturas do sistema rodando localmente com dados fictícios estão em [`docs/evidencias`](docs/evidencias).
