import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: [
    "*.ngrok-free.app",
    "*.ngrok-free.dev",
    "*.ngrok.io",
    "*.ngrok.dev",
    "*.trycloudflare.com",
    "*.loca.lt",
  ],
};

export default nextConfig;
