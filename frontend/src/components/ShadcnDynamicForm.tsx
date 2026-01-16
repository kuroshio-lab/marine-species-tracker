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
import { Button } from "./ui/button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField as ShadcnFormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "./ui/form";
import { Input } from "./ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { Textarea } from "./ui/textarea";
import { DynamicFormProps, FormField } from "../types/form";

function renderFieldControl(
  field: FormField,
  formField: any,
  loading: boolean,
) {
  switch (field.type) {
    case "select":
      return (
        <Select
          onValueChange={formField.onChange}
          defaultValue={formField.value}
          disabled={loading}
        >
          <SelectTrigger>
            <SelectValue
              placeholder={field.placeholder || `Select a ${field.label}`}
            />
          </SelectTrigger>
          <SelectContent position="popper" className="z-[9999]">
            {field.options?.map((option) => (
              <SelectItem key={option.value} value={option.value}>
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
          disabled={loading}
          maxLength={field.maxLength}
        />
      );
    case "multi-select":
      return (
        <div className="flex flex-wrap gap-2 p-3 border rounded-md bg-white min-h-[40px]">
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
                }}
                disabled={loading}
                className={`px-3 py-1 text-sm rounded-full border transition-all ${
                  isSelected
                    ? "bg-[#0077BA] text-white border-[#0077BA] shadow-sm"
                    : "bg-gray-50 text-gray-700 border-gray-200 hover:border-gray-300 hover:bg-gray-100"
                }`}
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
          disabled={loading}
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
  cardClass = "w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-md",
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
        // Use defaultValues if provided
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
    <div className={cardClass}>
      <h2 className="text-3xl font-bold text-center text-gray-900">
        {formTitle}
      </h2>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          {fields.map((field: FormField) => (
            <ShadcnFormField
              key={field.name}
              control={form.control}
              name={field.name as FieldPath<T>}
              render={({ field: formField }) => (
                <FormItem>
                  <FormLabel>{field.label}</FormLabel>
                  <FormControl>
                    {renderFieldControl(field, formField, loading)}
                  </FormControl>
                  {(field.description || field.helperText) && (
                    <FormDescription>
                      {field.description || field.helperText}
                    </FormDescription>
                  )}
                  <FormMessage />
                </FormItem>
              )}
            />
          ))}
          {error && <p className="text-red-500 text-sm text-center">{error}</p>}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Processing..." : submitButtonText}
          </Button>
        </form>
      </Form>
      <div className="space-y-2">
        {linkText && linkHref && (
          <p className="text-center text-sm text-gray-600">
            {linkText}{" "}
            <Link
              href={linkHref}
              className="font-medium text-blue-600 hover:underline"
            >
              {linkHref.includes("sign-up") ? "Sign up" : "Sign in"}
            </Link>
          </p>
        )}
        {additionalLinks?.map((link) => (
          <p key={link.href} className="text-center text-sm text-gray-600">
            <Link
              href={link.href}
              className="font-medium text-blue-600 hover:underline"
            >
              {link.text}
            </Link>
          </p>
        ))}
      </div>
    </div>
  );
}
