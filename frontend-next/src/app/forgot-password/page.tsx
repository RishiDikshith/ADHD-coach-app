"use client";

import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardTitle } from "@/components/ui/card";
import { api } from "@/services/api";

const forgotSchema = z.object({
  username: z.string().min(1, "Username is required"),
  email: z.string().email("Valid email is required"),
  newPassword: z.string().min(6, "Password must be at least 6 characters"),
  confirmPassword: z.string().min(6, "Please confirm your password"),
}).refine((data) => data.newPassword === data.confirmPassword, {
  message: "Passwords must match",
  path: ["confirmPassword"],
});

type ForgotForm = z.infer<typeof forgotSchema>;

export default function ForgotPasswordPage() {
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotForm>({
    resolver: zodResolver(forgotSchema),
  });

  const onSubmit = async (data: ForgotForm) => {
    setStatus("loading");
    setMessage("");
    try {
      const res = await api.resetPassword(data.username, data.email, data.newPassword);
      if (res.success) {
        setStatus("success");
        setMessage("Password reset successfully! You can now sign in.");
      } else {
        setStatus("error");
        setMessage(res.error || "Reset failed. Please check your credentials.");
      }
    } catch {
      setStatus("error");
      setMessage("Connection error. Please try again.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-b from-background via-[#0a1628] to-background">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <div className="text-center mb-8">
          <div className="text-4xl mb-3">🔑</div>
          <h1 className="text-2xl font-bold text-foreground">Reset Password</h1>
          <p className="text-sm text-muted mt-1">Enter your details to create a new password</p>
        </div>

        <Card className="p-6">
          {status === "success" ? (
            <div className="text-center space-y-4">
              <div className="text-5xl">✅</div>
              <CardTitle>Password Reset!</CardTitle>
              <p className="text-sm text-muted">{message}</p>
              <Link href="/login">
                <Button className="w-full mt-2">Sign In →</Button>
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <Input
                label="Username"
                id="username"
                placeholder="Enter your username"
                error={errors.username?.message}
                {...register("username")}
              />
              <Input
                label="Email"
                id="email"
                type="email"
                placeholder="Enter your email"
                error={errors.email?.message}
                {...register("email")}
              />
              <Input
                label="New Password"
                id="newPassword"
                type="password"
                placeholder="At least 6 characters"
                error={errors.newPassword?.message}
                {...register("newPassword")}
              />
              <Input
                label="Confirm Password"
                id="confirmPassword"
                type="password"
                placeholder="Repeat new password"
                error={errors.confirmPassword?.message}
                {...register("confirmPassword")}
              />

              {status === "error" && (
                <motion.p
                  initial={{ opacity: 0, y: -5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-sm text-danger-500 bg-danger-500/10 rounded-lg p-3"
                >
                  {message}
                </motion.p>
              )}

              <Button type="submit" loading={status === "loading"} className="w-full">
                Reset Password
              </Button>
            </form>
          )}
        </Card>

        <p className="text-center text-sm text-muted mt-6">
          Remember your password?{" "}
          <Link href="/login" className="text-calm-400 hover:text-calm-300 transition-colors font-medium">
            Sign in
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
