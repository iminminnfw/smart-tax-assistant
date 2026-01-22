// src/components/Footer/Footer.tsx
import Link from 'next/link';

export default function Footer() {
  return (
    <footer className="bg-slate-900" aria-labelledby="footer-heading">
      <h2 id="footer-heading" className="sr-only">Footer</h2>
      <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:py-16 lg:px-8">
        <div className="pb-8 xl:grid xl:grid-cols-5 xl:gap-8">
          <div className="grid grid-cols-2 gap-8 xl:col-span-4 md:grid-cols-4">
            {/* Column 1 */}
            <div>
              <h3 className="text-sm font-semibold text-slate-400 tracking-wider uppercase">เกี่ยวกับเรา</h3>
              <ul role="list" className="mt-4 space-y-4">
                <li><Link href="/about" className="text-sm text-slate-300 hover:text-white transition-colors">เกี่ยวกับบริษัท</Link></li>
                <li><Link href="/careers" className="text-sm text-slate-300 hover:text-white transition-colors">ร่วมงานกับเรา</Link></li>
                <li><Link href="/blog" className="text-sm text-slate-300 hover:text-white transition-colors">บล็อก</Link></li>
              </ul>
            </div>
            {/* Column 2 */}
            <div className="mt-12 md:mt-0">
              <h3 className="text-sm font-semibold text-slate-400 tracking-wider uppercase">บริการ</h3>
              <ul role="list" className="mt-4 space-y-4">
                <li><Link href="/#features" className="text-sm text-slate-300 hover:text-white transition-colors">คุณสมบัติ</Link></li>
                <li><Link href="/#pricing" className="text-sm text-slate-300 hover:text-white transition-colors">ราคา</Link></li>
                <li><Link href="/integrations" className="text-sm text-slate-300 hover:text-white transition-colors">การเชื่อมต่อ</Link></li>
              </ul>
            </div>
            {/* Column 3 */}
            <div className="mt-12 md:mt-0">
              <h3 className="text-sm font-semibold text-slate-400 tracking-wider uppercase">ความช่วยเหลือ</h3>
              <ul role="list" className="mt-4 space-y-4">
                <li><Link href="/faq" className="text-sm text-slate-300 hover:text-white transition-colors">คำถามที่พบบ่อย</Link></li>
                <li><Link href="/docs" className="text-sm text-slate-300 hover:text-white transition-colors">คู่มือการใช้งาน</Link></li>
                <li><Link href="/contact" className="text-sm text-slate-300 hover:text-white transition-colors">ติดต่อเรา</Link></li>
              </ul>
            </div>
            {/* Column 4 */}
            <div className="mt-12 md:mt-0">
              <h3 className="text-sm font-semibold text-slate-400 tracking-wider uppercase">กฎหมาย</h3>
              <ul role="list" className="mt-4 space-y-4">
                <li><Link href="/privacy" className="text-sm text-slate-300 hover:text-white transition-colors">นโยบายความเป็นส่วนตัว</Link></li>
                <li><Link href="/terms" className="text-sm text-slate-300 hover:text-white transition-colors">ข้อกำหนดการใช้งาน</Link></li>
              </ul>
            </div>
          </div>
          {/* Newsletter/Subscribe */}
          <div className="mt-12 xl:mt-0 xl:col-span-1">
             <h3 className="text-sm font-semibold text-slate-400 tracking-wider uppercase">ติดตามข่าวสาร</h3>
             <p className="mt-4 text-sm text-slate-300">รับข่าวสารและเคล็ดลับภาษีส่งตรงถึงอีเมลคุณ</p>
             <form className="mt-4 sm:flex sm:max-w-md">
                <label htmlFor="email-address" className="sr-only">Email address</label>
                <input type="email" name="email-address" id="email-address" autoComplete="email" required className="appearance-none min-w-0 w-full bg-slate-800 border border-slate-700 rounded-lg py-2 px-4 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="กรอกอีเมลของคุณ" />
                <div className="mt-3 sm:mt-0 sm:ml-3 sm:flex-shrink-0">
                  <button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 rounded-lg py-2 px-5 flex items-center justify-center text-sm font-medium text-white transition-colors">
                    ติดตาม
                  </button>
                </div>
             </form>
          </div>
        </div>
        {/* Bottom Footer */}
        <div className="pt-8 border-t border-slate-800">
          <p className="text-sm text-slate-400 text-center">
            © {new Date().getFullYear()} Smart Tax Assistant. สงวนลิขสิทธิ์.
          </p>
        </div>
      </div>
    </footer>
  );
}
