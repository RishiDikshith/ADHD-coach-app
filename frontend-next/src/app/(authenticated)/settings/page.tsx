"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Card, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { useUserStore } from "@/stores/user-store";
import { useAnalyticsStore } from "@/stores/analytics-store";
import { api } from "@/lib/api-client";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.08 } },
};
const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0 },
};

const supportedLanguages = [
  { code: "en", name: "English 🇺🇸" },
  { code: "es", name: "Spanish 🇪🇸" },
  { code: "fr", name: "French 🇫🇷" },
  { code: "de", name: "German 🇩🇪" },
  { code: "it", name: "Italian 🇮🇹" },
  { code: "pt", name: "Portuguese 🇵🇹" },
  { code: "hi", name: "Hindi 🇮🇳" },
  { code: "ja", name: "Japanese 🇯🇵" },
  { code: "zh", name: "Chinese 🇨🇳" },
  { code: "ar", name: "Arabic 🇸🇦" },
  { code: "ru", name: "Russian 🇷🇺" },
  { code: "ko", name: "Korean 🇰🇷" },
  { code: "nl", name: "Dutch 🇳🇱" },
  { code: "tr", name: "Turkish 🇹🇷" },
];

const supportedAccents = [
  { code: "auto", name: "System Default / Auto-Detect 🔍" },
  { code: "en-US", name: "US English Accent 🇺🇸" },
  { code: "en-GB", name: "British Accent 🇬🇧" },
  { code: "es-ES", name: "Spanish Accent 🇪🇸" },
  { code: "fr-FR", name: "French Accent 🇫🇷" },
  { code: "de-DE", name: "German Accent 🇩🇪" },
  { code: "ja-JP", name: "Japanese Accent 🇯🇵" },
  { code: "hi-IN", name: "Hindi Accent 🇮🇳" },
];

