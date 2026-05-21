"use client";

interface SliderProps {
  value: number;
  onChange: (val: number) => void;
  min?: number;
  max?: number;
  step?: number;
  label?: string;
}

export function Slider({ value, onChange, min = 0, max = 100, step = 1, label }: SliderProps) {
  const pct = ((value - min) / (max - min)) * 100;

  return (
    <div className="space-y-2">
      {label && (
        <label className="text-sm text-muted font-medium">{label}</label>
      )}
      <div className="relative">
        <input
          type="range"
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          min={min}
          max={max}
          step={step}
          className="
            w-full h-2 bg-border rounded-full appearance-none cursor-pointer
            accent-calm-500
            [&::-webkit-slider-thumb]:appearance-none
            [&::-webkit-slider-thumb]:w-5
            [&::-webkit-slider-thumb]:h-5
            [&::-webkit-slider-thumb]:rounded-full
            [&::-webkit-slider-thumb]:bg-calm-500
            [&::-webkit-slider-thumb]:border-2
            [&::-webkit-slider-thumb]:border-white
            [&::-webkit-slider-thumb]:shadow-lg
            [&::-webkit-slider-thumb]:transition-transform
            [&::-webkit-slider-thumb]:duration-200
            [&::-webkit-slider-thumb]:hover:scale-110
          "
        />
        <div
          className="absolute top-1/2 -translate-y-1/2 left-0 h-2 bg-calm-500/30 rounded-full pointer-events-none"
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="flex justify-between text-xs text-muted">
        <span>{min}</span>
        <span className="text-calm-400 font-semibold">{value}</span>
        <span>{max}</span>
      </div>
    </div>
  );
}
