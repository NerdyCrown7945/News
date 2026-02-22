/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  basePath: "/News",
  assetPrefix: "/News/",
  images: { unoptimized: true },
};

module.exports = nextConfig;
