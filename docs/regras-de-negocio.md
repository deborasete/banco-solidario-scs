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
