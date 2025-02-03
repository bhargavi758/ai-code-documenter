export type UserRole = 'admin' | 'editor' | 'viewer';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  createdAt: Date;
}

export interface ApiResponse<T> {
  data: T;
  error?: string;
  meta: {
    total: number;
    page: number;
  };
}

export type PaginationParams = {
  page: number;
  limit: number;
  sortBy?: string;
  order?: 'asc' | 'desc';
};
