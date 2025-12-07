"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import { ArrowRight } from "lucide-react"
import type { Question } from "@/lib/api"

interface QuestionsFlowProps {
  searchQuery: string
  task: string
  questions: Question[]  // Dynamic questions from Grok LLM
  onComplete: (answers: Record<string, string>) => void
}

export function QuestionsFlow({ searchQuery, task, questions, onComplete }: QuestionsFlowProps) {
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string>>({})

  const handleNext = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1)
    } else {
      // Pass answers to parent when complete
      onComplete(answers)
    }
  }

  const handleAnswer = (value: string) => {
    setAnswers({ ...answers, [questions[currentQuestion].id]: value })
  }

  const progress = ((currentQuestion + 1) / questions.length) * 100
  const currentQ = questions[currentQuestion]

  // Handle case where questions array is empty
  if (questions.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-b from-gray-900 via-gray-900 to-gray-800">
        <div className="text-center space-y-4">
          <p className="text-gray-400">No questions to display.</p>
          <Button onClick={() => onComplete({})} className="bg-white text-black hover:bg-gray-200">Continue</Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-b from-gray-900 via-gray-900 to-gray-800">
      <div className="w-full max-w-2xl space-y-8 animate-in fade-in duration-500">
        {/* Progress */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm text-gray-400">
            <span>
              Question {currentQuestion + 1} of {questions.length}
            </span>
            <span>{Math.round(progress)}%</span>
          </div>
          <Progress value={progress} className="h-2 bg-gray-800" />
        </div>

        {/* Question Card */}
        <div className="bg-gray-800 border border-white rounded-lg p-8 space-y-6">
          <div className="space-y-2">
            <p className="text-sm text-gray-400">
              {task && `Service: ${task} • `}Request: {searchQuery}
            </p>
            <h2 className="text-2xl font-semibold text-white text-balance">{currentQ.question}</h2>
          </div>

          {/* Answer Input - All questions use text input for simplicity */}
          <div className="space-y-4">
            <Input
              type="text"
              placeholder="Type your answer..."
              value={answers[currentQ.id] || ""}
              onChange={(e) => handleAnswer(e.target.value)}
              className="h-12 bg-transparent border-white text-white placeholder:text-gray-400 rounded-3xl"
              onKeyDown={(e) => {
                if (e.key === "Enter" && answers[currentQ.id]) {
                  handleNext()
                }
              }}
            />
          </div>

          {/* Navigation */}
          <div className="flex justify-end">
            <Button onClick={handleNext} disabled={!answers[currentQ.id]} size="lg" className="bg-white text-black hover:bg-gray-200">
              {currentQuestion < questions.length - 1 ? (
                <>
                  Next <ArrowRight className="ml-2 h-4 w-4" />
                </>
              ) : (
                "Find Providers"
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
