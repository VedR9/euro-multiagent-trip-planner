"use client";

import { useState, useRef } from "react";
import { Mic, Loader2, Compass, Printer, Volume2, VolumeX, RefreshCcw } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { motion, AnimatePresence } from "framer-motion";
import { useEffect } from "react";

type ChatMessage = {
  id: string;
  role: "user" | "ai";
  content: string;
};

export default function LandingPage() {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [loadingStepIndex, setLoadingStepIndex] = useState(0);
  const [sessionId, setSessionId] = useState<string>("");

  useEffect(() => {
    // Generate a unique session ID when the app loads
    setSessionId(crypto.randomUUID());
  }, []);
  
  const loadingSteps = ["Thinking...", "Researching attractions...", "Finding hotels...", "Validating budget...", "Formatting itinerary..."];

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isProcessing) {
      interval = setInterval(() => {
        setLoadingStepIndex((prev) => Math.min(prev + 1, loadingSteps.length - 1));
      }, 3000);
    } else {
      setLoadingStepIndex(0);
    }
    return () => clearInterval(interval);
  }, [isProcessing]);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        setIsProcessing(true);
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        const formData = new FormData();
        formData.append("file", audioBlob, "recording.webm");

        try {
          const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
          const res = await fetch(`${apiUrl}/api/transcribe`, {
            method: "POST",
            body: formData,
          });
          const data = await res.json();
          if (data.text) {
            setMessages(prev => [...prev, { id: crypto.randomUUID(), role: "user", content: data.text }]);
            await planTrip(data.text);
          }
        } catch (error) {
          console.error("Transcription error:", error);
          setIsProcessing(false);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Microphone permission denied", err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop());
    }
    setIsRecording(false);
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const planTrip = async (prompt: string) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/plan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, session_id: sessionId }),
      });
      const planData = await res.json();
      
      try {
        const parsedData = JSON.parse(planData.data);
        setMessages(prev => [...prev, { id: crypto.randomUUID(), role: "ai", content: parsedData.markdown_itinerary }]);
        speakSummary(parsedData.audio_summary);
      } catch (e) {
        setMessages(prev => [...prev, { id: crypto.randomUUID(), role: "ai", content: planData.data }]);
      }
    } catch (error) {
      console.error("Planning error:", error);
      setMessages(prev => [...prev, { id: crypto.randomUUID(), role: "ai", content: "Error generating itinerary. Check if the back-end is running." }]);
    } finally {
      setIsProcessing(false);
    }
  };

  const speakSummary = (text: string) => {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      utterance.pitch = 1.1;
      utterance.onend = () => setIsPlaying(false);
      setIsPlaying(true);
      window.speechSynthesis.speak(utterance);
    }
  };

  const stopAudio = () => {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      setIsPlaying(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const resetChat = () => {
    setSessionId(crypto.randomUUID());
    setMessages([]);
    stopAudio();
    setIsRecording(false);
    setIsProcessing(false);
  };

  return (
    <div className="min-h-screen bg-[#121212] text-white overflow-x-hidden relative">
      
      {/* Global Fixed Background Image */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <img 
          src="https://images.unsplash.com/photo-1499856871958-5b9627545d1a?q=80&w=2020&auto=format&fit=crop"  
          alt="Paris Europe" 
          className="w-full h-full object-cover opacity-40"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#121212]/60 to-[#121212]"></div>
      </div>

      {/* Top Banner */}
      <div className="relative z-50 w-full bg-[#1A1A1A] text-center text-xs text-gray-300 py-2 border-b border-[#333] print:hidden">
        ✨ Travel Your Dream Destination <span className="underline cursor-pointer hover:text-white transition-colors">Learn More</span>
      </div>

      {/* Header */}
      <header className="absolute top-10 w-full z-50 flex items-center justify-between px-10 py-6 print:hidden">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-purple-600 rounded-bl-xl rounded-tr-xl flex items-center justify-center rotate-45 shadow-[0_0_15px_rgba(139,92,246,0.5)]">
            <div className="-rotate-45 font-bold text-white tracking-widest text-lg"></div>
          </div>
          <span className="font-bold text-xl tracking-wide text-white">Multi-Agent Voice Trip Planner</span>
        </div>
        <nav className="hidden md:flex items-center gap-10 text-sm font-medium text-gray-200">
          <a href="#" className="hover:text-white transition-colors border-b-2 border-transparent hover:border-purple-500 pb-1">Home</a>
          <a href="#" className="hover:text-white transition-colors border-b-2 border-transparent hover:border-purple-500 pb-1">About Us</a>
          <a href="#" className="hover:text-white transition-colors border-b-2 border-transparent hover:border-purple-500 pb-1">Places</a>
          <a href="#" className="hover:text-white transition-colors border-b-2 border-transparent hover:border-purple-500 pb-1">Services</a>
        </nav>
        <div className="flex items-center gap-4">
          {messages.length > 0 && (
            <button onClick={resetChat} className="flex items-center gap-2 px-4 py-2.5 rounded-full border border-red-500/50 text-red-400 text-sm hover:bg-red-500 hover:text-white hover:border-red-500 transition-all font-medium">
              <RefreshCcw size={16} /> Reset Chat
            </button>
          )}
          <button className="px-6 py-2.5 rounded-full border border-gray-600 text-sm hover:bg-white hover:text-black transition-all font-medium">
            Contact Us
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      {messages.length === 0 ? (
        // INITIAL STATE: Centered Hero Layout
        <div className="relative w-full min-h-[90vh] flex flex-col items-center justify-center pt-20 pb-20 print:min-h-0 print:pt-0 print:pb-0">
          <div className="relative z-10 flex flex-col items-center w-full max-w-5xl px-4">
            <motion.h1 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
              className="text-4xl md:text-6xl font-bold text-center leading-tight mb-12 drop-shadow-2xl print:hidden"
            >
              Multi-Agent Voice Trip Planner <br/>
              <span className="text-2xl md:text-4xl mt-2 block text-gray-300">Orchestrating your dream trip with AI.</span>
            </motion.h1>

            {/* Big Microphone Action Button */}
            <motion.div 
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.4 }}
              className="flex flex-col items-center justify-center mt-6 print:hidden"
            >
              <p className="text-gray-300 mb-4 font-medium text-lg tracking-wide drop-shadow-md">
                Tap the mic and tell us your dream trip!
              </p>
              <button
                onClick={toggleRecording}
                className={`relative flex items-center gap-3 px-10 py-5 rounded-full font-bold text-lg text-white transition-all duration-300 shadow-xl ${
                  isRecording 
                    ? "bg-red-500 scale-105 mic-pulse" 
                    : isProcessing 
                    ? "bg-purple-800 opacity-80 cursor-wait"
                    : "bg-purple-600 hover:bg-purple-500 hover:-translate-y-1 hover:shadow-purple-500/30"
                }`}
              >
                {isProcessing ? (
                  <div className="flex items-center gap-3 w-64 justify-center">
                    <Loader2 className="w-6 h-6 animate-spin" />
                    <span className="w-48 text-left truncate">{loadingSteps[loadingStepIndex]}</span>
                  </div>
                ) : isRecording ? (
                  <>
                    <Mic className="w-6 h-6 animate-bounce" />
                    Tap to Stop Recording
                  </>
                ) : (
                  <>
                    <Mic className="w-6 h-6" />
                    Tap to Voice Search
                  </>
                )}
              </button>
            </motion.div>
          </div>
        </div>
      ) : (
        // CONVERSATION STATE: 2-Column Split Layout
        <div className="relative z-10 w-full min-h-screen pt-32 pb-20 px-8 max-w-[1400px] mx-auto print:pt-0 print:px-0">
          <div className="flex flex-col lg:flex-row gap-10">
            
            {/* LEFT COLUMN: Chat Input & User History */}
            <div className="w-full lg:w-1/3 flex flex-col gap-6 print:hidden">
              <div className="sticky top-32 flex flex-col gap-6">
                
                {/* Voice Input Card */}
                <div className="bg-[#1A1A1A] rounded-3xl p-6 border border-[#333] shadow-xl">
                  <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <Mic className="text-purple-500 w-5 h-5" /> Ask a follow-up
                  </h3>
                  <button
                    onClick={toggleRecording}
                    className={`w-full relative flex justify-center items-center gap-3 px-6 py-4 rounded-2xl font-bold text-md text-white transition-all duration-300 shadow-lg ${
                      isRecording 
                        ? "bg-red-500 scale-[1.02] mic-pulse" 
                        : isProcessing 
                        ? "bg-purple-800 opacity-80 cursor-wait"
                        : "bg-purple-600 hover:bg-purple-500 hover:-translate-y-1"
                    }`}
                  >
                    {isProcessing ? (
                      <div className="flex items-center gap-2">
                        <Loader2 className="w-5 h-5 animate-spin" />
                        <span className="truncate">{loadingSteps[loadingStepIndex]}</span>
                      </div>
                    ) : isRecording ? (
                      <>
                        <Mic className="w-5 h-5 animate-bounce" />
                        Listening...
                      </>
                    ) : (
                      <>
                        <Mic className="w-5 h-5" />
                        Hold to Speak
                      </>
                    )}
                  </button>
                </div>

                {/* User Prompt History */}
                <div className="flex flex-col gap-4 overflow-y-auto max-h-[50vh] pr-2 scrollbar-thin">
                  <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-2">Your Requests</h3>
                  <AnimatePresence>
                    {messages.filter(m => m.role === "user").map((msg, index) => (
                      <motion.div 
                        key={msg.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="bg-[#222] p-4 rounded-2xl border border-[#333] shadow-md"
                      >
                        <p className="text-md text-gray-200 italic">"{msg.content}"</p>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>

              </div>
            </div>

            {/* RIGHT COLUMN: AI Itineraries */}
            <div className="w-full lg:w-2/3 flex flex-col gap-10">
              <AnimatePresence>
                {messages.filter(m => m.role === "ai").map((msg, index, arr) => (
                  <motion.div 
                    key={msg.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                    className="w-full print:mt-0"
                  >
                    <div className="bg-[#1A1A1A] print:bg-white rounded-3xl p-8 md:p-10 border border-[#333] print:border-none shadow-2xl print:shadow-none relative overflow-hidden">
                      <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-purple-600 to-blue-500 print:hidden"></div>
                      
                      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                        <h2 className="text-2xl md:text-3xl font-bold text-white print:text-black flex items-center gap-3">
                          <Compass className="text-purple-500 w-8 h-8 print:hidden" />
                          Your AI-Crafted Itinerary
                        </h2>
                        {index === arr.length - 1 && (
                          <div className="flex items-center gap-3 print:hidden">
                            {isPlaying && (
                              <button onClick={stopAudio} className="flex items-center gap-2 px-3 py-2 bg-red-500/20 text-red-400 border border-red-500/30 rounded-full hover:bg-red-500 hover:text-white transition-colors text-sm font-bold">
                                <VolumeX size={16} /> Stop Audio
                              </button>
                            )}
                            <button onClick={handlePrint} className="flex items-center gap-2 px-4 py-2 bg-[#2A2A2A] text-gray-300 border border-[#444] rounded-full hover:bg-[#333] hover:text-white transition-colors text-sm font-bold">
                              <Printer size={16} /> Print
                            </button>
                          </div>
                        )}
                      </div>

                      <div className="prose prose-invert prose-purple max-w-none print:prose-p:text-black print:prose-headings:text-black print:prose-strong:text-purple-700">
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}
