import { classeSelo, separarLotes } from './pages/estoque/estoque.component';
import { campoInvalido, descreverValidade, somarDias, validarItem } from './pages/nova-doacao/nova-doacao.component';
import { Lote } from './core/modelos';

describe('validarItem (RF01)', () => {
  it('exige validade para hortifrúti', () => {
    expect(validarItem({ categoria: 'HORTIFRUTI', quantidade: 12, unidade: 'KG', data_validade: '' }))
      .toBe('Informe a validade: hortifrúti precisa de data.');
  });
  it('aceita não perecível sem validade', () => {
    expect(validarItem({ categoria: 'NAO_PERECIVEL', quantidade: 5, unidade: 'KG', data_validade: '' })).toBeNull();
  });
  it('rejeita quantidade zero', () => {
    expect(validarItem({ categoria: 'NAO_PERECIVEL', quantidade: 0, unidade: 'KG', data_validade: '' }))
      .toContain('quantidade');
  });
});

describe('classeSelo (RF02)', () => {
  const lote = (dias: number | null) => ({ dias_para_vencer: dias }) as Lote;
  it('classifica vencido, urgente e breve', () => {
    expect(classeSelo(lote(-1))).toBe('vencido');
    expect(classeSelo(lote(3))).toBe('urgente');
    expect(classeSelo(lote(6))).toBe('breve');
    expect(classeSelo(lote(null))).toBe('');
  });
});

describe('ajustes da 1ª rodada de validação', () => {
  const sab = new Date(2026, 10, 7); // 07/11/2026, sábado
  it('atalho de +3 dias gera a data sem contar nos dedos', () => {
    expect(somarDias(3, sab)).toBe('2026-11-10');
    expect(somarDias(30, sab)).toBe('2026-12-07');
  });
  it('descreve a validade com dia da semana e distância', () => {
    expect(descreverValidade('2026-11-10', sab)).toBe('terça, 10/11 (daqui a 3 dias)');
    expect(descreverValidade('2026-11-06', sab)).toContain('já vencido');
  });
  it('aponta o campo da validade para levar o foco até ele', () => {
    expect(campoInvalido({ categoria: 'HORTIFRUTI', quantidade: 12, unidade: 'KG', data_validade: '' })).toBe('val');
    expect(campoInvalido({ categoria: null, quantidade: 12, unidade: 'KG', data_validade: '' })).toBe('cat');
  });
  it('aceita "Outros" (pão, ovos) sem validade obrigatória', () => {
    expect(validarItem({ categoria: 'OUTROS', quantidade: 30, unidade: 'UNIDADE', data_validade: '' })).toBeNull();
  });
  it('separa vencidos dos lotes que ainda podem sair', () => {
    const l = (id: string, dias: number | null) => ({ id, dias_para_vencer: dias }) as Lote;
    const g = separarLotes([l('a', -1), l('b', 3), l('c', 3), l('d', null)]);
    expect(g.vencidos.map((x) => x.id)).toEqual(['a']);
    expect(g.aSair.map((x) => x.id)).toEqual(['b', 'c', 'd']);
  });
});
