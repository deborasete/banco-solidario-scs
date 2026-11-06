## O que este PR faz
<!-- Descreva a mudança e a história de usuário / requisito atendido (ex.: RF01, RNF04). -->

## Como testar
- [ ] `pytest` no back-end
- [ ] `npx ng test --watch=false` no front-end
- [ ] Testado manualmente no celular (ou emulação mobile)

## Checklist de auto-revisão
- [ ] O código segue a arquitetura em camadas (rotas → serviços → dados)
- [ ] Novas regras de negócio têm teste unitário
- [ ] Nenhum segredo, senha ou dado pessoal real foi incluído
- [ ] Entradas são validadas no servidor (Pydantic) e nada é concatenado em SQL
- [ ] Textos e alertas novos usam texto + ícone, não só cor (RNF04)
- [ ] Documentação mínima atualizada (README, ADR ou regras de negócio), se necessário
