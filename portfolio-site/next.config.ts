import type { NextConfig } from "next";

// Static export for GitHub Pages. This repo is a *project* page, so it is served
// under /gtm-signal-intelligence/ in production; basePath is disabled in dev.
const isProd = process.env.NODE_ENV === "production";
const repoBase = "/gtm-signal-intelligence";

const nextConfig: NextConfig = {
  output: "export",
  basePath: isProd ? repoBase : "",
  images: { unoptimized: true },
  trailingSlash: true,
};

export default nextConfig;
