import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { FilaOfflineService } from '../../core/fila-offline.service';
import { CANAIS, CATEGORIAS, Canal, Categoria, ItemDoacao, Unidade, ehPerecivel } from '../../core/modelos';

interface ItemForm {
  categoria: Categoria | null;
  quantidade: number | null;
  unidade: Unidade;
  data_validade: string;
}

type CampoItem = 'cat' | 'qtd' | 'val';

/** Atalhos de validade (feedback da 1ª rodada: a pessoa contava os dias nos dedos). */
export const ATALHOS_VALIDADE = [3, 7, 15, 30];

/** Data local (AAAA-MM-DD) somando `dias` a `base`, sem deslocamento de fuso. */
export function somarDias(dias: number, base: Date = new Date()): string {
  const d = new Date(base.getFullYear(), base.getMonth(), base.getDate() + dias);
  const p = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

/** Texto amigável da validade escolhida, por exemplo "terça, 10/11 (daqui a 3 dias)". */
export function descreverValidade(iso: string, hoje: Date = new Date()): string {
  if (!iso) return '';
  const [a, m, d] = iso.split('-').map(Number);
  const data = new Date(a, m - 1, d);
  const base = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate());
  const dias = Math.round((data.getTime() - base.getTime()) / 86_400_000);
  const semana = data.toLocaleDateString('pt-BR', { weekday: 'long' }).replace('-feira', '');
  const quando = dias === 0 ? 'vence hoje' : dias === 1 ? 'amanhã' : dias < 0 ? 'já vencido' : `daqui a ${dias} dias`;
  return `${semana}, ${String(d).padStart(2, '0')}/${String(m).padStart(2, '0')} (${quando})`;
}

/** Campo do item que tem erro, na ordem em que aparecem na tela. */
export function campoInvalido(i: ItemForm): CampoItem | null {
  if (!i.categoria) return 'cat';
  if (!i.quantidade || i.quantidade <= 0) return 'qtd';
  if (ehPerecivel(i.categoria) && !i.data_validade) return 'val';
  return null;
}

export function validarItem(i: ItemForm): string | null {
  switch (campoInvalido(i)) {
    case 'cat':
      return 'Escolha a categoria do item.';
    case 'qtd':
      return 'Informe uma quantidade maior que zero.';
    case 'val': {
      const nome = CATEGORIAS.find((c) => c.valor === i.categoria)?.rotulo.toLowerCase();
      return `Informe a validade: ${nome} precisa de data.`;
    }
    default:
      return null;
  }
}

/** Tela 2 – Nova doação (RF01). Escolhas por botões grandes; validade obrigatória para perecíveis. */
@Component({
  selector: 'bss-nova-doacao',
  standalone: true,
  imports: [FormsModule, RouterLink],
  template: `
    <header class="topo">
      <a routerLink="/">← Voltar</a>
      <h1>Nova doação</h1>
      <span style="width:56px"></span>
    </header>
    <main>
      <p class="status-conexao" role="status">
        <span aria-hidden="true">{{ fila.online() ? '●' : '○' }}</span>
        {{ fila.online() ? 'Conectado: a doação é enviada ao salvar.' : 'Sem internet: a doação fica salva no celular e é enviada depois.' }}
      </p>
      <form (ngSubmit)="salvar()" novalidate>
        <fieldset id="canal" tabindex="-1">
          <legend>Canal de origem</legend>
          <p class="dica">Toque em uma opção para marcar.</p>
          <div class="grade">
            @for (c of canais; track c.valor) {
              <label class="opcao">
                <input type="radio" name="canal" [value]="c.valor" [(ngModel)]="canal" />
                <span>{{ c.rotulo }}</span>
              </label>
            }
          </div>
          @if (tentouSalvar() && !canal) { <div class="msg-erro" role="alert">⚠ Escolha o canal de origem.</div> }
        </fieldset>

        @for (item of itens; track $index; let i = $index) {
          <fieldset [id]="'cat' + i" tabindex="-1">
            <legend>Categoria do item {{ i + 1 }}</legend>
            <div class="grade">
              @for (c of categorias; track c.valor) {
                <label class="opcao">
                  <input type="radio" [name]="'cat' + i" [value]="c.valor" [(ngModel)]="item.categoria" />
                  <span>
                    <span aria-hidden="true">{{ c.icone }}</span>
                    <span class="opcao-texto">{{ c.rotulo }}@if (c.dica) {<small>{{ c.dica }}</small>}</span>
                  </span>
                </label>
              }
            </div>
            @if (erroNo(item, 'cat')) { <div class="msg-erro" role="alert">⚠ {{ erroItem(item) }}</div> }
          </fieldset>

          <label class="rotulo" [for]="'qtd' + i" style="margin-top:14px">Quantidade</label>
          <p class="dica" [id]="'qtd-dica' + i">Informe o peso em kg ou o número de unidades.</p>
          <div style="display:flex;gap:8px">
            <input class="campo" [id]="'qtd' + i" [name]="'qtd' + i" type="number" inputmode="decimal" min="0.01" step="0.01"
                   [(ngModel)]="item.quantidade" style="flex:1" [class.invalido]="erroNo(item, 'qtd')"
                   [attr.aria-describedby]="'qtd-dica' + i" />
            <label class="opcao" style="width:84px">
              <input type="radio" [name]="'un' + i" value="KG" [(ngModel)]="item.unidade" /><span style="justify-content:center">kg</span>
            </label>
            <label class="opcao" style="width:84px">
              <input type="radio" [name]="'un' + i" value="UNIDADE" [(ngModel)]="item.unidade" /><span style="justify-content:center">unid.</span>
            </label>
          </div>
          @if (erroNo(item, 'qtd')) { <div class="msg-erro" role="alert">⚠ {{ erroItem(item) }}</div> }

          <label class="rotulo" [for]="'val' + i" style="margin-top:14px">
            Data de validade{{ perecivel(item) ? ' (obrigatória para perecíveis)' : ' (opcional)' }}
          </label>
          <div class="atalhos" role="group" [attr.aria-label]="'Atalhos de validade do item ' + (i + 1)">
            <span class="dica">Vence em:</span>
            @for (d of atalhos; track d) {
              <button type="button" class="chip" [class.ativo]="item.data_validade === dataEm(d)"
                      [attr.aria-pressed]="item.data_validade === dataEm(d)" (click)="item.data_validade = dataEm(d)">
                {{ d }} dias
              </button>
            }
          </div>
          <input class="campo" [id]="'val' + i" [name]="'val' + i" type="date" [(ngModel)]="item.data_validade"
                 [class.invalido]="erroNo(item, 'val')"
                 [attr.aria-describedby]="erroNo(item, 'val') ? 'erro' + i : null" />
          @if (item.data_validade) { <p class="dica">{{ descrever(item.data_validade) }}</p> }
          @if (erroNo(item, 'val')) {
            <div class="msg-erro" [id]="'erro' + i" role="alert">⚠ {{ erroItem(item) }}</div>
          }
        }

        <button type="button" class="btn" style="background:none;color:var(--azul);justify-content:flex-start;min-height:48px"
                (click)="adicionarItem()">+ Adicionar outro item</button>

        <div class="rodape-fixo rodape-coluna">
          @if (tentouSalvar() && pendencias().length) {
            <button type="button" class="resumo-erro" role="alert" (click)="irParaPrimeiroErro()">
              ⚠ Falta: {{ pendencias().join('; ') }}. <u>Corrigir</u>
            </button>
          }
          <button class="btn btn-principal" type="submit" [disabled]="salvando()">
            {{ salvando() ? 'Salvando…' : 'Salvar doação' }}
          </button>
        </div>
      </form>
    </main>
  `,
})
export class NovaDoacaoComponent {
  fila = inject(FilaOfflineService);
  private router = inject(Router);

