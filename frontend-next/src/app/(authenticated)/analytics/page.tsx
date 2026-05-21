"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Card, CardTitle, CardValue, CardLabel } from "@/components/ui/card";
import { Tabs } from "@/components/ui/tabs";
import { useUserStore } from "@/stores/user-store";
import { useAnalyticsStore } from "@/stores/analytics-store";
import { api } from "@/lib/api-client";
import { Celebration } from "@/components/shared/celebration";
import { ChartWrapper } from "@/components/shared/chart-wrapper";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, RadarChart,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  AreaChart, Area,
} from "recharts";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.08 } },
};
const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0 },
};

const moodData = [
  { name: "Mon", happy: 3, calm: 4, anxious: 2 },
  { name: "Tue", happy: 4, calm: 3, anxious: 1 },
  { name: "Wed", happy: 2, calm: 5, anxious: 3 },
  { name: "Thu", happy: 3, calm: 4, anxious: 2 },
  { name: "Fri", happy: 5, calm: 3, anxious: 1 },
  { name: "Sat", happy: 4, calm: 4, anxious: 2 },
  { name: "Sun", happy: 3, calm: 5, anxious: 1 },
];

const focusData = [
  { name: "Mon", focus: 78, distractions: 5 },
  { name: "Tue", focus: 85, distractions: 3 },
  { name: "Wed", focus: 65, distractions: 8 },
  { name: "Thu", focus: 72, distractions: 6 },
  { name: "Fri", focus: 90, distractions: 2 },
  { name: "Sat", focus: 80, distractions: 4 },
  { name: "Sun", focus: 75, distractions: 5 },
];

const radarData = [
  { subject: "Focus", A: 85, fullMark: 100 },
  { subject: "Energy", A: 70, fullMark: 100 },
  { subject: "Mood", A: 80, fullMark: 100 },
  { subject: "Sleep", A: 65, fullMark: 100 },
  { subject: "Productivity", A: 75, fullMark: 100 },
  { subject: "Consistency", A: 90, fullMark: 100 },
];

const ProductivityCorrelations = [
  { factor: "Sleep Quality", strength: 85, direction: "positive" as const, desc: "Better sleep → higher productivity" },
  { factor: "Stress Level", strength: 72, direction: "negative" as const, desc: "Lower stress → better focus" },
  { factor: "Exercise", strength: 63, direction: "positive" as const, desc: "Movement boosts output" },
  { factor: "Phone Distractions", strength: 78, direction: "negative" as const, desc: "Fewer distractions → more done" },
];

const healthItems = [
  { key: "adhd_risk", label: "ADHD Risk", color: "#6ee7b7", format: (v: number) => `${(v * 100).toFixed(0)}%` },
  { key: "mental_health_score", label: "Mental Health", color: "#667eea", format: (v: number) => `${v.toFixed(0)}%` },
  { key: "productivity_score", label: "Productivity", color: "#fbbf24", format: (v: number) => `${v.toFixed(0)}%` },
  { key: "depression_score", label: "Depression Risk", color: "#f87171", format: (v: number) => `${v.toFixed(0)}%` },
];

