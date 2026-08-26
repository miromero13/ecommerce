import { RolUsuario } from '../../features/shared/models/auth.model';

export function getDefaultRouteForRole(rol: RolUsuario | undefined): string {
  switch (rol) {
    case 'administrador':
      return '/app/admin';
    default:
      return '/app/perfil';
  }
}
