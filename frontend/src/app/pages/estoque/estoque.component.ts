import { HttpClient } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { environment } from '../../../environments/environment';
import { AuthService } from '../../core/auth.service';
import { FilaOfflineService } from '../../core/fila-offline.service';
import { mensagemDeErro } from '../../core/http';
import { CATEGORIAS, Categoria, Estoque, Lote, rotuloCategoria } from '../../core/modelos';

interface Confirmacao {
  enviado: boolean;
  resumo: string;
  alertas: string[];
}

export function classeSelo(l: Lote): string {
  if (l.dias_para_vencer === null) return '';
  if (l.dias_para_vencer < 0) return 'vencido';
  if (l.dias_para_vencer <= 3) return 'urgente';
  return 'breve';
}

/** Tela 3 – Estoque e alertas (RF02): confirmação, saldo por categoria e lotes por validade. */
@Component({
  selector: 'bss-estoque',
  standalone: true,
  imports: [RouterLink],
  template: `
    <header class="topo">
      <a routerLink="/">← Início</a>
      <h1>Estoque</h1>
      <span style="width:56px"></span>
    </header>
    <main>
      @if (confirmacao) {
        <div class="faixa" [class.ok]="confirmacao.enviado" [class.offline]="!confirmacao.enviado" role="status">
          <span class="ico" aria-hidden="true" style="color:#fff" [style.background]="confirmacao.enviado ? 'var(--ok)' : '#5f6368'">✓</span>
          <div>
            {{ confirmacao.enviado ? 'Doação registrada' : 'Salvo no celular' }}<br />
            <span style="font-weight:400">
              {{ confirmacao.enviado ? confirmacao.resumo : 'Será enviado quando a internet voltar' }}
            </span>
          </div>
        </div>
      }

      <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px" role="group" aria-label="Filtrar por categoria">
        <label class="opcao"><input type="radio" name="filtro" [checked]="!filtro()" (change)="filtrar(null)" /><span>Todos</span></label>
        @for (c of categoriasPereciveis; track c.valor) {
          <label class="opcao"><input type="radio" name="filtro" [checked]="filtro() === c.valor" (change)="filtrar(c.valor)" /><span>{{ c.rotulo }}</span></label>
        }
      </div>

      @if (erro()) { <div class="faixa erro" role="alert">{{ erro() }}</div> }

      @if (estoque(); as e) {
        <div class="cartao" style="display:flex;flex-wrap:wrap;gap:16px;justify-content:space-between">
          @for (r of e.resumo; track r.categoria + r.unidade) {
            <div><div class="sec">{{ rotulo(r.categoria) }}</div><strong>{{ r.saldo_total }} {{ r.unidade === 'KG' ? 'kg' : 'un' }}</strong></div>
          } @empty { <span class="sec">Nenhum item em estoque.</span> }
        </div>

        <h2 style="font-size:1.05rem;margin:14px 0 8px">Vencem primeiro</h2>
        <ul style="list-style:none;padding:0;margin:0">
          @for (l of e.vencem_primeiro; track l.id) {
            <li class="cartao">
              <div style="display:flex;justify-content:space-between;align-items:center;gap:8px">
                <strong>{{ l.descricao || rotulo(l.categoria) }} · {{ l.saldo }} {{ l.unidade === 'KG' ? 'kg' : 'un' }}</strong>
                @if (l.alerta) {
                  <span class="selo" [class]="'selo ' + classe(l)">
                    <span aria-hidden="true">{{ classe(l) === 'vencido' ? '✕' : classe(l) === 'urgente' ? '!' : '◷' }}</span>{{ l.alerta }}
                  </span>
                }
              </div>
              <div class="sec">{{ l.data_validade ? 'Validade ' + formatar(l.data_validade) : 'Sem validade' }}</div>
            </li>
          }
        </ul>
        @if (e.total_lotes > e.pagina * e.por_pagina) {
          <button class="btn" type="button" style="background:none;color:var(--azul)" (click)="maisPagina()">Mostrar mais</button>
        }
      } @else if (!erro()) {
        <p class="sec">{{ fila.online() ? 'Carregando…' : 'Sem internet: o estoque será atualizado quando a conexão voltar.' }}</p>
      }
    </main>
    <div class="rodape-fixo">
      <a class="btn btn-secundario" routerLink="/doacoes/nova" style="flex:1">+ Nova doação</a>
      @if (auth.temPerfil('COORDENACAO')) {
        <a class="btn btn-principal" routerLink="/" style="flex:1;font-size:1rem" title="Fluxo de retirada (RF04) via API">Registrar retirada</a>
      }
    </div>
  `,
})
export class EstoqueComponent implements OnInit {
  auth = inject(AuthService);
  fila = inject(FilaOfflineService);
  private http = inject(HttpClient);
  confirmacao: Confirmacao | null = inject(Router).getCurrentNavigation()?.extras.state?.['confirmacao'] ?? null;

  categoriasPereciveis = CATEGORIAS.filter((c) => c.perecivel);
  estoque = signal<Estoque | null>(null);
  filtro = signal<Categoria | null>(null);
  pagina = signal(1);
  erro = signal('');

  ngOnInit(): void {
    this.carregar();
  }
  rotulo = rotuloCategoria;
  classe = classeSelo;

  formatar(iso: string): string {
    const [a, m, d] = iso.split('-');
    return `${d}/${m}/${a}`;
  }
  filtrar(c: Categoria | null): void {
    this.filtro.set(c);
    this.pagina.set(1);
    this.carregar();
  }
  maisPagina(): void {
    this.pagina.update((p) => p + 1);
    this.carregar();
  }

  private carregar(): void {
    if (!this.fila.online()) return;
    const params: Record<string, string> = { pagina: '1', por_pagina: String(50 * this.pagina()) };
    const f = this.filtro();
    if (f) params['categoria'] = f;
    this.http.get<Estoque>(`${environment.apiUrl}/estoque`, { params }).subscribe({
      next: (e) => { this.erro.set(''); this.estoque.set(e); },
      error: (e) => this.erro.set(mensagemDeErro(e)),
    });
  }
}
