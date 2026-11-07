# Regras de negócio (documentação mínima viável)

1. Toda doação tem pelo menos um item, um canal de origem e quem a registrou.
2. Itens de hortifrúti, laticínios e proteína exigem data de validade.
3. A mesma doação não é gravada duas vezes: o `id_local` gerado no celular é único (fila offline).
4. O estoque mostra primeiro os lotes que vencem antes; lotes sem validade vão para o fim.
5. Alerta de validade: "Vencido" (data passada), "Vence hoje" ou "Vence em N dias" quando N ≤ 7.
6. Uma retirada nunca deixa o saldo de um lote negativo; a operação é atômica (tudo ou nada).
7. Lote com saldo zero passa a ESGOTADO; descarte exige motivo e zera o saldo (alimenta o indicador de perdas).
8. Apenas entidades ativas recebem retiradas; entidades não são excluídas, apenas desativadas.
9. Perfis: VOLUNTARIO registra doações e consulta estoque; COORDENACAO faz tudo; ENTIDADE vê só as próprias retiradas.
10. Não são coletados dados das famílias atendidas nem CPF de voluntários (minimização de dados / LGPD).

## Ajustes após a 1ª rodada de validação (07/11/2026)

| Observação na sessão | Ajuste |
|---|---|
| Salvou sem validade e levou ~6 s rolando a tela para achar o aviso | Resumo do que falta junto do botão *Salvar* e foco/rolagem automáticos até o primeiro campo com erro |
| Contou os dias nos dedos para chegar a "+3 dias" | Atalhos de validade (3, 7, 15 e 30 dias) e texto "terça, 10/11 (daqui a 3 dias)" |
| Pão e ovos sem lugar claro | Categoria **Outros** (pão, ovos e o que não couber acima), validade opcional |
| "Tudo enviado o quê? Eu não mandei nada ainda." | Status passa a dizer "Conectado à internet" e "Nenhuma doação aguardando envio"; a tela *Nova doação* também mostra a conexão |
| "Só fala o peso?" | Dica: "Informe o peso em kg ou o número de unidades" |
| Apontou o lote vencido por estar no topo; travou entre dois lotes iguais | Estoque separa **Vencidos: não entregar** de **Próximos a sair**, marca o lote que **sai primeiro** e mostra recebimento, canal e código do lote. Empate de validade: sai primeiro o recebido antes (FIFO) |
