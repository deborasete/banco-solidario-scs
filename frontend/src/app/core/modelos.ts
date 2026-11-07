export type Perfil = 'VOLUNTARIO' | 'COORDENACAO' | 'ENTIDADE';
export type Canal = 'SEDE' | 'DRIVE_THRU' | 'EVENTO' | 'CAMPANHA' | 'OUTRO';
export type Categoria =
  | 'NAO_PERECIVEL' | 'HORTIFRUTI' | 'LATICINIOS' | 'PROTEINA' | 'HIGIENE_LIMPEZA' | 'RACAO' | 'OUTROS';
export type Unidade = 'KG' | 'UNIDADE';

export const CANAIS: { valor: Canal; rotulo: string }[] = [
  { valor: 'SEDE', rotulo: 'Sede' },
  { valor: 'DRIVE_THRU', rotulo: 'Drive-thru' },
  { valor: 'EVENTO', rotulo: 'Evento' },
  { valor: 'CAMPANHA', rotulo: 'Campanha' },
];

export const CATEGORIAS: { valor: Categoria; rotulo: string; icone: string; perecivel: boolean; dica?: string }[] = [
  { valor: 'NAO_PERECIVEL', rotulo: 'Não perecível', icone: '🥫', perecivel: false },
  { valor: 'HORTIFRUTI', rotulo: 'Hortifrúti', icone: '🥕', perecivel: true },
  { valor: 'LATICINIOS', rotulo: 'Laticínios', icone: '🥛', perecivel: true },
  { valor: 'PROTEINA', rotulo: 'Proteína', icone: '🍗', perecivel: true },
  { valor: 'HIGIENE_LIMPEZA', rotulo: 'Higiene/Limpeza', icone: '🧴', perecivel: false },
  { valor: 'RACAO', rotulo: 'Ração', icone: '🐾', perecivel: false },
  // Feedback da 1ª rodada: pão e ovos não tinham lugar claro.
  { valor: 'OUTROS', rotulo: 'Outros', icone: '📦', perecivel: false, dica: 'pão, ovos e o que não couber acima' },
];

export function rotuloCanal(c: Canal | null | undefined): string {
  return CANAIS.find((x) => x.valor === c)?.rotulo ?? 'Outro canal';
}

export function rotuloCategoria(c: Categoria): string {
  return CATEGORIAS.find((x) => x.valor === c)?.rotulo ?? 'Outros';
}

export function ehPerecivel(c: Categoria | null): boolean {
  return !!c && !!CATEGORIAS.find((x) => x.valor === c)?.perecivel;
}

export interface ItemDoacao {
  categoria: Categoria;
  unidade: Unidade;
  quantidade: string;
  data_validade?: string | null;
  descricao?: string | null;
}

export interface DoacaoPendente {
  id_local: string;
  canal: Canal;
  itens: ItemDoacao[];
  data_recebimento: string;
}

export interface Lote {
  id: string;
  categoria: Categoria;
  descricao: string | null;
  unidade: Unidade;
  saldo: string;
  data_validade: string | null;
  dias_para_vencer: number | null;
  alerta: string | null;
  data_recebimento?: string | null;
  canal?: Canal | null;
}

export interface Estoque {
  resumo: { categoria: Categoria; unidade: Unidade; saldo_total: string }[];
  vencem_primeiro: Lote[];
  total_lotes: number;
  pagina: number;
  por_pagina: number;
}

export interface Sessao {
  token: string;
  nome: string;
  perfil: Perfil;
}
