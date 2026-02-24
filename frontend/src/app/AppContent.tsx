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

export default function AppContent({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      {children}
      <GlobalLoader useLoadingHook={useLoading} LoaderComponent={DNALoader} />
    </>
  );
}