export default function SettingsPage() {
  const { settings, updateSettings, username } = useUserStore();
  const { timeBlindnessEnabled, toggleTimeBlindness, startTinyMode, setStartTinyMode } = useAnalyticsStore();

  const [coachTone, setCoachTone] = useState(settings.coach_tone || "encouraging");
  const [focusArea, setFocusArea] = useState(settings.focus_area || "general");
  const [timerDuration, setTimerDuration] = useState(settings.timer_duration || 25);
  const [selectedLanguage, setSelectedLanguage] = useState(settings.language || "en");
  const [voiceAutospeak, setVoiceAutospeak] = useState(settings.voice_autospeak ?? false);
  const [voiceSpeed, setVoiceSpeed] = useState(settings.voice_speed ?? 1.0);
  const [voicePitch, setVoicePitch] = useState(settings.voice_pitch ?? 1.0);
  const [voiceAccent, setVoiceAccent] = useState(settings.voice_accent || "auto");
  const [saved, setSaved] = useState(false);

  // Security PIN and Trusted Devices states
  const [hasPin, setHasPin] = useState(false);
  const [showPinSetup, setShowPinSetup] = useState(false);
  const [enteredPin, setEnteredPin] = useState("");
  const [pinMessage, setPinMessage] = useState("");
  const [pinError, setPinError] = useState("");
  const [devices, setDevices] = useState<any[]>([]);
  const [loadingDevices, setLoadingDevices] = useState(false);

  const fetchDevices = async () => {
    try {
      setLoadingDevices(true);
      const res = await api.getDevices();
      setDevices(res);
    } catch (err) {
      console.error("Failed to load trusted devices:", err);
    } finally {
      setLoadingDevices(false);
    }
  };

  useEffect(() => {
    if (username) {
      api.hasPin(username)
        .then((res) => setHasPin(res.has_pin))
        .catch(() => {});
      fetchDevices();
    }
  }, [username]);

  const handleSetPin = async () => {
    if (enteredPin.length !== 4) {
      setPinError("PIN must be exactly 4 digits");
      return;
    }
    try {
      const devId = useUserStore.getState().getDeviceId();
      const devName = typeof window !== "undefined" ? window.navigator.userAgent.slice(0, 100) : "Unknown Device";
      
      const res = await api.setPin(enteredPin, devId, devName);
      if (res.success) {
        setHasPin(true);
        setShowPinSetup(false);
        setEnteredPin("");
        setPinMessage("✅ PIN updated successfully!");
        setPinError("");
        fetchDevices();
        setTimeout(() => setPinMessage(""), 3000);
      } else {
        setPinError(res.message || "Failed to set PIN");
      }
    } catch (err: any) {
      setPinError(err.message || "Error setting PIN");
    }
  };

  const handleRemovePin = async () => {
    try {
      const res = await api.removePin();
      if (res.success) {
        setHasPin(false);
        setPinMessage("🗑️ PIN removed successfully!");
        setPinError("");
        fetchDevices();
        setTimeout(() => setPinMessage(""), 3000);
      } else {
        setPinError(res.message || "Failed to remove PIN");
      }
    } catch (err: any) {
      setPinError(err.message || "Error removing PIN");
    }
  };

  const handleRemoveDevice = async (deviceIdToRemove: string) => {
    try {
      const res = await api.removeDevice(deviceIdToRemove);
      if (res.success) {
        setPinMessage("🗑️ Device de-authorized successfully!");
        fetchDevices();
        
        // If they de-authorized their current device, check if they need to clear PIN states locally
        const currentDevId = useUserStore.getState().getDeviceId();
        if (deviceIdToRemove === currentDevId) {
          setHasPin(false);
        }
        setTimeout(() => setPinMessage(""), 3000);
      } else {
        setPinError(res.message || "Failed to remove device");
      }
    } catch (err: any) {
      setPinError(err.message || "Error removing device");
    }
  };

  const handleSave = () => {
    updateSettings({
      coach_tone: coachTone as "encouraging" | "direct" | "gentle" | "humorous",
      focus_area: focusArea,
      timer_duration: timerDuration,
      language: selectedLanguage,
      voice_autospeak: voiceAutospeak,
      voice_speed: voiceSpeed,
      voice_pitch: voicePitch,
      voice_accent: voiceAccent,
    });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const playVoiceTest = () => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    
    let text = "Hello! Your new ADHD voice companion is ready.";
    if (selectedLanguage === "es") text = "¡Hola! Tu nuevo asistente de voz para TDAH está listo.";
    else if (selectedLanguage === "fr") text = "Bonjour! Votre nouveau compagnon vocal est prêt.";
    else if (selectedLanguage === "de") text = "Hallo! Dein neuer ADHS-Sprachbegleiter ist bereit.";
    else if (selectedLanguage === "it") text = "Ciao! Il tuo nuovo assistente vocale è pronto.";
    else if (selectedLanguage === "pt") text = "Olá! O seu novo companheiro de voz está pronto.";
    else if (selectedLanguage === "ja") text = "こんにちは。ADHD音声アシスタントの準備ができました。";
    else if (selectedLanguage === "zh") text = "你好！您的ADHD语音助手已准备就绪。";
    else if (selectedLanguage === "hi") text = "नमस्ते! आपका नया एडीएचडी वॉयस असिस्टेंट तैयार है।";
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = voiceSpeed;
    utterance.pitch = voicePitch;
    
    const voices = window.speechSynthesis.getVoices();
    let matchedVoice = null;
    
    if (voiceAccent !== "auto") {
      matchedVoice = voices.find(v => v.lang.startsWith(voiceAccent));
    }
    
    if (!matchedVoice) {
      matchedVoice = voices.find(v => v.lang.startsWith(selectedLanguage));
    }
    
    if (matchedVoice) {
      utterance.voice = matchedVoice;
    }
    
    window.speechSynthesis.speak(utterance);
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="max-w-3xl mx-auto p-6 space-y-6"
    >
      {/* Header */}
      <motion.div variants={itemVariants}>
        <h1 className="text-3xl font-bold text-foreground">⚙️ Settings</h1>
        <p className="text-muted mt-1">Personalize your ADHD Coach experience</p>
      </motion.div>

      {/* Coach Preferences */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardTitle>🧠 ADHD Coach Preferences</CardTitle>
          <div className="mt-4 space-y-5">
            {/* Coach Tone */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Coach Tone</label>
              <p className="text-xs text-muted mb-3">How would you like your AI coach to speak to you?</p>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { id: "encouraging", emoji: "🌟", label: "Encouraging", desc: "Warm, supportive, celebratory" },
                  { id: "direct", emoji: "🎯", label: "Direct", desc: "Clear, concise, no fluff" },
                  { id: "gentle", emoji: "🌿", label: "Gentle", desc: "Soft, calming, patient" },
                  { id: "humorous", emoji: "😄", label: "Humorous", desc: "Light, funny, playful" },
                ].map((tone) => (
                  <motion.button
                     key={tone.id}
                     whileHover={{ scale: 1.02 }}
                     whileTap={{ scale: 0.98 }}
                     onClick={() => setCoachTone(tone.id as "encouraging" | "direct" | "gentle" | "humorous")}
                     className={`p-3 rounded-xl text-left transition-all duration-200 border ${
                       coachTone === tone.id
                         ? "bg-calm-500/10 border-calm-500/50 text-calm-400"
                         : "bg-surface border-border text-muted hover:border-calm-500/30"
                     }`}
                  >
                    <span className="text-lg block mb-1">{tone.emoji}</span>
                    <span className="text-sm font-medium block">{tone.label}</span>
                    <span className="text-[10px]">{tone.desc}</span>
                  </motion.button>
                ))}
              </div>
            </div>

            {/* Focus Area */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Primary Focus Area</label>
              <p className="text-xs text-muted mb-3">What would you like to work on most?</p>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { id: "general", emoji: "🧠", label: "General" },
                  { id: "productivity", emoji: "⚡", label: "Productivity" },
                  { id: "focus", emoji: "🎯", label: "Focus" },
                  { id: "emotional", emoji: "😌", label: "Emotional Health" },
                  { id: "habits", emoji: "🔄", label: "Habit Building" },
                  { id: "organization", emoji: "📋", label: "Organization" },
                ].map((area) => (
                  <motion.button
                    key={area.id}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setFocusArea(area.id)}
                    className={`p-2.5 rounded-xl text-sm text-left transition-all duration-200 border ${
                      focusArea === area.id
                        ? "bg-focus-500/10 border-focus-500/50 text-focus-400"
                        : "bg-surface border-border text-muted hover:border-focus-500/30"
                    }`}
                  >
                    <span className="mr-1.5">{area.emoji}</span>
                    {area.label}
                  </motion.button>
                ))}
              </div>
            </div>
          </div>
          <div className="mt-6 flex items-center gap-3">
            <Button onClick={handleSave}>{saved ? "✅ Saved!" : "Save Preferences"}</Button>
          </div>
        </Card>
      </motion.div>

      {/* Multilingual & Voice Card */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardTitle>🌐 Multilingual & Voice Assistant Preferences</CardTitle>
          <div className="mt-4 space-y-5">
            {/* Lang Dropdown */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Default Coach Language</label>
              <p className="text-xs text-muted mb-2.5">
                Which language should the agent chat, analyze context, and store memories in?
              </p>
              <select
                value={selectedLanguage}
                onChange={(e) => setSelectedLanguage(e.target.value)}
                className="w-full bg-surface border border-border/80 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-calm-500 text-foreground transition-all cursor-pointer font-medium"
              >
                {supportedLanguages.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Accent Style Selector */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Speaking Accent / Style</label>
              <p className="text-xs text-muted mb-2.5">
                Choose the localized synthesis profile for the voice feedback.
              </p>
              <select
                value={voiceAccent}
                onChange={(e) => setVoiceAccent(e.target.value)}
                className="w-full bg-surface border border-border/80 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-calm-500 text-foreground transition-all cursor-pointer font-medium"
              >
                {supportedAccents.map((acc) => (
                  <option key={acc.code} value={acc.code}>
                    {acc.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Auto Speak Toggle */}
            <div className="flex items-center justify-between py-2 border-t border-border/40">
              <div>
                <p className="text-sm font-medium text-foreground">🔊 Auto-Speak Agent Responses</p>
                <p className="text-xs text-muted">Automatically speaks agent replies aloud as they finish streaming</p>
              </div>
              <button
                onClick={() => setVoiceAutospeak(!voiceAutospeak)}
                className={`w-11 h-6 rounded-full transition-all duration-300 relative ${voiceAutospeak ? "bg-calm-500" : "bg-border"}`}
              >
                <motion.div
                  className="absolute top-0.5 w-5 h-5 rounded-full bg-white shadow"
                  animate={{ left: voiceAutospeak ? 22 : 2 }}
                  transition={{ type: "spring", stiffness: 500, damping: 30 }}
                />
              </button>
            </div>

            {/* Pitch & Speed Sliders */}
            <div className="space-y-4 pt-2 border-t border-border/40">
              <Slider
                label={`Speaking Rate / Speed: ${voiceSpeed.toFixed(2)}x`}
                value={voiceSpeed}
                onChange={setVoiceSpeed}
                min={0.5}
                max={2.0}
                step={0.05}
              />
              <Slider
                label={`Speech Pitch / Tone: ${voicePitch.toFixed(2)}`}
                value={voicePitch}
                onChange={setVoicePitch}
                min={0.5}
                max={1.5}
                step={0.05}
              />
            </div>

            {/* Voice Testing Box */}
            <div className="flex items-center gap-3 pt-3 border-t border-border/40">
              <Button onClick={playVoiceTest} variant="outline" size="sm" className="text-xs font-bold rounded-xl flex items-center gap-1">
                🗣️ Play Test Phrase
              </Button>
              <Button onClick={handleSave} size="sm" className="text-xs font-bold rounded-xl">
                {saved ? "✅ Saved!" : "Save Voice Preferences"}
              </Button>
            </div>
          </div>
        </Card>
      </motion.div>

      {/* Focus Timer */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardTitle>⏱️ Focus Timer</CardTitle>
          <div className="mt-4">
            <Slider label="Default session duration (minutes)" value={timerDuration} onChange={setTimerDuration} min={5} max={120} step={5} />
            <motion.div whileTap={{ scale: 0.98 }}>
              <Button className="mt-3" size="sm" onClick={() => { updateSettings({ timer_duration: timerDuration }); setSaved(true); setTimeout(() => setSaved(false), 2000); }}>
                Update Timer Duration
              </Button>
            </motion.div>
          </div>
        </Card>
      </motion.div>

      {/* ADHD UX Features */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardTitle>🎨 ADHD UX Features</CardTitle>
          <div className="mt-4 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-foreground">🌙 Time Blindness Helper</p>
                <p className="text-xs text-muted">Shows a visual day progress bar in the sidebar</p>
              </div>
              <button onClick={toggleTimeBlindness} className={`w-11 h-6 rounded-full transition-all duration-300 relative ${timeBlindnessEnabled ? "bg-calm-500" : "bg-border"}`}>
                <motion.div className="absolute top-0.5 w-5 h-5 rounded-full bg-white shadow" animate={{ left: timeBlindnessEnabled ? 22 : 2 }} transition={{ type: "spring", stiffness: 500, damping: 30 }} />
              </button>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-foreground">🐣 Start Tiny Mode</p>
                <p className="text-xs text-muted">Default to micro-tasks and small wins</p>
              </div>
              <button onClick={() => setStartTinyMode(!startTinyMode)} className={`w-11 h-6 rounded-full transition-all duration-300 relative ${startTinyMode ? "bg-calm-500" : "bg-border"}`}>
                <motion.div className="absolute top-0.5 w-5 h-5 rounded-full bg-white shadow" animate={{ left: startTinyMode ? 22 : 2 }} transition={{ type: "spring", stiffness: 500, damping: 30 }} />
              </button>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-foreground">🎉 Celebration Effects</p>
                <p className="text-xs text-muted">Dopamine-friendly confetti on achievements</p>
              </div>
              <span className="text-xs text-muted">✨ Enabled</span>
            </div>
          </div>
        </Card>
      </motion.div>

      {/* Security PIN Settings */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardTitle>🔒 Security PIN Settings</CardTitle>
          
          {showPinSetup ? (
            <div className="space-y-4 pt-3 mt-4 border-t border-border/40">
              <p className="text-sm font-medium text-foreground text-center">
                Enter a 4-Digit Security PIN
              </p>
              
              <div className="flex justify-center gap-3 py-2">
                {[0, 1, 2, 3].map((index) => (
                  <div
                    key={index}
                    className={`w-4 h-4 rounded-full border-2 transition-all duration-200 ${
                      enteredPin.length > index
                        ? "bg-calm-500 border-calm-500 scale-110 shadow-[0_0_8px_rgba(110,231,183,0.5)]"
                        : "border-border bg-surface"
                    }`}
                  />
                ))}
              </div>
              
              {pinError && (
                <p className="text-xs text-danger-500 text-center font-medium">
                  {pinError}
                </p>
              )}
              
              {/* Keypad */}
              <div className="grid grid-cols-3 gap-2 max-w-[200px] mx-auto">
                {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((num) => (
                  <button
                    key={num}
                    type="button"
                    onClick={() => {
                      if (enteredPin.length < 4) {
                        setEnteredPin((prev) => prev + num);
                        setPinError("");
                      }
                    }}
                    className="w-12 h-12 rounded-full bg-surface border border-border/80 text-foreground font-semibold hover:bg-white/5 active:scale-95 transition-all text-sm mx-auto flex items-center justify-center cursor-pointer"
                  >
                    {num}
                  </button>
                ))}
                <button
                  type="button"
                  onClick={() => {
                    setEnteredPin("");
                    setPinError("");
                  }}
                  className="text-xs text-muted hover:text-foreground font-medium cursor-pointer"
                >
                  Clear
                </button>
                <button
                  type="button"
                  onClick={() => {
                    if (enteredPin.length < 4) {
                      setEnteredPin((prev) => prev + "0");
                      setPinError("");
                    }
                  }}
                  className="w-12 h-12 rounded-full bg-surface border border-border/80 text-foreground font-semibold hover:bg-white/5 active:scale-95 transition-all text-sm mx-auto flex items-center justify-center cursor-pointer"
                >
                  0
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setEnteredPin((prev) => prev.slice(0, -1));
                    setPinError("");
                  }}
                  className="text-xs text-muted hover:text-foreground font-medium cursor-pointer"
                >
                  Delete
                </button>
              </div>

              <div className="flex gap-2 justify-center pt-2">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => {
                    setShowPinSetup(false);
                    setEnteredPin("");
                    setPinError("");
                  }}
                >
                  Cancel
                </Button>
                <Button
                  size="sm"
                  onClick={handleSetPin}
                  disabled={enteredPin.length !== 4}
                >
                  Confirm PIN
                </Button>
              </div>
            </div>
          ) : (
            <div className="mt-4 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-foreground">
                    {hasPin ? "🔒 Security PIN Enabled" : "🔓 Security PIN Disabled"}
                  </p>
                  <p className="text-xs text-muted mt-1">
                    {hasPin
                      ? "You can unlock and log in with your 4-digit PIN on this device."
                      : "Set a 4-digit PIN to enable quick login without your full password."}
                  </p>
                </div>
              </div>

              {pinMessage && (
                <p className="text-xs text-calm-400 bg-calm-500/10 rounded-lg p-2 text-center font-medium">
                  {pinMessage}
                </p>
              )}
              {pinError && (
                <p className="text-xs text-danger-500 bg-danger-500/10 rounded-lg p-2 text-center font-medium">
                  {pinError}
                </p>
              )}

              <div className="flex gap-2">
                {hasPin ? (
                  <>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setShowPinSetup(true);
                        setEnteredPin("");
                        setPinError("");
                      }}
                    >
                      Change PIN
                    </Button>
                    <Button size="sm" variant="danger" onClick={handleRemovePin}>
                      Remove PIN
                    </Button>
                  </>
                ) : (
                  <Button
                    size="sm"
                    onClick={() => {
                      setShowPinSetup(true);
                      setEnteredPin("");
                      setPinError("");
                    }}
                  >
                    Setup Security PIN
                  </Button>
                )}
              </div>

              {/* Trusted Devices List */}
              {devices.length > 0 && (
                <div className="pt-4 mt-4 border-t border-border/40 w-full space-y-3">
                  <h4 className="text-xs font-semibold text-foreground">📱 Trusted Devices</h4>
                  <div className="space-y-2">
                    {devices.map((dev) => (
                      <div
                        key={dev.device_id}
                        className="flex justify-between items-center p-3 rounded-xl border border-border/60 bg-surface-secondary/40 text-xs"
                      >
                        <div className="space-y-1">
                          <p className="font-semibold text-foreground text-xs">{dev.device_name}</p>
                          <p className="text-[10px] text-muted">
                            Last Used: {new Date(dev.last_used).toLocaleString()}
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleRemoveDevice(dev.device_id)}
                          className="px-2.5 py-1 rounded-lg text-[10px] font-bold text-danger-500 border border-danger-500/25 hover:bg-danger-500/5 transition-all cursor-pointer"
                        >
                          Revoke
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </Card>
      </motion.div>

      {/* About */}
      <motion.div variants={itemVariants}>
        <Card variant="glass">
          <CardTitle>🧠 About ADHD AI Coach</CardTitle>
          <div className="mt-3 text-sm text-muted space-y-2">
            <p>Version 2.0 — ADHD Executive Function Ecosystem</p>
            <p>Free & Open Source · Built with Next.js + FastAPI</p>
            <p>Designed specifically for ADHD brains — reducing cognitive load, providing dopamine-friendly feedback, and offering emotionally intelligent support.</p>
          </div>
        </Card>
      </motion.div>
    </motion.div>
  );
}
