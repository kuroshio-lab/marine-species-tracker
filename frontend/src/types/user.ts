export type UserRole =
  | "hobbyist"
  | "researcher_pending"
  | "researcher_community"
  | "researcher_institutional";

export type User = {
  id: number;
  username: string;
  email: string;
  role: UserRole;
  email_verified: boolean;
  needs_researcher_profile_completion?: boolean;
  can_validate_observations?: boolean;
  is_verified_researcher?: boolean;
  verification_status_display?: string;
  institution_name?: string;
  research_focus?: string[];
};
