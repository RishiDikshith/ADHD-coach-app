"use client";

import { Sidebar } from "@/components/shared/sidebar";
import { BottomNav } from "@/components/shared/bottom-nav";
import { PinSetupModal } from "@/components/shared/PinSetupModal";

export default function AuthenticatedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Global quick PIN setup prompt */}
      <PinSetupModal />

      {/* Desktop sidebar - hidden on mobile */}
      <div className="hidden md:block h-screen shrink-0 overflow-hidden">
        <Sidebar />
      </div>
      <main className="flex-1 overflow-y-auto bg-gradient-to-b from-background via-background-secondary to-background pb-16 md:pb-0">
        <div className="max-w-6xl mx-auto">
          {children}
        </div>
      </main>
      {/* Mobile bottom navigation */}
      <div className="md:hidden">
        <BottomNav />
      </div>
    </div>
  );
}
