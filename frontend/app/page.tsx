"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import {
  Search,
  Activity,
  User,
  Calendar,
  Weight,
  Ruler,
  Timer,
  Shield,
  Zap,
  Loader2,
  AlertCircle,
  CheckCircle,
  ArrowLeft,
  Bug,
} from "lucide-react"

// API configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "https://neurisk-backend.onrender.com"

export default function NeuriskApp() {
  const [activeTab, setActiveTab] = useState("test")
  const [searchQuery, setSearchQuery] = useState("")
  const [searchResults, setSearchResults] = useState<any[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)
  const [debugInfo, setDebugInfo] = useState<string[]>([])

  // Form and session states
  const [formData, setFormData] = useState({
    name: "",
    age: "25",
    height: "170",
    weight: "70",
    trainingFrequency: "3",
    previousInjury: "none",
    muscleGroup: "quadriceps",
    contractionType: "isometric",
    deviceId: "",
    sessionDuration: "5",
  })

  // Session states
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [timer, setTimer] = useState<number>(0)
  const [timerActive, setTimerActive] = useState(false)
  const [loading, setLoading] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const timerRef = useRef<NodeJS.Timeout | null>(null)

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  // Add debug info
  const addDebugInfo = (info: string) => {
    setDebugInfo((prev) => [...prev, `${new Date().toLocaleTimeString()}: ${info}`])
    console.log(info)
  }

  // Test backend connectivity with detailed debugging
  const testBackendConnection = async () => {
    addDebugInfo("Testing backend connectivity...")

    try {
      // Test OPTIONS request first
      const optionsResponse = await fetch(`${API_BASE_URL}/api/start_session/`, {
        method: "OPTIONS",
        headers: {
          "Content-Type": "application/json",
        },
      })
      addDebugInfo(`OPTIONS request: ${optionsResponse.status} ${optionsResponse.statusText}`)

      // Test a simple GET request to see if server responds
      try {
        const getResponse = await fetch(`${API_BASE_URL}/api/start_session/`, {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        })
        addDebugInfo(`GET request: ${getResponse.status} ${getResponse.statusText}`)
      } catch (e) {
        addDebugInfo(`GET request failed: ${e}`)
      }
    } catch (error) {
      addDebugInfo(`Connection test failed: ${error}`)
    }
  }

  // Start session handler with enhanced debugging
  const handleStartSession = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setResult(null)
    setProcessing(false)
    setLoading(true)
    setSessionId(null)
    setTimer(0)
    setDebugInfo([])

    try {
      const sessionData = {
        user: {
          // Changed from user_data to user
          name: formData.name,
          age: Number.parseInt(formData.age),
          height: Number.parseInt(formData.height),
          weight: Number.parseInt(formData.weight),
          training_frequency: Number.parseInt(formData.trainingFrequency),
          previous_injury: formData.previousInjury,
          muscle_group: formData.muscleGroup,
          contraction_type: formData.contractionType,
        },
        duration: Number.parseInt(formData.sessionDuration),
        device_id: formData.deviceId,
      }

      addDebugInfo(`Attempting POST to: ${API_BASE_URL}/api/start_session/`)
      addDebugInfo(`Request data: ${JSON.stringify(sessionData, null, 2)}`)

      // First test OPTIONS
      try {
        const optionsResponse = await fetch(`${API_BASE_URL}/api/start_session/`, {
          method: "OPTIONS",
          headers: {
            "Content-Type": "application/json",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
          },
        })
        addDebugInfo(`OPTIONS preflight: ${optionsResponse.status} ${optionsResponse.statusText}`)
      } catch (optionsError) {
        addDebugInfo(`OPTIONS preflight failed: ${optionsError}`)
      }

      // Now try the actual POST request
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 30000) // 30 second timeout

      const response = await fetch(`${API_BASE_URL}/api/start_session/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": "exempt", // Since you're using DRF APIView
        },
        body: JSON.stringify(sessionData),
        signal: controller.signal,
      })

      clearTimeout(timeoutId)
      addDebugInfo(`POST response: ${response.status} ${response.statusText}`)
      addDebugInfo(`Response headers: ${JSON.stringify([...response.headers.entries()])}`)

      if (!response.ok) {
        const errorText = await response.text()
        addDebugInfo(`Error response body: ${errorText}`)

        let errorData
        try {
          errorData = JSON.parse(errorText)
        } catch {
          errorData = { error: errorText }
        }

        throw new Error(errorData.error || errorData.detail || `HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      addDebugInfo(`Success response: ${JSON.stringify(data)}`)

      setSessionId(data.session_id.toString())
      setTimer(Number.parseInt(formData.sessionDuration))
      setTimerActive(true)
    } catch (err: any) {
      addDebugInfo(`Error caught: ${err.name}: ${err.message}`)

      if (err.name === "AbortError") {
        setError("Request timed out. The server may be slow to respond.")
      } else if (err.name === "TypeError" && err.message.includes("fetch")) {
        setError(`Network error: Cannot connect to ${API_BASE_URL}. Check if the server is accessible.`)
      } else if (err.message.includes("404")) {
        setError("API endpoint not found. The backend may not have the expected API routes configured.")
      } else if (err.message.includes("500")) {
        setError("Backend server error. There may be an issue with the Django application or database connection.")
      } else if (err.message.includes("CORS")) {
        setError("CORS error. The backend needs to allow requests from this domain.")
      } else {
        setError(err?.message || "Failed to start session. Check debug info below.")
      }
    } finally {
      setLoading(false)
    }
  }

  // Timer countdown effect
  useEffect(() => {
    if (timerActive && timer > 0) {
      timerRef.current = setTimeout(() => setTimer(timer - 1), 1000)
    } else if (timerActive && timer === 0 && sessionId) {
      setTimerActive(false)
      handleEndSession(sessionId)
    }
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [timerActive, timer, sessionId])

  // End session and poll for results
  const handleEndSession = async (sessionId: string) => {
    setProcessing(true)
    setError(null)

    try {
      addDebugInfo(`Ending session: ${sessionId}`)

      const response = await fetch(`${API_BASE_URL}/api/end_session/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
        body: JSON.stringify({
          session_id: sessionId,
          fs: 1000,
        }),
      })

      addDebugInfo(`End session response: ${response.status}`)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || errorData.detail || "Failed to end session")
      }

      // Start polling for results
      pollForResult(sessionId)
    } catch (err: any) {
      addDebugInfo(`End session error: ${err.message}`)
      setError(err?.message || "Failed to end session")
      setProcessing(false)
    }
  }

  // Poll for session result
  const pollForResult = async (sessionId: string) => {
    let attempts = 0
    const maxAttempts = 30

    const poll = async () => {
      try {
        addDebugInfo(`Polling for result, attempt ${attempts + 1}`)

        const response = await fetch(`${API_BASE_URL}/api/session_status/?session_id=${sessionId}`, {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const data = await response.json()
        addDebugInfo(`Poll response: ${JSON.stringify(data)}`)

        if (data.status === "completed" && data.result) {
          setResult(data.result)
          setProcessing(false)
        } else if (data.status === "failed") {
          setError(data.error || "Session processing failed")
          setProcessing(false)
        } else if (data.status === "processing" && attempts < maxAttempts) {
          attempts++
          setTimeout(poll, 2000)
        } else if (attempts >= maxAttempts) {
          setError("Processing timeout. Please try again.")
          setProcessing(false)
        }
      } catch (err: any) {
        addDebugInfo(`Poll error: ${err.message}`)
        if (attempts < maxAttempts) {
          attempts++
          setTimeout(poll, 2000)
        } else {
          setError("Error getting session result")
          setProcessing(false)
        }
      }
    }

    poll()
  }

  // Reset session
  const resetSession = () => {
    setSessionId(null)
    setTimer(0)
    setTimerActive(false)
    setProcessing(false)
    setResult(null)
    setError(null)
    setDebugInfo([])
    if (timerRef.current) {
      clearTimeout(timerRef.current)
    }
  }

  // Search for users
  const handleSearch = async () => {
    setIsSearching(true)
    setSearchError(null)

    try {
      const queryParam = searchQuery ? `?query=${encodeURIComponent(searchQuery)}` : ""
      const response = await fetch(`${API_BASE_URL}/api/search_users/${queryParam}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      setSearchResults(data.results || data.users || [])
    } catch (err: any) {
      console.error("Error searching users:", err)

      if (err.name === "TypeError" && err.message.includes("fetch")) {
        setSearchError("Cannot connect to backend server. Please ensure the Django server is running.")
      } else {
        setSearchError(err?.message || "Failed to search users")
      }
      setSearchResults([])
    } finally {
      setIsSearching(false)
    }
  }

  // Test connection on component mount
  useEffect(() => {
    testBackendConnection()
  }, [])

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row justify-between items-center h-auto sm:h-16 py-3 sm:py-0">
            <div className="flex items-center space-x-2 mb-3 sm:mb-0">
              <Activity className="h-6 w-6 sm:h-8 sm:w-8 text-black" />
              <h1 className="text-xl sm:text-2xl font-bold text-black tracking-tight">Neurisk</h1>
            </div>
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full sm:w-auto">
              <TabsList className="grid w-full grid-cols-2 bg-gray-100">
                <TabsTrigger
                  value="test"
                  className="data-[state=active]:bg-black data-[state=active]:text-white transition-all duration-200 hover:bg-gray-200 text-sm sm:text-base"
                >
                  <Zap className="h-3 w-3 sm:h-4 sm:w-4 mr-1 sm:mr-2" />
                  Test
                </TabsTrigger>
                <TabsTrigger
                  value="search"
                  className="data-[state=active]:bg-black data-[state=active]:text-white transition-all duration-200 hover:bg-gray-200 text-sm sm:text-base"
                >
                  <Search className="h-3 w-3 sm:h-4 sm:w-4 mr-1 sm:mr-2" />
                  Search
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </div>
      </header>

      {/* Backend Status Banner */}
      <div className="bg-blue-50 border-b border-blue-200 py-2">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-center text-sm text-blue-800">
            <Bug className="h-4 w-4 mr-2" />
            Backend: {API_BASE_URL} | Debug mode enabled
          </div>
        </div>
      </div>

      <main className="max-w-4xl mx-auto px-3 sm:px-4 lg:px-8 py-4 sm:py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          {/* Test Tab */}
          <TabsContent value="test" className="space-y-8">
            <div className="text-center space-y-3 sm:space-y-4">
              <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-black tracking-tight">Neurisk</h2>
              <p className="text-base sm:text-lg text-gray-600 max-w-2xl mx-auto px-4 sm:px-0">
                Muscle Injury Risk Prediction for Basketball Players
              </p>
            </div>

            {/* Debug Info Card */}
            {debugInfo.length > 0 && (
              <Card className="border-2 border-blue-200 shadow-lg">
                <CardHeader className="bg-blue-50 border-b border-blue-200">
                  <CardTitle className="flex items-center space-x-2 text-blue-800">
                    <Bug className="h-5 w-5" />
                    <span>Debug Information</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-4">
                  <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm max-h-60 overflow-y-auto">
                    {debugInfo.map((info, index) => (
                      <div key={index} className="mb-1">
                        {info}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Form Card */}
            {!result && !sessionId && (
              <Card className="border-2 border-gray-100 shadow-lg hover:shadow-xl transition-shadow duration-300">
                <CardHeader className="bg-gray-50 border-b">
                  <CardTitle className="flex items-center space-x-2">
                    <User className="h-5 w-5" />
                    <span>Player Assessment</span>
                  </CardTitle>
                  <CardDescription>Enter player information to assess injury risk</CardDescription>
                </CardHeader>
                <CardContent className="p-6">
                  <form onSubmit={handleStartSession} className="space-y-6">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
                      {/* Name */}
                      <div className="space-y-2">
                        <Label htmlFor="name" className="text-sm font-medium flex items-center space-x-2">
                          <User className="h-4 w-4" />
                          <span>Name</span>
                        </Label>
                        <Input
                          id="name"
                          placeholder="Enter player name"
                          value={formData.name}
                          onChange={(e) => handleInputChange("name", e.target.value)}
                          className="transition-all duration-200 focus:ring-2 focus:ring-black focus:border-black hover:border-gray-400"
                          disabled={loading || timerActive}
                          required
                        />
                      </div>

                      {/* Age */}
                      <div className="space-y-2">
                        <Label htmlFor="age" className="text-sm font-medium flex items-center space-x-2">
                          <Calendar className="h-4 w-4" />
                          <span>Age</span>
                        </Label>
                        <Input
                          id="age"
                          type="number"
                          placeholder="25"
                          value={formData.age}
                          onChange={(e) => handleInputChange("age", e.target.value)}
                          className="transition-all duration-200 focus:ring-2 focus:ring-black focus:border-black hover:border-gray-400"
                          disabled={loading || timerActive}
                          required
                        />
                      </div>

                      {/* Height */}
                      <div className="space-y-2">
                        <Label htmlFor="height" className="text-sm font-medium flex items-center space-x-2">
                          <Ruler className="h-4 w-4" />
                          <span>Height (cm)</span>
                        </Label>
                        <Input
                          id="height"
                          type="number"
                          placeholder="170"
                          value={formData.height}
                          onChange={(e) => handleInputChange("height", e.target.value)}
                          className="transition-all duration-200 focus:ring-2 focus:ring-black focus:border-black hover:border-gray-400"
                          disabled={loading || timerActive}
                          required
                        />
                      </div>

                      {/* Weight */}
                      <div className="space-y-2">
                        <Label htmlFor="weight" className="text-sm font-medium flex items-center space-x-2">
                          <Weight className="h-4 w-4" />
                          <span>Weight (kg)</span>
                        </Label>
                        <Input
                          id="weight"
                          type="number"
                          placeholder="70"
                          value={formData.weight}
                          onChange={(e) => handleInputChange("weight", e.target.value)}
                          className="transition-all duration-200 focus:ring-2 focus:ring-black focus:border-black hover:border-gray-400"
                          disabled={loading || timerActive}
                          required
                        />
                      </div>

                      {/* Training Frequency */}
                      <div className="space-y-2">
                        <Label htmlFor="training" className="text-sm font-medium flex items-center space-x-2">
                          <Activity className="h-4 w-4" />
                          <span>Training Frequency (sessions/week)</span>
                        </Label>
                        <Input
                          id="training"
                          type="number"
                          placeholder="3"
                          value={formData.trainingFrequency}
                          onChange={(e) => handleInputChange("trainingFrequency", e.target.value)}
                          className="transition-all duration-200 focus:ring-2 focus:ring-black focus:border-black hover:border-gray-400"
                          disabled={loading || timerActive}
                          required
                        />
                      </div>

                      {/* Previous Injury */}
                      <div className="space-y-2">
                        <Label className="text-sm font-medium flex items-center space-x-2">
                          <Shield className="h-4 w-4" />
                          <span>Previous Injury</span>
                        </Label>
                        <Select
                          value={formData.previousInjury}
                          onValueChange={(value) => handleInputChange("previousInjury", value)}
                          disabled={loading || timerActive}
                        >
                          <SelectTrigger className="transition-all duration-200 focus:ring-2 focus:ring-black focus:border-black hover:border-gray-400">
                            <SelectValue placeholder="Select injury history" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="none">None</SelectItem>
                            <SelectItem value="calves">Calves</SelectItem>
                            <SelectItem value="hamstrings">Hamstrings</SelectItem>
                            <SelectItem value="quadriceps">Quadriceps</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      {/* Muscle Group */}
                      <div className="space-y-2">
                        <Label className="text-sm font-medium">Muscle Group</Label>
                        <Select
                          value={formData.muscleGroup}
                          onValueChange={(value) => handleInputChange("muscleGroup", value)}
                          disabled={loading || timerActive}
                        >
                          <SelectTrigger className="transition-all duration-200 focus:ring-2 focus:ring-black focus:border-black hover:border-gray-400">
                            <SelectValue placeholder="Select muscle group" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="quadriceps">Quadriceps</SelectItem>
                            <SelectItem value="hamstrings">Hamstrings</SelectItem>
                            <SelectItem value="calves">Calves</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      {/* Contraction Type */}
                      <div className="space-y-2">
                        <Label className="text-sm font-medium">Contraction Type</Label>
                        <Select
                          value={formData.contractionType}
                          onValueChange={(value) => handleInputChange("contractionType", value)}
                          disabled={loading || timerActive}
                        >
                          <SelectTrigger className="transition-all duration-200 focus:ring-2 focus:ring-black focus:border-black hover:border-gray-400">
                            <SelectValue placeholder="Select contraction type" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="isometric">Isometric</SelectItem>
                            <SelectItem value="isotonic">Isotonic</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      {/* Device ID */}
                      <div className="space-y-2 md:col-span-2">
                        <Label htmlFor="device" className="text-sm font-medium">
                          Device ID (MAC address)
                        </Label>
                        <Input
                          id="device"
                          placeholder="e.g. 24:6F:28:AA:BB:CC"
                          value={formData.deviceId}
                          onChange={(e) => handleInputChange("deviceId", e.target.value)}
                          className="transition-all duration-200 focus:ring-2 focus:ring-black focus:border-black hover:border-gray-400"
                          disabled={loading || timerActive}
                          required
                        />
                      </div>

                      {/* Session Duration */}
                      <div className="space-y-2 md:col-span-2">
                        <Label htmlFor="duration" className="text-sm font-medium flex items-center space-x-2">
                          <Timer className="h-4 w-4" />
                          <span>Session Duration (seconds)</span>
                        </Label>
                        <Input
                          id="duration"
                          type="number"
                          placeholder="5"
                          value={formData.sessionDuration}
                          onChange={(e) => handleInputChange("sessionDuration", e.target.value)}
                          className="transition-all duration-200 focus:ring-2 focus:ring-black focus:border-black hover:border-gray-400"
                          disabled={loading || timerActive}
                          min={1}
                          max={60}
                          required
                        />
                      </div>
                    </div>

                    <div className="mt-6 sm:mt-8 flex flex-col sm:flex-row justify-center space-y-3 sm:space-y-0 sm:space-x-4">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={testBackendConnection}
                        disabled={loading}
                        className="w-full sm:w-auto"
                      >
                        <Bug className="h-4 w-4 mr-2" />
                        Test Connection
                      </Button>
                      <Button
                        type="submit"
                        size="lg"
                        disabled={loading || timerActive || !formData.name || !formData.deviceId}
                        className="bg-black hover:bg-gray-800 text-white px-6 sm:px-8 py-2 sm:py-3 text-base sm:text-lg font-medium transition-all duration-200 hover:scale-105 hover:shadow-lg w-full sm:w-auto"
                      >
                        {loading ? (
                          <>
                            <Loader2 className="h-4 w-4 sm:h-5 sm:w-5 mr-2 animate-spin" />
                            Starting...
                          </>
                        ) : (
                          <>
                            <Activity className="h-4 w-4 sm:h-5 sm:w-5 mr-2" />
                            Start Session
                          </>
                        )}
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            )}

            {/* Session Status Card */}
            {sessionId && !result && (
              <Card className="border-2 border-gray-100 shadow-lg">
                <CardHeader className="bg-gray-50 border-b">
                  <CardTitle className="flex items-center space-x-2">
                    <Activity className="h-5 w-5" />
                    <span>Session Status</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <span className="text-sm font-medium text-gray-700">Session ID:</span>
                      <Badge variant="outline" className="font-mono text-sm">
                        {sessionId}
                      </Badge>
                    </div>

                    <div className="text-sm text-gray-600 bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <p className="font-medium text-blue-800 mb-2">Instructions:</p>
                      <p className="text-blue-700">
                        Share this Session ID with your ESP32 device to start sending EMG data.
                      </p>
                    </div>

                    {timerActive && (
                      <div className="flex items-center justify-center space-x-3 p-4 bg-green-50 border border-green-200 rounded-lg">
                        <Loader2 className="h-5 w-5 text-green-600 animate-spin" />
                        <span className="text-green-800 font-medium">Session in progress... {timer}s remaining</span>
                      </div>
                    )}

                    {processing && (
                      <div className="flex items-center justify-center space-x-3 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                        <Loader2 className="h-5 w-5 text-yellow-600 animate-spin" />
                        <span className="text-yellow-800 font-medium">Processing session data...</span>
                      </div>
                    )}

                    {!timerActive && !processing && (
                      <div className="flex justify-center">
                        <Button variant="outline" onClick={resetSession} className="hover:bg-gray-50">
                          <ArrowLeft className="h-4 w-4 mr-2" />
                          Start New Session
                        </Button>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Error Card */}
            {error && (
              <Card className="border-2 border-red-200 shadow-lg">
                <CardHeader className="bg-red-50 border-b border-red-200">
                  <CardTitle className="flex items-center space-x-2 text-red-800">
                    <AlertCircle className="h-5 w-5" />
                    <span>Error</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <p className="text-red-700 font-medium">{error}</p>
                  <div className="mt-4">
                    <Button
                      variant="outline"
                      onClick={resetSession}
                      className="hover:bg-red-50 border-red-200 text-red-700"
                    >
                      <ArrowLeft className="h-4 w-4 mr-2" />
                      Try Again
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Results Card */}
            {result && (
              <div className="space-y-6">
                {/* Risk Score Display */}
                <Card
                  className={`border-2 shadow-lg ${
                    result.risk_level === "low"
                      ? "border-green-200"
                      : result.risk_level === "medium"
                        ? "border-yellow-200"
                        : "border-red-200"
                  }`}
                >
                  <CardHeader
                    className={`border-b ${
                      result.risk_level === "low"
                        ? "bg-green-50 border-green-200"
                        : result.risk_level === "medium"
                          ? "bg-yellow-50 border-yellow-200"
                          : "bg-red-50 border-red-200"
                    }`}
                  >
                    <CardTitle
                      className={`flex items-center space-x-2 ${
                        result.risk_level === "low"
                          ? "text-green-800"
                          : result.risk_level === "medium"
                            ? "text-yellow-800"
                            : "text-red-800"
                      }`}
                    >
                      <CheckCircle className="h-5 w-5" />
                      <span>Assessment Results</span>
                    </CardTitle>
                    <CardDescription
                      className={`${
                        result.risk_level === "low"
                          ? "text-green-700"
                          : result.risk_level === "medium"
                            ? "text-yellow-700"
                            : "text-red-700"
                      }`}
                    >
                      Risk assessment completed successfully
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="p-6">
                    <div className="text-center p-4 sm:p-6 bg-gray-50 rounded-lg">
                      <h3 className="text-base sm:text-lg font-medium text-gray-700 mb-3 sm:mb-4">
                        Predicted Injury Risk Level
                      </h3>
                      <div className="text-3xl sm:text-4xl lg:text-5xl font-bold text-black mb-3 sm:mb-4">
                        {(result.risk_level || "medium").toUpperCase()}
                      </div>
                      <Badge
                        variant="outline"
                        className={`text-sm sm:text-lg font-medium px-3 sm:px-4 py-1 sm:py-2 ${
                          result.risk_level === "low"
                            ? "bg-green-100 text-green-800 border-green-200"
                            : result.risk_level === "medium"
                              ? "bg-yellow-100 text-yellow-800 border-yellow-200"
                              : "bg-red-100 text-red-800 border-red-200"
                        }`}
                      >
                        {result.risk_level === "low"
                          ? "Low Risk"
                          : result.risk_level === "medium"
                            ? "Medium Risk"
                            : "High Risk"}
                      </Badge>
                    </div>
                  </CardContent>
                </Card>

                {/* Training Regime Card */}
                <Card className="border-2 border-gray-100 shadow-lg">
                  <CardHeader className="bg-gray-50 border-b">
                    <CardTitle className="flex items-center space-x-2">
                      <Activity className="h-5 w-5" />
                      <span>Recommended Training Plan</span>
                    </CardTitle>
                    <CardDescription>
                      {result.training_assignment ||
                        "Personalized training recommendations based on your risk assessment"}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="p-6">
                    <div className="space-y-6">
                      {/* Display training assignment from backend */}
                      {result.training_assignment && (
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                          <h4 className="text-lg font-semibold text-blue-800 mb-2">Recommended Training:</h4>
                          <p className="text-blue-700 whitespace-pre-wrap">{result.training_assignment}</p>
                        </div>
                      )}

                      {/* Additional recommendations based on risk level */}
                      <div>
                        <h4 className="text-lg font-semibold text-gray-800 mb-3">Additional Recommendations:</h4>
                        {result.risk_level === "low" && (
                          <div className="space-y-2 text-gray-700">
                            <div>
                              <strong>Objective:</strong> Maintain optimal musculoskeletal health and prevent injury.
                            </div>
                            <div>
                              <strong>Recommended Interventions:</strong>
                              <ul className="list-disc list-inside ml-4">
                                <li>Continue regular strength and conditioning.</li>
                                <li>Emphasize warm-up, cool-down, and recovery.</li>
                                <li>Monitor training load.</li>
                              </ul>
                            </div>
                            <div>
                              <strong>Specific Training Regime:</strong>
                              <ul className="list-disc list-inside ml-4">
                                <li>
                                  <strong>Before Practice:</strong> 10–15 min dynamic warm-up (leg swings, high knees, butt kicks, dynamic lunges), light plyometrics (skipping, bounding), activation exercises (mini-band walks, glute bridges)
                                </li>
                                <li>
                                  <strong>During Practice:</strong> Full participation in team drills and scrimmages, integrate neuromuscular exercises (balance, agility ladders) into skill drills
                                </li>
                                <li>
                                  <strong>After Practice:</strong> 10 min static stretching (hamstrings, quads, calves), foam rolling major muscle groups, hydration and nutrition for recovery
                                </li>
                              </ul>
                            </div>
                          </div>
                        )}
                        {result.risk_level === "medium" && (
                          <div className="space-y-2 text-gray-700">
                            <div>
                              <strong>Objective:</strong> Address early signs of fatigue or imbalance and prevent progression to high risk.
                            </div>
                            <div>
                              <strong>Recommended Interventions:</strong>
                              <ul className="list-disc list-inside ml-4">
                                <li>Add targeted neuromuscular and eccentric strengthening.</li>
                                <li>Monitor fatigue and muscle imbalances.</li>
                                <li>Integrate recovery modalities.</li>
                              </ul>
                            </div>
                            <div>
                              <strong>Specific Training Regime:</strong>
                              <ul className="list-disc list-inside ml-4">
                                <li>
                                  <strong>Before Practice:</strong> 15 min dynamic warm-up with added focus on single-leg balance and proprioceptive drills (e.g., single-leg stance, wobble board), eccentric strengthening (2–3 sets of Nordic hamstring curls, eccentric calf raises)
                                </li>
                                <li>
                                  <strong>During Practice:</strong> Participate in team drills, but include 2–3 sets of neuromuscular exercises (agility ladder, perturbation training) between drills, monitor perceived exertion and modify intensity if needed
                                </li>
                                <li>
                                  <strong>After Practice:</strong> 10–15 min static stretching and foam rolling, 5–10 min yoga or guided mobility work, use of ice or compression if soreness is present
                                </li>
                              </ul>
                            </div>
                          </div>
                        )}
                        {result.risk_level === "high" && (
                          <div className="space-y-2 text-gray-700">
                            <div>
                              <strong>Objective:</strong> Mitigate injury risk, address deficits, and ensure safe return to play.
                            </div>
                            <div>
                              <strong>Recommended Interventions:</strong>
                              <ul className="list-disc list-inside ml-4">
                                <li>Supervised rehabilitation with a physiotherapist.</li>
                                <li>Individualized corrective exercise program.</li>
                                <li>Gradual return-to-play protocol.</li>
                              </ul>
                            </div>
                            <div>
                              <strong>Specific Training Regime:</strong>
                              <ul className="list-disc list-inside ml-4">
                                <li>
                                  <strong>Before Practice:</strong> 20 min supervised rehab warm-up (isokinetic strengthening, proprioceptive retraining, glute/core activation), corrective exercises targeting weaknesses (e.g., single-leg bridges, clamshells)
                                </li>
                                <li>
                                  <strong>During Practice:</strong> Modified or limited participation in team drills, focus on technique and low-intensity skill work, continue supervised rehab exercises as tolerated
                                </li>
                                <li>
                                  <strong>After Practice:</strong> Extended cool-down with static stretching and foam rolling, physiotherapist-guided recovery (manual therapy, modalities as needed), education session on injury prevention and self-monitoring
                                </li>
                              </ul>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Action Buttons */}
                      <div className="flex flex-col sm:flex-row justify-center space-y-3 sm:space-y-0 sm:space-x-4 pt-4">
                        <Button variant="outline" onClick={resetSession} className="hover:bg-gray-50 w-full sm:w-auto">
                          <ArrowLeft className="h-4 w-4 mr-2" />
                          New Assessment
                        </Button>
                        <Button className="bg-black hover:bg-gray-800 text-white transition-all duration-200 hover:scale-105 w-full sm:w-auto">
                          <Activity className="h-4 w-4 mr-2" />
                          Save Results
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>

          {/* Search Tab */}
          <TabsContent value="search" className="space-y-8">
            <div className="text-center space-y-4">
              <h2 className="text-4xl font-bold text-black tracking-tight">User Results</h2>
              <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                Search for previous users and view their risk scores and training regimes
              </p>
            </div>

            <Card className="border-2 border-gray-100 shadow-lg">
              <CardHeader className="bg-gray-50 border-b">
                <CardTitle className="flex items-center space-x-2">
                  <Search className="h-5 w-5" />
                  <span>Search Players</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-6">
                <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-4">
                  <Input
                    placeholder="Search by name (optional)"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="flex-1 transition-all duration-200 focus:ring-2 focus:ring-black focus:border-black hover:border-gray-400"
                    disabled={isSearching}
                  />
                  <Button
                    className="bg-black hover:bg-gray-800 text-white px-6 transition-all duration-200 hover:scale-105 w-full sm:w-auto"
                    onClick={handleSearch}
                    disabled={isSearching}
                  >
                    {isSearching ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <>
                        <Search className="h-4 w-4 mr-2" />
                        Search
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Search Error */}
            {searchError && (
              <Card className="border-2 border-red-200 shadow-lg">
                <CardHeader className="bg-red-50 border-b border-red-200">
                  <CardTitle className="flex items-center space-x-2 text-red-800">
                    <AlertCircle className="h-5 w-5" />
                    <span>Search Error</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <p className="text-red-700 font-medium">{searchError}</p>
                </CardContent>
              </Card>
            )}

            {/* Results */}
            <Card className="border-2 border-gray-100 shadow-lg">
              <CardHeader className="bg-gray-50 border-b">
                <CardTitle>Search Results</CardTitle>
                <CardDescription>
                  {searchResults.length} player{searchResults.length !== 1 ? "s" : ""} found
                </CardDescription>
              </CardHeader>
              <CardContent className="p-6">
                {searchResults.length > 0 ? (
                  <div className="space-y-4">
                    {searchResults.map((result, index) => (
                      <div
                        key={result.id || index}
                        className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-gray-300 hover:shadow-md transition-all duration-200 cursor-pointer"
                      >
                        <div className="flex items-center space-x-4">
                          <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
                            <User className="h-5 w-5 text-gray-600" />
                          </div>
                          <div>
                            <h3 className="font-medium text-black">{result.name || result.user_name}</h3>
                            <p className="text-sm text-gray-600">Age: {result.age}</p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-4">
                          <div className="text-right">
                            <div
                              className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                                result.risk_level === "low" || result.risk_score < 30
                                  ? "bg-green-100 text-green-800"
                                  : result.risk_level === "medium" ||
                                      (result.risk_score >= 30 && result.risk_score < 70)
                                    ? "bg-yellow-100 text-yellow-800"
                                    : "bg-red-100 text-red-800"
                              }`}
                            >
                              {result.risk_level
                                ? `${result.risk_level.charAt(0).toUpperCase() + result.risk_level.slice(1)} Risk`
                                : result.risk_score < 30
                                  ? "Low Risk"
                                  : result.risk_score < 70
                                    ? "Medium Risk"
                                    : "High Risk"}
                            </div>
                            <p className="text-xs text-gray-500 mt-1">
                              Last: {result.last_session || result.created_at || "N/A"}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500 text-lg">No results found</p>
                    <p className="text-gray-400 text-sm mt-2">Try adjusting your search criteria</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
