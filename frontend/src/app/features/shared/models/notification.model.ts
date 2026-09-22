import { RolUsuario } from './auth.model';

export interface NotificationItem {
  id: string;
  title: string;
  body: string;
  data: Record<string, unknown>;
  read_at: string | null;
  created_at: string;
}

function safeId(value: unknown): string | null {
  return typeof value === 'string' && /^[A-Za-z0-9_-]+$/.test(value) ? value : null;
}

export function notificationRoute(data: Record<string, unknown>, role: RolUsuario | undefined): string {
  const requestedRoute = data['route'];
  if (
    typeof requestedRoute === 'string' &&
    /^\/app\/(notifications|cliente\/orders|cliente\/my-reservations|admin\/inventory|encargado\/inventory)$/.test(requestedRoute)
  ) {
    return requestedRoute;
  }

  switch (data['destination']) {
    case 'orders':
      return role === 'encargado' ? '/app/encargado/orders' : role === 'cliente' ? '/app/cliente/orders' : '/app/notifications';
    case 'reservations':
      return role === 'encargado' ? '/app/encargado/reservations' : role === 'cliente' ? '/app/cliente/my-reservations' : '/app/notifications';
    case 'inventory':
      return role === 'administrador' ? '/app/admin/inventory' : role === 'encargado' ? '/app/encargado/inventory' : '/app/notifications';
    case 'product': {
      const productId = safeId(data['product_id']);
      return role === 'cliente' && productId ? `/app/cliente/products/${productId}` : '/app/notifications';
    }
    default:
      return '/app/notifications';
  }
}
