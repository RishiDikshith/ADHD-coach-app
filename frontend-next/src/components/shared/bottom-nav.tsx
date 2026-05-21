"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";

const navItems = [
  { href: "/dashboard", icon: "📊", label: "Home" },
  { href: "/chat", icon: "💬", label: "Chat" },
  { href: "/focus", icon: "🎯", label: "Focus" },
  { href: "/tasks", icon: "📋", label: "Tasks" },
  { href: "/analytics", icon: "📈", label: "Analytics" },
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 safe-bottom">
      <div className="glass-strong rounded-t-2xl border-t border-border px-2 pb-safe pb-2">
        <div className="flex items-center justify-around py-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className="relative flex flex-col items-center gap-0.5 py-1 px-3 min-touch-target"
              >
                {isActive && (
                  <motion.div
                    layoutId="bottom-nav-indicator"
                    className="absolute -top-0.5 w-8 h-0.5 rounded-full bg-calm-500"
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                  />
                )}
                <span className={`text-lg transition-all ${isActive ? "scale-110" : "opacity-60"}`}>
                  {item.icon}
                </span>
                <span className={`text-[10px] font-medium ${isActive ? "text-calm-400" : "text-muted"}`}>
                  {item.label}
                </span>
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
