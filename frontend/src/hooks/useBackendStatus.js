import { useCallback, useEffect, useState } from "react";
import { checkHealth } from "../api";

/** Polls /health so the UI can say plainly when the backend isn't running. */
export function useBackendStatus(intervalMs = 15_000) {
  const [status, setStatus] = useState("checking"); // checking | online | offline

  const check = useCallback(async () => {
    try {
      await checkHealth();
      setStatus("online");
    } catch {
      setStatus("offline");
    }
  }, []);

  useEffect(() => {
    check();
    const timer = setInterval(check, intervalMs);
    return () => clearInterval(timer);
  }, [check, intervalMs]);

  return { status, recheck: check };
}
