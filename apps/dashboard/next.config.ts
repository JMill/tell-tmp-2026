import type { NextConfig } from "next";
import createMDX from "@next/mdx";

const nextConfig: NextConfig = {
  pageExtensions: ["ts", "tsx", "md", "mdx"],
  async redirects() {
    return [
      {
        source: "/tmp26",
        destination: "/tmp26/index.html",
        permanent: false,
      },
      {
        source: "/talk",
        destination: "/tmp26/index.html",
        permanent: false,
      },
      {
        source: "/talk/index.html",
        destination: "/tmp26/index.html",
        permanent: false,
      },
    ];
  },
};

const withMDX = createMDX({});

export default withMDX(nextConfig);
