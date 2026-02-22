/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  basePath: '/News',
  assetPrefix: '/News/',
  images: { unoptimized: true },
  env: {
    NEXT_PUBLIC_BASE_PATH: '/News',
  },
}

module.exports = nextConfig
