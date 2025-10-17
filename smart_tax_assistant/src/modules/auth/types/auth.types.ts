/**
 * Authentication Module Type Definitions
 */

export interface RegisterInput {
  name: string;
  email: string;
  password: string;
}

export interface LoginInput {
  email: string;
  password: string;
}

export interface AuthUser {
  id: string;
  email: string;
  name: string | null;
}

export interface RegisterResult {
  success: boolean;
  user?: AuthUser;
  error?: string;
}

export interface LoginResult {
  success: boolean;
  user?: AuthUser;
  error?: string;
}
