import { Cloud } from "lucide-react";

import { NotConnected } from "@/components/layout/not-connected";

export default function WeatherPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-8 md:px-8">
      <h1 className="text-xl font-semibold text-neutral-50">Weather</h1>
      <p className="mb-6 text-sm text-neutral-500">Local forecast for your primary location.</p>
      <NotConnected
        icon={Cloud}
        title="No weather provider connected yet"
        description="Weather integration is planned but needs a provider API key (e.g. OpenWeather) configured in the backend before it can be wired up."
      />
    </div>
  );
}
