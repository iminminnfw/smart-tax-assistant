import Link from 'next/link';

interface LogoProps {
  href?: string;      // ทำให้ href ไม่บังคับ
  onClick?: () => void; // สำหรับการทำงานอื่น ๆ เช่น ปิดเมนูมือถือ
}

// ถ้ามี href จะใช้ <Link>, ถ้าไม่มีจะใช้ <div> ธรรมดา
export default function Logo({ href, onClick }: LogoProps) {
  const logoContent = (
    <div className="flex items-center cursor-pointer" onClick={!href ? onClick : undefined}>
      <svg className="h-9 w-auto text-blue-600" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
         <path d="M12 2L2 7V17L12 22L22 17V7L12 2Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="rgba(59, 130, 246, 0.1)"/>
         <path d="M17 9.5L12 12L7 9.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
         <path d="M12 17.5V12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
         <path d="M7 14.5L12 17.5L17 14.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
      <span className="ml-2 text-2xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">
        SmartTax
      </span>
    </div>
  );

  if (href) {
    return (
      <Link href={href} onClick={onClick}>
        {logoContent}
      </Link>
    );
  }
  
  return logoContent; // คืนค่าเป็น div ธรรมดาถ้าไม่มี href
}