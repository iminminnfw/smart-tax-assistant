// src/utils/dateUtils.ts
export const formatThaiDate = (date: Date | string): string => {
  const thaiMonths = [
    'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน',
    'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'
  ];

  const dateObj = typeof date === 'string' ? new Date(date) : date;
  const month = thaiMonths[dateObj.getMonth()];
  const year = dateObj.getFullYear() + 543; // แปลง ค.ศ. เป็น พ.ศ.
  
  return `${month} ${year}`;
};

export const formatThaiDateWithDay = (date: Date | string): string => {
  const thaiMonths = [
    'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน',
    'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'
  ];

  const dateObj = typeof date === 'string' ? new Date(date) : date;
  const day = dateObj.getDate();
  const month = thaiMonths[dateObj.getMonth()];
  const year = dateObj.getFullYear() + 543;
  
  return `${day} ${month} ${year}`;
};