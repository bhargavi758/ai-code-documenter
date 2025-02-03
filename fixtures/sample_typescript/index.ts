import { User, UserRole } from './types';
import { formatDate, slugify } from './utils';

export class UserService {
  private users: Map<string, User> = new Map();

  constructor(private readonly apiUrl: string) {}

  async getUser(id: string): Promise<User | null> {
    return this.users.get(id) ?? null;
  }

  async createUser(name: string, email: string, role?: UserRole): Promise<User> {
    const user: User = {
      id: crypto.randomUUID(),
      name,
      email,
      role: role ?? 'viewer',
      createdAt: new Date(),
    };
    this.users.set(user.id, user);
    return user;
  }

  async deleteUser(id: string): Promise<boolean> {
    return this.users.delete(id);
  }

  listUsers(): User[] {
    return Array.from(this.users.values());
  }
}

export async function initializeApp(config: { apiUrl: string; debug?: boolean }): Promise<UserService> {
  const service = new UserService(config.apiUrl);
  return service;
}

export function healthCheck(): { status: string; timestamp: string } {
  return {
    status: 'ok',
    timestamp: new Date().toISOString(),
  };
}
