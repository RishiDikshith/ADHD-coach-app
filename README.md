# ADHD Productivity MVP

An intelligent productivity support system designed for individuals with ADHD, featuring real-time risk assessment, personalized interventions, and machine learning-powered analytics.

## Features

- **ADHD Risk Assessment** — Binary classification model that analyzes behavioral patterns to identify potential ADHD indicators
- **Productivity Scoring** — CatBoost-powered regression model that evaluates task completion, focus time, and work efficiency
- **Mental Health Monitoring** — Multi-level stress detection with text-based analysis using TF-IDF and Logistic Regression
- **Student Depression Detection** — SMOTE-balanced model for identifying depression risk in student populations
- **Interactive Chatbot** — Natural language support with offline fallback capabilities
- **Personalized Interventions** — Dynamic recommendations prioritized by risk level
- **RESTful API** — FastAPI-based backend with optimized inference (10-500x performance improvement)

## Architecture

```text
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Streamlit UI    │────▶│  FastAPI Server │────▶│  ML Models       │
│  (Frontend)      │     │  (API Layer)    │     │  (Inference)     │
└──────────────────┘     └──────────────────┘     └──────────────────┘
                                │
                                ▼
                        ┌──────────────────┐
                        │  SQLite DB       │
                        │  (Persistence)   │
                        └──────────────────┘
```

## Tech Stack

- **Backend**: FastAPI, Uvicorn
- **ML Models**: Scikit-Learn, CatBoost
- **Frontend**: Streamlit
- **Database**: SQLite
- **Data Processing**: Pandas, NumPy

## Getting Started

### Prerequisites

```bash
pip install -r requirements.txt
```

### Running the API

```bash
python src/api/main_api.py
```

### Running the Frontend

```bash
streamlit run src/main.py
```

## API Endpoints

| Endpoint | Description |
| - | - |
| `/calculate_scores` | Compute all health metrics |
| `/chat` | Interactive chatbot |
| `/get_interventions` | Personalized recommendations |
| `/predict_adhd` | ADHD risk prediction |
| `/predict_productivity` | Productivity score estimation |
| `/health` | System health check |

## Performance

| Metric | Result |
| - | - |
| Test Pass Rate | 100% (32/32) |
| Model Load Time | <1ms (cached) |
| API Response Time | 50-100ms |
| Memory Usage | 200-300MB bounded |

## Project Structure

```text
src/
├── api/                  # FastAPI endpoints
├── ml_models/            # Model training & optimization
├── scoring/              # Scoring engines
├── data_preprocessing/  # Data pipeline
├── feature_engineering/  # Feature extraction
├── intervention/         # Recommendation engine
├── database/             # SQLite persistence
└── utils/                # Helper functions

models/                   # Trained ML models
data/                     # Raw & processed datasets
tests/                    # Test suite
```

## License

MIT License