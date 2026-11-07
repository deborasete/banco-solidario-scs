import { HttpClient } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { NgTemplateOutlet } from '@angular/common';
import { Router, RouterLink } from '@angular/router';

import { environment } from '../../../environments/environment';
import { AuthService } from '../../core/auth.service';
import { FilaOfflineService } from '../../core/fila-offline.service';
import { mensagemDeErro } from '../../core/http';
import { CATEGORIAS, Categoria, Estoque, Lote, rotuloCanal, rotuloCategoria } from '../../core/modelos';

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

/** Separa os vencidos (descartar) dos lotes que ainda podem sair, mantendo a ordem da API. */
export function separarLotes(lotes: Lote[]): { vencidos: Lote[]; aSair: Lote[] } {
  const vencido = (l: Lote) => l.dias_para_vencer !== null && l.dias_para_vencer < 0;
  return { vencidos: lotes.filter(vencido), aSair: lotes.filter((l) => !vencido(l)) };
}

/** Tela 3 – Estoque e alertas (RF02): confirmação, saldo por categoria e lotes por validade. */
@Component({
  selector: 'bss-estoque',
  standalone: true,
  imports: [RouterLink, NgTemplateOutlet],
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

        @if (separar(e.vencem_primeiro); as g) {
          @if (g.vencidos.length) {
            <section class="secao-vencidos" aria-labelledby="tit-vencidos">
              <h2 id="tit-vencidos" style="font-size:1.05rem;margin:14px 0 4px">Vencidos: não entregar</h2>
              <p class="dica">Separe para descarte. Estes lotes não devem sair para as entidades.</p>
              <ul style="list-style:none;padding:0;margin:0">
                @for (l of g.vencidos; track l.id) {
                  <ng-container *ngTemplateOutlet="cartaoLote; context: { $implicit: l, primeiro: false }" />
                }
              </ul>
            </section>
          }
          <h2 style="font-size:1.05rem;margin:14px 0 4px">Próximos a sair</h2>
          <p class="dica">O primeiro da lista é o que deve sair primeiro.</p>
          <ul style="list-style:none;padding:0;margin:0">
            @for (l of g.aSair; track l.id; let primeiro = $first) {
              <ng-container *ngTemplateOutlet="cartaoLote; context: { $implicit: l, primeiro: primeiro }" />
            } @empty { <li class="sec">Nenhum lote disponível.</li> }
          </ul>
        }

        <ng-template #cartaoLote let-l let-primeiro="primeiro">
          <li class="cartao">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap">
              <strong>{{ l.descricao || rotulo(l.categoria) }} · {{ l.saldo }} {{ l.unidade === 'KG' ? 'kg' : 'un' }}</strong>
              @if (primeiro) { <span class="selo primeiro"><span aria-hidden="true">➜</span>Sai primeiro</span> }
              @if (l.alerta) {
                <span class="selo" [class]="'selo ' + classe(l)">
                  <span aria-hidden="true">{{ classe(l) === 'vencido' ? '✕' : classe(l) === 'urgente' ? '!' : '◷' }}</span>{{ l.alerta }}
                </span>
              }
            </div>
            <div class="lote-info">
              <span>{{ l.data_validade ? 'Validade ' + formatar(l.data_validade) : 'Sem validade' }}</span>
              @if (l.data_recebimento) { <span>Recebido {{ formatarRecebimento(l.data_recebimento) }}</span> }
              @if (l.canal) { <span>{{ canal(l.canal) }}</span> }
              <span>Lote {{ l.id.slice(0, 4).toUpperCase() }}</span>
            </div>
          </li>
        </ng-template>
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
  confirmacao: Confirmacao | null = inject(Router).currentNavigation()?.extras.state?.['confirmacao'] ?? null;

  categoriasPereciveis = CATEGORIAS.filter((c) => c.perecivel);
  estoque = signal<Estoque | null>(null);
  filtro = signal<Categoria | null>(null);
  pagina = signal(1);
  erro = signal('');

  ngOnInit(): void {
    this.carregar();
  }
  rotulo = rotuloCategoria;
  canal = rotuloCanal;
  classe = classeSelo;
  separar = separarLotes;

  formatarRecebimento(iso: string): string {
    const d = new Date(iso);
    const p = (n: number) => String(n).padStart(2, '0');
    return `${p(d.getDate())}/${p(d.getMonth() + 1)} às ${p(d.getHours())}h${p(d.getMinutes())}`;
  }

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
