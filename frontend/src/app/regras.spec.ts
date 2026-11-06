import { classeSelo } from './pages/estoque/estoque.component';
import { validarItem } from './pages/nova-doacao/nova-doacao.component';
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
