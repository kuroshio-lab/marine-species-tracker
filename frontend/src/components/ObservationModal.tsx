// frontend/src/components/ObservationModal.tsx
import React, { useState, useEffect } from "react";
import { z } from "zod";
import {
  useForm,
  FieldPath,
  ControllerRenderProps,
  Resolver,
} from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "./ui/dialog";
import SpeciesSearch from "./SpeciesSearch";
import { Observation } from "../types/observation";
import { FormField } from "../types/form";
import { createObservation, updateObservation } from "../lib/observation";
import { useUser } from "./UserProvider";
import { ScrollArea } from "./ui/scroll-area";
import {
  Form,
  FormControl,
  FormItem,
  FormLabel,
  FormMessage,
  FormField as ShadcnFormField,
} from "./ui/form";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { Textarea } from "./ui/textarea";

interface ObservationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onObservationUpserted: () => void;
  mode: "add" | "edit";
  observation?: Observation | null;
}

const observationFormSchema = z.object({
  speciesName: z.string().min(1, "Species is required"),
  commonName: z.string().nullable().optional(),
  locationName: z.string().min(1, "Location name is required"),
  latitude: z.preprocess((val) => Number(val), z.number().min(-90).max(90)),
  longitude: z.preprocess((val) => Number(val), z.number().min(-180).max(180)),
  observationDatetime: z
    .string()
    .min(1, "Observation date and time is required"),
  depthMin: z
    .preprocess(
      (val) => (val === "" ? null : Number(val)),
      z.number().nullable(),
    )
    .optional(),
  depthMax: z
    .preprocess(
      (val) => (val === "" ? null : Number(val)),
      z.number().nullable(),
    )
    .optional(),
  bathymetry: z
    .preprocess(
      (val) => (val === "" ? null : Number(val)),
      z.number().nullable(),
    )
    .optional(),
  temperature: z
    .preprocess(
      (val) => (val === "" ? null : Number(val)),
      z.number().nullable(),
    )
    .optional(),
  visibility: z
    .preprocess(
      (val) => (val === "" ? null : Number(val)),
      z.number().nullable(),
    )
    .optional(),
  notes: z.string().nullable().optional(),
  sex: z.enum(["male", "female", "unknown"]).nullable().optional(),
});

type ObservationFormData = z.infer<typeof observationFormSchema>;

const observationFormFields: FormField[] = [
  {
    name: "locationName",
    label: "Location Name",
    type: "text",
    optional: true,
  },
  {
    name: "latitude",
    label: "Latitude",
    type: "number",
    placeholder: "e.g., 34.05",
  },
  {
    name: "longitude",
    label: "Longitude",
    type: "number",
    placeholder: "e.g., -118.25",
  },
  {
    name: "observationDatetime",
    label: "Observation Date/Time",
    type: "datetime-local",
  },
  {
    name: "depthMin",
    label: "Minimum Depth (m)",
    type: "number",
    optional: true,
  },
  {
    name: "depthMax",
    label: "Maximum Depth (m)",
    type: "number",
    optional: true,
  },
  {
    name: "bathymetry",
    label: "Bathymetry (m)",
    type: "number",
    optional: true,
  },
  {
    name: "temperature",
    label: "Temperature (°C)",
    type: "number",
    optional: true,
  },
  {
    name: "visibility",
    label: "Visibility (m)",
    type: "number",
    optional: true,
  },
  { name: "notes", label: "Notes", type: "textarea", optional: true },
  {
    name: "sex",
    label: "Sex",
    type: "select",
    options: [
      { value: "male", label: "Male" },
      { value: "female", label: "Female" },
      { value: "unknown", label: "Unknown" },
    ],
    optional: true,
  },
];

