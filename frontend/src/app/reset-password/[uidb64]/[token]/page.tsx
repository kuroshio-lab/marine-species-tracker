"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { z } from "zod";
import AuthLayout from "@/components/AuthLayout";
import ShadcnDynamicForm from "@/components/ShadcnDynamicForm";
import { FormField } from "@/types/form";
import { useLoading } from "@/hooks/useLoading";

const resetPasswordSchema = z
  .object({
    new_password: z
      .string()
      .min(8, { message: "Password must be at least 8 characters long." })
      .regex(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, {
        message:
          "Password must contain at least one uppercase letter, one lowercase letter, and one number.",
      }),
    re_new_password: z.string(),
  })
  .refine((data) => data.new_password === data.re_new_password, {
    message: "Passwords do not match.",
    path: ["re_new_password"],
  });

interface ResetPasswordPageProps {
  params: {
    uidb64: string;
    token: string;
  };
}

export default function ResetPasswordPage({ params }: ResetPasswordPageProps) {
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const router = useRouter();
  const { startLoading, stopLoading, isLoading } = useLoading();

  const resetPasswordFields: FormField[] = [
    {
      name: "new_password",
      label: "New Password",
      type: "password",
      placeholder: "Enter your new password",
      description:
        "Must be at least 8 characters with uppercase, lowercase, and number.",
    },
    {
      name: "re_new_password",
      label: "Confirm New Password",
      type: "password",
      placeholder: "Confirm your new password",
    },
  ];

  const handleResetPassword = useCallback(
    async (values: z.infer<typeof resetPasswordSchema>) => {
      startLoading();
      setError("");
      setSuccess(false);

      const API_URL = process.env.NEXT_PUBLIC_API_URL;

      try {
        const res = await fetch(
          `${API_URL}/api/v1/auth/password-reset/confirm/`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              uidb64: decodeURIComponent(params.uidb64),
              token: decodeURIComponent(params.token),
              new_password: values.new_password,
              re_new_password: values.re_new_password,
            }),
          },
        );

        if (res.ok) {
          setSuccess(true);
          // Redirect to sign-in after a short delay
          setTimeout(() => {
            router.replace("/sign-in");
          }, 3000);
        } else {
          const errorData = await res.json();
          // eslint-disable-next-line no-console
          console.error(
            "Password reset confirm failed, status:",
            res.status,
            "body:",
            errorData,
          );

          // Handle specific error cases
          if (
            errorData.detail?.includes("token") ||
            errorData.detail?.includes("invalid")
          ) {
            setError(
              "This password reset link is invalid or has expired. Please request a new one.",
            );
          } else {
            setError(
              errorData.detail ||
                errorData.new_password?.[0] ||
                errorData.re_new_password?.[0] ||
                "Failed to reset password. Please try again.",
            );
          }
        }
      } catch (err) {
        console.error("Network error during password reset confirm:", err); // eslint-disable-line no-console
        setError("Network error. Please try again.");
      } finally {
        stopLoading();
      }
    },
    [startLoading, stopLoading, params.uidb64, params.token, router],
  );

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
                Password Reset Successful
              </h2>
            </div>
            <div className="space-y-2">
              <p className="text-center text-white/70">
                Your password has been successfully reset.
              </p>
              <p className="text-center text-sm text-white/40">
                You will be redirected to the sign-in page shortly.
              </p>
            </div>
          </div>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout>
      <ShadcnDynamicForm
        schema={resetPasswordSchema}
        fields={resetPasswordFields}
        onSubmit={handleResetPassword}
        submitButtonText="Reset Password"
        formTitle="Set New Password"
        error={error}
        loading={isLoading}
        linkText="Remember your password?"
        linkHref="/sign-in"
        cardClass="w-full max-w-md rounded-2xl border border-white/10 bg-brand-primary-900/90 p-8 shadow-2xl backdrop-blur-md"
      />
    </AuthLayout>
  );
}
