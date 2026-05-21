"use client";

import { motion } from "framer-motion";

interface SwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  disabled?: boolean;
}

export function Switch({ checked, onChange, label, disabled }: SwitchProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full transition-colors duration-200 ${
        disabled ? "opacity-50 cursor-not-allowed" : ""
      } ${checked ? "bg-calm-500" : "bg-border"}`}
    >
      <motion.span
        className="pointer-events-none absolute top-0.5 left-0.5 inline-block h-5 w-5 rounded-full bg-white shadow"
        animate={{ x: checked ? 22 : 0 }}
        transition={{ type: "spring", stiffness: 500, damping: 30 }}
      />
    </button>
  );
}

interface SwitchGroupProps {
  items: {
    id: string;
    label: string;
    description?: string;
    checked: boolean;
    onChange: (checked: boolean) => void;
  }[];
}

export function SwitchGroup({ items }: SwitchGroupProps) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.id} className="flex items-center justify-between">
          <div className="flex-1">
            <p className="text-sm text-foreground">{item.label}</p>
            {item.description && (
              <p className="text-xs text-muted">{item.description}</p>
            )}
          </div>
          <Switch checked={item.checked} onChange={item.onChange} />
        </div>
      ))}
    </div>
  );
}
