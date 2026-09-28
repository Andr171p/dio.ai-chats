/** Учётная запись DIO desk. */
export interface User {
  id: string;
  email: string;
  username: string | null;
  full_name: string | null;
  avatar_url: string | null;
  roles: string[];
}

export function displayName(user: User): string {
  return user.full_name ?? user.username ?? user.email;
}

export function isAdmin(user: User | null): boolean {
  return user?.roles.includes('admin') ?? false;
}
