// frontend/src/types/form.ts
import { z } from "zod";
import { DefaultValues, FieldValues } from "react-hook-form";

export type ShadcnFormFieldType =
  | "text"
  | "email"
  | "password"
  | "select"
  | "multi-select"
  | "number"
  | "date"
  | "datetime-local"
  | "textarea";

export interface FormFieldOption {
  value: string;
  label: string;
}

export interface FormField {
  name: string;
  label: string;
  type: ShadcnFormFieldType;
  placeholder?: string;
  description?: string;
  helperText?: string;
  options?: FormFieldOption[];
  optional?: boolean;
  maxLength?: number;
}

export interface DynamicFormProps<T extends FieldValues> {
  schema: z.ZodSchema<T, any>;
  fields: FormField[];
  onSubmit: (values: T) => Promise<void>;
  submitButtonText: string;
  formTitle: string;
  error?: string | null;
  loading?: boolean;
  linkText?: string;
  linkHref?: string;
  defaultValues?: DefaultValues<T>;
  onFieldChange?: (name: string, value: any) => void;
}
