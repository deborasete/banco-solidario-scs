import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, NgZone, inject, signal } from '@angular/core';
import Dexie, { Table } from 'dexie';
import { firstValueFrom } from 'rxjs';

import { environment } from '../../environments/environment';
import { DoacaoPendente } from './modelos';

class BancoLocal extends Dexie {
  pendentes!: Table<DoacaoPendente, string>;
  constructor() {
    super('banco-solidario-scs');
    this.version(1).stores({ pendentes: 'id_local' });
  }
}

export type ResultadoEnvio = { enviado: true; alertas: string[] } | { enviado: false };

/**
 * Fila offline de doações (RF01).
 * Somente doações ficam na fila: elas apenas somam ao estoque, sem risco de conflito de saldo.
 * O id_local garante que um reenvio não duplica o registro no servidor.
 */
@Injectable({ providedIn: 'root' })
export class FilaOfflineService {
  private http = inject(HttpClient);
  private zone = inject(NgZone);
  private db = new BancoLocal();

  readonly online = signal<boolean>(navigator.onLine);
  readonly pendentes = signal<number>(0);

  constructor() {
    window.addEventListener('online', () => this.zone.run(() => { this.online.set(true); void this.sincronizar(); }));
    window.addEventListener('offline', () => this.zone.run(() => this.online.set(false)));
    void this.atualizarContagem().then(() => this.sincronizar());
  }

  async registrar(doacao: DoacaoPendente): Promise<ResultadoEnvio> {
    await this.db.pendentes.put(doacao);
    await this.atualizarContagem();
    if (!this.online()) return { enviado: false };
    try {
      const alertas = await this.enviar(doacao);
      return { enviado: true, alertas };
    } catch {
      return { enviado: false };
    }
  }

  async sincronizar(): Promise<void> {
    if (!this.online()) return;
    for (const d of await this.db.pendentes.toArray()) {
      try {
        await this.enviar(d);
      } catch {
        break; // tenta de novo quando a conexão voltar
      }
    }
  }

  private async enviar(d: DoacaoPendente): Promise<string[]> {
    try {
      const r = await firstValueFrom(this.http.post<{ alertas: string[] }>(`${environment.apiUrl}/doacoes`, d));
      await this.db.pendentes.delete(d.id_local);
      await this.atualizarContagem();
      return r.alertas ?? [];
    } catch (e) {
      // Erro de validação (422) não se resolve reenviando: tira da fila para não travar as demais.
      if (e instanceof HttpErrorResponse && e.status === 422) {
        await this.db.pendentes.delete(d.id_local);
        await this.atualizarContagem();
      }
      throw e;
    }
  }

  private async atualizarContagem(): Promise<void> {
    const n = await this.db.pendentes.count();
    this.zone.run(() => this.pendentes.set(n));
  }
}
