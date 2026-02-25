"use client";

import { useState, useCallback } from "react";
import { z } from "zod";
import AuthLayout from "@/components/AuthLayout";
import ShadcnDynamicForm from "@/components/ShadcnDynamicForm";
import { FormField } from "@/types/form";
import { useLoading } from "@/hooks/useLoading";

const forgotPasswordSchema = z.object({
  email: z.string().email({ message: "Please enter a valid email address." }),
});

export default function ForgotPasswordPage() {
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const { startLoading, stopLoading, isLoading } = useLoading();

  const forgotPasswordFields: FormField[] = [
    {
      name: "email",
      label: "Email",
      type: "email",
      placeholder: "Enter your email address",
    },
  ];

  const handleForgotPassword = useCallback(
    async (values: z.infer<typeof forgotPasswordSchema>) => {
      startLoading();
      setError("");
      setSuccess(false);

      const API_URL = process.env.NEXT_PUBLIC_API_URL;

      try {
        const res = await fetch(`${API_URL}/api/v1/auth/password-reset/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(values),
        });

        if (res.ok) {
          setSuccess(true);
        } else {
          const errorData = await res.json();
          // eslint-disable-next-line no-console
          console.error(
            "Password reset failed, status:",
            res.status,
            "body:",
            errorData,
          );
          setError(
            errorData.detail ||
              errorData.email?.[0] ||
              "Failed to send password reset email. Please try again.",
          );
        }
      } catch (err) {
        console.error("Network error during password reset:", err); // eslint-disable-line no-console
        setError("Network error. Please try again.");
      } finally {
        stopLoading();
      }
    },
    [startLoading, stopLoading],
  );

  if (success) {
    return (
      <AuthLayout>
        <div className="relative w-full max-w-md overflow-hidden rounded-2xl border border-white/10 bg-brand-primary-900/90 p-8 shadow-2xl backdrop-blur-md">
          <div className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-brand-primary-500 via-brand-primary-200 to-brand-primary-500" />

          <div className="space-y-6">
            <h2 className="bg-gradient-to-r from-white via-brand-primary-100 to-brand-primary-300 bg-clip-text text-center text-3xl font-bold text-transparent">
              Check Your Email
            </h2>
            <div className="space-y-4">
              <p className="text-center text-white/70">
                We&apos;ve sent you an email with instructions to reset your
                password.
              </p>
              <p className="text-center text-sm text-white/40">
                If you don&apos;t see the email in your inbox, please check your
                spam folder.
              </p>
            </div>
            <div className="text-center">
              <button
                type="button"
                onClick={() => {
                  setSuccess(false);
                  setError("");
                }}
                className="text-sm font-medium text-brand-primary-300 transition-colors hover:text-white"
              >
                Try a different email address
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
        schema={forgotPasswordSchema}
        fields={forgotPasswordFields}
        onSubmit={handleForgotPassword}
        submitButtonText="Send Reset Email"
        formTitle="Reset Your Password"
        error={error}
        loading={isLoading}
        linkText="Remember your password?"
        linkHref="/sign-in"
        cardClass="w-full max-w-md rounded-2xl border border-white/10 bg-brand-primary-900/90 p-8 shadow-2xl backdrop-blur-md"
      />
    </AuthLayout>
  );
}
