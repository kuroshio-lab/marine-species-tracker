// frontend/src/app/layout.tsx

import "../styles/globals.css";
import React from "react";
import { Inter } from "next/font/google";
import { UserProvider } from "../components/UserProvider";
import AppContent from "./AppContent";
import { LoadingProvider } from "../hooks/useLoading";
import GlobalLoader from "../components/GlobalLoader";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title:
    "Kuroshio-Lab: Marine Species Observation Tracker | Biodiversity Mapping & Citizen Science Platform",
  description:
    "Empower divers, biologists, and hobbyists to log, explore, and contribute to marine species observations on an interactive map. Track biodiversity, share discoveries, access verified species data, and support marine conservation through crowdsourced research with public data export.",
  icons: {
    icon: "/favicon.ico",
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
        <UserProvider>
          <LoadingProvider>
            <AppContent>{children}</AppContent>
            <GlobalLoader />
          </LoadingProvider>
        </UserProvider>
      </body>
    </html>
  );
}
