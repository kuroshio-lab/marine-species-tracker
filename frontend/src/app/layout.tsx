// frontend/src/app/layout.tsx

import "../styles/globals.css";
import React from "react";
import { Inter } from "next/font/google";
import { UserProvider } from "@kuroshio-lab/components";
import AppContent from "./AppContent";
import { LoadingProvider } from "../hooks/useLoading";

const inter = Inter({ subsets: ["latin"] });

const siteUrl =
  process.env.NEXT_PUBLIC_SITE_URL || "https://species.kuroshio-lab.com";

const title =
  "Kuroshio-Lab: Marine Species Observation Tracker | Biodiversity Mapping & Citizen Science Platform";
const description =
  "Empower divers, biologists, and hobbyists to log, explore, and contribute to marine species observations on an interactive map. Track biodiversity, share discoveries, access verified species data, and support marine conservation through crowdsourced research with public data export.";

export const metadata = {
  metadataBase: new URL(siteUrl),
  title,
  description,
  openGraph: {
    title,
    description,
    url: siteUrl,
    siteName: "Kuroshio-Lab",
    images: [
      {
        url: "/opengraph-image",
        width: 1200,
        height: 630,
        alt: "Kuroshio-Lab — Marine Species Observation Tracker",
      },
    ],
    type: "website",
    locale: "en_US",
  },
  twitter: {
    card: "summary_large_image",
    title,
    description,
    images: ["/opengraph-image"],
  },
  icons: {
    icon: "/icon.svg",
    apple: "/icon.svg",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <UserProvider apiUrl={process.env.NEXT_PUBLIC_API_URL}>
          <LoadingProvider>
            <AppContent>{children}</AppContent>
          </LoadingProvider>
        </UserProvider>
      </body>
    </html>
  );
}
