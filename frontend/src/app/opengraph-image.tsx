// frontend/src/app/opengraph-image.tsx

import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "Kuroshio-Lab — Marine Species Observation Tracker";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function Image() {
  return new ImageResponse(
    <div
      style={{
        background:
          "linear-gradient(135deg, #0a1628 0%, #0d2444 60%, #0a2a3a 100%)",
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "sans-serif",
        color: "white",
        padding: "60px",
      }}
    >
      {/* Logo */}
      <svg
        width="100"
        height="100"
        viewBox="0 0 200 200"
        style={{ marginBottom: "36px" }}
      >
        <rect
          width="200"
          height="200"
          rx="16"
          fill="#FFFFFF"
          fillOpacity="0.08"
        />
        <path
          d="M40 140C40 84.7715 84.7715 40 140 40"
          stroke="#21C6E3"
          strokeWidth="12"
          strokeLinecap="round"
        />
        <path
          d="M65 145C65 100.817 100.817 65 145 65"
          stroke="#0077BA"
          strokeWidth="16"
          strokeLinecap="round"
        />
        <path
          d="M90 150C90 116.863 116.863 90 150 90"
          stroke="#005A8D"
          strokeWidth="20"
          strokeLinecap="round"
        />
        <circle cx="150" cy="150" r="12" fill="#30C39E" />
      </svg>

      {/* Title */}
      <div
        style={{
          fontSize: "58px",
          fontWeight: 700,
          letterSpacing: "-1px",
          marginBottom: "16px",
        }}
      >
        Kuroshio-Lab
      </div>

      {/* Subtitle */}
      <div
        style={{
          fontSize: "28px",
          color: "#21C6E3",
          marginBottom: "24px",
          letterSpacing: "0.5px",
        }}
      >
        Marine Species Observation Tracker
      </div>

      {/* Description */}
      <div
        style={{
          fontSize: "20px",
          color: "#94a3b8",
          textAlign: "center",
          maxWidth: "860px",
          lineHeight: 1.5,
        }}
      >
        Log, explore, and contribute to marine biodiversity observations on an
        interactive map.
      </div>
    </div>,
    { ...size },
  );
}
