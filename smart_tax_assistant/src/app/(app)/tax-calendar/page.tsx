'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Calendar as CalendarIcon,
  Clock,
  ArrowLeft,
  Home,
  AlertCircle,
  FileText,
  Upload,
  CheckCircle2,
  Info,
  Bell,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';

interface TaxDeadline {
  id: string;
  date: Date;
  title: string;
  form: string;
  filingMethod: 'paper' | 'efiling';
  description: string;
  type: '40(6)' | '40(8)' | 'both';
  year: number;
  category: 'mid-year' | 'annual';
}

const TAX_DEADLINES: TaxDeadline[] = [
  // 2025 Mid-Year (P.N.D. 94)
  {
    id: 'pnd94-2025-paper',
    date: new Date('2025-09-30'),
    title: 'ยื่นภ.ง.ด. 94 กลางปี (เอกสาร)',
    form: 'ภ.ง.ด. 94',
    filingMethod: 'paper',
    description: 'สำหรับรายได้ที่ได้รับตั้งแต่ 1 มกราคม - 30 มิถุนายน 2568',
    type: 'both',
    year: 2025,
    category: 'mid-year'
  },
  {
    id: 'pnd94-2025-efiling',
    date: new Date('2025-10-08'),
    title: 'ยื่นภ.ง.ด. 94 กลางปี (ออนไลน์)',
    form: 'ภ.ง.ด. 94',
    filingMethod: 'efiling',
    description: 'ยื่นผ่านระบบอิเล็กทรอนิกส์สำหรับรายได้ม.ค.-มิ.ย. 2568',
    type: 'both',
    year: 2025,
    category: 'mid-year'
  },
  // 2026 Annual (P.N.D. 90)
  {
    id: 'pnd90-2025-paper',
    date: new Date('2026-03-31'),
    title: 'ยื่นภ.ง.ด. 90 ประจำปี (เอกสาร)',
    form: 'ภ.ง.ด. 90',
    filingMethod: 'paper',
    description: 'สำหรับรายได้ทั้งปี 2568 (1 มกราคม - 31 ธันวาคม 2568)',
    type: 'both',
    year: 2025,
    category: 'annual'
  },
  {
    id: 'pnd90-2025-efiling',
    date: new Date('2026-04-08'),
    title: 'ยื่นภ.ง.ด. 90 ประจำปี (ออนไลน์)',
    form: 'ภ.ง.ด. 90',
    filingMethod: 'efiling',
    description: 'ยื่นผ่านระบบอิเล็กทรอนิกส์สำหรับรายได้ทั้งปี 2568',
    type: 'both',
    year: 2025,
    category: 'annual'
  }
];

