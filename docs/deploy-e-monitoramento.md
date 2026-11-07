# Publicação (deploy) e monitoramento

O Banco Solidário SCS roda em um único projeto na **Vercel**:

| Parte | Onde roda | Como |
|---|---|---|
| PWA (Angular) | CDN da Vercel | `ng build`, pasta `frontend/dist/web/browser` |
| API (FastAPI) | Função Python serverless | `api/index.py` carrega `backend/app` e responde em `/api/*` |
| Banco de dados | PostgreSQL gerenciado (Neon, integração da Vercel) | variável `DATABASE_URL` criada pela integração |

Configuração em [`vercel.json`](../vercel.json). Como a API e o app ficam no mesmo domínio, não há CORS a liberar.

## Variáveis de ambiente (Vercel → Settings → Environment Variables)

| Variável | Obrigatória | Para que serve |
|---|---|---|
| `DATABASE_URL` | sim | criada automaticamente ao conectar o Neon em *Storage* |
| `BSS_JWT_SECRET` | sim | chave dos tokens de login, com 32+ caracteres aleatórios (a API não sobe sem ela) |
| `BSS_SEED_EMAIL` / `BSS_SEED_SENHA` | no primeiro deploy | cria o usuário da coordenação, se ainda não existir |
| `BSS_SEED_DEMO` | não | `1` carrega entidades e doações fictícias para demonstração |

Nenhum segredo fica no código. Gere a chave com `python -c "import secrets; print(secrets.token_urlsafe(48))"`.

## Ajustes para rodar em serverless

- Revogação de sessão (logout) e bloqueio após 5 tentativas de login passaram da memória para o banco
  (tabelas `token_revogado` e `falha_login`), porque cada requisição pode cair numa instância diferente.
- Conexões com `pool_pre_ping` e reciclagem a cada 5 minutos, para não usar conexões encerradas pelo Neon.
- `/api/health` testa a API **e** o banco (`SELECT 1`) e devolve HTTP 503 se o banco cair.

## Monitoramento pós-lançamento

1. **Verificação automática** – workflow [`monitoramento.yml`](../.github/workflows/monitoramento.yml) roda a cada
   30 minutos no GitHub Actions: chama `/api/health` e a página inicial, registra o tempo de resposta no resumo da
   execução e, se falhar, deixa o job vermelho (aviso por e-mail) e abre a issue **"Alerta: app fora do ar"**.
2. **Logs e métricas da Vercel** – aba *Logs* (erros da API, que só registram detalhes técnicos no servidor) e
   *Observability* (requisições, duração e erros por rota).
3. **Integração contínua** – a CI testa o adaptador `api/index.py` contra um PostgreSQL real antes de cada merge.
