/**
 * Authentication Service
 *
 * Handles user registration, login, and authentication logic
 */

import { prisma } from '@/lib/prisma';
import { hash, compare } from 'bcryptjs';
import type {
  RegisterInput,
  LoginInput,
  RegisterResult,
  LoginResult,
  AuthUser,
} from '../types/auth.types';

export class AuthService {
  /**
   * Register a new user
   */
  async register(input: RegisterInput): Promise<RegisterResult> {
    try {
      // Check if user already exists
      const existingUser = await prisma.user.findUnique({
        where: { email: input.email },
      });

      if (existingUser) {
        return {
          success: false,
          error: 'User with this email already exists',
        };
      }

      // Hash password
      const hashedPassword = await hash(input.password, 10);

      // Create user
      const user = await prisma.user.create({
        data: {
          name: input.name,
          email: input.email,
          password: hashedPassword,
        },
        select: {
          id: true,
          email: true,
          name: true,
        },
      });

      return {
        success: true,
        user: user as AuthUser,
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to register user',
      };
    }
  }

  /**
   * Authenticate user login
   */
  async login(input: LoginInput): Promise<LoginResult> {
    try {
      // Find user
      const user = await prisma.user.findUnique({
        where: { email: input.email },
        select: {
          id: true,
          email: true,
          name: true,
          password: true,
        },
      });

      if (!user || !user.password) {
        return {
          success: false,
          error: 'Invalid email or password',
        };
      }

      // Verify password
      const isValid = await compare(input.password, user.password);

      if (!isValid) {
        return {
          success: false,
          error: 'Invalid email or password',
        };
      }

      // Remove password from return value
      const { password, ...userWithoutPassword } = user;

      return {
        success: true,
        user: userWithoutPassword as AuthUser,
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to login',
      };
    }
  }

  /**
   * Verify credentials for NextAuth
   */
  async verifyCredentials(
    email: string,
    password: string
  ): Promise<AuthUser | null> {
    const result = await this.login({ email, password });

    if (result.success && result.user) {
      return result.user;
    }

    return null;
  }

  /**
   * Validate email format
   */
  validateEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  /**
   * Validate password strength
   */
  validatePassword(password: string): {
    valid: boolean;
    errors: string[];
  } {
    const errors: string[] = [];

    if (password.length < 8) {
      errors.push('Password must be at least 8 characters long');
    }

    if (!/[A-Z]/.test(password)) {
      errors.push('Password must contain at least one uppercase letter');
    }

    if (!/[a-z]/.test(password)) {
      errors.push('Password must contain at least one lowercase letter');
    }

    if (!/[0-9]/.test(password)) {
      errors.push('Password must contain at least one number');
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  /**
   * Generate password reset token
   * TODO: Implement password reset functionality
   */
  async generatePasswordResetToken(email: string): Promise<string | null> {
    // TODO: Implement token generation and storage
    throw new Error('Password reset not implemented yet');
  }

  /**
   * Reset password using token
   * TODO: Implement password reset functionality
   */
  async resetPassword(token: string, newPassword: string): Promise<boolean> {
    // TODO: Implement password reset logic
    throw new Error('Password reset not implemented yet');
  }
}
