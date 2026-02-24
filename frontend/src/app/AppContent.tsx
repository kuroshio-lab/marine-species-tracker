// frontend/src/app/AppContent.tsx

"use client";

import React from "react";
import dynamic from "next/dynamic";
import { GlobalLoader } from "@kuroshio-lab/components";
import { useLoading } from "../hooks/useLoading";

const DNA = dynamic(
  () => import("react-loader-spinner").then((m) => ({ default: m.DNA })),
  { ssr: false },
);

function DNALoader() {
  return (
    <DNA
      visible
      height="80"
      width="80"
      ariaLabel="dna-loading"
      wrapperStyle={{}}
      wrapperClass="dna-wrapper"
    />
  );
}

function MobileBlock() {
  return (
    <div className="md:hidden fixed inset-0 z-[9999] flex flex-col items-center justify-center bg-[#0D1B2A] px-8 text-center">
      <div className="mb-6 text-6xl">🌊</div>
      <h1 className="text-2xl font-bold text-white mb-3">Desktop Only</h1>
      <p className="text-[#A8C5DA] text-sm leading-relaxed max-w-xs">
        The species app of Kuroshio Lab is designed for desktop use. Please open
        this app on a larger screen to access the full experience.
      </p>
    </div>
  );
}

export default function AppContent({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <MobileBlock />
      <div className="hidden md:block h-full">{children}</div>
      <GlobalLoader useLoadingHook={useLoading} LoaderComponent={DNALoader} />
    </>
  );
}
