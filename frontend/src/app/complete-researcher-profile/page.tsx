"use client";

import { useState, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { z } from "zod";
import AuthLayout from "@/components/AuthLayout";
import ShadcnDynamicForm from "@/components/ShadcnDynamicForm";
import { getCsrfToken } from "@/lib/api";
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
          if (
            userData.role !== "researcher_pending" ||
            !userData.needs_researcher_profile_completion
          ) {
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

  const handleSubmit = useCallback(
    async (values: ProfileFormValues) => {
      setLoading(true);
      setError("");

      const API_URL = process.env.NEXT_PUBLIC_API_URL;
      const csrfToken = getCsrfToken();

      try {
        const res = await fetch(
          `${API_URL}/api/v1/auth/researcher/complete-profile/`,
          {
            method: "PATCH",
            credentials: "include",
            headers: {
              "Content-Type": "application/json",
              ...(csrfToken && { "X-CSRFToken": csrfToken }),
            },
            body: JSON.stringify(values),
          },
        );

        if (res.ok) {
          router.push("/");
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
    },
    [router],
  );

  if (checkingAuth) {
    return (
      <AuthLayout>
        <div className="relative w-full max-w-md overflow-hidden rounded-2xl border border-white/10 bg-brand-primary-900/90 p-8 shadow-2xl backdrop-blur-md">
          <div className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-brand-primary-500 via-brand-primary-200 to-brand-primary-500" />
          <div className="flex items-center justify-center">
            <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-t-2 border-brand-primary-400" />
          </div>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout>
      <div className="mx-auto w-full max-w-2xl">
        <div className="mb-6 rounded-lg border border-brand-primary-400/30 bg-brand-primary-900/70 p-4 backdrop-blur-sm">
          <div className="flex items-start">
            <span className="mr-3 text-xl text-brand-primary-300">📋</span>
            <div>
              <h3 className="mb-1 font-semibold text-brand-primary-200">
                Complete Your Researcher Profile
              </h3>
              <p className="text-sm text-white/70">
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
