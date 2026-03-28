import type { Metadata } from 'next';
import PrivacyContent from './PrivacyContent';

export const metadata: Metadata = {
  title: 'นโยบายความเป็นส่วนตัว - SmartTax Assistant',
  description: 'นโยบายความเป็นส่วนตัวและการคุ้มครองข้อมูลส่วนบุคคลตาม PDPA ของ SmartTax Assistant',
};

export default function PrivacyPage() {
  return <PrivacyContent />;
}
