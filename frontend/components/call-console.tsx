"use client";

import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Phone, Pause, Play, DollarSign } from "lucide-react";
import { getProviderStatus, startCalls, type Provider } from "@/lib/api";

interface CallConsoleProps {
  searchQuery: string;
  priceLimit: string;
  zipcode: string;
  providers: Provider[]; // Initial providers from API
  jobId: string; // Job ID for polling
}

type CallStatus = "calling" | "negotiating" | "ended";

export function CallConsole({
  searchQuery,
  priceLimit,
  zipcode,
  providers: initialProviders,
  jobId,
}: CallConsoleProps) {
  const [providers, setProviders] = useState<Provider[]>(initialProviders);
  const [currentProviderIndex, setCurrentProviderIndex] = useState(0);
  const [isPolling, setIsPolling] = useState(true);
  const [callsStarted, setCallsStarted] = useState(false);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Find the current active provider (one that's in_progress or the first pending)
  const activeProvider =
    providers.find((p, idx) => {
      if (p.call_status === "in_progress") return true;
      if (idx === currentProviderIndex && p.call_status === "pending")
        return true;
      return false;
    }) ||
    providers[currentProviderIndex] ||
    providers[0];

  // Map backend call_status to frontend CallStatus
  const getCallStatus = (provider: Provider | undefined): CallStatus => {
    if (!provider) return "calling";
    const status = provider.call_status;
    if (status === "in_progress") return "negotiating";
    if (status === "completed" || status === "failed") return "ended";
    return "calling";
  };

  const currentCallStatus = getCallStatus(activeProvider);

  // Start calls when component mounts
  useEffect(() => {
    const triggerCalls = async () => {
      if (callsStarted || providers.length === 0) return;

      try {
        await startCalls(jobId);
        setCallsStarted(true);
        console.log("✅ Calls started for job:", jobId);
      } catch (error) {
        console.error("Failed to start calls:", error);
      }
    };

    triggerCalls();
  }, [jobId, callsStarted, providers.length]);

  // Poll for provider status updates
  useEffect(() => {
    if (!isPolling || !jobId) return;

    const pollStatus = async () => {
      try {
        const updatedProviders = await getProviderStatus(jobId);
        setProviders(updatedProviders);

        // Update current provider index based on call status
        const inProgressIndex = updatedProviders.findIndex(
          (p) => p.call_status === "in_progress"
        );
        if (inProgressIndex !== -1) {
          setCurrentProviderIndex(inProgressIndex);
        } else {
          // Find first pending provider
          const pendingIndex = updatedProviders.findIndex(
            (p) => p.call_status === "pending"
          );
          if (pendingIndex !== -1) {
            setCurrentProviderIndex(pendingIndex);
          }
        }

        // Check if all calls are complete
        const allComplete = updatedProviders.every(
          (p) => p.call_status === "completed" || p.call_status === "failed"
        );
        if (allComplete) {
          setIsPolling(false);
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
          }
        }
      } catch (error) {
        console.error("Failed to poll provider status:", error);
      }
    };

    // Poll immediately, then every 3 seconds
    pollStatus();
    pollingIntervalRef.current = setInterval(pollStatus, 3000);

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, [jobId, isPolling]);

  const getStatusText = (status: CallStatus) => {
    switch (status) {
      case "calling":
        return "Calling...";
      case "negotiating":
        return "In Negotiation...";
      case "ended":
        return "Call Ended";
      default:
        return "Idle";
    }
  };

  const getStatusColor = (status: CallStatus) => {
    switch (status) {
      case "calling":
        return "bg-blue-500/20 text-blue-400 border-blue-500/40";
      case "negotiating":
        return "bg-yellow-500/20 text-yellow-400 border-yellow-500/40";
      case "ended":
        return "bg-green-500/20 text-green-400 border-green-500/40";
      default:
        return "bg-gray-700 text-gray-400 border-gray-600";
    }
  };

  // Handle empty providers
  if (providers.length === 0) {
    return (
      <div className="min-h-screen p-4 md:p-8 bg-gradient-to-b from-gray-900 via-gray-900 to-gray-800">
        <div className="max-w-6xl mx-auto space-y-6">
          <div className="space-y-2">
            <h1 className="text-3xl font-bold text-white">Call Console</h1>
            <p className="text-gray-400">
              Request: {searchQuery} • {zipcode} • Budget: {priceLimit}
            </p>
          </div>
          <Card className="bg-gray-800 border-white">
            <CardContent className="py-12 text-center">
              <p className="text-gray-400">No providers found in your area.</p>
              <p className="text-sm text-gray-500 mt-2">
                Try adjusting your search or location.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4 md:p-8 bg-gradient-to-b from-gray-900 via-gray-900 to-gray-800">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-3xl font-bold text-white">Call Console</h1>
          <p className="text-gray-400">
            Request: {searchQuery} • {zipcode} • Budget: {priceLimit}
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Providers List */}
          <Card className="bg-gray-800 border-white">
            <CardHeader>
              <CardTitle className="text-white">
                Service Providers ({providers.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {providers.map((provider, index) => {
                const isActive = provider.id === activeProvider?.id;
                const providerStatus = getCallStatus(provider);
                const statusColor = getStatusColor(providerStatus);

                return (
                  <div
                    key={provider.id}
                    className={`p-4 rounded-lg border transition-colors ${
                      isActive
                        ? "bg-white/10 border-white"
                        : "bg-gray-900 border-white/30"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <h3 className="font-semibold text-white">
                          {provider.name}
                        </h3>
                        <div className="flex items-center gap-2 text-sm text-gray-400">
                          <Phone className="h-3 w-3" />
                          {provider.phone || "No phone"}
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        {provider.estimated_price && (
                          <Badge
                            variant="secondary"
                            className="text-sm bg-white/20 text-white border-white/30"
                          >
                            ${provider.estimated_price}
                          </Badge>
                        )}
                        {provider.call_status && (
                          <Badge className={`text-xs ${statusColor}`}>
                            {provider.call_status}
                          </Badge>
                        )}
                      </div>
                    </div>

                    {provider.negotiated_price && (
                      <div className="mt-3 pt-3 border-t border-white/30">
                        <div className="flex items-center gap-2 text-green-400 font-semibold">
                          <DollarSign className="h-4 w-4" />
                          Negotiated: ${provider.negotiated_price}
                        </div>
                      </div>
                    )}

                    {provider.call_status === "completed" &&
                      !provider.negotiated_price && (
                        <div className="mt-3 text-xs text-gray-500">
                          Call completed - no price agreed
                        </div>
                      )}

                    {provider.call_status === "failed" && (
                      <div className="mt-3 text-xs text-red-400">
                        Call failed
                      </div>
                    )}
                  </div>
                );
              })}
            </CardContent>
          </Card>

          {/* Call Status */}
          <div className="space-y-6">
            <Card className="bg-gray-800 border-white">
              <CardHeader>
                <CardTitle className="text-white">Current Call</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {activeProvider ? (
                  <>
                    <div className="space-y-2">
                      <div className="text-sm text-gray-400">Provider</div>
                      <div className="text-lg font-semibold text-white">
                        {activeProvider.name}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <div className="text-sm text-gray-400">Phone</div>
                      <div className="text-base text-white">
                        {activeProvider.phone || "No phone available"}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <div className="text-sm text-gray-400">Status</div>
                      <Badge className={getStatusColor(currentCallStatus)}>
                        {getStatusText(currentCallStatus)}
                      </Badge>
                    </div>

                    {activeProvider.negotiated_price && (
                      <div className="space-y-2">
                        <div className="text-sm text-gray-400">Final Price</div>
                        <div className="text-2xl font-bold text-green-400">
                          ${activeProvider.negotiated_price}
                        </div>
                        {activeProvider.estimated_price && (
                          <div className="text-xs text-gray-500">
                            Saved $
                            {activeProvider.estimated_price -
                              activeProvider.negotiated_price}
                          </div>
                        )}
                      </div>
                    )}
                  </>
                ) : (
                  <div className="py-8 text-center">
                    <div className="text-lg font-semibold mb-2 text-white">
                      No Active Calls
                    </div>
                    <p className="text-sm text-gray-400">
                      Waiting for calls to start...
                    </p>
                  </div>
                )}

                {!isPolling &&
                  providers.every(
                    (p) =>
                      p.call_status === "completed" ||
                      p.call_status === "failed"
                  ) && (
                    <div className="mt-4 pt-4 border-t border-white/30">
                      <div className="text-sm font-semibold mb-1 text-white">
                        All Calls Complete
                      </div>
                      <p className="text-xs text-gray-400">
                        We've contacted all {providers.length} providers in your
                        area.
                      </p>
                    </div>
                  )}
              </CardContent>
            </Card>

            {/* Control Buttons (Representational Only) */}
            <Card className="bg-gray-800 border-white">
              <CardHeader>
                <CardTitle className="text-white">Controls</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="lg"
                    className="w-full bg-transparent border-white text-white hover:bg-gray-700"
                    disabled
                  >
                    {isPolling ? (
                      <>
                        <Pause className="mr-2 h-5 w-5" />
                        Monitoring Calls...
                      </>
                    ) : (
                      <>
                        <Play className="mr-2 h-5 w-5" />
                        All Complete
                      </>
                    )}
                  </Button>
                </div>
                <p className="text-xs text-gray-500 text-center">
                  {isPolling
                    ? "Polling for updates every 3 seconds"
                    : "All calls have completed"}
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
