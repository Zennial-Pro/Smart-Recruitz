import { z } from "zod";

export const registrationSchema = z.object({
  full_name: z
    .string()
    .min(2, "Name must be at least 2 characters")
    .max(255),
  email: z.string().email("Invalid email address"),
  phone: z
    .string()
    .min(10, "Phone number must be at least 10 digits")
    .max(15),
  target_role: z.string().optional(),
});

export type RegistrationFormData = z.infer<typeof registrationSchema>;
