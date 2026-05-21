"use client";

import { useState, type ReactNode } from "react";

interface Tab {
  id: string;
  label: string;
  icon?: string;
}

interface TabsProps {
  tabs: Tab[];
  children: (activeTab: string) => ReactNode;
  defaultTab?: string;
  className?: string;
}

export function Tabs({ tabs, children, defaultTab, className = "" }: TabsProps) {
  const [active, setActive] = useState(defaultTab || tabs[0]?.id);

  return (
    <div className={className}>
      <div className="flex border-b border-border mb-4 overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActive(tab.id)}
            className={`
              px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-all duration-200
              border-b-2 -mb-px
              ${active === tab.id
                ? "border-calm-500 text-calm-400"
                : "border-transparent text-muted hover:text-foreground hover:border-border"
              }
            `}
          >
            {tab.icon && <span className="mr-1.5">{tab.icon}</span>}
            {tab.label}
          </button>
        ))}
      </div>
      <div className="animate-fade-in">{children(active)}</div>
    </div>
  );
}
