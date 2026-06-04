"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardTitle } from "@/components/ui/card";
import { useUserStore } from "@/stores/user-store";
import { api } from "@/services/api";

const loginSchema = z.object({
  username: z.string().min(1, "Username is required"),
  password: z.string().min(1, "Password is required"),
});

type LoginForm = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const { login: loginUser } = useUserStore();
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({ resolver: zodResolver(loginSchema) });

  const onSubmit = async (data: LoginForm) => {
    try {
      const res = await api.login(data.username, data.password);
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
            Welcome <span className="gradient-text">Back</span>
          </h1>
          <p className="text-sm text-muted mt-1">Sign in to your ADHD Coach</p>
        </div>

        <Card className="p-6">
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

            <div className="flex justify-end">
              <Link href="/forgot-password" className="text-xs text-calm-400 hover:text-calm-300 transition-colors">
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
          </form>
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
