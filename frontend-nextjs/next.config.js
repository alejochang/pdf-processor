/** @type {import('next').NextConfig} */
const nextConfig = {
  // Use standalone output only for Docker builds
  output: process.env.DOCKER_BUILD === 'true' ? 'standalone' : undefined,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
}

module.exports = nextConfig
