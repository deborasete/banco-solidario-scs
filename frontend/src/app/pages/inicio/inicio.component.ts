import { HttpClient } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { environment } from '../../../environments/environment';
import { AuthService } from '../../core/auth.service';
import { FilaOfflineService } from '../../core/fila-offline.service';
import { Estoque } from '../../core/modelos';

/** Tela 1 – Início: acesso destacado à função prioritária "Nova doação". */
@Component({
  selector: 'bss-inicio',
  standalone: true,
  imports: [RouterLink],
  template: `
    <header class="topo">
      <div>
        <h1>Banco Solidário SCS</h1>
        <div class="sub">Olá, {{ auth.sessao()?.nome }} · {{ perfilTexto() }}</div>
      </div>
      <button class="link" type="button" (click)="auth.sair()">Sair</button>
    </header>
    <main>
      <div class="faixa" [class.offline]="!fila.online()" [class.ok]="fila.online()" role="status">
        <span class="ico" aria-hidden="true" [style.background]="fila.online() ? 'var(--ok)' : '#5f6368'" style="color:#fff">
          {{ fila.online() ? '✓' : '!' }}
        </span>
        <div>
          {{ fila.online() ? 'Online' : 'Sem internet' }}<br />
          <span style="font-weight:400">
            @if (fila.pendentes() > 0) { {{ fila.pendentes() }} doação(ões) aguardando envio }
            @else { Tudo enviado }
          </span>
        </div>
      </div>

      <a class="btn btn-principal" routerLink="/doacoes/nova" style="min-height:72px;font-size:1.3rem">
        <span class="ico" aria-hidden="true" style="background:#fff;color:var(--azul)">+</span>Nova doação
      </a>
      <div style="height:12px"></div>
      <a class="btn btn-secundario" routerLink="/estoque">Estoque</a>

      @if (vencendo() > 0) {
        <div class="faixa aviso" style="margin-top:24px;display:block">
          <div style="display:flex;gap:10px;align-items:center">
            <span class="ico" aria-hidden="true" style="background:var(--aviso);color:#fff">!</span>
            {{ vencendo() }} lote(s) vencem em até 7 dias
          </div>
          <a routerLink="/estoque" style="display:inline-flex;min-height:44px;align-items:center;margin-left:36px;color:var(--aviso-texto);font-weight:700">Ver estoque →</a>
        </div>
      }
      @if (!auth.temPerfil('COORDENACAO')) {
        <p class="sec">Retiradas e entidades ficam disponíveis apenas para a coordenação.</p>
      }
    </main>
  `,
})
export class InicioComponent implements OnInit {
  auth = inject(AuthService);
  fila = inject(FilaOfflineService);
  private http = inject(HttpClient);
  vencendo = signal(0);

  perfilTexto(): string {
    const p = this.auth.sessao()?.perfil;
    return p === 'COORDENACAO' ? 'Coordenação' : p === 'ENTIDADE' ? 'Entidade' : 'Voluntária(o)';
  }

  ngOnInit(): void {
    if (!this.fila.online()) return;
    this.http.get<Estoque>(`${environment.apiUrl}/estoque`).subscribe({
      next: (e) =>
        this.vencendo.set(e.vencem_primeiro.filter((l) => l.dias_para_vencer !== null && l.dias_para_vencer >= 0 && l.dias_para_vencer <= 7).length),
      error: () => this.vencendo.set(0),
    });
  }
}