export default function TaxCalendarPage() {
  const router = useRouter();
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedYear, setSelectedYear] = useState(2025);
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth());
  const [nextDeadline, setNextDeadline] = useState<TaxDeadline | null>(null);
  const [countdown, setCountdown] = useState({
    days: 0,
    hours: 0,
    minutes: 0,
    seconds: 0
  });
  const [selectedDeadline, setSelectedDeadline] = useState<TaxDeadline | null>(null);
  const [showInfo, setShowInfo] = useState(false);

  // Find next deadline
  useEffect(() => {
    const now = new Date();
    const upcomingDeadlines = TAX_DEADLINES
      .filter(d => d.date > now)
      .sort((a, b) => a.date.getTime() - b.date.getTime());

    if (upcomingDeadlines.length > 0) {
      setNextDeadline(upcomingDeadlines[0]);
    }
  }, []);

  // Update countdown every second
  useEffect(() => {
    if (!nextDeadline) return;

    const interval = setInterval(() => {
      const now = new Date().getTime();
      const target = nextDeadline.date.getTime();
      const diff = target - now;

      if (diff > 0) {
        setCountdown({
          days: Math.floor(diff / (1000 * 60 * 60 * 24)),
          hours: Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)),
          minutes: Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60)),
          seconds: Math.floor((diff % (1000 * 60)) / 1000)
        });
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [nextDeadline]);

  // Calendar helpers
  const getDaysInMonth = (year: number, month: number) => {
    return new Date(year, month + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (year: number, month: number) => {
    return new Date(year, month, 1).getDay();
  };

  const getDeadlinesForDate = (year: number, month: number, day: number) => {
    return TAX_DEADLINES.filter(d => {
      const deadlineDate = d.date;
      return deadlineDate.getFullYear() === year &&
             deadlineDate.getMonth() === month &&
             deadlineDate.getDate() === day;
    });
  };

  const changeMonth = (direction: 'prev' | 'next') => {
    if (direction === 'prev') {
      if (selectedMonth === 0) {
        setSelectedMonth(11);
        setSelectedYear(selectedYear - 1);
      } else {
        setSelectedMonth(selectedMonth - 1);
      }
    } else {
      if (selectedMonth === 11) {
        setSelectedMonth(0);
        setSelectedYear(selectedYear + 1);
      } else {
        setSelectedMonth(selectedMonth + 1);
      }
    }
  };

  const renderCalendar = () => {
    const daysInMonth = getDaysInMonth(selectedYear, selectedMonth);
    const firstDay = getFirstDayOfMonth(selectedYear, selectedMonth);
    const days = [];

    // Empty cells for days before month starts
    for (let i = 0; i < firstDay; i++) {
      days.push(<div key={`empty-${i}`} className="p-2"></div>);
    }

    // Actual days
    for (let day = 1; day <= daysInMonth; day++) {
      const deadlines = getDeadlinesForDate(selectedYear, selectedMonth, day);
      const hasDeadline = deadlines.length > 0;
      const isToday =
        day === currentDate.getDate() &&
        selectedMonth === currentDate.getMonth() &&
        selectedYear === currentDate.getFullYear();

      days.push(
        <div
          key={day}
          onClick={() => hasDeadline && setSelectedDeadline(deadlines[0])}
          className={`
            p-2 min-h-[80px] border border-gray-200 rounded-lg cursor-pointer transition-all duration-200
            ${isToday ? 'ring-2 ring-blue-500 bg-blue-50' : ''}
            ${hasDeadline ? 'bg-red-50 hover:bg-red-100 hover:shadow-md' : 'hover:bg-gray-50'}
          `}
        >
          <div className="font-semibold text-gray-900 mb-1">{day}</div>
          {hasDeadline && (
            <div className="space-y-1">
              {deadlines.map(deadline => (
                <div
                  key={deadline.id}
                  className={`text-xs px-2 py-1 rounded-full font-medium ${
                    deadline.filingMethod === 'efiling'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-orange-100 text-orange-800'
                  }`}
                >
                  {deadline.form}
                </div>
              ))}
            </div>
          )}
        </div>
      );
    }

    return days;
  };

  const monthNames = [
    'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน',
    'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-4">
            <button
              onClick={() => router.push('/WelcomeHome')}
              className="p-3 bg-white hover:bg-gray-50 rounded-2xl shadow-sm hover:shadow-md transition-all duration-200 border border-gray-200"
            >
              <ArrowLeft className="w-5 h-5 text-gray-600" />
            </button>

            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-red-500 to-orange-600 rounded-2xl flex items-center justify-center">
                <CalendarIcon className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-red-600 to-orange-600 bg-clip-text text-transparent">
                  ปฏิทินภาษี 2025-2026
                </h1>
                <p className="text-gray-600">สำหรับผู้มีรายได้ตาม ม.40(6) และ 40(8)</p>
              </div>
            </div>

            <button
              onClick={() => setShowInfo(true)}
              className="ml-auto p-3 bg-blue-100 text-blue-600 rounded-xl hover:bg-blue-200 transition-colors"
            >
              <Info className="w-5 h-5" />
            </button>
          </div>

          {/* Info Banner */}
          <div className="bg-blue-50 border-2 border-blue-200 rounded-2xl p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-blue-800">
              <strong>หมายเหตุ:</strong> ปฏิทินนี้เฉพาะผู้มีรายได้จาก <strong>อาชีพอิสระ (ม.40(6))</strong> และ <strong>ธุรกิจ/พาณิชย์ (ม.40(8))</strong> เช่น ฟรีแลนซ์, คนขายของออนไลน์, ผู้รับเหมา ฯลฯ
            </div>
          </div>
        </div>

        {/* Countdown Timer */}
        {nextDeadline && (
          <div className="bg-gradient-to-br from-red-500 to-orange-600 rounded-3xl shadow-2xl p-8 mb-8 text-white">
            <div className="text-center mb-6">
              <div className="flex items-center justify-center gap-2 mb-2">
                <Clock className="w-6 h-6" />
                <h2 className="text-2xl font-bold">เหลือเวลาอีก</h2>
              </div>
              <p className="text-white/90 text-lg">{nextDeadline.title}</p>
              <p className="text-white/80 text-sm mt-1">
                กำหนดส่ง: {nextDeadline.date.toLocaleDateString('th-TH', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                })}
              </p>
            </div>

            <div className="grid grid-cols-4 gap-4 max-w-2xl mx-auto">
              {[
                { label: 'วัน', value: countdown.days },
                { label: 'ชั่วโมง', value: countdown.hours },
                { label: 'นาที', value: countdown.minutes },
                { label: 'วินาที', value: countdown.seconds }
              ].map((item) => (
                <div key={item.label} className="bg-white/20 backdrop-blur-sm rounded-2xl p-4">
                  <div className="text-4xl font-bold mb-1">
                    {item.value.toString().padStart(2, '0')}
                  </div>
                  <div className="text-white/80 text-sm">{item.label}</div>
                </div>
              ))}
            </div>

            <div className="mt-6 flex justify-center gap-4">
              <div className={`px-4 py-2 rounded-full text-sm font-medium ${
                nextDeadline.filingMethod === 'efiling'
                  ? 'bg-green-500/30 text-white'
                  : 'bg-orange-500/30 text-white'
              }`}>
                {nextDeadline.filingMethod === 'efiling' ? '📱 ยื่นออนไลน์' : '📄 ยื่นเอกสาร'}
              </div>
              <div className="px-4 py-2 bg-white/20 rounded-full text-sm font-medium text-white">
                {nextDeadline.form}
              </div>
            </div>
          </div>
        )}

        {/* Calendar */}
        <div className="bg-white rounded-3xl shadow-xl p-6">
          {/* Calendar Header */}
          <div className="flex items-center justify-between mb-6">
            <button
              onClick={() => changeMonth('prev')}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ChevronLeft className="w-6 h-6" />
            </button>

            <h3 className="text-2xl font-bold text-gray-900">
              {monthNames[selectedMonth]} {selectedYear + 543}
            </h3>

            <button
              onClick={() => changeMonth('next')}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ChevronRight className="w-6 h-6" />
            </button>
          </div>

          {/* Days of Week */}
          <div className="grid grid-cols-7 gap-2 mb-4">
            {['อา.', 'จ.', 'อ.', 'พ.', 'พฤ.', 'ศ.', 'ส.'].map((day) => (
              <div key={day} className="text-center font-semibold text-gray-600 py-2">
                {day}
              </div>
            ))}
          </div>

          {/* Calendar Grid */}
          <div className="grid grid-cols-7 gap-2">
            {renderCalendar()}
          </div>

          {/* Legend */}
          <div className="mt-6 flex flex-wrap gap-4 justify-center">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-orange-100 border border-orange-300 rounded"></div>
              <span className="text-sm text-gray-600">ยื่นเอกสาร</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-100 border border-green-300 rounded"></div>
              <span className="text-sm text-gray-600">ยื่นออนไลน์</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-blue-50 border-2 border-blue-500 rounded"></div>
              <span className="text-sm text-gray-600">วันนี้</span>
            </div>
          </div>
        </div>

        {/* All Deadlines List */}
        <div className="mt-8 bg-white rounded-3xl shadow-xl p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Bell className="w-5 h-5 text-orange-600" />
            กำหนดการยื่นภาษีทั้งหมด
          </h3>

          <div className="space-y-4">
            {TAX_DEADLINES.sort((a, b) => a.date.getTime() - b.date.getTime()).map((deadline) => {
              const isPast = deadline.date < new Date();

              return (
                <div
                  key={deadline.id}
                  className={`p-4 rounded-2xl border-2 transition-all duration-200 ${
                    isPast
                      ? 'bg-gray-50 border-gray-200 opacity-60'
                      : 'bg-gradient-to-r from-red-50 to-orange-50 border-red-200 hover:shadow-md'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-2xl">
                          {deadline.filingMethod === 'efiling' ? '📱' : '📄'}
                        </span>
                        <div>
                          <h4 className="font-bold text-gray-900">{deadline.title}</h4>
                          <p className="text-sm text-gray-600">{deadline.description}</p>
                        </div>
                      </div>

                      <div className="flex flex-wrap gap-2 mt-3">
                        <span className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-xs font-medium">
                          {deadline.form}
                        </span>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          deadline.filingMethod === 'efiling'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-orange-100 text-orange-800'
                        }`}>
                          {deadline.filingMethod === 'efiling' ? 'ยื่นออนไลน์' : 'ยื่นเอกสาร'}
                        </span>
                        <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                          {deadline.category === 'mid-year' ? 'กลางปี' : 'ประจำปี'}
                        </span>
                      </div>
                    </div>

                    <div className="text-right ml-4">
                      <div className="text-2xl font-bold text-gray-900">
                        {deadline.date.getDate()}
                      </div>
                      <div className="text-sm text-gray-600">
                        {monthNames[deadline.date.getMonth()]}
                      </div>
                      <div className="text-sm font-medium text-gray-900">
                        {deadline.date.getFullYear() + 543}
                      </div>
                      {isPast && (
                        <div className="mt-2">
                          <CheckCircle2 className="w-5 h-5 text-gray-400 mx-auto" />
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Info Modal */}
        {showInfo && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-3xl p-8 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
              <div className="flex items-start justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-blue-100 rounded-2xl flex items-center justify-center">
                    <Info className="w-6 h-6 text-blue-600" />
                  </div>
                  <h3 className="text-2xl font-bold text-gray-900">ข้อมูลเกี่ยวกับภาษี</h3>
                </div>
                <button
                  onClick={() => setShowInfo(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-6">
                <div>
                  <h4 className="font-bold text-lg text-gray-900 mb-2">ผู้มีรายได้ตาม ม.40(6)</h4>
                  <p className="text-gray-700 mb-2">รายได้จากวิชาชีพอิสระ เช่น:</p>
                  <ul className="list-disc list-inside text-gray-600 space-y-1 ml-4">
                    <li>กฎหมาย (ทนายความ)</li>
                    <li>การแพทย์ (แพทย์, ทันตแพทย์)</li>
                    <li>วิศวกรรม</li>
                    <li>สถาปัตยกรรม</li>
                    <li>การบัญชี</li>
                    <li>ศิลปะ (จิตรกร, ประติมากร)</li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-bold text-lg text-gray-900 mb-2">ผู้มีรายได้ตาม ม.40(8)</h4>
                  <p className="text-gray-700 mb-2">รายได้จากการประกอบธุรกิจ พาณิชยกรรม เช่น:</p>
                  <ul className="list-disc list-inside text-gray-600 space-y-1 ml-4">
                    <li>ฟรีแลนซ์ (Graphic Designer, Content Creator)</li>
                    <li>ผู้รับเหมา (Contractor)</li>
                    <li>ขายของออนไลน์</li>
                    <li>ธุรกิจขนส่ง</li>
                    <li>เกษตรกรรม</li>
                    <li>ธุรกิจอื่นๆ ที่ไม่ระบุไว้</li>
                  </ul>
                </div>

                <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
                  <h4 className="font-bold text-yellow-900 mb-2">⚠️ สำคัญ!</h4>
                  <p className="text-yellow-800 text-sm">
                    วันที่ระบุเป็นตามประกาศกรมสรรพากร อาจมีการเปลี่ยนแปลงหรือขยายเวลา
                    กรุณาติดตามประกาศอย่างเป็นทางการจากกรมสรรพากรเพิ่มเติม
                  </p>
                </div>

                <div>
                  <h4 className="font-bold text-lg text-gray-900 mb-2">แบบฟอร์มภาษี</h4>
                  <div className="space-y-3">
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <p className="font-medium text-gray-900">ภ.ง.ด. 94</p>
                      <p className="text-sm text-gray-600">แบบแสดงรายการภาษีเงินได้บุคคลธรรมดาครึ่งปี</p>
                    </div>
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <p className="font-medium text-gray-900">ภ.ง.ด. 90</p>
                      <p className="text-sm text-gray-600">แบบแสดงรายการภาษีเงินได้บุคคลธรรมดา (ทั้งปี)</p>
                    </div>
                  </div>
                </div>
              </div>

              <button
                onClick={() => setShowInfo(false)}
                className="w-full mt-6 py-3 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-700 transition-colors"
              >
                เข้าใจแล้ว
              </button>
            </div>
          </div>
        )}

        {/* Selected Deadline Modal */}
        {selectedDeadline && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-3xl p-8 max-w-lg w-full">
              <div className="text-center mb-6">
                <div className="text-6xl mb-4">
                  {selectedDeadline.filingMethod === 'efiling' ? '📱' : '📄'}
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-2">
                  {selectedDeadline.title}
                </h3>
                <p className="text-gray-600">{selectedDeadline.description}</p>
              </div>

              <div className="space-y-4 mb-6">
                <div className="flex justify-between items-center p-4 bg-gray-50 rounded-xl">
                  <span className="text-gray-600">วันที่</span>
                  <span className="font-bold text-gray-900">
                    {selectedDeadline.date.toLocaleDateString('th-TH', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })}
                  </span>
                </div>

                <div className="flex justify-between items-center p-4 bg-gray-50 rounded-xl">
                  <span className="text-gray-600">แบบฟอร์ม</span>
                  <span className="font-bold text-gray-900">{selectedDeadline.form}</span>
                </div>

                <div className="flex justify-between items-center p-4 bg-gray-50 rounded-xl">
                  <span className="text-gray-600">วิธีการยื่น</span>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    selectedDeadline.filingMethod === 'efiling'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-orange-100 text-orange-800'
                  }`}>
                    {selectedDeadline.filingMethod === 'efiling' ? 'ยื่นออนไลน์' : 'ยื่นเอกสาร'}
                  </span>
                </div>
              </div>

              <button
                onClick={() => setSelectedDeadline(null)}
                className="w-full py-3 bg-gray-600 text-white font-bold rounded-xl hover:bg-gray-700 transition-colors"
              >
                ปิด
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
