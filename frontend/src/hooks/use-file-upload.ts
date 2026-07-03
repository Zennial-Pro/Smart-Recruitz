"use client";

import { useState, useCallback } from "react";
import type { TaskCreatedResponse } from "@/types";
import { api } from "@/lib/api-client";

interface UseFileUploadOptions {
  endpoint: string;
  fieldName?: string;
  extraFields?: Record<string, string>;
}

export function useFileUpload({ endpoint, fieldName = "file", extraFields }: UseFileUploadOptions) {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const upload = useCallback(
    async (file: File): Promise<TaskCreatedResponse | null> => {
      setIsUploading(true);
      setError(null);

      try {
        const form = new FormData();
        form.set(fieldName, file);

        if (extraFields) {
          for (const [key, value] of Object.entries(extraFields)) {
            form.set(key, value);
          }
        }

        const result = await api.post(endpoint, { body: form }).json<TaskCreatedResponse>();
        return result;
      } catch (err) {
        const message = err instanceof Error ? err.message : "Upload failed";
        setError(message);
        return null;
      } finally {
        setIsUploading(false);
      }
    },
    [endpoint, fieldName, extraFields]
  );

  return { upload, isUploading, error };
}
