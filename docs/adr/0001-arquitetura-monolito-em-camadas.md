# ADR 0001 – Cliente-servidor com back-end monolítico em camadas

**Status:** aceito

**Contexto:** desenvolvimento individual, cerca de 30 entidades e poucos usuários simultâneos; necessidade de
testar regras de negócio com facilidade e de permitir modo offline no celular.

**Decisão:** front-end PWA separado (cliente) e um único back-end FastAPI organizado em rotas → serviços → dados.

**Alternativas consideradas:** microsserviços (complexidade operacional sem ganho no volume atual); aplicação
monolítica com páginas renderizadas no servidor (dificulta o modo offline).

**Consequências:** um único deploy e um único repositório; regras testáveis sem banco; possibilidade futura de
extrair módulos (ex.: campanhas) se o sistema crescer.
