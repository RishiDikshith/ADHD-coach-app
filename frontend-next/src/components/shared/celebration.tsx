"use client";

import { useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface CelebrationProps {
  type: "confetti" | "balloons" | "sparkle" | "levelUp" | "momentum" | "streak";
  show: boolean;
  onComplete?: () => void;
  message?: string;
}

const COLORS = ["#6ee7b7", "#667eea", "#fbbf24", "#f87171", "#c084fc", "#f472b6", "#34d399", "#fb923c", "#818cf8"];
const MOMENTUM_COLORS = ["#6ee7b7", "#34d399", "#059669"];
const STREAK_COLORS = ["#fbbf24", "#fb923c", "#f59e0b"];

interface Particle {
  x: number; y: number; vx: number; vy: number;
  size: number; color: string;
  rotation: number; rotationSpeed: number;
  alpha: number; shape: "circle" | "square" | "star" | "diamond";
  update: () => void;
  draw: (ctx: CanvasRenderingContext2D) => void;
}

function createParticle(canvas: HTMLCanvasElement, type: string, index: number, total: number): Particle {
  const cx = canvas.width / 2;
  const cy = canvas.height / 2;
  const angle = Math.random() * Math.PI * 2;
  const speed = type === "levelUp" ? 8 + Math.random() * 14
    : type === "momentum" ? 3 + Math.random() * 5
    : type === "streak" ? 5 + Math.random() * 8
    : 4 + Math.random() * 8;

  // For momentum, particles rise upward
  const vx = type === "momentum"
    ? (Math.random() - 0.5) * 3
    : Math.cos(angle) * speed;
  const vy = type === "momentum"
    ? -Math.random() * 4 - 1
    : Math.sin(angle) * speed - (type === "balloons" ? 3 : 0);

  const particleColors = type === "momentum" ? MOMENTUM_COLORS
    : type === "streak" ? STREAK_COLORS
    : COLORS;

  // Spiral position for momentum (start from center bottom)
  const spiralAngle = (index / total) * Math.PI * 4;
  const spiralRadius = type === "momentum" ? 20 + index * 3 : 0;

  return {
    x: type === "sparkle" ? Math.random() * canvas.width
      : type === "momentum" ? cx + Math.cos(spiralAngle) * spiralRadius
      : cx + (Math.random() - 0.5) * 120,
    y: type === "sparkle" ? Math.random() * canvas.height
      : type === "momentum" ? cy + 100
      : cy + (Math.random() - 0.5) * 120,
    vx, vy,
    size: type === "sparkle" ? 2 + Math.random() * 3
      : type === "momentum" ? 4 + Math.random() * 6
      : 5 + Math.random() * 8,
    color: particleColors[Math.floor(Math.random() * particleColors.length)],
    rotation: Math.random() * 360,
    rotationSpeed: (Math.random() - 0.5) * 10,
    alpha: 1,
    shape: type === "sparkle" ? "star"
      : type === "momentum" ? "circle"
      : Math.random() > 0.5 ? "circle" : "square",

    update() {
      this.x += this.vx;
      this.y += this.vy;
      this.vy += type === "momentum" ? 0.05 : 0.15;
      this.vx *= 0.99;
      this.rotation += this.rotationSpeed;
      this.alpha -= type === "momentum" ? 0.003 : 0.005;
    },

    draw(ctx: CanvasRenderingContext2D) {
      ctx.save();
      ctx.translate(this.x, this.y);
      ctx.rotate((this.rotation * Math.PI) / 180);
      ctx.globalAlpha = Math.max(0, this.alpha);
      ctx.fillStyle = this.color;

      if (this.shape === "circle") {
        ctx.beginPath();
        ctx.arc(0, 0, this.size / 2, 0, Math.PI * 2);
        ctx.fill();
      } else if (this.shape === "star") {
        // Draw a small star
        const spikes = 4;
        const outerR = this.size / 2;
        const innerR = this.size / 4;
        ctx.beginPath();
        for (let i = 0; i < spikes * 2; i++) {
          const r = i % 2 === 0 ? outerR : innerR;
          const a = (i * Math.PI) / spikes - Math.PI / 2;
          if (i === 0) ctx.moveTo(r * Math.cos(a), r * Math.sin(a));
          else ctx.lineTo(r * Math.cos(a), r * Math.sin(a));
        }
        ctx.closePath();
        ctx.fill();
      } else if (this.shape === "diamond") {
        ctx.beginPath();
        ctx.moveTo(0, -this.size / 2);
        ctx.lineTo(this.size / 2, 0);
        ctx.lineTo(0, this.size / 2);
        ctx.lineTo(-this.size / 2, 0);
        ctx.closePath();
        ctx.fill();
      } else {
        ctx.fillRect(-this.size / 2, -this.size / 2, this.size, this.size);
      }
      ctx.restore();
    },
  };
}

export function Celebration({ type, show, onComplete, message }: CelebrationProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Particle[]>([]);
  const animFrameRef = useRef<number>(0);

  useEffect(() => {
    if (!show) {
      particlesRef.current = [];
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      return;
    }

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const count = type === "levelUp" ? 150
      : type === "momentum" ? 60
      : type === "streak" ? 100
      : type === "confetti" ? 80
      : 40;

    particlesRef.current = Array.from({ length: count }, (_, i) => createParticle(canvas, type, i, count));

    const startTime = Date.now();
    const duration = type === "sparkle" ? 1500
      : type === "momentum" ? 4000
      : type === "streak" ? 3500
      : 3000;

    const animate = () => {
      if (Date.now() - startTime > duration) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particlesRef.current = [];
        onComplete?.();
        return;
      }
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const particles = particlesRef.current;
      for (let i = 0; i < particles.length; i++) {
        particles[i].update();
        particles[i].draw(ctx);
      }
      animFrameRef.current = requestAnimationFrame(animate);
    };

    animFrameRef.current = requestAnimationFrame(animate);

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [show, type, onComplete]);

  return (
    <AnimatePresence>
      {show && (
        <>
          <canvas
            ref={canvasRef}
            className="fixed inset-0 pointer-events-none z-[9999]"
            aria-hidden="true"
          />
          {message && (
            <motion.div
              initial={{ opacity: 0, scale: 0.5, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.5, y: -20 }}
              transition={{ type: "spring", stiffness: 300, damping: 15 }}
              className="fixed top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 z-[10000] pointer-events-none text-center"
            >
              <motion.p
                className="text-lg font-bold gradient-text"
                animate={{ scale: [1, 1.05, 1] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              >
                {message}
              </motion.p>
            </motion.div>
          )}
        </>
      )}
    </AnimatePresence>
  );
}

// Momentum Ring — elegant circular progress indicator for streaks/momentum
export function MomentumRing({
  progress,
  size = 80,
  strokeWidth = 4,
  color = "#6ee7b7",
  label,
}: {
  progress: number; // 0-100
  size?: number;
  strokeWidth?: number;
  color?: string;
  label?: string;
}) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (progress / 100) * circumference;

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="rgba(255,255,255,0.08)"
          strokeWidth={strokeWidth}
          fill="none"
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.5, ease: "easeOut" }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-lg font-bold gradient-text">{Math.round(progress)}%</span>
      </div>
      {label && (
        <span className="absolute -bottom-5 text-[10px] text-muted whitespace-nowrap">{label}</span>
      )}
    </div>
  );
}

// Streak Flame — animated flame icon for streak milestones
export function StreakFlame({ streak }: { streak: number }) {
  const flameEmoji = streak >= 30 ? "🔥🔥🔥"
    : streak >= 14 ? "🔥🔥"
    : streak >= 7 ? "🔥"
    : streak >= 3 ? "⭐"
    : "🌱";

  return (
    <motion.div
      className="inline-flex items-center gap-1"
      animate={{ scale: [1, 1.05, 1] }}
      transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
    >
      <span className="text-2xl">{flameEmoji}</span>
      <span className="text-sm font-bold gradient-text-warm">{streak}</span>
    </motion.div>
  );
}

// Level-Up Badge — animated badge for milestone achievements
export function LevelUpBadge({
  level,
  visible,
}: {
  level: number;
  visible: boolean;
}) {
  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ scale: 0, rotate: -180 }}
          animate={{ scale: 1, rotate: 0 }}
          exit={{ scale: 0, rotate: 180 }}
          transition={{ type: "spring", stiffness: 200, damping: 12 }}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gradient-to-r from-warm-500/20 to-calm-500/20 border border-warm-500/30"
        >
          <span className="text-sm">🏆</span>
          <span className="text-xs font-bold gradient-text-warm">Lvl {level}</span>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
