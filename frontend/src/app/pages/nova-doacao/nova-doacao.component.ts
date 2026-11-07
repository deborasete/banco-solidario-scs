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

export function validarItem(i: ItemForm): string | null {
  if (!i.categoria) return 'Escolha a categoria do item.';
  if (!i.quantidade || i.quantidade <= 0) return 'Informe uma quantidade maior que zero.';
  if (ehPerecivel(i.categoria) && !i.data_validade) {
    const nome = CATEGORIAS.find((c) => c.valor === i.categoria)?.rotulo.toLowerCase();
    return `Informe a validade: ${nome} precisa de data.`;
  }
  return null;
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
      <form (ngSubmit)="salvar()" novalidate>
        <fieldset>
          <legend>Canal de origem</legend>
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
          <fieldset>
            <legend>Categoria do item {{ i + 1 }}</legend>
            <div class="grade">
              @for (c of categorias; track c.valor) {
                <label class="opcao">
                  <input type="radio" [name]="'cat' + i" [value]="c.valor" [(ngModel)]="item.categoria" />
                  <span><span aria-hidden="true">{{ c.icone }}</span> {{ c.rotulo }}</span>
                </label>
              }
            </div>
          </fieldset>

          <label class="rotulo" [for]="'qtd' + i" style="margin-top:14px">Quantidade</label>
          <div style="display:flex;gap:8px">
            <input class="campo" [id]="'qtd' + i" [name]="'qtd' + i" type="number" inputmode="decimal" min="0.01" step="0.01"
                   [(ngModel)]="item.quantidade" style="flex:1" />
            <label class="opcao" style="width:84px">
              <input type="radio" [name]="'un' + i" value="KG" [(ngModel)]="item.unidade" /><span style="justify-content:center">kg</span>
            </label>
            <label class="opcao" style="width:84px">
              <input type="radio" [name]="'un' + i" value="UNIDADE" [(ngModel)]="item.unidade" /><span style="justify-content:center">unid.</span>
            </label>
          </div>

          <label class="rotulo" [for]="'val' + i" style="margin-top:14px">
            Data de validade{{ perecivel(item) ? ' (obrigatória para perecíveis)' : ' (opcional)' }}
          </label>
          <input class="campo" [id]="'val' + i" [name]="'val' + i" type="date" [(ngModel)]="item.data_validade"
                 [class.invalido]="tentouSalvar() && erroItem(item)"
                 [attr.aria-describedby]="tentouSalvar() && erroItem(item) ? 'erro' + i : null" />
          @if (tentouSalvar() && erroItem(item)) {
            <div class="msg-erro" [id]="'erro' + i" role="alert">⚠ {{ erroItem(item) }}</div>
          }
        }

        <button type="button" class="btn" style="background:none;color:var(--azul);justify-content:flex-start;min-height:48px"
                (click)="adicionarItem()">+ Adicionar outro item</button>

        <div class="rodape-fixo">
          <button class="btn btn-principal" type="submit" [disabled]="salvando()">
            {{ salvando() ? 'Salvando…' : 'Salvar doação' }}
          </button>
        </div>
      </form>
    </main>
  `,
})
export class NovaDoacaoComponent {
  private fila = inject(FilaOfflineService);
  private router = inject(Router);

  canais = CANAIS;
  categorias = CATEGORIAS;
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

  async salvar(): Promise<void> {
    this.tentouSalvar.set(true);
    if (!this.canal || this.itens.some((i) => validarItem(i))) return;
    this.salvando.set(true);
    const itens: ItemDoacao[] = this.itens.map((i) => ({
      categoria: i.categoria as Categoria,
      unidade: i.unidade,
      quantidade: String(i.quantidade),
      data_validade: i.data_validade || null,
    }));
    const resultado = await this.fila.registrar({
      id_local: crypto.randomUUID(),
      canal: this.canal,
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
