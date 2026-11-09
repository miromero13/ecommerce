import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { toast } from '@spartan-ng/brain/sonner';

import { SessionService } from '../services/session.service';
import { getDefaultRouteForRole } from '../../../core/utils/role-route.util';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmFieldImports } from '../../../components/field/src';
import { HlmInput } from '../../../components/input/src';
import { HlmTabsImports } from '../../../components/tabs/src';

export interface QuickDemoAccount {
  name: string;
  roleTitle: string;
  badge: string;
  badgeClass: string;
  icon: string;
  email: string;
  password: string;
  tab: 'cliente' | 'administrativo';
  category: 'superadmin' | 'tenant_admin' | 'cliente' | 'cadena_suministro' | 'sucursal';
  description: string;
}

@Component({
  selector: 'app-login-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, HlmButton, HlmInput, ...HlmCardImports, ...HlmFieldImports, ...HlmTabsImports],
  templateUrl: './login-page.component.html',
})
export class LoginPageComponent {
  private readonly fb = inject(FormBuilder);
  private readonly session = inject(SessionService);
  private readonly router = inject(Router);

  protected readonly loading = signal(false);
  protected readonly activeTab = signal<'cliente' | 'administrativo'>('cliente');
  protected readonly quickCategory = signal<'todos' | 'superadmin' | 'tenant_admin' | 'cliente' | 'cadena_suministro' | 'sucursal'>('todos');

  // Superadmin destacado
  protected readonly superadminAccount: QuickDemoAccount = {
    name: 'Superadministrador',
    roleTitle: 'Plataforma SaaS Global',
    badge: '👑 SuperAdmin SaaS',
    badgeClass: 'bg-amber-100 text-amber-900 border-amber-300 font-bold',
    icon: '👑',
    email: 'superadmin@fashionstore.com',
    password: 'SuperAdmin2026!',
    tab: 'administrativo',
    category: 'superadmin',
    description: 'Gestión de tenants, planes de suscripción, telemetría y auditoría.',
  };

  protected readonly demoAccounts: QuickDemoAccount[] = [
    // 👑 SUPERADMIN
    this.superadminAccount,

    // 🏢 ADMINS DE TENANT
    {
      name: 'Ayni Moda',
      roleTitle: 'Carolina Vargas (Admin)',
      badge: 'Enterprise · La Paz',
      badgeClass: 'bg-rose-50 text-rose-700 border-rose-200',
      icon: '🏢',
      email: 'carolina.quiroga@ayni-moda.demo.bo',
      password: 'Fashion2026!',
      tab: 'administrativo',
      category: 'tenant_admin',
      description: 'Tienda principal con 4 sucursales, plan Enterprise.',
    },
    {
      name: 'Kantuta Boutique',
      roleTitle: 'Mariana Justiniano (Admin)',
      badge: 'Pro · Santa Cruz',
      badgeClass: 'bg-pink-50 text-pink-700 border-pink-200',
      icon: '👗',
      email: 'mariana.suarez@kantuta-boutique.demo.bo',
      password: 'Fashion2026!',
      tab: 'administrativo',
      category: 'tenant_admin',
      description: 'Boutique en Equipetrol con vestidos y alta costura.',
    },
    {
      name: 'Urbana Denim',
      roleTitle: 'Sergio Antezana (Admin)',
      badge: 'Pro · Cochabamba',
      badgeClass: 'bg-indigo-50 text-indigo-700 border-indigo-200',
      icon: '👖',
      email: 'sergio.claros@urbana-denim.demo.bo',
      password: 'Fashion2026!',
      tab: 'administrativo',
      category: 'tenant_admin',
      description: 'Moda juvenil y vaquera en Cochabamba y Tarija.',
    },
    {
      name: 'Luna Satén',
      roleTitle: 'Verónica Salinas (Admin)',
      badge: 'Básico · Sopocachi',
      badgeClass: 'bg-purple-50 text-purple-700 border-purple-200',
      icon: '🌙',
      email: 'veronica.pinto@luna-saten.demo.bo',
      password: 'Fashion2026!',
      tab: 'administrativo',
      category: 'tenant_admin',
      description: 'Lencería y pijamas finos en La Paz y Oruro.',
    },

    // 🛍️ CLIENTES
    {
      name: 'María Quispe',
      roleTitle: 'Cliente Final',
      badge: 'Cliente · La Paz',
      badgeClass: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      icon: '🛍️',
      email: 'maria.quispe@clientes.demo.bo',
      password: 'Cliente2026!',
      tab: 'cliente',
      category: 'cliente',
      description: 'Historial de compras, puntos y pedidos delivery.',
    },
    {
      name: 'Camila Roca',
      roleTitle: 'Cliente Final',
      badge: 'Cliente · Santa Cruz',
      badgeClass: 'bg-teal-50 text-teal-700 border-teal-200',
      icon: '🛍️',
      email: 'camila.roca@clientes.demo.bo',
      password: 'Cliente2026!',
      tab: 'cliente',
      category: 'cliente',
      description: 'Prendas favoritas en Kantuta Equipetrol.',
    },
    {
      name: 'Daniela Ruiz',
      roleTitle: 'Cliente Final',
      badge: 'Cliente · Cochabamba',
      badgeClass: 'bg-cyan-50 text-cyan-700 border-cyan-200',
      icon: '🛍️',
      email: 'daniela.ruiz@clientes.demo.bo',
      password: 'Cliente2026!',
      tab: 'cliente',
      category: 'cliente',
      description: 'Vestidor virtual con IA y cupones de descuento.',
    },

    // 🚚 REPARTIDOR Y 🏭 PROVEEDOR (Cadena de Suministro y Despacho)
    {
      name: 'Javier Coaquira',
      roleTitle: 'Repartidor / Logística',
      badge: '🚚 Delivery · PIN',
      badgeClass: 'bg-orange-50 text-orange-800 border-orange-300 font-semibold',
      icon: '🚚',
      email: 'javier.mamani@repartidores.demo.bo',
      password: 'Fashion2026!',
      tab: 'administrativo',
      category: 'cadena_suministro',
      description: 'Hoja de ruta y confirmación de entregas con código PIN.',
    },
    {
      name: 'Carlos Mendoza',
      roleTitle: 'Proveedor (Textiles Andinos)',
      badge: '🏭 Proveedor Ayni',
      badgeClass: 'bg-amber-50 text-amber-800 border-amber-300 font-semibold',
      icon: '🏭',
      email: 'carlos.aliaga@ayni-moda-proveedores.demo.bo',
      password: 'Fashion2026!',
      tab: 'administrativo',
      category: 'cadena_suministro',
      description: 'Portal de proveedores, remitos y catálogo de insumos.',
    },

    // 🏬 SUCURSAL OPERATIVA (Encargado y Cajero)
    {
      name: 'Rodrigo Mamani',
      roleTitle: 'Encargado de Sucursal',
      badge: '📦 Encargado · Ayni Central',
      badgeClass: 'bg-blue-50 text-blue-700 border-blue-200',
      icon: '📦',
      email: 'rodrigo.choque@ayni-moda.demo.bo',
      password: 'Fashion2026!',
      tab: 'administrativo',
      category: 'sucursal',
      description: 'Ingesta OCR/RPA de facturas y traspasos de stock.',
    },
    {
      name: 'Lucía Condori',
      roleTitle: 'Cajera Punto de Venta',
      badge: '💵 Cajero POS · Tienda',
      badgeClass: 'bg-violet-50 text-violet-700 border-violet-200',
      icon: '💵',
      email: 'lucia.apaza@ayni-moda.demo.bo',
      password: 'Fashion2026!',
      tab: 'administrativo',
      category: 'sucursal',
      description: 'Ventas en tienda física, emisión de tickets y modo offline.',
    },
  ];

