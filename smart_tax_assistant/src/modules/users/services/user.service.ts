/**
 * User Service
 *
 * Handles user-related business logic
 */

import { prisma } from '@/lib/prisma';
import { hash, compare } from 'bcryptjs';
import type {
  User,
  UserProfile,
  UpdateProfileInput,
  ChangePasswordInput,
} from '../types/user.types';

export class UserService {
  /**
   * Get user by ID
   */
  async getUserById(id: string): Promise<User | null> {
    const user = await prisma.user.findUnique({
      where: { id },
    });

    return user as User | null;
  }

  /**
   * Get user by email
   */
  async getUserByEmail(email: string): Promise<User | null> {
    const user = await prisma.user.findUnique({
      where: { email },
    });

    return user as User | null;
  }

  /**
   * Get user profile with statistics
   */
  async getUserProfile(userId: string): Promise<UserProfile | null> {
    const user = await this.getUserById(userId);
    if (!user) return null;

    const [documentCount, folderCount] = await Promise.all([
      prisma.documentFile.count({
        where: { userId, isDeleted: false },
      }),
      prisma.documentFolder.count({
        where: { userId, isDeleted: false },
      }),
    ]);

    return {
      id: user.id,
      email: user.email,
      name: user.name,
      image: user.image,
      documentCount,
      folderCount,
    };
  }

  /**
   * Update user profile
   */
  async updateProfile(
    userId: string,
    input: UpdateProfileInput
  ): Promise<User> {
    const updated = await prisma.user.update({
      where: { id: userId },
      data: input,
    });

    return updated as User;
  }

  /**
   * Change user password
   */
  async changePassword(
    userId: string,
    input: ChangePasswordInput
  ): Promise<void> {
    // Get user with password
    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: { id: true, password: true },
    });

    if (!user || !user.password) {
      throw new Error('User not found or password not set');
    }

    // Verify current password
    const isValid = await compare(input.currentPassword, user.password);
    if (!isValid) {
      throw new Error('Current password is incorrect');
    }

    // Hash new password
    const hashedPassword = await hash(input.newPassword, 10);

    // Update password
    await prisma.user.update({
      where: { id: userId },
      data: { password: hashedPassword },
    });
  }

  /**
   * Delete user account
   */
  async deleteUser(userId: string): Promise<void> {
    // Delete user's documents
    await prisma.documentFile.deleteMany({
      where: { userId },
    });

    // Delete user's folders
    await prisma.documentFolder.deleteMany({
      where: { userId },
    });

    // Delete user
    await prisma.user.delete({
      where: { id: userId },
    });
  }

  /**
   * Check if email exists
   */
  async emailExists(email: string, excludeUserId?: string): Promise<boolean> {
    const where: any = { email };

    if (excludeUserId) {
      where.id = { not: excludeUserId };
    }

    const count = await prisma.user.count({ where });
    return count > 0;
  }

  /**
   * Get total user count
   */
  async getUserCount(): Promise<number> {
    return prisma.user.count();
  }
}
