import { Calendar } from "lucide-react";

import { NotConnected } from "@/components/layout/not-connected";

export default function CalendarPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-8 md:px-8">
      <h1 className="text-xl font-semibold text-neutral-50">Calendar</h1>
      <p className="mb-6 text-sm text-neutral-500">
        Google, Microsoft, and Yahoo calendar integration.
      </p>
      <NotConnected
        icon={Calendar}
        title="No calendar connected yet"
        description="Calendar integration (Google/Microsoft OAuth) is planned but not wired up in this environment — it needs real OAuth app credentials to build and test safely."
      />
    </div>
  );
}
