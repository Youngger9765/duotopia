/**
 * Batch Operation Utilities
 *
 * Provides rate-limited batch processing to prevent DOS and server overload.
 */

export interface BatchDeleteResult {
  succeeded: string[];
  failed: Array<{ id: string; error: string }>;
}

/**
 * Delete items in batches with rate limiting
 *
 * @param ids - Array of item IDs to delete
 * @param deleteFunc - Async function to delete a single item (returns true on success)
 * @param options - Configuration options
 * @returns Results with succeeded and failed deletions
 */
export async function deleteInBatches(
  ids: string[],
  deleteFunc: (id: string) => Promise<boolean>,
  options: {
    batchSize?: number;
    delayMs?: number;
    onProgress?: (completed: number, total: number) => void;
  } = {},
): Promise<BatchDeleteResult> {
  const { batchSize = 5, delayMs = 100, onProgress } = options;

  const result: BatchDeleteResult = {
    succeeded: [],
    failed: [],
  };

  // Process in batches
  for (let i = 0; i < ids.length; i += batchSize) {
    const batch = ids.slice(i, i + batchSize);

    // Process current batch in parallel
    const batchResults = await Promise.allSettled(
      batch.map(async (id) => {
        try {
          const success = await deleteFunc(id);
          if (success) {
            return { success: true, id };
          } else {
            return { success: false, id, error: "Delete failed" };
          }
        } catch (error) {
          return {
            success: false,
            id,
            error: error instanceof Error ? error.message : String(error),
          };
        }
      }),
    );

    // Collect results
    batchResults.forEach((batchResult, index) => {
      if (batchResult.status === "fulfilled") {
        const { success, id, error } = batchResult.value;
        if (success) {
          result.succeeded.push(id);
        } else {
          result.failed.push({ id, error: error || "Unknown error" });
        }
      } else {
        // Promise rejected
        const id = batch[index];
        result.failed.push({
          id,
          error: batchResult.reason?.message || "Promise rejected",
        });
      }
    });

    // Report progress
    if (onProgress) {
      onProgress(i + batch.length, ids.length);
    }

    // Delay before next batch (except for last batch)
    if (i + batchSize < ids.length) {
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
  }

  return result;
}

/**
 * Helper to format batch operation results for user display
 */
export function formatBatchResult(result: BatchDeleteResult): string {
  const total = result.succeeded.length + result.failed.length;
  const succeeded = result.succeeded.length;
  const failed = result.failed.length;

  if (failed === 0) {
    return `Successfully deleted ${succeeded} item(s)`;
  } else if (succeeded === 0) {
    return `Failed to delete all ${failed} item(s)`;
  } else {
    return `Deleted ${succeeded} of ${total} item(s). ${failed} failed.`;
  }
}
