import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { AuthService } from '../../core/auth.service';
import { mensagemDeErro } from '../../core/http';

@Component({
  selector: 'bss-login',
  standalone: true,
  imports: [FormsModule],
  template: `
    <header class="topo"><h1>Banco Solidário SCS</h1></header>
    <main>
      <h2 style="margin:8px 0 16px">Entrar</h2>
      <form (ngSubmit)="entrar()" novalidate>
        <label class="rotulo" for="email">E-mail</label>
        <input id="email" name="email" class="campo" type="email" autocomplete="username" required
               [(ngModel)]="email" />
        <label class="rotulo" for="senha" style="margin-top:14px">Senha</label>
        <input id="senha" name="senha" class="campo" type="password" autocomplete="current-password" required
               [(ngModel)]="senha" />
        @if (erro()) {
          <div class="faixa erro" role="alert" style="margin-top:14px">
            <span class="ico" aria-hidden="true" style="background:var(--erro);color:#fff">!</span>{{ erro() }}
          </div>
        }
        <button class="btn btn-principal" type="submit" style="margin-top:20px" [disabled]="enviando()">
          {{ enviando() ? 'Entrando…' : 'Entrar' }}
        </button>
      </form>
    </main>
  `,
})
export class LoginComponent {
  private auth = inject(AuthService);
  private router = inject(Router);
  email = '';
  senha = '';
  erro = signal('');
  enviando = signal(false);

  async entrar(): Promise<void> {
    this.erro.set('');
    if (!this.email || !this.senha) {
      this.erro.set('Informe e-mail e senha.');
      return;
    }
    this.enviando.set(true);
    try {
      await this.auth.entrar(this.email.trim(), this.senha);
      this.senha = '';
      await this.router.navigateByUrl('/');
    } catch (e) {
      this.erro.set(mensagemDeErro(e));
    } finally {
      this.enviando.set(false);
    }
  }
}