export default function AnalyticsPage() {
  const { username, game } = useUserStore();
  const { scores, insights, moodHistory, setInsights, setScores } = useAnalyticsStore();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!username) return;
    Promise.all([
      api.getScores(username, {}).then(setScores).catch(() => {}),
      api.getAnalytics(username).then((data) => setInsights(data.insights || [])).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, [username, setInsights, setScores]);

  const moodCounts: Record<string, number> = {};
  moodHistory.forEach((m) => { moodCounts[m.emoji] = (moodCounts[m.emoji] || 0) + 1; });
  const topMood = Object.entries(moodCounts).sort((a, b) => b[1] - a[1])[0]?.[0];
  const moodLabels: Record<string, string> = { "😊": "Happy", "😌": "Calm", "😐": "Okay", "😟": "Worried", "😰": "Anxious", "😤": "Frustrated" };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="max-w-5xl mx-auto p-6 space-y-6"
    >
      {/* Header */}
      <motion.div variants={itemVariants}>
        <h1 className="text-3xl font-bold text-foreground">📈 Analytics</h1>
        <p className="text-muted mt-1">Behavioral intelligence — patterns, insights, and recommendations</p>
      </motion.div>

      <Tabs
        tabs={[
          { id: "overview", label: "Overview", icon: "📊" },
          { id: "charts", label: "Charts", icon: "📈" },
          { id: "insights", label: "Insights", icon: "💡" },
          { id: "correlations", label: "Correlations", icon: "🔗" },
        ]}
      >
        {(activeTab) => (
          <>
            {activeTab === "overview" && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="space-y-6"
              >
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {healthItems.map((item) => {
                    const val = scores[item.key as keyof typeof scores];
                    return (
                      <Card key={item.key} variant="stat" className="text-center">
                        <CardLabel>{item.label}</CardLabel>
                        <CardValue className="mt-1 block" style={{ color: item.color }}>
                          {val != null ? item.format(val as number) : "--"}
                        </CardValue>
                      </Card>
                    );
                  })}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Card>
                    <CardTitle>⚡ Activity Summary</CardTitle>
                    <div className="mt-3 grid grid-cols-3 gap-4 text-center">
                      <div><CardValue className="text-xl">{game.session_count}</CardValue><CardLabel>Sessions</CardLabel></div>
                      <div><CardValue className="text-xl">{game.streak}</CardValue><CardLabel>Streak</CardLabel></div>
                      <div><CardValue className="text-xl">{game.level}</CardValue><CardLabel>Level</CardLabel></div>
                    </div>
                  </Card>

                  <Card>
                    <CardTitle>🏆 Points Progress</CardTitle>
                    <div className="mt-3">
                      <div className="flex justify-between text-sm text-muted mb-1">
                        <span>{game.points} pts</span>
                        <span>Level {game.level}</span>
                      </div>
                      <div className="h-3 bg-border rounded-full overflow-hidden">
                        <motion.div
                          className="h-full bg-gradient-to-r from-calm-500 to-focus-500 rounded-full"
                          initial={{ width: 0 }}
                          animate={{ width: `${Math.min(100, (game.points / (game.level * 100)) * 100)}%` }}
                          transition={{ duration: 1, ease: "easeOut" }}
                        />
                      </div>
                    </div>
                  </Card>
                </div>

                {/* Wellness Radar */}
                <Card>
                  <CardTitle>🎯 Wellness Radar</CardTitle>
                  <div className="mt-3">
                    <ChartWrapper height="h-72">
                      <ResponsiveContainer width="100%" height="100%">
                        <RadarChart data={radarData}>
                          <PolarGrid stroke="#1e293b" />
                          <PolarAngleAxis dataKey="subject" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                          <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: "#64748b", fontSize: 10 }} />
                          <Radar name="Score" dataKey="A" stroke="#6ee7b7" fill="#6ee7b7" fillOpacity={0.2} />
                        </RadarChart>
                      </ResponsiveContainer>
                    </ChartWrapper>
                  </div>
                </Card>

                {game.badges.length > 0 && (
                  <Card>
                    <CardTitle>🏅 Badges Earned</CardTitle>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {game.badges.map((badge) => (
                        <span key={badge} className="px-3 py-1.5 rounded-full text-sm font-medium bg-gradient-to-r from-purple-500/20 to-pink-500/20 text-purple-300 border border-purple-500/30">
                          {badge}
                        </span>
                      ))}
                    </div>
                  </Card>
                )}
              </motion.div>
            )}

            {activeTab === "charts" && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="space-y-4"
              >
                {/* Focus Trend */}
                <Card>
                  <CardTitle>🎯 Focus Trend</CardTitle>
                  <div className="mt-3">
                    <ChartWrapper height="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={focusData}>
                          <defs>
                            <linearGradient id="colorFocus" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#6ee7b7" stopOpacity={0.3} />
                              <stop offset="95%" stopColor="#6ee7b7" stopOpacity={0} />
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                          <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                          <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
                          <Tooltip
                            contentStyle={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 8 }}
                            labelStyle={{ color: "#fff" }}
                          />
                          <Area type="monotone" dataKey="focus" stroke="#6ee7b7" fill="url(#colorFocus)" strokeWidth={2} />
                          <Area type="monotone" dataKey="distractions" stroke="#f87171" fill="none" strokeWidth={2} strokeDasharray="4 4" />
                        </AreaChart>
                      </ResponsiveContainer>
                    </ChartWrapper>
                  </div>
                </Card>

                {/* Mood Distribution */}
                <Card>
                  <CardTitle>😊 Mood Distribution</CardTitle>
                  <div className="mt-3">
                    <ChartWrapper height="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={moodData}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                          <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                          <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
                          <Tooltip
                            contentStyle={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 8 }}
                            labelStyle={{ color: "#fff" }}
                          />
                          <Bar dataKey="happy" stackId="a" fill="#6ee7b7" radius={[4, 4, 0, 0]} />
                          <Bar dataKey="calm" stackId="a" fill="#667eea" radius={[4, 4, 0, 0]} />
                          <Bar dataKey="anxious" stackId="a" fill="#f87171" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </ChartWrapper>
                  </div>
                </Card>

                {/* Productivity Trend */}
                <Card>
                  <CardTitle>📈 Productivity Trend</CardTitle>
                  <div className="mt-3">
                    <ChartWrapper height="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={focusData}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                          <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                          <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} domain={[0, 100]} />
                          <Tooltip
                            contentStyle={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 8 }}
                            labelStyle={{ color: "#fff" }}
                          />
                          <Line type="monotone" dataKey="focus" stroke="#fbbf24" strokeWidth={2} dot={{ fill: "#fbbf24" }} />
                        </LineChart>
                      </ResponsiveContainer>
                    </ChartWrapper>
                  </div>
                </Card>
              </motion.div>
            )}

            {activeTab === "insights" && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="space-y-3"
              >
                {topMood && (
                  <Card variant="glass" className="text-center">
                    <p className="text-4xl mb-2">{topMood}</p>
                    <CardLabel>Most Frequent Mood</CardLabel>
                    <p className="text-sm text-muted mt-1">{moodLabels[topMood] || topMood}</p>
                  </Card>
                )}

                {insights.length === 0 ? (
                  <Card>
                    <p className="text-sm text-muted">Chat with your ADHD Coach to generate personalized insights about your patterns.</p>
                  </Card>
                ) : (
                  insights.map((insight, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                    >
                      <Card
                        className={`border-l-4 ${
                          insight.priority === "high"
                            ? "border-l-danger-500"
                            : insight.priority === "medium"
                            ? "border-l-warm-500"
                            : "border-l-calm-500"
                        }`}
                      >
                        <div className="flex items-start gap-2">
                          <span className="text-lg mt-0.5">
                            {insight.trend === "up" ? "📈" : insight.trend === "down" ? "📉" : "➡️"}
                          </span>
                          <div>
                            <p className="text-sm font-medium text-foreground">{insight.title}</p>
                            <p className="text-xs text-muted mt-0.5">{insight.description}</p>
                            {insight.value != null && (
                              <p className="text-xs text-calm-400 mt-1 font-medium">Score: {insight.value.toFixed(1)}</p>
                            )}
                          </div>
                        </div>
                      </Card>
                    </motion.div>
                  ))
                )}

                {/* Mood timeline */}
                {moodHistory.length > 0 && (
                  <Card>
                    <CardTitle>📊 Mood Timeline</CardTitle>
                    <div className="mt-3 space-y-1.5 max-h-48 overflow-y-auto">
                      {[...moodHistory].reverse().slice(0, 30).map((entry, i) => (
                        <div key={i} className="flex items-center gap-3 text-sm py-1">
                          <span className="text-lg">{entry.emoji}</span>
                          <span className="text-xs text-muted">
                            {new Date(entry.timestamp).toLocaleDateString([], {
                              weekday: "short", hour: "2-digit", minute: "2-digit",
                            })}
                          </span>
                        </div>
                      ))}
                    </div>
                  </Card>
                )}
              </motion.div>
            )}

            {activeTab === "correlations" && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="space-y-4"
              >
                <Card variant="glass">
                  <CardTitle>🔗 Productivity Correlations</CardTitle>
                  <p className="text-sm text-muted mt-2">
                    Understanding what affects your productivity helps you make better decisions.
                  </p>
                </Card>

                <div className="grid gap-3">
                  {ProductivityCorrelations.map((corr, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.1 }}
                    >
                      <Card>
                        <div className="flex items-center justify-between mb-2">
                          <p className="text-sm font-medium text-foreground">{corr.factor}</p>
                          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                            corr.direction === "positive"
                              ? "bg-calm-500/10 text-calm-400"
                              : "bg-danger-500/10 text-danger-400"
                          }`}>
                            {corr.direction === "positive" ? "↑ Positive" : "↓ Negative"}
                          </span>
                        </div>
                        <div className="h-2 bg-border rounded-full overflow-hidden">
                          <motion.div
                            className={`h-full rounded-full ${
                              corr.direction === "positive" ? "bg-calm-500" : "bg-danger-500"
                            }`}
                            initial={{ width: 0 }}
                            animate={{ width: `${corr.strength}%` }}
                            transition={{ duration: 1, delay: i * 0.15 }}
                          />
                        </div>
                        <p className="text-xs text-muted mt-2">{corr.desc} ({corr.strength}%)</p>
                      </Card>
                    </motion.div>
                  ))}
                </div>

                <Card variant="glass">
                  <CardTitle>💤 Pro Tip</CardTitle>
                  <p className="text-xs text-muted mt-2">
                    Sleep quality is your strongest productivity predictor. Focus on improving sleep
                    consistency for the biggest impact on your focus and mood.
                  </p>
                </Card>
              </motion.div>
            )}
          </>
        )}
      </Tabs>
    </motion.div>
  );
}
