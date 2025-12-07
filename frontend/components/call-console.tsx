"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Phone, Pause, Play, DollarSign } from "lucide-react"
import type { Provider } from "@/lib/api"

interface CallConsoleProps {
  searchQuery: string
  priceLimit: string
  zipcode: string
  providers: Provider[]  // Real providers from API
}

type CallStatus = "calling" | "negotiating" | "ended"

export function CallConsole({ searchQuery, priceLimit, zipcode, providers }: CallConsoleProps) {
  const [currentProvider, setCurrentProvider] = useState(0)
  const [callStatus, setCallStatus] = useState<CallStatus>("calling")
  const [negotiatedPrice, setNegotiatedPrice] = useState<number | null>(null)
  const [isRunning, setIsRunning] = useState(true)

  useEffect(() => {
    if (!isRunning || providers.length === 0) return

    // Simulate call progression
    const timer = setTimeout(() => {
      if (callStatus === "calling") {
        setCallStatus("negotiating")
      } else if (callStatus === "negotiating") {
        const provider = providers[currentProvider]
        // Simulate negotiated price (10-20% off estimated price, or random if no estimate)
        const basePrice = provider.estimated_price || 150
        const discount = Math.floor(basePrice * (0.1 + Math.random() * 0.1))
        setNegotiatedPrice(basePrice - discount)
        setCallStatus("ended")
      } else if (callStatus === "ended") {
        if (currentProvider < providers.length - 1) {
          setCurrentProvider(currentProvider + 1)
          setCallStatus("calling")
          setNegotiatedPrice(null)
        } else {
          setIsRunning(false)
        }
      }
    }, 3000)

    return () => clearTimeout(timer)
  }, [callStatus, currentProvider, isRunning, providers])

  const getStatusText = () => {
    switch (callStatus) {
      case "calling":
        return "Calling..."
      case "negotiating":
        return "In Negotiation..."
      case "ended":
        return "Call Ended"
      default:
        return "Idle"
    }
  }

  const getStatusColor = () => {
    switch (callStatus) {
      case "calling":
        return "bg-blue-500/20 text-blue-400 border-blue-500/40"
      case "negotiating":
        return "bg-yellow-500/20 text-yellow-400 border-yellow-500/40"
      case "ended":
        return "bg-green-500/20 text-green-400 border-green-500/40"
      default:
        return "bg-gray-700 text-gray-400 border-gray-600"
    }
  }

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
              <p className="text-sm text-gray-500 mt-2">Try adjusting your search or location.</p>
            </CardContent>
          </Card>
        </div>
      </div>
    )
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
              <CardTitle className="text-white">Service Providers ({providers.length})</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {providers.map((provider, index) => (
                <div
                  key={provider.id}
                  className={`p-4 rounded-lg border transition-colors ${
                    index === currentProvider && isRunning ? "bg-white/10 border-white" : "bg-gray-900 border-white/30"
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <h3 className="font-semibold text-white">{provider.name}</h3>
                      <div className="flex items-center gap-2 text-sm text-gray-400">
                        <Phone className="h-3 w-3" />
                        {provider.phone || "No phone"}
                      </div>
                    </div>
                    {provider.estimated_price && (
                      <Badge variant="secondary" className="text-sm bg-white/20 text-white border-white/30">
                        ${provider.estimated_price}
                      </Badge>
                    )}
                  </div>

                  {index === currentProvider && callStatus === "ended" && negotiatedPrice && (
                    <div className="mt-3 pt-3 border-t border-white/30">
                      <div className="flex items-center gap-2 text-green-400 font-semibold">
                        <DollarSign className="h-4 w-4" />
                        Negotiated: ${negotiatedPrice}
                      </div>
                    </div>
                  )}

                  {index < currentProvider && <div className="mt-3 text-xs text-gray-500">Completed</div>}
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Call Status */}
          <div className="space-y-6">
            <Card className="bg-gray-800 border-white">
              <CardHeader>
                <CardTitle className="text-white">Current Call</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {isRunning ? (
                  <>
                    <div className="space-y-2">
                      <div className="text-sm text-gray-400">Provider</div>
                      <div className="text-lg font-semibold text-white">{providers[currentProvider].name}</div>
                    </div>

                    <div className="space-y-2">
                      <div className="text-sm text-gray-400">Phone</div>
                      <div className="text-base text-white">{providers[currentProvider].phone || "No phone available"}</div>
                    </div>

                    <div className="space-y-2">
                      <div className="text-sm text-gray-400">Status</div>
                      <Badge className={getStatusColor()}>{getStatusText()}</Badge>
                    </div>

                    {negotiatedPrice && (
                      <div className="space-y-2">
                        <div className="text-sm text-gray-400">Final Price</div>
                        <div className="text-2xl font-bold text-green-400">${negotiatedPrice}</div>
                        {providers[currentProvider].estimated_price && (
                          <div className="text-xs text-gray-500">
                            Saved ${providers[currentProvider].estimated_price! - negotiatedPrice}
                          </div>
                        )}
                      </div>
                    )}
                  </>
                ) : (
                  <div className="py-8 text-center">
                    <div className="text-lg font-semibold mb-2 text-white">All Calls Complete</div>
                    <p className="text-sm text-gray-400">
                      We've contacted all {providers.length} providers in your area.
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
                  <Button variant="outline" size="lg" className="w-full bg-transparent border-white text-white hover:bg-gray-700" disabled>
                    {callStatus === "ended" && isRunning ? (
                      <>
                        <Play className="mr-2 h-5 w-5" />
                        Continue
                      </>
                    ) : (
                      <>
                        <Pause className="mr-2 h-5 w-5" />
                        Running...
                      </>
                    )}
                  </Button>
                </div>
                <p className="text-xs text-gray-500 text-center">System automatically manages calls</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
