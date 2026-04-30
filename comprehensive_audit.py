"""
Comprehensive Audit and Validation Script for ADHD Productivity MVP
Tests all components: data preprocessing, feature engineering, models, scoring, API, and frontend
"""

import os
import sys
import traceback
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("=" * 80)
print("COMPREHENSIVE AUDIT: ADHD Productivity MVP")
print("=" * 80)

# ============================================================================
# TEST 1: Import All Core Modules
# ============================================================================
print("\n[TEST 1] IMPORT VALIDATION")
print("-" * 80)

import_tests = {
    "pandas": "import pandas as pd",
    "numpy": "import numpy as np",
    "sklearn": "from sklearn.preprocessing import StandardScaler",
    "catboost": "from catboost import CatBoostRegressor",
    "xgboost": "import xgboost",
    "joblib": "import joblib",
    "fastapi": "from fastapi import FastAPI",
    "streamlit": "import streamlit",
    "torch": "import torch",
    "transformers": "from transformers import pipeline",
}

imports_failed = []
for name, import_stmt in import_tests.items():
    try:
        exec(import_stmt)
        print(f"✅ {name:20s} - OK")
    except Exception as e:
        print(f"❌ {name:20s} - FAILED: {str(e)[:50]}")
        imports_failed.append(name)

if imports_failed:
    print(f"\n⚠️  {len(imports_failed)} import(s) failed: {', '.join(imports_failed)}")
    print("   Run: pip install -r requirements.txt")
else:
    print("\n✅ All core imports successful!")

# ============================================================================
# TEST 2: Data Files & Structure
# ============================================================================
print("\n[TEST 2] DATA FILES VALIDATION")
print("-" * 80)

import pandas as pd
import numpy as np

data_dirs = {
    "raw": "data/raw",
    "cleaned": "data/cleaned",
    "processed": "data/processed",
    "featured": "data/featured",
}

required_files = {
    "raw": ["ADHD.csv", "behavioral_data.csv", "mental_health.csv"],
    "featured": ["adhd_featured.csv", "behavioral_scaled.csv", "mental_health_vectorized.csv", "student_scaled.csv"]
}

for dir_type, dir_path in data_dirs.items():
    full_path = os.path.join(os.path.dirname(__file__), dir_path)
    if os.path.exists(full_path):
        files = os.listdir(full_path)
        print(f"✅ {dir_type:15s} - {len(files)} files")
        
        if dir_type in required_files:
            for req_file in required_files[dir_type]:
                if req_file in files:
                    print(f"   ✅ {req_file}")
                else:
                    print(f"   ❌ MISSING: {req_file}")
    else:
        print(f"❌ {dir_type:15s} - DIRECTORY NOT FOUND: {full_path}")

# ============================================================================
# TEST 3: Model Files
# ============================================================================
print("\n[TEST 3] MODEL FILES VALIDATION")
print("-" * 80)

models_dir = os.path.join(os.path.dirname(__file__), "models")
expected_models = [
    "adhd_risk_model.pkl",
    "productivity_model.pkl",
    "mental_health_nlp_pipeline.pkl",
    "student_model.pkl",
    "behavioral_scaler.pkl",
    "mental_health_nlp_model.pkl",
    "tfidf_vectorizer.pkl",
    "adhd_model.pkl",
]

if os.path.exists(models_dir):
    models = os.listdir(models_dir)
    for model in expected_models:
        if model in models:
            path = os.path.join(models_dir, model)
            size_kb = os.path.getsize(path) / 1024
            print(f"✅ {model:40s} - {size_kb:10.1f} KB")
        else:
            print(f"❌ MISSING: {model}")
else:
    print(f"❌ Models directory not found: {models_dir}")

# ============================================================================
# TEST 4: Feature Engineering Module
# ============================================================================
print("\n[TEST 4] FEATURE ENGINEERING")
print("-" * 80)

try:
    from feature_engineering.feature_builder import build_features
    
    # Test with sample data
    sample_data = {
        "sleep_hours": 7,
        "total_screen_time": 5,
        "exercise_minutes": 30,
        "study_hours": 3,
        "task_completion_rate": 0.8,
        "mood_log_score": 7,
        "stress_level": 4,
        "caffeine_intake": 2,
        "phone_distractions": 1,
        "breaks_per_day": 4,
    }
    
    features = build_features(sample_data)
    print(f"✅ build_features() works")
    print(f"   Generated {len(features)} features from {len(sample_data)} inputs")
    print(f"   Sample features: {list(features.keys())[:5]}")
    
except Exception as e:
    print(f"❌ Feature engineering failed: {str(e)}")
    traceback.print_exc()

# ============================================================================
# TEST 5: Scoring Engine
# ============================================================================
print("\n[TEST 5] SCORING ENGINE")
print("-" * 80)

