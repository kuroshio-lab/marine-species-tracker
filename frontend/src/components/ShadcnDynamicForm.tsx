// frontend/src/components/ShadcnDynamicForm.tsx

"use client";

import React from "react";
import {
  useForm,
  FieldPath,
  FieldValues,
  DefaultValues,
  Resolver,
} from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { cn } from "@kuroshio-lab/styles";
import {
  Button,
  Form,
  FormControl,
  FormDescription,
  FormField as ShadcnFormField,
  FormItem,
  FormLabel,
  FormMessage,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Textarea,
} from "@kuroshio-lab/ui";
import { DynamicFormProps, FormField } from "../types/form";

const inputClass =
  "bg-white/10 border-white/20 text-white placeholder:text-white/30 focus-visible:ring-brand-primary-400/50 focus-visible:border-white/40";

function renderFieldControl(
  field: FormField,
  formField: any,
  loading: boolean,
  onFieldChange?: (name: string, value: any) => void,
) {
  switch (field.type) {
    case "select":
      return (
        <Select
          onValueChange={(value) => {
            formField.onChange(value);
            onFieldChange?.(field.name, value);
          }}
          defaultValue={formField.value}
          disabled={loading}
        >
          <SelectTrigger className={inputClass}>
            <SelectValue
              placeholder={field.placeholder || `Select a ${field.label}`}
            />
          </SelectTrigger>
          <SelectContent
            position="popper"
            className="z-[9999] !border-white/20 !bg-brand-primary-900 !text-white"
          >
            {field.options?.map((option) => (
              <SelectItem
                key={option.value}
                value={option.value}
                className="!text-white focus:!bg-white/10 focus:!text-white"
              >
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      );
    case "textarea":
      return (
        <Textarea
          placeholder={field.placeholder}
          {...formField}
          onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => {
            formField.onChange(e);
            onFieldChange?.(field.name, e.target.value);
          }}
          disabled={loading}
          maxLength={field.maxLength}
          className={inputClass}
        />
      );
    case "multi-select":
      return (
        <div className="flex flex-wrap gap-2 p-3 border border-white/20 rounded-md bg-white/5 min-h-[40px]">
          {field.options?.map((option) => {
            const isSelected =
              Array.isArray(formField.value) &&
              formField.value.includes(option.value);
            return (
              <button
                key={option.value}
                type="button"
                onClick={() => {
                  const currentValues = Array.isArray(formField.value)
                    ? formField.value
                    : [];
                  const nextValues = isSelected
                    ? currentValues.filter((v: string) => v !== option.value)
                    : [...currentValues, option.value];
                  formField.onChange(nextValues);
                  onFieldChange?.(field.name, nextValues);
                }}
                disabled={loading}
                className={cn(
                  "px-3 py-1 text-sm rounded-full border transition-all",
                  isSelected
                    ? "bg-brand-primary-500 text-white border-brand-primary-400 shadow-sm"
                    : "bg-white/10 text-white/70 border-white/20 hover:bg-white/20 hover:text-white",
                )}
              >
                {option.label}
              </button>
            );
          })}
        </div>
      );
    default:
      return (
        <Input
          type={field.type}
          placeholder={field.placeholder}
          {...formField}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
            formField.onChange(e);
            onFieldChange?.(field.name, e.target.value);
          }}
          disabled={loading}
          className={inputClass}
        />
      );
  }
}

export default function ShadcnDynamicForm<T extends FieldValues>({
  schema,
  fields,
  onSubmit,
  submitButtonText,
  formTitle,
  error,
  loading = false,
  linkText,
  linkHref,
  defaultValues,
  cardClass = "w-full rounded-2xl border border-white/10 bg-brand-primary-900/90 p-8 shadow-2xl backdrop-blur-md",
  additionalLinks,
  onFieldChange,
}: DynamicFormProps<T> & {
  cardClass?: string;
  additionalLinks?: Array<{ text: string; href: string }>;
}) {
  const form = useForm<T>({
    resolver: zodResolver(schema as any) as Resolver<T>,
    defaultValues:
      defaultValues ||
      (Object.fromEntries(
        fields.map((field) => {
          switch (field.type) {
            case "multi-select":
              return [field.name, []];
            case "number":
              return [field.name, ""];
            case "date":
              return [field.name, ""];
            case "select":
            case "text":
            case "email":
            case "password":
            case "textarea":
            default:
              return [field.name, ""];
          }
        }),
      ) as DefaultValues<T>),
  });

  React.useEffect(() => {
    if (defaultValues) {
      form.reset(defaultValues);
    }
  }, [defaultValues, form]);

  return (
    <div className={cn(cardClass, "relative overflow-hidden")}>
      {/* Top accent bar */}
      <div className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-brand-primary-500 via-brand-primary-200 to-brand-primary-500" />

      <h2 className="mb-6 bg-gradient-to-r from-white via-brand-primary-100 to-brand-primary-300 bg-clip-text text-center text-2xl font-bold text-transparent">
        {formTitle}
      </h2>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">
          {fields.map((field: FormField) => (
            <ShadcnFormField
              key={field.name}
              control={form.control}
              name={field.name as FieldPath<T>}
              render={({ field: formField }) => (
                <FormItem>
                  <FormLabel className="text-white/80">{field.label}</FormLabel>
                  <FormControl>
                    {renderFieldControl(
                      field,
                      formField,
                      loading,
                      onFieldChange,
                    )}
                  </FormControl>
                  {(field.description || field.helperText) && (
                    <FormDescription className="text-brand-primary-100/50">
                      {field.description || field.helperText}
                    </FormDescription>
                  )}
                  <FormMessage />
                </FormItem>
              )}
            />
          ))}
          {error && <p className="text-center text-sm text-red-400">{error}</p>}
          <Button
            type="submit"
            variant="addingObs"
            className="w-full"
            disabled={loading}
          >
            {loading ? "Processing..." : submitButtonText}
          </Button>
        </form>
      </Form>

      <div className="mt-5 space-y-2">
        {linkText && linkHref && (
          <p className="text-center text-sm text-brand-primary-100/60">
            {linkText}{" "}
            <Link
              href={linkHref}
              className="font-medium text-brand-primary-300 transition-colors hover:text-white"
            >
              {linkHref.includes("sign-up") ? "Sign up" : "Sign in"}
            </Link>
          </p>
        )}
        {additionalLinks?.map((link) => (
          <p key={link.href} className="text-center text-sm">
            <Link
              href={link.href}
              className="font-medium text-brand-primary-300/80 transition-colors hover:text-white"
            >
              {link.text}
            </Link>
          </p>
        ))}
      </div>
    </div>
  );
}
