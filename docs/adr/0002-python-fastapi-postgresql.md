# ADR 0002 – Python + FastAPI + PostgreSQL

**Status:** aceito

**Decisão:** Python 3.12 (padrão autorizado pela disciplina) com FastAPI, Pydantic e SQLAlchemy; PostgreSQL 16
gerenciado em plano gratuito.

**Motivos:** validação declarativa na entrada (Pydantic), documentação OpenAPI automática (documentação mínima
viável), ORM com consultas parametrizadas (prevenção de injeção de SQL), transações e restrições CHECK para
garantir que o saldo nunca fique negativo.

**Consequências:** SQLite é usado só em testes e desenvolvimento rápido; produção exige PostgreSQL. Migrações
com Alembic ficam para a próxima iteração (hoje as tabelas são criadas a partir dos modelos).
