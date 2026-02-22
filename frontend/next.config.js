/** @type {import('next').NextConfig} */
const nextConfig = {
  // GitHub Pages의 /News 경로 지원
  basePath: process.env.NEXT_PUBLIC_BASE_PATH || "",
  assetPrefix: process.env.NEXT_PUBLIC_BASE_PATH || "",
  images: { unoptimized: true },
};

module.exports = nextConfig;
