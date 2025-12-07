"use client"

import type React from "react"

import { useState } from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { CalendarIcon, Search } from "lucide-react"
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
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-4xl space-y-8 animate-in fade-in duration-700">
        {/* Title */}
        <h1 className="text-7xl md:text-8xl font-bold text-center tracking-tight text-balance">Haggle</h1>

        {/* Search Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Main Search Bar */}
          <div className="flex flex-col gap-4">
            <Input
              type="text"
              placeholder="What service do you need? (e.g., Fix my toilet)"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="h-14 text-lg px-6 bg-card border-border"
            />

            {/* House Address */}
            <Input
              type="text"
              placeholder="House Address (e.g., 123 Main St, San Jose, CA)"
              value={houseAddress}
              onChange={(e) => setHouseAddress(e.target.value)}
              className="h-12 bg-card border-border"
            />

            {/* Constants Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Price Limit */}
              <Select value={priceLimit} onValueChange={setPriceLimit}>
                <SelectTrigger className="h-12 bg-card border-border">
                  <SelectValue placeholder="Price Limit" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="$50">$50</SelectItem>
                  <SelectItem value="$100">$100</SelectItem>
                  <SelectItem value="$150">$150</SelectItem>
                  <SelectItem value="$200">$200</SelectItem>
                  <SelectItem value="$250">$250</SelectItem>
                  <SelectItem value="$300">$300</SelectItem>
                  <SelectItem value="$500">$500</SelectItem>
                  <SelectItem value="$1000">$1000</SelectItem>
                  <SelectItem value="No Limit">No Limit</SelectItem>
                </SelectContent>
              </Select>

              {/* Zipcode */}
              <Input
                type="text"
                placeholder="Zipcode"
                value={zipcode}
                onChange={(e) => setZipcode(e.target.value)}
                maxLength={10}
                className="h-12 bg-card border-border"
              />

              {/* Date Picker */}
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" className="h-12 justify-start text-left font-normal bg-card border-border">
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {date ? format(date, "PPP") : "Date Needed"}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar mode="single" selected={date} onSelect={setDate} initialFocus />
                </PopoverContent>
              </Popover>
            </div>
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            size="lg"
            className="w-full h-12 text-base"
            disabled={!query.trim() || !houseAddress.trim() || !zipcode.trim() || !date}
          >
            <Search className="mr-2 h-5 w-5" />
            Find Providers
          </Button>
        </form>
      </div>
    </div>
  )
}
