# Scripts Directory

Scripts สำหรับจัดการ database และ maintenance tasks

---

## 📝 รายการ Scripts

### 1. `migrate-existing-users.ts`

**วัตถุประสงค์:** อัพเดท `emailVerified` สำหรับ user เก่าที่สมัครก่อนมีระบบ MFA

**สถานการณ์ที่ใช้:**
- เมื่อเพิ่มระบบ MFA ให้กับโปรเจกต์ที่มี user เก่าอยู่แล้ว
- User เก่าไม่สามารถ login ได้เพราะ `emailVerified = null`

**วิธีใช้:**

```bash
# 1. ติดตั้ง tsx (ถ้ายังไม่มี)
npm install -D tsx

# 2. เปิดไฟล์ migrate-existing-users.ts
# 3. เปลี่ยน CONFIRM_UPDATE = true (ในไฟล์)
# 4. รัน script
npx tsx scripts/migrate-existing-users.ts
```

**ผลลัพธ์:**
- User เก่าทั้งหมดจะได้ `emailVerified = วันที่รัน script`
- User สามารถ login ได้ทันทีโดยไม่ต้องยืนยันอีเมล

**ข้อควรระวัง:**
- ควรทำ database backup ก่อนรัน
- ตรวจสอบรายชื่อ user ที่จะอัพเดทก่อนยืนยัน
- Script จะแสดงรายชื่อทั้งหมดก่อนอัพเดท

---

## 🔒 ความปลอดภัย

- Script ทุกตัวต้อง review ก่อนรัน
- ควร test บน development database ก่อน
- ทำ backup database ก่อนรัน production script

---

## 📚 เพิ่ม Script ใหม่

เมื่อสร้าง script ใหม่:

1. ตั้งชื่อไฟล์แบบ kebab-case: `my-new-script.ts`
2. เพิ่ม comment อธิบายวัตถุประสงค์
3. เพิ่มการจัดการ error
4. เพิ่มการ disconnect prisma
5. อัพเดท README นี้
