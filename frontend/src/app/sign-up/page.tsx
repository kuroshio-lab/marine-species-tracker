"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { z } from "zod";
import AuthLayout from "@/components/AuthLayout";
import ShadcnDynamicForm from "@/components/ShadcnDynamicForm";
import { FormField } from "@/types/form";

const signupSchema = z.object({
  username: z
    .string()
    .min(2, { message: "Username must be at least 2 characters." }),
  email: z.string().email({ message: "Please enter a valid email address." }),
  password: z
    .string()
    .min(8, { message: "Password must be at least 8 characters." }),
  role: z.enum(["hobbyist", "researcher_pending"], {
    message: "Please select a valid role.",
  }),
});

type SignupFormValues = z.infer<typeof signupSchema>;

export default function SignupPage() {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [selectedRole, setSelectedRole] = useState<string>("hobbyist");
  const router = useRouter();

  const signupFields: FormField[] = [
    {
      name: "username",
      label: "Username",
      type: "text",
      placeholder: "Enter your username",
    },
    {
      name: "email",
      label: "Email",
      type: "email",
      placeholder: "Enter your email",
      helperText:
        selectedRole === "researcher_pending"
          ? "Use your institutional/professional email (.edu, .gov, etc.)"
          : undefined,
    },
    {
      name: "password",
      label: "Password",
      type: "password",
      placeholder: "Enter your password",
    },
    {
      name: "role",
      label: "Role",
      type: "select",
      options: [
        { value: "hobbyist", label: "Hobbyist" },
        { value: "researcher_pending", label: "Researcher" },
      ],
    },
  ];

  const handleSignup = useCallback(async (values: SignupFormValues) => {
    setLoading(true);
    setError("");
    setSuccess(false);

    const API_URL = process.env.NEXT_PUBLIC_API_URL;

    try {
      const res = await fetch(`${API_URL}/api/v1/auth/register/`, {
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
          "Sign up failed, status:",
          res.status,
          "body:",
          errorData,
        );
        setError(
          errorData.detail ||
            errorData.email?.[0] ||
            errorData.username?.[0] ||
            errorData.password?.[0] ||
            "Sign up failed. Please try again.",
        );
      }
    } catch (err) {
      console.error("Network error during sign up:", err); // eslint-disable-line no-console
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  if (success) {
    return (
      <AuthLayout>
        <div className="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-lg">
          <div className="text-center">
            <div className="mx-auto w-16 h-16 bg-gradient-to-br from-[#21C6E3] to-[#0077BA] rounded-full flex items-center justify-center mb-4">
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
                  d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                />
              </svg>
            </div>
            <h2 className="text-3xl font-bold text-[#0D1B2A]">
              Check Your Email
            </h2>
          </div>

          <div className="space-y-4">
            <p className="text-center text-[#1E2D3A]">
              We&apos;ve sent a verification email to your address. Please check
              your inbox and click the verification link to activate your
              account.
            </p>

            {selectedRole === "researcher_pending" && (
              <div className="bg-[#E8FAFF] border border-[#21C6E3] rounded-lg p-4">
                <h3 className="font-semibold text-[#0077BA] mb-2">
                  📋 Next Steps for Researchers:
                </h3>
                <ol className="text-sm text-[#1E2D3A] space-y-1 list-decimal list-inside">
                  <li>Click the verification link in your email</li>
                  <li>Complete your researcher profile</li>
                  <li>Our team will review your credentials (2-5 days)</li>
                  <li>
                    You&apos;ll receive approval notification and can start
                    validating observations!
                  </li>
                </ol>
              </div>
            )}

            <p className="text-center text-sm text-[#A7B2B7]">
              Didn&apos;t receive the email? Check your spam folder or{" "}
              <button
                type="button"
                onClick={() => setSuccess(false)}
                className="text-[#0077BA] hover:underline"
              >
                try again
              </button>
              .
            </p>
          </div>

          <div className="text-center">
            <button
              type="button"
              onClick={() => router.push("/sign-in")}
              className="text-[#A7B2B7] hover:text-[#0077BA] text-sm"
            >
              Back to Sign In
            </button>
          </div>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout>
      <div className="w-full max-w-md">
        {selectedRole === "researcher_pending" && (
          <div className="mb-6 bg-[#FFF6E1] border border-[#FFCF5C] rounded-lg p-4">
            <div className="flex items-start">
              <span className="text-2xl mr-3">ℹ️</span>
              <div>
                <h3 className="font-semibold text-[#0D1B2A] mb-1">
                  Researcher Account
                </h3>
                <p className="text-sm text-[#1E2D3A]">
                  Use your institutional email (.edu, .gov, research org) to
                  speed up verification. You&apos;ll complete your profile after
                  verifying your email.
                </p>
              </div>
            </div>
          </div>
        )}

        <ShadcnDynamicForm
          schema={signupSchema}
          fields={signupFields}
          onSubmit={handleSignup}
          submitButtonText="Sign Up"
          formTitle="Create Your Account"
          error={error}
          loading={loading}
          linkText="Already have an account?"
          linkHref="/sign-in"
          onFieldChange={(name, value) => {
            if (name === "role") {
              setSelectedRole(value as string);
            }
          }}
        />
      </div>
    </AuthLayout>
  );
}
