// frontend/src/app/page.tsx

"use client";

import React, { useEffect } from "react";
import { useLoading } from "../hooks/useLoading";
import UserObservationSection from "../components/UserObservationSection";

export default function Home() {
  const { startLoading, stopLoading } = useLoading();

  useEffect(() => {
    const fetchData = async () => {
      startLoading();
      try {
        await new Promise((resolve) => {
          setTimeout(resolve, 2000);
        });
      } catch (error) {
        // eslint-disable-next-line no-console
        console.error("Failed to fetch data:", error);
      } finally {
        stopLoading();
      }
    };

    fetchData();
  }, [startLoading, stopLoading]);

  return (
    <main className="h-screen flex flex-col">
      <div className="mx-auto max-w-[2560px] h-full max-h-[1076px] w-full p-4">
        <UserObservationSection className="h-full" />
      </div>
    </main>
  );
}
