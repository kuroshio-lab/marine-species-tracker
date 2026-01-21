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
        <div className="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-lg">
          <div className="text-center">
            <div className="mx-auto w-16 h-16 bg-gradient-to-br from-[#30C39E] to-[#0077BA] rounded-full flex items-center justify-center mb-4">
              <svg
                className="w-8 h-8 text-white"
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
            <h2 className="text-3xl font-bold text-[#0D1B2A] mb-2">
              Email Verified!
            </h2>
          </div>

          <div className="space-y-4">
            <p className="text-center text-[#1E2D3A]">
              Your email has been verified successfully.
            </p>

            {needsProfileCompletion ? (
              <div className="bg-[#E8FAFF] border border-[#21C6E3] rounded-lg p-4">
                <h3 className="font-semibold text-[#0077BA] mb-2">
                  📋 Next Step: Complete Your Profile
                </h3>
                <p className="text-sm text-[#1E2D3A]">
                  As a researcher, please complete your institutional profile to
                  begin the verification process.
                </p>
              </div>
            ) : (
              <div className="bg-[#E6F7F3] border border-[#30C39E] rounded-lg p-4">
                <p className="text-sm text-[#0D1B2A]">
                  You can now sign in to your account!
                </p>
              </div>
            )}

            <p className="text-center text-sm text-[#A7B2B7]">
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
                className="text-[#0077BA] hover:underline text-sm"
              >
                Click here if not redirected automatically
              </button>
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
        cardClass="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-lg"
      />
    </AuthLayout>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense
      fallback={
        <AuthLayout>
          <div className="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-lg">
            <div className="text-center">
              <div className="mx-auto w-16 h-16 bg-gradient-to-br from-[#21C6E3] to-[#0077BA] rounded-full flex items-center justify-center mb-4">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-white" />
              </div>
              <p className="text-[#A7B2B7]">Verifying your email...</p>
            </div>
          </div>
        </AuthLayout>
      }
    >
      <VerifyEmailContent />
    </Suspense>
  );
}
