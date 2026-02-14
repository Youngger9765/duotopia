import { BookA, BookText, FileText, type LucideIcon } from "lucide-react";

/**
 * Returns the appropriate Lucide icon for a given content type.
 *
 * - VOCABULARY_SET → BookA
 * - EXAMPLE_SENTENCES → BookText
 * - Others → FileText (default)
 */
export function getContentTypeIcon(type?: string | null): LucideIcon {
  switch (type?.toUpperCase()) {
    case "VOCABULARY_SET":
      return BookA;
    case "EXAMPLE_SENTENCES":
      return BookText;
    default:
      return FileText;
  }
}
