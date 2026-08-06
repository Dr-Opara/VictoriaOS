import * as React from "react";

import { cn } from "@/lib/utils";

const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        ref={ref}
        className={cn(
          "flex h-9 w-full rounded-lg border border-[var(--border)] bg-white/[0.02] px-3 py-1 text-sm text-[var(--foreground)] placeholder:text-[var(--muted)] outline-none transition-colors focus-visible:border-[var(--accent)] focus-visible:glow-cyan disabled:cursor-not-allowed disabled:opacity-50",
          className,
        )}
        {...props}
      />
    );
  },
);
Input.displayName = "Input";

export { Input };
