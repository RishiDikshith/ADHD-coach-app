"use client";

import { useState, useEffect, useRef, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { useUserStore } from "@/stores/user-store";
import { api, setAccessToken } from "@/services/api";
import { API_URL } from "@/lib/api";

const shakeVariants = {
  shake: {
    x: [0, -10, 10, -10, 10, -5, 5, 0],
    transition: { duration: 0.4 },
  },
};

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const oauthError = searchParams.get("error");
  const [displayedError] = useState<string | null>(oauthError);

  useEffect(() => {
    if (oauthError) {
      if (typeof window !== "undefined") {
        window.history.replaceState({}, "", window.location.pathname);
      }
    }
  }, [oauthError]);

  const {
    login: loginUser,
    isAuthenticated,
    authStatus,
    lastUsername,
    getDeviceId,
  } = useUserStore();

  const [isCheckingPin, setIsCheckingPin] = useState(() =>
    typeof window !== "undefined" ? Boolean(getDeviceId()) : true
  );
  const [hasPin, setHasPin] = useState(false);
  const [usePin, setUsePin] = useState(false);
  const [enteredPin, setEnteredPin] = useState("");
  const [pinError, setPinError] = useState("");
  const [isShaking, setIsShaking] = useState(false);
  const [pinSubmitting, setPinSubmitting] = useState(false);

  // Remember this device checkbox state
  const [rememberDevice, setRememberDevice] = useState(true);

  // Admin login states
  const [isAdminLogin, setIsAdminLogin] = useState(false);
  const [adminUsername, setAdminUsername] = useState("");
  const [adminUsernameError, setAdminUsernameError] = useState("");

  const hasCheckedRef = useRef(false);

  // Check trusted device on load (idempotent, single execution)
  useEffect(() => {
    if (authStatus === "authenticated" && isAuthenticated) {
      router.push("/dashboard");
      return;
    }

    if (authStatus === "unauthenticated") {
      setAccessToken(null);
    }

    if (hasCheckedRef.current) return;
    hasCheckedRef.current = true;

    const devId = getDeviceId();
    if (!devId) {
      return;
    }

    api
      .checkTrustedDevice(devId)
      .then((res) => {
        if (res && res.is_trusted && res.username) {
          setHasPin(Boolean(res.has_pin));
          if (res.has_pin) {
            useUserStore.setState({ lastUsername: res.username });
          }
        }
      })
      .catch((err) => {
        console.warn(
          "[TRUSTED DEVICE] Check unverified:",
          err instanceof Error ? err.message : err
        );
      })
      .finally(() => setIsCheckingPin(false));
  }, [authStatus, isAuthenticated, getDeviceId, router]);

  const handleOAuthRedirect = (provider: "google" = "google") => {
    const backendUrl = API_URL || "http://localhost:8000";
    window.location.href = `${backendUrl}/auth/oauth/${provider}/login?remember_device=${rememberDevice}`;
  };

  // PIN keypad handling
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
          if (!res.token) throw new Error("PIN login response did not include an access token.");
          loginUser(
            res.username || (isAdminLogin ? adminUsername.trim() : lastUsername!),
            res.token,
            res.role
          );
          router.push("/dashboard");
        } else {
          setPinError(res.error || "Incorrect PIN");
          setEnteredPin("");
          setIsShaking(true);
          setTimeout(() => setIsShaking(false), 500);
        }
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Failed to log in with PIN";
        setPinError(message);
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
            {isAdminLogin ? "Log in with administrative PIN" : "Sign in securely with Google"}
          </p>
        </div>

        <Card className="p-6 overflow-hidden">
          {/* OAuth error alert */}
          {displayedError && !usePin && (
            <motion.div
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-4 text-xs text-danger-500 bg-danger-500/10 border border-danger-500/20 rounded-lg p-3 text-center font-medium"
            >
              Authentication error: {decodeURIComponent(displayedError).replace(/_/g, " ")}
            </motion.div>
          )}

          {isCheckingPin ? (
            <div className="flex flex-col items-center py-12 space-y-4">
              <div className="w-10 h-10 border-4 border-calm-500/30 border-t-calm-500 rounded-full animate-spin" />
              <p className="text-xs text-muted">Securing session...</p>
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
                    <label className="block text-xs font-semibold text-muted mb-1.5">
                      Admin Username
                    </label>
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
                    <p className="text-sm font-semibold text-foreground">
                      Unlock for {lastUsername}
                    </p>
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

              {/* Switch back to OAuth */}
              <div className="flex flex-col gap-2.5 items-center w-full pt-4 border-t border-border/40 text-xs">
                <button
                  type="button"
                  onClick={() => {
                    setUsePin(false);
                    setIsAdminLogin(false);
                    setPinError("");
                    setEnteredPin("");
                  }}
                  className="text-calm-400 hover:text-calm-300 font-medium transition-colors cursor-pointer"
                >
                  ← Sign in with Google
                </button>
              </div>
            </motion.div>
          ) : (
            /* Primary OAuth 2.0 / OpenID Connect Interface */
            <div className="space-y-5">
              <div className="space-y-3">
                {/* Continue with Google */}
                <button
                  type="button"
                  onClick={() => handleOAuthRedirect("google")}
                  className="w-full flex items-center justify-center px-4 py-3 border border-border/80 rounded-xl bg-surface hover:bg-white/5 hover:border-calm-500/40 text-foreground font-medium text-sm transition-all duration-200 shadow-sm cursor-pointer group"
                >
                  <svg className="w-5 h-5 mr-3 flex-shrink-0" viewBox="0 0 24 24">
                    <path
                      fill="#4285F4"
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    />
                    <path
                      fill="#34A853"
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    />
                    <path
                      fill="#FBBC05"
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                    />
                    <path
                      fill="#EA4335"
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                    />
                  </svg>
                  <span className="group-hover:translate-x-0.5 transition-transform">
                    Continue with Google
                  </span>
                </button>
              </div>

              {/* Remember this device checkbox */}
              <div className="flex items-center space-x-2.5 pt-2 pb-1 px-1">
                <input
                  type="checkbox"
                  id="rememberDevice"
                  checked={rememberDevice}
                  onChange={(e) => setRememberDevice(e.target.checked)}
                  className="w-4 h-4 rounded border-border text-calm-500 focus:ring-calm-500/40 bg-surface cursor-pointer"
                />
                <label
                  htmlFor="rememberDevice"
                  className="text-xs text-foreground font-medium cursor-pointer select-none"
                >
                  Remember this device{" "}
                  <span className="text-muted text-[11px] block font-normal">
                    Keep session trusted on this browser for 30 days
                  </span>
                </label>
              </div>

              {/* Secondary Options: PIN unlock & Admin Portal */}
              <div className="pt-4 border-t border-border/40 flex flex-col gap-2 items-center text-xs">
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
                    🔒 Unlock with Security PIN
                  </button>
                )}

                <button
                  type="button"
                  onClick={() => {
                    setIsAdminLogin(true);
                    setUsePin(true);
                    setEnteredPin("");
                    setPinError("");
                  }}
                  className="text-muted hover:text-foreground transition-colors cursor-pointer font-medium"
                >
                  🔑 Admin Portal
                </button>
              </div>
            </div>
          )}
        </Card>

        <p className="text-center text-sm text-muted mt-6">
          Don&apos;t have an account?{" "}
          <Link
            href="/register"
            className="text-calm-400 hover:text-calm-300 transition-colors font-medium"
          >
            Create one with OAuth
          </Link>
        </p>

        <p className="text-center text-xs text-muted/50 mt-4">
          Free & Open Source · End-to-end encrypted identity · Data stays private
        </p>
      </motion.div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-b from-background via-[#0a1628] to-background">
          <div className="w-8 h-8 border-4 border-calm-500/30 border-t-calm-500 rounded-full animate-spin" />
        </div>
      }
    >
      <LoginContent />
    </Suspense>
  );
}
