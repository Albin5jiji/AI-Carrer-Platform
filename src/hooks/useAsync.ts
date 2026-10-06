import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "../api/client";

export type AsyncState<T> = {
  data: T | null;
  error: string;
  loading: boolean;
  reload: () => void;
  setData: (value: T | null) => void;
};

/** Minimal data loading hook: loading flag, readable error, manual reload. */
export function useAsync<T>(loader: () => Promise<T>, key: string = ""): AsyncState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const loaderRef = useRef(loader);
  loaderRef.current = loader;

  const run = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await loaderRef.current();
      setData(result);
    } catch (caught) {
      const message =
        caught instanceof ApiError
          ? caught.message
          : caught instanceof Error
            ? caught.message
            : "Something went wrong while loading data";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void run();
    // `key` is the intended dependency: it changes when the caller wants fresh data.
  }, [key, run]);

  return { data, error, loading, reload: () => void run(), setData };
}

/** Small helper for form submissions and one-off actions. */
export function useAction() {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const run = useCallback(async <T,>(task: () => Promise<T>): Promise<T | false> => {
    setPending(true);
    setError("");
    setSuccess("");
    try {
      const result = await task();
      if (typeof result === "string") setSuccess(result);
      return result;
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : caught instanceof Error
            ? caught.message
            : "The action could not be completed",
      );
      return false;
    } finally {
      setPending(false);
    }
  }, []);

  return { pending, error, success, run, setError, setSuccess };
}
