"use client"

import type React from "react"

import { useState } from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { CalendarIcon, Search, MapPin } from "lucide-react"
import { format } from "date-fns"

interface LandingPageProps {
  onStartSearch: (query: string, priceLimit: string, houseAddress: string, zipcode: string, date: string) => void
}

export function LandingPage({ onStartSearch }: LandingPageProps) {
  const [query, setQuery] = useState("")
  const [priceLimit, setPriceLimit] = useState("$200")
  const [houseAddress, setHouseAddress] = useState("")
  const [zipcode, setZipcode] = useState("")
  const [date, setDate] = useState<Date>()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim() && houseAddress.trim() && zipcode.trim() && date) {
      onStartSearch(query, priceLimit, houseAddress, zipcode, format(date, "PPP"))
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-b from-gray-900 via-gray-900 to-gray-800">
      <div className="w-full max-w-4xl space-y-8 animate-in fade-in duration-700">
        {/* Title */}
        <h1 className="text-8xl md:text-9xl font-bold text-center tracking-tight text-balance font-serif text-white">Haggle 🤝</h1>

        {/* Search Form */}
        <form onSubmit={handleSubmit} className="space-y-3">
          {/* Main Search Bar */}
          <div className="flex flex-col gap-3">
            {/* Row 1: Service Query */}
            <Input
              type="text"
              placeholder="What service do you need? (e.g., Fix my toilet)"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="h-14 text-sm px-6 bg-transparent border-white text-white placeholder:text-gray-400 rounded-3xl"
            />

            {/* Row 2: Price, Address, Zipcode, Date */}
            <div className="flex flex-wrap justify-center items-center gap-3">
              {/* Price Limit */}
              <Select value={priceLimit} onValueChange={setPriceLimit}>
                <SelectTrigger className="h-12 min-h-12 w-40 bg-transparent border-white text-white rounded-3xl px-4 py-0 flex items-center leading-normal text-sm">
                  <span className="text-gray-400 mr-1 text-sm">Limit:</span>
                  <SelectValue placeholder="Price Limit" className="text-white text-sm" />
                </SelectTrigger>
                <SelectContent className="bg-gray-800 border-white text-white">
                  <SelectItem value="$50" className="text-white hover:bg-gray-700">$50</SelectItem>
                  <SelectItem value="$100" className="text-white hover:bg-gray-700">$100</SelectItem>
                  <SelectItem value="$150" className="text-white hover:bg-gray-700">$150</SelectItem>
                  <SelectItem value="$200" className="text-white hover:bg-gray-700">$200</SelectItem>
                  <SelectItem value="$250" className="text-white hover:bg-gray-700">$250</SelectItem>
                  <SelectItem value="$300" className="text-white hover:bg-gray-700">$300</SelectItem>
                  <SelectItem value="$500" className="text-white hover:bg-gray-700">$500</SelectItem>
                  <SelectItem value="$1000" className="text-white hover:bg-gray-700">$1000</SelectItem>
                  <SelectItem value="No Limit" className="text-white hover:bg-gray-700">No Limit</SelectItem>
                </SelectContent>
              </Select>

              {/* House Address */}
              <div className="relative">
                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  type="text"
                  placeholder="Address"
                  value={houseAddress}
                  onChange={(e) => setHouseAddress(e.target.value)}
                  className="h-12 min-h-12 w-44 pl-10 bg-transparent border-white text-white placeholder:text-gray-400 rounded-3xl leading-normal text-sm"
                />
              </div>

              {/* Zipcode */}
              <Input
                type="text"
                placeholder="Zipcode"
                value={zipcode}
                onChange={(e) => setZipcode(e.target.value)}
                maxLength={10}
                className="h-12 min-h-12 w-28 bg-transparent border-white text-white placeholder:text-gray-400 rounded-3xl leading-normal text-sm"
              />

              {/* Date Picker */}
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" className="h-12 min-h-12 w-36 justify-start text-left font-normal bg-transparent border-white text-white hover:bg-gray-800 rounded-3xl px-4 py-0 leading-normal text-sm">
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {date ? format(date, "PP") : "Date"}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0 bg-gray-800 border-white" align="start">
                  <Calendar mode="single" selected={date} onSelect={setDate} initialFocus />
                </PopoverContent>
              </Popover>
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex justify-center">
            <Button
              type="submit"
              size="lg"
              className="h-12 text-base bg-white text-black hover:bg-gray-200 rounded-3xl border-0 transition-colors px-16"
              disabled={!query.trim() || !houseAddress.trim() || !zipcode.trim() || !date}
            >
              <Search className="mr-2 h-5 w-5" />
              Find Providers
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
