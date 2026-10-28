export interface Permission {
  id: string;
  name: string;
  module: string;
  description: string;
}

export interface Role {
  id: string;
  tenant_id: string | null;
  code: string;
  name: string;
  base_rol: string | null;
  is_system: boolean;
  permissions: Permission[];
}

export interface RoleCreate {
  name: string;
  code: string;
  permission_ids: string[];
}

export interface RoleUpdate {
  name?: string;
  permission_ids?: string[];
}

export interface UserRolesAssign {
  role_ids: string[];
}
