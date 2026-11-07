import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { environment } from '../../environments/environment';
import { Perfil, Sessao } from './modelos';

const CHAVE = 'bss.sessao';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);
  private router = inject(Router);

  /** Token fica em sessionStorage (some ao fechar o navegador), nunca em cookie sem proteção. */
  readonly sessao = signal<Sessao | null>(this.ler());
  readonly logado = computed(() => this.sessao() !== null);

  private ler(): Sessao | null {
    try {
      const v = sessionStorage.getItem(CHAVE);
      return v ? (JSON.parse(v) as Sessao) : null;
    } catch {
      return null;
    }
  }

  token(): string | null {
    return this.sessao()?.token ?? null;
  }

  temPerfil(...perfis: Perfil[]): boolean {
    const s = this.sessao();
    return !!s && perfis.includes(s.perfil);
  }

  async entrar(email: string, senha: string): Promise<void> {
    const r = await firstValueFrom(
      this.http.post<{ access_token: string; nome: string; perfil: Perfil }>(`${environment.apiUrl}/auth/login`, {
        email,
        senha,
      }),
    );
    const s: Sessao = { token: r.access_token, nome: r.nome, perfil: r.perfil };
    sessionStorage.setItem(CHAVE, JSON.stringify(s));
    this.sessao.set(s);
  }

  async sair(): Promise<void> {
    try {
      await firstValueFrom(this.http.post(`${environment.apiUrl}/auth/logout`, {}));
    } catch {
      /* mesmo sem rede o token é descartado localmente */
    }
    this.limpar();
  }

  limpar(): void {
    sessionStorage.removeItem(CHAVE);
    this.sessao.set(null);
    void this.router.navigateByUrl('/login');
  }
}
