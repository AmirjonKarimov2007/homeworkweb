/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  productionBrowserSourceMaps: false,
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
      {
        protocol: 'http',
        hostname: '**',
      }
    ],
    unoptimized: true,
  },
  poweredByHeader: false,
  allowedDevOrigins: ['192.168.1.108', 'http://192.168.1.108', 'http://localhost:3000'],
  turbopack: {},
};

export default nextConfig;
