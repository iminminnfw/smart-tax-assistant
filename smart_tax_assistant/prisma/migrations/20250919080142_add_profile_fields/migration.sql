/*
  Warnings:

  - You are about to alter the column `phone` on the `users` table. The data in that column could be lost. The data in that column will be cast from `Text` to `VarChar(20)`.

*/
-- AlterTable
ALTER TABLE "public"."users" ADD COLUMN     "taxType" "public"."TaxType" NOT NULL DEFAULT 'INDIVIDUAL',
ALTER COLUMN "phone" SET DATA TYPE VARCHAR(20);
