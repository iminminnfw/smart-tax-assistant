
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // อนุญาตให้เข้าถึงจาก IP ในเครือข่ายเดียวกัน (ปิด warning)
  allowedDevOrigins: ['192.168.100.55'],
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'images.unsplash.com',
        port: '',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: 'placehold.co',
        port: '',
        pathname: '/**',
      },
    ],
  },
};

export default nextConfig; 