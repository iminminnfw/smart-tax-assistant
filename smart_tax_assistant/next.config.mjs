// next.config.mjs
/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true, 
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
        hostname: 'placehold.co', // <-- เปลี่ยนเป็นอันนี้
        port: '',
        pathname: '/**',
        },
      ],
    },
  };
  
  export default nextConfig;