  canais = CANAIS;
  categorias = CATEGORIAS;
  atalhos = ATALHOS_VALIDADE;
  canal: Canal | null = null;
  itens: ItemForm[] = [this.novoItem()];
  tentouSalvar = signal(false);
  salvando = signal(false);

  novoItem(): ItemForm {
    return { categoria: null, quantidade: null, unidade: 'KG', data_validade: '' };
  }
  adicionarItem(): void {
    this.itens.push(this.novoItem());
  }
  perecivel(i: ItemForm): boolean {
    return ehPerecivel(i.categoria);
  }
  erroItem(i: ItemForm): string | null {
    return validarItem(i);
  }
  erroNo(i: ItemForm, campo: CampoItem): boolean {
    return this.tentouSalvar() && campoInvalido(i) === campo;
  }
  dataEm(dias: number): string {
    return somarDias(dias);
  }
  descrever(iso: string): string {
    return descreverValidade(iso);
  }

  /** Lista curta do que falta, mostrada junto do botão Salvar (sempre visível). */
  pendencias(): string[] {
    const nomes: Record<CampoItem, string> = { cat: 'categoria', qtd: 'quantidade', val: 'validade' };
    const lista: string[] = [];
    if (!this.canal) lista.push('canal de origem');
    this.itens.forEach((item, i) => {
      const c = campoInvalido(item);
      if (c) lista.push(`${nomes[c]} do item ${i + 1}`);
    });
    return lista;
  }

  /** Rola até o primeiro campo com erro e coloca o foco nele. */
  irParaPrimeiroErro(): void {
    let id: string | null = this.canal ? null : 'canal';
    if (!id) {
      const i = this.itens.findIndex((item) => campoInvalido(item));
      if (i >= 0) id = `${campoInvalido(this.itens[i])}${i}`;
    }
    const el = id ? document.getElementById(id) : null;
    el?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    el?.focus({ preventScroll: true });
  }

  async salvar(): Promise<void> {
    this.tentouSalvar.set(true);
    if (this.pendencias().length) {
      setTimeout(() => this.irParaPrimeiroErro());
      return;
    }
    this.salvando.set(true);
    const itens: ItemDoacao[] = this.itens.map((i) => ({
      categoria: i.categoria as Categoria,
      unidade: i.unidade,
      quantidade: String(i.quantidade),
      data_validade: i.data_validade || null,
    }));
    const resultado = await this.fila.registrar({
      id_local: crypto.randomUUID(),
      canal: this.canal as Canal,
      itens,
      data_recebimento: new Date().toISOString(),
    });
    this.salvando.set(false);
    const resumo = itens.map((i) => `${i.quantidade} ${i.unidade === 'KG' ? 'kg' : 'un'}`).join(', ');
    await this.router.navigate(['/estoque'], {
      state: { confirmacao: { enviado: resultado.enviado, resumo, alertas: resultado.enviado ? resultado.alertas : [] } },
    });
  }
}
