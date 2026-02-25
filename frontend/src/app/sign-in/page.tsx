// frontend/src/app/sign-in/page.tsx

"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { z } from "zod";
import { useUser } from "@kuroshio-lab/components";
import ShadcnDynamicForm from "@/components/ShadcnDynamicForm";
import { FormField } from "@/types/form";
import { useLoading } from "@/hooks/useLoading";
import AuthLayout from "@/components/AuthLayout";

const signinSchema = z.object({
  email: z.string().email({ message: "Please enter a valid email address." }),
  password: z.string().min(1, { message: "Password is required." }),
});

export default function SigninPage() {
  const [error, setError] = useState("");
  const router = useRouter();
  const { refetchUser } = useUser();
  const { startLoading, stopLoading, isLoading } = useLoading();

  const signinFields: FormField[] = [
    {
      name: "email",
      label: "Email",
      type: "email",
      placeholder: "Enter your email",
    },
    {
      name: "password",
      label: "Password",
      type: "password",
      placeholder: "Enter your password",
    },
  ];

  const handleSignin = useCallback(
    async (values: z.infer<typeof signinSchema>) => {
      startLoading();
      setError("");

      const API_URL = process.env.NEXT_PUBLIC_API_URL;

      try {
        const res = await fetch(`${API_URL}/api/v1/auth/login/`, {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(values),
        });

        if (res.ok) {
          console.log("Login successful, refetching user..."); // eslint-disable-line no-console
          await refetchUser();
          console.log("User refetched, redirecting..."); // eslint-disable-line no-console
          router.replace("/");
          console.log("Redirect initiated."); // eslint-disable-line no-console
        } else if (res.status === 401) {
          // Check if account needs email verification
          const errorData = await res.json().catch(() => ({}));
          if (
            errorData.detail?.includes("verify") ||
            errorData.detail?.includes("email")
          ) {
            setError("Please verify your email address before signing in.");
          } else {
            setError("Invalid credentials");
          }
        } else {
          const text = await res.text();
          console.error("Sign in fail, status:", res.status, "body:", text); // eslint-disable-line no-console
          setError("Invalid credentials");
        }
      } catch (err) {
        console.error("Caught error in handleSignin::", err); // eslint-disable-line no-console
        setError("Network error. Please try again.");
      } finally {
        stopLoading();
      }
    },
    [setError, refetchUser, router, startLoading, stopLoading],
  );

  return (
    <AuthLayout>
      <ShadcnDynamicForm
        schema={signinSchema}
        fields={signinFields}
        onSubmit={handleSignin}
        submitButtonText="Sign In"
        formTitle="Welcome Back"
        error={error}
        loading={isLoading}
        linkText="Don't have an account yet?"
        linkHref="/sign-up"
        additionalLinks={[
          { text: "Forgot Password?", href: "/forgot-password" },
          { text: "Need to verify email?", href: "/verify-email" },
        ]}
        cardClass="w-full max-w-md rounded-2xl border border-white/10 bg-brand-primary-900/90 p-8 shadow-2xl backdrop-blur-md"
      />
    </AuthLayout>
  );
}
