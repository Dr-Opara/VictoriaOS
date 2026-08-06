import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "border-transparent bg-[var(--accent)] text-[#03181b]",
        secondary: "border-transparent bg-white/[0.06] text-[var(--foreground)]",
        outline: "border-[var(--border)] text-[var(--muted)]",
        success: "border-transparent bg-[var(--success)]/15 text-[var(--success)]",
        warning: "border-transparent bg-[var(--warning)]/15 text-[var(--warning)]",
        destructive: "border-transparent bg-[var(--danger)]/15 text-[var(--danger)]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
