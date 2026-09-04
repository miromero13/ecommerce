import { RolUsuario } from '../../features/shared/models/auth.model';

export function getDefaultRouteForRole(rol: RolUsuario | undefined): string {
  switch (rol) {
    case 'administrador':
      return '/app/admin';
    case 'cliente':
      return '/app/cliente';
    case 'proveedor':
      return '/app/proveedor';
    case 'encargado':
      return '/app/encargado';
    case 'cajero':
      return '/app/cajero';
    case 'delivery':
      return '/app/delivery';
    default:
      return '/app/perfil';
  }
}