function renderFieldControl(
  field: FormField,
  formField: ControllerRenderProps<
    ObservationFormData,
    FieldPath<ObservationFormData>
  >,
  loading: boolean,
) {
  switch (field.type) {
    case "select":
      return (
        <Select
          onValueChange={formField.onChange}
          defaultValue={
            formField.value !== null && formField.value !== undefined
              ? String(formField.value)
              : undefined
          }
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
          value={
            formField.value !== null && formField.value !== undefined
              ? String(formField.value)
              : undefined
          }
          onChange={formField.onChange}
          onBlur={formField.onBlur}
          disabled={loading}
        />
      );
    default:
      return (
        <Input
          type={field.type}
          placeholder={field.placeholder}
          value={
            formField.value !== null && formField.value !== undefined
              ? String(formField.value)
              : undefined
          }
          onChange={formField.onChange}
          onBlur={formField.onBlur}
          disabled={loading}
        />
      );
  }
}

export default function ObservationModal({
  isOpen,
  onClose,
  onObservationUpserted,
  mode,
  observation,
}: ObservationModalProps) {
  const { user } = useUser();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedSpecies, setSelectedSpecies] = useState<{
    speciesName: string;
    commonName: string;
  } | null>(null);
  const [defaultValues, setDefaultValues] = useState<
    Partial<ObservationFormData> | undefined
  >(undefined);

  const form = useForm<ObservationFormData>({
    resolver: zodResolver(
      observationFormSchema,
    ) as Resolver<ObservationFormData>,
    defaultValues: defaultValues || {
      speciesName: "",
      commonName: undefined,
      locationName: "",
      latitude: 0,
      longitude: 0,
      observationDatetime: new Date().toISOString().substring(0, 16),
      depthMin: undefined,
      depthMax: undefined,
      bathymetry: undefined,
      temperature: undefined,
      visibility: undefined,
      notes: undefined,
      sex: "unknown" as const,
    },
  });

  useEffect(() => {
    if (mode === "edit" && observation) {
      const species = {
        speciesName: observation.speciesName,
        commonName: observation.commonName || "",
      };
      setSelectedSpecies(species);
      const values = {
        speciesName: observation.speciesName,
        commonName: observation.commonName ?? undefined,
        locationName: observation.locationName,
        latitude: observation.location.coordinates[1],
        longitude: observation.location.coordinates[0],
        observationDatetime: observation.observationDatetime
          ? new Date(observation.observationDatetime)
              .toISOString()
              .substring(0, 16)
          : undefined,
        depthMin: observation.depthMin ?? undefined,
        depthMax: observation.depthMax ?? undefined,
        bathymetry: observation.bathymetry ?? undefined,
        temperature: observation.temperature ?? undefined,
        visibility: observation.visibility ?? undefined,
        notes: observation.notes ?? undefined,
        sex: observation.sex ?? undefined,
      };
      setDefaultValues(values);
      form.reset(values);
    } else {
      setSelectedSpecies(null);
      const values = {
        speciesName: "",
        commonName: undefined,
        locationName: "",
        latitude: 0,
        longitude: 0,
        observationDatetime: new Date().toISOString().substring(0, 16),
        depthMin: undefined,
        depthMax: undefined,
        bathymetry: undefined,
        temperature: undefined,
        visibility: undefined,
        notes: undefined,
        sex: "unknown" as const,
      };
      setDefaultValues(values);
      form.reset(values);
    }
  }, [mode, observation, isOpen, form]);

  const onSubmit = async (data: z.infer<typeof observationFormSchema>) => {
    if (!user) {
      setError("User not authenticated.");
      return;
    }
    if (mode === "edit" && !observation) {
      setError("No observation selected for editing.");
      return;
    }
    if (!selectedSpecies) {
      setError("Please select a species.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      if (mode === "edit" && observation) {
        const updatedObservationData = {
          speciesName: selectedSpecies.speciesName,
          commonName: selectedSpecies.commonName || null,
          locationName: data.locationName,
          location: {
            type: "Point" as const,
            coordinates: [data.longitude, data.latitude] as [number, number],
          },
          observationDatetime: data.observationDatetime
            ? new Date(data.observationDatetime).toISOString()
            : undefined,
          depthMin: data.depthMin ?? null,
          depthMax: data.depthMax ?? null,
          bathymetry: data.bathymetry ?? null,
          temperature: data.temperature ?? null,
          visibility: data.visibility ?? null,
          notes: data.notes ?? null,
          sex: data.sex ?? "unknown",
        };
        await updateObservation(observation.id, updatedObservationData);
      } else {
        const newObservationData = {
          speciesName: selectedSpecies.speciesName,
          commonName: selectedSpecies.commonName || null,
          locationName: data.locationName,
          latitude: data.latitude,
          longitude: data.longitude,
          observationDatetime: new Date(data.observationDatetime).toISOString(),
          depthMin: data.depthMin ?? null,
          depthMax: data.depthMax ?? null,
          bathymetry: data.bathymetry ?? null,
          temperature: data.temperature ?? null,
          visibility: data.visibility ?? null,
          notes: data.notes ?? null,
          sex: data.sex ?? "unknown",
          userId: user.id,
          username: user.username,
        };
        await createObservation({
          ...newObservationData,
          machineObservation: "User Observation",
        });
      }
      onObservationUpserted();
      onClose();
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error(`ObservationModal: Failed to ${mode} observation:`, err);
      setError(`Failed to ${mode} observation. Please try again.`);
    } finally {
      setLoading(false);
    }
  };

  const dialogTitle =
    mode === "add" ? "Add New Observation" : "Edit Observation";
  const dialogDescription =
    mode === "add"
      ? "Fill in the details for your new marine species observation."
      : "Make changes to your observation here. Click save when you're done.";
  const submitButtonText =
    mode === "add" ? "Create Observation" : "Save Changes";

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="fixed left-[50%] top-[50%] translate-x-[-50%] translate-y-[-50%] max-h-[90vh] w-[90vw] max-w-md flex flex-col p-0 z-[1050]">
        <DialogHeader className="p-6 pb-2">
          <DialogTitle>{dialogTitle}</DialogTitle>
          <DialogDescription>{dialogDescription}</DialogDescription>
        </DialogHeader>
        <ScrollArea className="flex-1 p-6 overflow-y-auto">
          {(mode === "add" || (mode === "edit" && observation)) && (
            // eslint-disable-next-line react/jsx-props-no-spreading
            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="space-y-6"
              >
                <ShadcnFormField
                  control={form.control}
                  name="speciesName"
                  render={({ field: formField }) => (
                    <FormItem>
                      <FormLabel>Species *</FormLabel>
                      <FormControl>
                        <SpeciesSearch
                          value={selectedSpecies}
                          onChange={(species) => {
                            setSelectedSpecies(species);
                            if (species) {
                              form.setValue("speciesName", species.speciesName);
                              form.setValue(
                                "commonName",
                                species.commonName || null,
                              );
                            } else {
                              form.setValue("speciesName", "");
                              form.setValue("commonName", null);
                            }
                          }}
                          onBlur={formField.onBlur} // Pass onBlur from react-hook-form
                          disabled={loading}
                          placeholder="Search for species by scientific or common name..."
                          error={!!form.formState.errors.speciesName}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                {observationFormFields.map((field: FormField) => (
                  <ShadcnFormField
                    key={field.name}
                    control={form.control}
                    name={field.name as FieldPath<ObservationFormData>}
                    render={({ field: formField }) => (
                      <FormItem>
                        <FormLabel>
                          {field.label}
                          {!field.optional && " *"}
                        </FormLabel>
                        <FormControl>
                          {renderFieldControl(field, formField, loading)}
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                ))}
                {error && (
                  <p className="text-red-500 text-sm text-center">{error}</p>
                )}
                <Button type="submit" className="w-full" disabled={loading}>
                  {loading ? "Processing..." : submitButtonText}
                </Button>
              </form>
            </Form>
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