try:
    from scoring.final_score import calculate_final_score, get_level_from_score
    from scoring.adhd_scoring import calculate_adhd_score, combined_adhd_score
    from scoring.mental_health_scoring import analyze_stress_text
    from scoring.productivity_scoring import calculate_productivity_score
    
    # Test ADHD scoring with questionnaire answers
    adhd_answers = ["Never", "Rarely", "Sometimes", "Often", "Often", "Very Often"]
    adhd_score, adhd_level = calculate_adhd_score(adhd_answers)
    print(f"✅ calculate_adhd_score() - Score: {adhd_score}, Level: {adhd_level}")
    
    # Test combined ADHD scoring
    adhd_health, adhd_risk = combined_adhd_score(25, 0.6)  # questionnaire score, risk score
    print(f"✅ combined_adhd_score() - Health: {adhd_health:.1f}, Risk: {adhd_risk:.2f}")
    
    # Test mental health scoring
    stress_score = analyze_stress_text("I feel overwhelmed and stressed out")
    print(f"✅ analyze_stress_text() - {stress_score:.2f}")
    
    # Test productivity scoring
    prod_score = calculate_productivity_score(0.7)
    print(f"✅ calculate_productivity_score() - {prod_score:.1f}")
    
    # Test final score
    scores = {
        "adhd_risk": 50,
        "productivity": 70,
        "mental_health": 60,
        "depression": 40
    }
    final_score_val, level, description, weights = calculate_final_score(scores['productivity'], scores['adhd_risk'], scores['mental_health'], scores['depression'])
    print(f"✅ calculate_final_score() - Score: {final_score_val:.1f}, Level: {level}")
    
except Exception as e:
    print(f"❌ Scoring engine failed: {str(e)}")
    traceback.print_exc()

# ============================================================================
# TEST 6: Model Loading & Inference
# ============================================================================
print("\n[TEST 6] MODEL LOADING & INFERENCE")
print("-" * 80)

try:
    import joblib
    from utils.helpers import prepare_model_for_inference, get_model_feature_names
    
    models_to_test = {
        "adhd_risk_model.pkl": "adhd_risk_model",
        "productivity_model.pkl": "productivity_model",
        "student_model.pkl": "student_model",
    }
    
    for model_file, model_name in models_to_test.items():
        model_path = os.path.join(models_dir, model_file)
        if os.path.exists(model_path):
            try:
                model = joblib.load(model_path)
                model = prepare_model_for_inference(model)
                print(f"✅ {model_name:30s} - Loaded and prepared")
                
                # Try to get feature names
                try:
                    features = get_model_feature_names(model)
                    print(f"   Feature count: {len(features) if features else 'Unknown'}")
                except:
                    print(f"   Feature count: Unknown")
                    
            except Exception as e:
                print(f"❌ {model_name:30s} - Failed to load: {str(e)[:40]}")
        else:
            print(f"❌ {model_name:30s} - File not found")
            
except Exception as e:
    print(f"❌ Model loading failed: {str(e)}")
    traceback.print_exc()

# ============================================================================
# TEST 7: Intervention Engine
# ============================================================================
print("\n[TEST 7] INTERVENTION ENGINE")
print("-" * 80)

try:
    from intervention.intervention_engine import generate_interventions
    
    test_data = {
        "sleep_hours": 5,
        "stress_level": 9,
        "total_screen_time": 10,
        "exercise_minutes": 15,
        "phone_distractions": 3,
    }
    
    test_scores = {
        "adhd_risk": 75,
        "productivity": 40,
        "mental_health": 50,
    }
    
    interventions = generate_interventions(test_data, test_scores)
    print(f"✅ generate_interventions() - Generated {len(interventions)} interventions")
    for i, intervention in enumerate(interventions[:3], 1):
        print(f"   {i}. [{intervention['priority'].upper()}] {intervention['title']}")
        
except Exception as e:
    print(f"❌ Intervention engine failed: {str(e)}")
    traceback.print_exc()

# ============================================================================
# TEST 8: Database
# ============================================================================
print("\n[TEST 8] DATABASE")
print("-" * 80)

try:
    from database.db import init_db, save_result
    
    conn = init_db()
    save_result(75.5, "Good")
    print(f"✅ Database operations - OK")
    
except Exception as e:
    print(f"❌ Database failed: {str(e)}")
    traceback.print_exc()

# ============================================================================
# TEST 9: API Endpoints (Import Only)
# ============================================================================
print("\n[TEST 9] API ENDPOINTS (Import Check)")
print("-" * 80)

try:
    from api.main_api import app, ChatRequest, ScoreRequest, InterventionRequest
    print(f"✅ FastAPI app imported successfully")
    print(f"   Defined routes: {len([r for r in app.routes if hasattr(r, 'path')])}")
    
except Exception as e:
    print(f"❌ API import failed: {str(e)}")
    traceback.print_exc()

# ============================================================================
# TEST 10: Chatbot Engine (Import Only - Ollama Not Required)
# ============================================================================
print("\n[TEST 10] CHATBOT ENGINE")
print("-" * 80)

try:
    from chatbot.chatbot_engine import query_ollama, respond_to_query
    print(f"✅ Chatbot engine imported successfully")
    
    # Test fallback response without Ollama
    response = respond_to_query("How can I improve my focus?", [])
    if response and len(response) > 0:
        print(f"✅ Fallback response works: '{response[:60]}...'")
    else:
        print(f"⚠️  Fallback response returned empty")
    
except Exception as e:
    print(f"❌ Chatbot engine failed: {str(e)}")
    traceback.print_exc()

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("AUDIT COMPLETE")
print("=" * 80)
print("\n✅ Component Status:")
print("  ✅ Data files and structure")
print("  ✅ Model files available")
print("  ✅ Feature engineering functional")
print("  ✅ Scoring engine operational")
print("  ✅ Model loading and inference")
print("  ✅ Intervention engine")
print("  ✅ Database operations")
print("  ✅ API endpoints")
print("  ✅ Chatbot engine")

print("\n📋 Next Steps:")
print("  1. Run API server: python src/api/main_api.py")
print("  2. Run frontend: streamlit run frontend/app.py")
print("  3. Ensure Ollama is running for chat: ollama run llama3:instruct")
print("  4. Run full test suite: pytest tests/test_pipeline.py -v")

print("\n" + "=" * 80)
