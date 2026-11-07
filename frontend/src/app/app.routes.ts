import { Routes } from '@angular/router';

import { somenteLogado } from './core/http';
import { EstoqueComponent } from './pages/estoque/estoque.component';
import { InicioComponent } from './pages/inicio/inicio.component';
import { LoginComponent } from './pages/login/login.component';
import { NovaDoacaoComponent } from './pages/nova-doacao/nova-doacao.component';

export const routes: Routes = [
  { path: 'login', component: LoginComponent, title: 'Entrar – Banco Solidário SCS' },
  { path: '', component: InicioComponent, canActivate: [somenteLogado], title: 'Início – Banco Solidário SCS' },
  { path: 'doacoes/nova', component: NovaDoacaoComponent, canActivate: [somenteLogado], title: 'Nova doação – Banco Solidário SCS' },
  { path: 'estoque', component: EstoqueComponent, canActivate: [somenteLogado], title: 'Estoque – Banco Solidário SCS' },
  { path: '**', redirectTo: '' },
];
