"""
Analytics Intelligence
======================
Advanced analytics engine for generating behavioral insights,
productivity patterns, and actionable recommendations.

Features:
- Behavioral insight generation
- Focus pattern analysis
- Sleep/productivity correlation
- Distraction analysis
- Burnout trend detection
- Actionable recommendation generation
"""

from .insight_engine import InsightEngine
from .pattern_analyzer import PatternAnalyzer
from .recommendation_engine import RecommendationEngine

__all__ = [
    "InsightEngine",
    "PatternAnalyzer",
    "RecommendationEngine",
]
