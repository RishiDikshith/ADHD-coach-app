"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useUserStore } from "@/stores/user-store";
import { api } from "@/services/api";
import { Button } from "@/components/ui/button";

const shakeVariants = {
  shake: {
    x: [0, -10, 10, -10, 10, -5, 5, 0],
    transition: { duration: 0.4 }
  }
};

export function PinSetupModal() {
  const { username, getDeviceId } = useUserStore();
  const [showModal, setShowModal] = useState(false);
  const [enteredPin, setEnteredPin] = useState("");
  const [isShaking, setIsShaking] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!username) return;

    // Check if user already has a PIN
    api.hasPin(username)
      .then((res) => {
        // If they don't have a PIN, and haven't skipped it in this browser session
        const skipped = sessionStorage.getItem("adhd_pin_setup_skipped");
        if (!res.has_pin && !skipped) {
          setShowModal(true);
        }
      })
      .catch((err) => console.error("Error checking PIN status:", err));
  }, [username]);

  const handleDigit = (digit: string) => {
    if (enteredPin.length >= 4 || loading) return;
    setEnteredPin((prev) => prev + digit);
    setError("");
  };

  const handleBackspace = () => {
    if (enteredPin.length > 0 && !loading) {
      setEnteredPin((prev) => prev.slice(0, -1));
      setError("");
    }
  };

  const handleClear = () => {
    if (!loading) {
      setEnteredPin("");
      setError("");
    }
  };

  const handleConfirm = async () => {
    if (enteredPin.length !== 4) {
      setError("PIN must be exactly 4 digits");
      setIsShaking(true);
      setTimeout(() => setIsShaking(false), 500);
      return;
    }

    setLoading(true);
    try {
      const devId = getDeviceId();
      const devName = typeof window !== "undefined" ? window.navigator.userAgent.slice(0, 100) : "Unknown Device";
      
      const res = await api.setPin(enteredPin, devId, devName);
      if (res.success) {
        setShowModal(false);
        // Dispatch setting change to trigger UI refresh elsewhere if needed
      } else {
        setError(res.message || "Failed to save PIN");
        setEnteredPin("");
        setIsShaking(true);
        setTimeout(() => setIsShaking(false), 500);
      }
    } catch (err: any) {
      setError(err.message || "An error occurred");
      setEnteredPin("");
      setIsShaking(true);
      setTimeout(() => setIsShaking(false), 500);
    } finally {
      setLoading(false);
    }
  };

  const handleSkip = () => {
    sessionStorage.setItem("adhd_pin_setup_skipped", "true");
    setShowModal(false);
  };

  if (!showModal) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={handleSkip}
          className="absolute inset-0 bg-background/80 backdrop-blur-sm"
        />

        {/* Modal content */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="relative w-full max-w-sm rounded-2xl border border-border/80 bg-surface p-6 shadow-2xl overflow-hidden flex flex-col items-center"
        >
          <div className="text-center mb-4">
            <span className="text-3xl block mb-2">🔒</span>
            <h3 className="text-lg font-bold text-foreground">Set a Quick Login PIN</h3>
            <p className="text-xs text-muted mt-1 max-w-[250px] mx-auto">
              Minimize typing your full password on this device next time!
            </p>
          </div>

          {/* PIN circles */}
          <motion.div
            variants={shakeVariants}
            animate={isShaking ? "shake" : "default"}
            className="flex gap-4 my-3"
          >
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
          </motion.div>

          {error && (
            <p className="text-xs text-danger-500 font-medium my-1">{error}</p>
          )}

          {/* Keypad */}
          <div className="grid grid-cols-3 gap-2.5 max-w-[200px] w-full mt-2">
            {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((num) => (
              <button
                key={num}
                type="button"
                disabled={loading}
                onClick={() => handleDigit(num.toString())}
                className="w-12 h-12 rounded-full bg-surface-secondary border border-border/60 text-foreground font-semibold hover:bg-white/5 active:scale-95 disabled:opacity-50 transition-all text-sm mx-auto flex items-center justify-center cursor-pointer shadow-sm"
              >
                {num}
              </button>
            ))}
            <button
              type="button"
              disabled={loading}
              onClick={handleClear}
              className="text-xs text-muted hover:text-foreground font-medium cursor-pointer flex items-center justify-center"
            >
              Clear
            </button>
            <button
              type="button"
              disabled={loading}
              onClick={() => handleDigit("0")}
              className="w-12 h-12 rounded-full bg-surface-secondary border border-border/60 text-foreground font-semibold hover:bg-white/5 active:scale-95 disabled:opacity-50 transition-all text-sm mx-auto flex items-center justify-center cursor-pointer shadow-sm"
            >
              0
            </button>
            <button
              type="button"
              disabled={loading}
              onClick={handleBackspace}
              className="text-xs text-muted hover:text-foreground font-medium cursor-pointer flex items-center justify-center"
            >
              Delete
            </button>
          </div>

          <div className="flex gap-3 mt-6 w-full pt-4 border-t border-border/40 justify-center">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleSkip}
              className="text-xs text-muted hover:text-foreground"
            >
              Skip for now
            </Button>
            <Button
              size="sm"
              onClick={handleConfirm}
              loading={loading}
              disabled={enteredPin.length !== 4}
              className="text-xs"
            >
              Confirm PIN
            </Button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
