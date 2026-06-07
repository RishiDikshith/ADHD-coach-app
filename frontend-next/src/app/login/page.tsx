"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { useUserStore } from "@/stores/user-store";
import { api } from "@/services/api";

const loginSchema = z.object({
  username: z.string().min(1, "Username is required"),
  password: z.string().min(1, "Password is required"),
});

type LoginForm = z.infer<typeof loginSchema>;

const shakeVariants = {
  shake: {
    x: [0, -10, 10, -10, 10, -5, 5, 0],
    transition: { duration: 0.4 }
  }
};

export default function LoginPage() {
  const router = useRouter();
  const { login: loginUser, isAuthenticated, lastUsername, getDeviceId } = useUserStore();
  
  const [isCheckingPin, setIsCheckingPin] = useState(true);
  const [hasPin, setHasPin] = useState(false);
  const [usePin, setUsePin] = useState(false);
  const [enteredPin, setEnteredPin] = useState("");
  const [pinError, setPinError] = useState("");
  const [isShaking, setIsShaking] = useState(false);
  const [pinSubmitting, setPinSubmitting] = useState(false);

  // Admin login states
  const [isAdminLogin, setIsAdminLogin] = useState(false);
  const [adminUsername, setAdminUsername] = useState("");
  const [adminUsernameError, setAdminUsernameError] = useState("");

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({ resolver: zodResolver(loginSchema) });

  // Auto-login & PIN presence check via Trusted Device Recognition
  useEffect(() => {
    if (isAuthenticated) {
      router.push("/dashboard");
      return;
    }

    const devId = getDeviceId();
    
    // Check if the current device is already trusted
    api.checkTrustedDevice(devId)
      .then((res) => {
        if (res.is_trusted && res.username) {
          setHasPin(res.has_pin || false);
          if (res.has_pin) {
            setUsePin(true);
            // Pre-populate last username in store for quick login
            useUserStore.setState({ lastUsername: res.username });
          }
        }
      })
      .catch((err) => console.error("Trusted device validation failed:", err))
      .finally(() => setIsCheckingPin(false));
  }, [isAuthenticated, getDeviceId, router]);

  // Form submit (username/password)
  const onSubmit = async (data: LoginForm) => {
    try {
      const devId = getDeviceId();
      const devName = typeof window !== "undefined" ? window.navigator.userAgent.slice(0, 100) : "Unknown Device";
      
      const res = await api.login(data.username, data.password, devId, devName);
      if (res.success) {
        loginUser(data.username, res.role);
        router.push("/dashboard");
      } else {
        setError("root", { message: res.error || "Login failed. Please check your credentials." });
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Connection error. Please try again.";
      setError("root", { message: msg });
    }
  };

  // PIN entry validation and submission
  const handlePinDigit = async (digit: string) => {
    if (enteredPin.length >= 4 || pinSubmitting) return;
    
    const newPin = enteredPin + digit;
    setEnteredPin(newPin);
    setPinError("");

    if (newPin.length === 4) {
      if (isAdminLogin && !adminUsername.trim()) {
        setAdminUsernameError("Admin username is required");
        setEnteredPin("");
        return;
      }
      setAdminUsernameError("");
      setPinSubmitting(true);
      
      try {
        const devId = getDeviceId();
        let res;
        
        if (isAdminLogin) {
          res = await api.adminPinLogin(adminUsername.trim(), newPin);
        } else {
          res = await api.loginPin(lastUsername!, newPin, devId);
        }

        if (res.success) {
          loginUser(isAdminLogin ? adminUsername.trim() : lastUsername!, res.role);
          router.push("/dashboard");
        } else {
          setPinError(res.error || "Incorrect PIN");
          setEnteredPin("");
          setIsShaking(true);
          setTimeout(() => setIsShaking(false), 500);
        }
      } catch (err: any) {
        setPinError(err.message || "Failed to log in with PIN");
        setEnteredPin("");
        setIsShaking(true);
        setTimeout(() => setIsShaking(false), 500);
      } finally {
        setPinSubmitting(false);
      }
    }
  };

  const handlePinBackspace = () => {
    if (enteredPin.length > 0 && !pinSubmitting) {
      setEnteredPin(enteredPin.slice(0, -1));
      setPinError("");
    }
  };

  const handlePinClear = () => {
    if (!pinSubmitting) {
      setEnteredPin("");
      setPinError("");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-b from-background via-[#0a1628] to-background">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        <div className="text-center mb-8">
          <motion.div
            className="text-4xl mb-3 inline-block"
            animate={{ y: [0, -6, 0] }}
            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
          >
            🧠
          </motion.div>
          <h1 className="text-2xl font-bold text-foreground">
            {isAdminLogin ? "Admin Portal" : "Welcome Back"}
          </h1>
          <p className="text-sm text-muted mt-1">
            {isAdminLogin ? "Log in with administrative PIN" : "Sign in to your ADHD Coach"}
          </p>
        </div>

        <Card className="p-6 overflow-hidden">
          {isCheckingPin ? (
            <div className="flex flex-col items-center py-12 space-y-4">
              <div className="w-10 h-10 border-4 border-calm-500/30 border-t-calm-500 rounded-full animate-spin" />
              <p className="text-xs text-muted">Checking security session...</p>
            </div>
          ) : usePin && (lastUsername || isAdminLogin) ? (
            /* PIN login interface */
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="space-y-6 flex flex-col items-center"
            >
              <div className="text-center w-full">
                {isAdminLogin ? (
                  <div className="mb-4 text-left w-full px-2">
                    <label className="block text-xs font-semibold text-muted mb-1.5">Admin Username</label>
                    <Input
                      id="adminUsername"
                      value={adminUsername}
                      placeholder="Enter admin username"
                      onChange={(e) => {
                        setAdminUsername(e.target.value);
                        setAdminUsernameError("");
                      }}
                      error={adminUsernameError}
                      className="text-sm py-1.5"
                    />
                  </div>
                ) : (
                  <>
                    <p className="text-sm font-semibold text-foreground">Unlock for {lastUsername}</p>
                    <p className="text-xs text-muted mt-1">Enter your 4-digit security PIN</p>
                  </>
                )}
              </div>

              {/* PIN circles indicator */}
              <motion.div
                variants={shakeVariants}
                animate={isShaking ? "shake" : "default"}
                className="flex gap-4 my-2"
              >
                {[0, 1, 2, 3].map((index) => (
                  <div
                    key={index}
                    className={`w-4 h-4 rounded-full border-2 transition-all duration-200 ${
                      enteredPin.length > index
                        ? "bg-calm-500 border-calm-500 scale-110 shadow-[0_0_10px_rgba(110,231,183,0.5)]"
                        : "border-border bg-surface"
                    }`}
                  />
                ))}
              </motion.div>

              {pinError && (
                <p className="text-xs text-danger-500 bg-danger-500/10 rounded-lg px-3 py-1.5 text-center font-medium">
                  {pinError}
                </p>
              )}

              {/* Pin numeric keypad */}
              <div className="grid grid-cols-3 gap-3 max-w-[240px] w-full pt-2">
                {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((num) => (
                  <button
                    key={num}
                    type="button"
                    disabled={pinSubmitting}
                    onClick={() => handlePinDigit(num.toString())}
                    className="w-14 h-14 rounded-full bg-surface border border-border/80 text-foreground font-semibold hover:bg-white/5 active:scale-90 disabled:opacity-50 transition-all text-lg mx-auto flex items-center justify-center cursor-pointer shadow-sm"
                  >
                    {num}
                  </button>
                ))}
                <button
                  type="button"
                  disabled={pinSubmitting}
                  onClick={handlePinClear}
                  className="text-xs text-muted hover:text-foreground font-medium cursor-pointer flex items-center justify-center w-14 h-14 rounded-full"
                >
                  Clear
                </button>
                <button
                  type="button"
                  disabled={pinSubmitting}
                  onClick={() => handlePinDigit("0")}
                  className="w-14 h-14 rounded-full bg-surface border border-border/80 text-foreground font-semibold hover:bg-white/5 active:scale-90 disabled:opacity-50 transition-all text-lg mx-auto flex items-center justify-center cursor-pointer shadow-sm"
                >
                  0
                </button>
                <button
                  type="button"
                  disabled={pinSubmitting}
                  onClick={handlePinBackspace}
                  className="text-xs text-muted hover:text-foreground font-medium cursor-pointer flex items-center justify-center w-14 h-14 rounded-full"
                >
                  Delete
                </button>
              </div>

              {/* Option switch links */}
              <div className="flex flex-col gap-2.5 items-center w-full pt-4 border-t border-border/40 text-xs">
                {!isAdminLogin && (
                  <button
                    type="button"
                    onClick={() => {
                      setUsePin(false);
                      setPinError("");
                      setEnteredPin("");
                    }}
                    className="text-calm-400 hover:text-calm-300 font-medium transition-colors cursor-pointer"
                  >
                    Log in with password instead
                  </button>
                )}
                
                <button
                  type="button"
                  onClick={() => {
                    setUsePin(false);
                    setHasPin(false);
                    setIsAdminLogin(!isAdminLogin);
                    setPinError("");
                    setEnteredPin("");
                    setAdminUsername("");
                    if (isAdminLogin) {
                      // Switch back to normal pin if we had one
                      api.checkTrustedDevice(getDeviceId()).then(res => {
                        if (res.is_trusted && res.username && res.has_pin) {
                          setHasPin(true);
                          setUsePin(true);
                        }
                      });
                    } else {
                      setUsePin(true); // admin requires pin keypad
                    }
                  }}
                  className="text-muted hover:text-foreground transition-colors cursor-pointer font-medium"
                >
                  {isAdminLogin ? "← Switch to user login" : "🔑 Are you an admin?"}
                </button>
              </div>
            </motion.div>
          ) : (
            /* Standard username/password login interface */
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <Input
                label="Username"
                id="username"
                placeholder="Enter your username"
                error={errors.username?.message}
                autoFocus
                {...register("username")}
              />
              <Input
                label="Password"
                id="password"
                type="password"
                placeholder="Enter your password"
                error={errors.password?.message}
                {...register("password")}
              />

              <div className="flex justify-between items-center text-xs">
                {hasPin && lastUsername && (
                  <button
                    type="button"
                    onClick={() => {
                      setUsePin(true);
                      setPinError("");
                      setEnteredPin("");
                    }}
                    className="text-calm-400 hover:text-calm-300 font-medium transition-colors cursor-pointer"
                  >
                    🔒 Use Security PIN
                  </button>
                )}
                <Link href="/forgot-password" className="text-muted hover:text-foreground ml-auto transition-colors">
                  Forgot password?
                </Link>
              </div>

              {errors.root && (
                <motion.p
                  initial={{ opacity: 0, y: -5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-sm text-danger-500 bg-danger-500/10 rounded-lg p-3"
                >
                  {errors.root.message}
                </motion.p>
              )}

              <Button type="submit" loading={isSubmitting} className="w-full">
                Sign In
              </Button>
              
              <div className="text-center pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setIsAdminLogin(true);
                    setUsePin(true);
                    setEnteredPin("");
                    setPinError("");
                  }}
                  className="text-xs text-muted hover:text-foreground transition-colors cursor-pointer font-medium"
                >
                  🔑 Are you an admin?
                </button>
              </div>
            </form>
          )}
        </Card>

        <p className="text-center text-sm text-muted mt-6">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-calm-400 hover:text-calm-300 transition-colors font-medium">
            Create one
          </Link>
        </p>

        <p className="text-center text-xs text-muted/50 mt-4">
          Free & Open Source · Your data stays private
        </p>
      </motion.div>
    </div>
  );
}