  protected readonly filteredAccounts = computed(() => {
    const cat = this.quickCategory();
    if (cat === 'todos') {
      return this.demoAccounts;
    }
    return this.demoAccounts.filter((acc) => acc.category === cat);
  });

  protected readonly form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required]],
  });

  protected selectTab(tab: string): void {
    this.activeTab.set(tab as 'cliente' | 'administrativo');
  }

  protected normalizeEmailInput(event: Event): void {
    const input = event.target as HTMLInputElement | null;
    if (!input) return;

    const value = input.value.trim().toLowerCase();
    this.form.controls.email.setValue(value, { emitEvent: false });
  }

  protected async quickLogin(account: QuickDemoAccount): Promise<void> {
    this.activeTab.set(account.tab);
    this.form.patchValue({
      email: account.email,
      password: account.password,
    });

    this.loading.set(true);
    try {
      const request = this.session.login(account.email.trim().toLowerCase(), account.password);
      toast.promise(request, {
        loading: `Iniciando sesión como ${account.name}...`,
        success: `Bienvenido, ${account.roleTitle}`,
        error: () => 'No se pudo iniciar sesión. Asegúrate de que el backend esté activo en el puerto 8000.',
      });
      await request;
      const targetRoute = getDefaultRouteForRole(this.session.user()?.rol);
      await this.router.navigateByUrl(targetRoute);
    } catch {
      // El toast ya muestra el error
    } finally {
      this.loading.set(false);
    }
  }

  protected async submit(): Promise<void> {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.loading.set(true);
    try {
      const { email, password } = this.form.getRawValue();
      const request = this.session.login(email.trim().toLowerCase(), password);
      toast.promise(request, {
        loading: 'Iniciando sesión...',
        success: 'Sesión iniciada correctamente.',
        error: () => 'No se pudo iniciar sesión. Verifica tus credenciales.',
      });
      await request;
      await this.router.navigateByUrl(getDefaultRouteForRole(this.session.user()?.rol));
    } catch {
      // El toast de error ya se mostró con toast.promise
    } finally {
      this.loading.set(false);
    }
  }
}
