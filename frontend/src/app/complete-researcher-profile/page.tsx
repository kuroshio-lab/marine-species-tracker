"use client";

import { useState, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { z } from "zod";
import AuthLayout from "@/components/AuthLayout";
import ShadcnDynamicForm from "@/components/ShadcnDynamicForm";
import { FormField } from "@/types/form";

const researcherProfileSchema = z.object({
  institution_name: z
    .string()
    .min(2, { message: "Institution name is required." }),
  ror_id: z.string().optional(),
  orcid: z
    .string()
    .regex(/^\d{4}-\d{4}-\d{4}-\d{3}[0-9X]$/, {
      message: "Invalid ORCID format (e.g., 0000-0000-0000-0000)",
    })
    .optional()
    .or(z.literal("")),
  research_focus: z
    .array(z.string())
    .min(1, { message: "Select at least one research focus area." }),
  years_experience: z.coerce.number().optional(),
  bio: z
    .string()
    .max(500, { message: "Bio must not exceed 500 characters." })
    .optional(),
});

type ProfileFormValues = z.infer<typeof researcherProfileSchema>;

export default function CompleteResearcherProfilePage() {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [autoApproved, setAutoApproved] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // Check if user is authenticated and is a pending researcher
    const checkAuth = async () => {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/profiles/me/`,
          {
            credentials: "include",
          },
        );

        if (res.ok) {
          const userData = await res.json();

          // If not a pending researcher or profile already complete, redirect
          if (userData.role !== "researcher_pending") {
            router.push("/");
          }
        } else {
          router.push("/sign-in");
        }
      } catch (err) {
        console.error("Auth check failed:", err); // eslint-disable-line no-console
        router.push("/sign-in");
        return;
      } finally {
        setCheckingAuth(false);
      }
    };

    checkAuth();
  }, [router]);

  const profileFields: FormField[] = [
    {
      name: "institution_name",
      label: "Institution/Organization *",
      type: "text",
      placeholder: "Marine Biology Institute",
      helperText: "Your research institution or organization",
    },
    {
      name: "ror_id",
      label: "ROR ID (optional)",
      type: "text",
      placeholder: "https://ror.org/...",
      helperText: "Research Organization Registry ID (if known)",
    },
    {
      name: "orcid",
      label: "ORCID (optional)",
      type: "text",
      placeholder: "0000-0000-0000-0000",
      helperText: "Your ORCID identifier can speed up verification",
    },
    {
      name: "research_focus",
      label: "Research Focus Areas *",
      type: "multi-select",
      options: [
        { value: "coral", label: "Coral Reefs" },
        { value: "fish", label: "Fish" },
        { value: "invertebrates", label: "Invertebrates" },
        { value: "mammals", label: "Marine Mammals" },
        { value: "ecology", label: "Marine Ecology" },
        { value: "conservation", label: "Conservation" },
        { value: "oceanography", label: "Oceanography" },
        { value: "other", label: "Other" },
      ],
      helperText: "Select all that apply",
    },
    {
      name: "years_experience",
      label: "Years of Research Experience (optional)",
      type: "number",
      placeholder: "0",
      helperText: "Helps us understand your background",
    },
    {
      name: "bio",
      label: "Brief Professional Bio (optional)",
      type: "textarea",
      placeholder: "Tell us about your research interests and experience...",
      maxLength: 500,
      helperText: "Up to 500 characters describing your research background",
    },
  ];

  const handleSubmit = useCallback(async (values: ProfileFormValues) => {
    setLoading(true);
    setError("");
    setSuccess(false);

    const API_URL = process.env.NEXT_PUBLIC_API_URL;

    try {
      const res = await fetch(
        `${API_URL}/api/v1/auth/researcher/complete-profile/`,
        {
          method: "PATCH",
          credentials: "include", // Use cookie-based auth
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(values),
        },
      );

      if (res.ok) {
        const data = await res.json();
        setSuccess(true);

        // Check if user was auto-approved
        if (data.message?.includes("automatically verified")) {
          setAutoApproved(true);
        }
      } else {
        const errorData = await res.json();
        // eslint-disable-next-line no-console
        console.error(
          "Profile completion failed, status:",
          res.status,
          "body:",
          errorData,
        );
        setError(
          errorData.detail ||
            errorData.institution_name?.[0] ||
            errorData.research_focus?.[0] ||
            "Failed to complete profile. Please try again.",
        );
      }
    } catch (err) {
      console.error("Network error during profile completion:", err); // eslint-disable-line no-console
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  if (checkingAuth) {
    return (
      <AuthLayout>
        <div className="w-full max-w-md p-8 flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#0077BA]" />
        </div>
      </AuthLayout>
    );
  }

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
            <h2 className="text-3xl font-bold text-[#0D1B2A]">
              {autoApproved ? "Profile Verified!" : "Profile Complete!"}
            </h2>
          </div>

          <div className="space-y-4">
            {autoApproved ? (
              <div className="bg-[#E6F7F3] border border-[#30C39E] rounded-lg p-4">
                <h3 className="font-semibold text-[#30C39E] mb-2">
                  ✓ Automatically Verified
                </h3>
                <p className="text-sm text-[#1E2D3A]">
                  Your institutional email domain is trusted! Your account has
                  been automatically verified as a Community Researcher. You can
                  now validate observations.
                </p>
              </div>
            ) : (
              <div className="bg-[#FFF6E1] border border-[#FFCF5C] rounded-lg p-4">
                <h3 className="font-semibold text-[#0D1B2A] mb-2">
                  ⏱️ Pending Review
                </h3>
                <p className="text-sm text-[#1E2D3A]">
                  Your profile is complete! Our team will review your
                  credentials within 2-5 business days. You&apos;ll receive an
                  email notification once approved.
                </p>
              </div>
            )}

            <p className="text-center text-[#1E2D3A]">
              You can track your verification status from your homepage.
            </p>
          </div>

          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => router.push("/")}
              className="flex-1 px-4 py-2 bg-[#0077BA] hover:bg-[#005A8D] text-white rounded-lg font-medium transition-colors"
            >
              Go to Dashboard
            </button>
          </div>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout>
      <div className="w-full max-w-2xl">
        <div className="mb-6 bg-[#E8FAFF] border border-[#21C6E3] rounded-lg p-4">
          <div className="flex items-start">
            <span className="text-2xl mr-3">📋</span>
            <div>
              <h3 className="font-semibold text-[#0077BA] mb-1">
                Complete Your Researcher Profile
              </h3>
              <p className="text-sm text-[#1E2D3A]">
                Provide your institutional details to complete verification.
                Fields marked with * are required.
              </p>
            </div>
          </div>
        </div>

        <ShadcnDynamicForm
          schema={researcherProfileSchema}
          fields={profileFields}
          onSubmit={handleSubmit}
          submitButtonText="Complete Profile"
          formTitle="Researcher Information"
          error={error}
          loading={loading}
        />
      </div>
    </AuthLayout>
  );
}
