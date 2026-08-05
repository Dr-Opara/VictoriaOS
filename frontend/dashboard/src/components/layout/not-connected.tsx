import { type LucideIcon } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";

interface NotConnectedProps {
  icon: LucideIcon;
  title: string;
  description: string;
}

export function NotConnected({ icon: Icon, title, description }: NotConnectedProps) {
  return (
    <Card>
      <CardContent className="flex flex-col items-center gap-3 py-16 text-center">
        <Icon className="size-8 text-neutral-700" />
        <div>
          <p className="text-sm font-medium text-neutral-200">{title}</p>
          <p className="mt-1 max-w-sm text-sm text-neutral-500">{description}</p>
        </div>
      </CardContent>
    </Card>
  );
}
