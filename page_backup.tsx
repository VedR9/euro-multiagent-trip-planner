"use client";

import { useState, useRef } from "react";
import { Mic, Square, Navigation, Map, ShieldCheck, Euro } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from 'react-markdown';

export default function Home() {
  const [isRecording, setIsRecording] = useState(false);
  const [loading, setLoading] = useState(false);
  const [itinerary, setItinerary] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<BlobPart[]>([]);

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

      mediaRecorder.onstop = handleStopRecording;
      mediaRecorder.start();
      setIsRecording(true);
      setItinerary(null);
    } catch (error) {
      console.error("Error accessing microphone:", error);
      alert("Please allow microphone access to use the voice planner.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop());
      setIsRecording(false);
    }
  };

  const speakSummary = (text: string) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.voice = speechSynthesis.getVoices().find(v => v.lang === 'en-GB') || null;
      utterance.pitch = 1.1;
      utterance.rate = 1.0;
      speechSynthesis.speak(utterance);
    }
  };

  const handleStopRecording = async () => {
    setLoading(true);
    const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
    
    // 1. Send Audio to FastApi Backend to Transcribe
    const formData = new FormData();
    formData.append("file", audioBlob, "voice_prompt.webm");

    try {
      // Assuming Backend runs on 8000
      const transcribeRes = await fetch("http://localhost:8000/api/transcribe", {
        method: "POST",
        body: formData,
      });
      const transcribeData = await transcribeRes.json();
      
      if (!transcribeData.success) throw new Error(transcribeData.detail);
      
      // 2. Send Transcribed Text to Planner API
      const planRes = await fetch("http://localhost:8000/api/plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: transcribeData.text }),
      });
      
      const planData = await planRes.json();
      if (!planData.success) throw new Error(planData.detail);
      
      try {
        const parsedData = JSON.parse(planData.data);
        setItinerary(parsedData.markdown_itinerary);
        speakSummary(parsedData.audio_summary);
      } catch (e) {
        // Fallback if not valid JSON
        setItinerary(planData.data);
      }
      
    } catch (error) {
      console.error("Pipeline failed:", error);
      alert("Failed to generate itinerary. Ensure backend is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-50 selection:bg-indigo-500/30">
      <main className="max-w-5xl mx-auto px-6 py-24 flex flex-col items-center">
        
        {/* Header Hero */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center max-w-2xl mb-16"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-400 text-sm font-medium mb-6 border border-indigo-500/20">
            <ShieldCheck className="w-4 h-4" />
            AI-Powered Multi-Agent System
          </div>
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6 bg-gradient-to-br from-white to-neutral-500 bg-clip-text text-transparent">
            Euro Trip Planner
          </h1>
          <p className="text-lg text-neutral-400 leading-relaxed">
            Speak your dream European vacation. Our elite squad of AI agents will find the flights, book the hotels, and craft the perfect daily itinerary.
          </p>
        </motion.div>

        {/* Feature Grid */}
        {!loading && !itinerary && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16 w-full max-w-3xl"
          >
            {[
              { icon: Navigation, title: "Smart Routing", desc: "Optimized European transit" },
              { icon: Euro, title: "Euro Budgets", desc: "Live currency parsing" },
              { icon: Map, title: "Live Discovery", desc: "Real-time MCP searching" }
            ].map((Feature, i) => (
              <div key={i} className="p-6 rounded-2xl bg-neutral-900/50 border border-neutral-800/50 backdrop-blur-sm">
                <Feature.icon className="w-8 h-8 text-indigo-400 mb-4" />
                <h3 className="font-semibold mb-2">{Feature.title}</h3>
                <p className="text-sm text-neutral-500">{Feature.desc}</p>
              </div>
            ))}
          </motion.div>
        )}

        {/* Microphone Controller */}
        <div className="relative z-10 flex flex-col items-center">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={isRecording ? stopRecording : startRecording}
            className={`relative flex items-center justify-center w-24 h-24 rounded-full shadow-2xl transition-all duration-300 ${
              isRecording 
                ? "bg-red-500 text-white shadow-red-500/30" 
                : "bg-indigo-600 text-white hover:bg-indigo-500 shadow-indigo-600/30"
            }`}
          >
            <AnimatePresence mode="wait">
              {isRecording ? (
                <motion.div key="stop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                  <Square className="w-8 h-8 fill-current" />
                </motion.div>
              ) : (
                <motion.div key="mic" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                  <Mic className="w-8 h-8" />
                </motion.div>
              )}
            </AnimatePresence>
            
            {/* Ping animation when recording */}
            {isRecording && (
              <div className="absolute inset-0 rounded-full bg-red-500/40 animate-ping" />
            )}
          </motion.button>
          
          <p className="mt-6 text-sm font-medium text-neutral-400">
            {isRecording ? "Listening to your request... Click to stop" : "Tap to speak your travel request"}
          </p>
        </div>

        {/* Loading State */}
        {loading && (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-16 text-center"
          >
            <div className="flex gap-2 justify-center mb-4">
              {[0, 1, 2].map((i) => (
                <motion.div
                  key={i}
                  animate={{ y: [0, -10, 0] }}
                  transition={{ repeat: Infinity, delay: i * 0.15, duration: 0.8 }}
                  className="w-3 h-3 bg-indigo-500 rounded-full"
                />
              ))}
            </div>
            <p className="text-neutral-400 font-medium">Orchestrating AI Agents...</p>
          </motion.div>
        )}

        {/* Results */}
        {itinerary && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-16 w-full max-w-4xl p-8 rounded-3xl bg-neutral-900 border border-neutral-800 shadow-2xl overflow-hidden relative"
          >
            {/* Glass decoration */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 blur-3xl rounded-full translate-x-1/2 -translate-y-1/2 pointer-events-none" />
            
            <div className="prose prose-invert prose-indigo max-w-none relative z-10">
              <ReactMarkdown>{itinerary}</ReactMarkdown>
            </div>
          </motion.div>
        )}

      </main>
    </div>
  );
}
