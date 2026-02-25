"use client";

import { useState, useEffect, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { z } from "zod";
import AuthLayout from "@/components/AuthLayout";
import ShadcnDynamicForm from "@/components/ShadcnDynamicForm";
import { FormField } from "@/types/form";
import { useLoading } from "@/hooks/useLoading";
import { getCsrfToken } from "@/lib/api";

const verifyEmailSchema = z.object({
  token: z.string().min(1, { message: "Verification token is required." }),
});

function VerifyEmailContent() {
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [tokenFromUrl, setTokenFromUrl] = useState("");
  const [needsProfileCompletion, setNeedsProfileCompletion] = useState(false);
  const [redirectMessage, setRedirectMessage] = useState("");
  const router = useRouter();
  const searchParams = useSearchParams();
  const { startLoading, stopLoading, isLoading } = useLoading();

  const verifyEmailFields: FormField[] = [
    {
      name: "token",
      label: "Verification Code",
      type: "text",
      placeholder: "Enter your verification code",
      description: "Check your email for the verification code",
    },
  ];

  const handleVerifyEmail = useCallback(
    async (values: z.infer<typeof verifyEmailSchema>) => {
      startLoading();
      setError("");
      setSuccess(false);

      const API_URL = process.env.NEXT_PUBLIC_API_URL;
      const csrfToken = getCsrfToken();

      try {
        const res = await fetch(`${API_URL}/api/v1/auth/verify-email/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(csrfToken && { "X-CSRFToken": csrfToken }),
          },
          body: JSON.stringify(values),
          credentials: "include",
        });

        if (res.ok) {
          const data = await res.json();
          setSuccess(true);

          // Check if user is a researcher who needs to complete their profile
          if (data.user?.needs_researcher_profile_completion) {
            setNeedsProfileCompletion(true);
            setRedirectMessage(
              "Redirecting to complete your researcher profile...",
            );
            // Redirect to profile completion after a short delay
            setTimeout(() => {
              router.replace("/complete-researcher-profile");
            }, 2000);
          } else {
            setRedirectMessage("Redirecting to sign in...");
            // Redirect to sign-in after a short delay
            setTimeout(() => {
              router.replace("/sign-in");
            }, 2000);
          }
        } else {
          const errorData = await res.json();
          // eslint-disable-next-line no-console
          console.error(
            "Email verification failed, status:",
            res.status,
            "body:",
            errorData,
          );
          setError(
            errorData.detail ||
              errorData.token?.[0] ||
              "Email verification failed. Please try again.",
          );
        }
      } catch (err) {
        console.error("Network error during email verification:", err); // eslint-disable-line no-console
        setError("Network error. Please try again.");
      } finally {
        stopLoading();
      }
    },
    [startLoading, stopLoading, router],
  );

  // Get token from URL parameters and auto-submit
  useEffect(() => {
    const token = searchParams.get("token");
    if (token) {
      setTokenFromUrl(token);
      // Auto-submit if token is present
      handleVerifyEmail({ token });
    }
  }, [searchParams, handleVerifyEmail]);

  if (success) {
    return (
      <AuthLayout>
        <div className="relative w-full max-w-md overflow-hidden rounded-2xl border border-white/10 bg-brand-primary-900/90 p-8 shadow-2xl backdrop-blur-md">
          <div className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-brand-primary-500 via-brand-primary-200 to-brand-primary-500" />

          <div className="space-y-6">
            <div className="text-center">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-brand-primary-400 to-brand-primary-700">
                <svg
                  className="h-8 w-8 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <h2 className="bg-gradient-to-r from-white via-brand-primary-100 to-brand-primary-300 bg-clip-text text-3xl font-bold text-transparent">
                Email Verified!
              </h2>
            </div>

            <div className="space-y-4">
              <p className="text-center text-white/70">
                Your email has been verified successfully.
              </p>

              {needsProfileCompletion ? (
                <div className="rounded-lg border border-brand-primary-400/30 bg-brand-primary-800/50 p-4">
                  <h3 className="mb-2 font-semibold text-brand-primary-200">
                    Next Step: Complete Your Profile
                  </h3>
                  <p className="text-sm text-white/70">
                    As a researcher, please complete your institutional profile
                    to begin the verification process.
                  </p>
                </div>
              ) : (
                <div className="rounded-lg border border-brand-primary-400/30 bg-brand-primary-800/50 p-4">
                  <p className="text-sm text-white/70">
                    You can now sign in to your account!
                  </p>
                </div>
              )}

              <p className="text-center text-sm text-white/40">
                {redirectMessage}
              </p>

              <div className="text-center">
                <button
                  type="button"
                  onClick={() =>
                    router.replace(
                      needsProfileCompletion
                        ? "/complete-researcher-profile"
                        : "/sign-in",
                    )
                  }
                  className="text-sm font-medium text-brand-primary-300 transition-colors hover:text-white"
                >
                  Click here if not redirected automatically
                </button>
              </div>
            </div>
          </div>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout>
      <ShadcnDynamicForm
        schema={verifyEmailSchema}
        fields={verifyEmailFields}
        onSubmit={handleVerifyEmail}
        submitButtonText="Verify Email"
        formTitle="Verify Your Email"
        error={error}
        loading={isLoading}
        defaultValues={tokenFromUrl ? { token: tokenFromUrl } : undefined}
        linkText="Need to sign up?"
        linkHref="/sign-up"
        cardClass="w-full max-w-md rounded-2xl border border-white/10 bg-brand-primary-900/90 p-8 shadow-2xl backdrop-blur-md"
      />
    </AuthLayout>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense
      fallback={
        <AuthLayout>
          <div className="relative w-full max-w-md overflow-hidden rounded-2xl border border-white/10 bg-brand-primary-900/90 p-8 shadow-2xl backdrop-blur-md">
            <div className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-brand-primary-500 via-brand-primary-200 to-brand-primary-500" />
            <div className="flex flex-col items-center gap-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-brand-primary-400 to-brand-primary-700">
                <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-t-2 border-white" />
              </div>
              <p className="text-white/50">Verifying your email...</p>
            </div>
          </div>
        </AuthLayout>
      }
    >
      <VerifyEmailContent />
    </Suspense>
  );
}
