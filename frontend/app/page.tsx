"use client"

import { useState } from "react"
import { LandingPage } from "@/components/landing-page"
import { QuestionsFlow } from "@/components/questions-flow"
import { CallConsole } from "@/components/call-console"
import { startJob, completeJob, type Question, type Provider } from "@/lib/api"

type Screen = "landing" | "loading-questions" | "questions" | "loading-console" | "console"

export default function Home() {
  const [screen, setScreen] = useState<Screen>("landing")
  const [searchQuery, setSearchQuery] = useState("")
  const [priceLimit, setPriceLimit] = useState("$200")
  const [houseAddress, setHouseAddress] = useState("")
  const [zipcode, setZipcode] = useState("")
  const [dateNeeded, setDateNeeded] = useState("")
  
  // New state for API data
  const [jobId, setJobId] = useState<string>("")
  const [task, setTask] = useState<string>("")
  const [questions, setQuestions] = useState<Question[]>([])
  const [providers, setProviders] = useState<Provider[]>([])
  const [error, setError] = useState<string | null>(null)

  const handleStartSearch = async (query: string, price: string, address: string, zip: string, date: string) => {
    setSearchQuery(query)
    setPriceLimit(price)
    setHouseAddress(address)
    setZipcode(zip)
    setDateNeeded(date)
    setError(null)
    setScreen("loading-questions")

    try {
      // Call the backend API to start job and get LLM-generated questions
      const response = await startJob(query, address, zip, price, date)
      
      setJobId(response.job_id)
      setTask(response.task)
      setQuestions(response.questions)
      setScreen("questions")
    } catch (err) {
      console.error("Failed to start job:", err)
      setError(err instanceof Error ? err.message : "Failed to start job")
      setScreen("landing")
    }
  }

  const handleQuestionsComplete = async (answers: Record<string, string>) => {
    setError(null)
    setScreen("loading-console")

    try {
      // Call the backend API to complete job and get providers
      const response = await completeJob(jobId, answers)
      
      setProviders(response.providers)
      setScreen("console")
    } catch (err) {
      console.error("Failed to complete job:", err)
      setError(err instanceof Error ? err.message : "Failed to find providers")
      setScreen("questions")
    }
  }

  return (
    <div className="min-h-screen">
      {error && (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 bg-red-500/10 border border-red-500/20 text-red-500 px-4 py-2 rounded-lg z-50">
          {error}
        </div>
      )}

      {screen === "landing" && <LandingPage onStartSearch={handleStartSearch} />}

      {screen === "loading-questions" && (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center space-y-4">
            <div className="w-16 h-16 border-4 border-primary/30 border-t-primary rounded-full animate-spin mx-auto" />
            <p className="text-muted-foreground">Analyzing your request with AI...</p>
          </div>
        </div>
      )}

      {screen === "questions" && (
        <QuestionsFlow 
          searchQuery={searchQuery} 
          task={task}
          questions={questions}
          onComplete={handleQuestionsComplete} 
        />
      )}

      {screen === "loading-console" && (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center space-y-4">
            <div className="w-16 h-16 border-4 border-primary/30 border-t-primary rounded-full animate-spin mx-auto" />
            <p className="text-muted-foreground">Finding providers near you...</p>
          </div>
        </div>
      )}

      {screen === "console" && (
        <CallConsole 
          searchQuery={searchQuery} 
          priceLimit={priceLimit} 
          zipcode={zipcode}
          providers={providers}
        />
      )}
    </div>
  )
}
