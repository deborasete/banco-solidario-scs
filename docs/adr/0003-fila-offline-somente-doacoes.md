# ADR 0003 – Fila offline apenas para doações

**Status:** aceito

**Contexto:** o galpão tem internet instável; retiradas feitas offline em dois aparelhos poderiam baixar o mesmo
lote duas vezes.

**Decisão:** somente o registro de doações (que apenas soma ao estoque) funciona sem internet, usando IndexedDB
(Dexie) e reenvio automático ao reconectar. O `id_local` torna o envio idempotente. Retiradas exigem conexão e o
servidor valida o saldo em transação.

**Consequências:** nenhum conflito de saldo; a coordenação precisa de conexão para registrar retiradas.
