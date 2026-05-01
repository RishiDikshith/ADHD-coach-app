# ML Model Optimization - Quick Start Guide

This guide shows how to use the optimized ML inference system.

## Installation

Models are already optimized. No additional installation needed beyond the base requirements:

```bash
pip install -r requirements.txt
```

## Basic Usage

### 1. Using EfficientInference Class

The easiest way to use optimized models:

```python
from src.ml_models.efficient_inference import EfficientInference
import pandas as pd

# Create inference wrapper
adhd_inference = EfficientInference(
    "models/adhd_risk_model.pkl",
    "ADHD Risk Model"
)

# Prepare your features
features_df = pd.DataFrame({
    'feature1': [value1],
    'feature2': [value2],
    # ... more features
})

# Make prediction (cached if model seen before)
predictions = adhd_inference.predict(features_df)
print(f"ADHD Risk: {predictions[0]}")

# Get probabilities if available
probs = adhd_inference.predict_proba(features_df)
```

### 2. Using Model Cache

For explicit control over model loading:

```python
from src.ml_models.efficient_inference import load_model_cached

# Load model (cached after first load)
model = load_model_cached("models/adhd_risk_model.pkl")

# Make predictions
features = prepare_features(data)
prediction = model.predict(features)
```

### 3. Batch Prediction

Process multiple samples efficiently:

```python
from src.ml_models.efficient_inference import BatchPredictor

# Create batch predictor
batch_pred = BatchPredictor(model, batch_size=32)

# Predict on large dataset
predictions = batch_pred.predict_batch(large_df)
```

### 4. Prediction Caching

Cache predictions for repeated queries:

```python
from src.ml_models.efficient_inference import cached_predict, store_prediction

features_dict = {"sleep": 7, "stress": 5}

# Check cache first
result = cached_predict(model, features_dict)

if result is None:
    # Not cached, compute
    result = model.predict([features_dict])[0]
    # Store for future use
    store_prediction(features_dict, result)
```

## API Integration

The FastAPI is already integrated with optimizations. To use:

```bash
# The API is now imported directly into Streamlit to save memory on cloud platforms.
# Start the Streamlit app:
streamlit run frontend/app.py
```

### Example API Requests

```bash
# Calculate scores
curl -X POST http://localhost:8000/calculate_scores \
  -H "Content-Type: application/json" \
  -d '{
    "user_data": {
      "sleep_hours": 7,
      "stress_level": 5,
      "exercise_minutes": 30
    },
    "adhd_answers": ["Never", "Rarely", "Sometimes"],
    "text": "I feel stressed"
  }'

# Chat with ADHD coach
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "text": "How can I focus better?",
    "history": []
  }'
```

## Performance Monitoring

### Check Cache Hit Rate

```python
from src.ml_models.efficient_inference import _prediction_cache, _model_cache_instance

print(f"Predictions cached: {len(_prediction_cache)}")
print(f"Models in cache: {_model_cache_instance.cache.keys()}")
```

### Profile Inference Speed

```python
from src.ml_models.efficient_inference import InferenceProfiler
import pandas as pd

profiler = InferenceProfiler()
stats = profiler.profile_inference(
    "ADHD Model",
    model,
    test_data,
    n_runs=100
)

print(profiler.get_report())
```

### Monitor with Logs

```bash
# Watch for cache hits
tail -f logs/app.log | grep -i cache

# Watch for model loads
tail -f logs/app.log | grep -i "loaded"
```

## Advanced Features

### Multi-Model Orchestration

```python
from src.ml_models.efficient_inference import BatchInferenceOrchestrator

# Create orchestrator
orchestrator = BatchInferenceOrchestrator()

# Register models
orchestrator.register_model("adhd", "models/adhd_risk_model.pkl")
orchestrator.register_model("productivity", "models/productivity_model.pkl")

# Get predictions from all models
results = orchestrator.predict_all(data_df)
# Returns: {
#     "adhd": [predictions...],
#     "productivity": [predictions...]
# }
```

### Get Model Statistics

```python
from src.ml_models.efficient_inference import get_model_stats

stats = get_model_stats("models/adhd_risk_model.pkl")

print(f"Model size: {stats['size_mb']:.2f} MB")
print(f"Features: {stats['n_features']}")
print(f"Type: {stats['model_type']}")
print(f"Has predict_proba: {stats['has_predict_proba']}")
```

### Manual Cache Management

```python
from src.ml_models.efficient_inference import (
    unload_model_cache,
    clear_prediction_cache
)

# Free up memory if needed
unload_model_cache()

# Clear prediction cache
clear_prediction_cache()
```

## Common Use Cases

### Use Case 1: Batch Processing

```python
import pandas as pd
from src.ml_models.efficient_inference import EfficientInference

# Load data
data = pd.read_csv("user_responses.csv")

# Create inference
inference = EfficientInference("models/adhd_risk_model.pkl", "ADHD")

# Batch predict
predictions = inference.predict(data, use_batch=True)

# Save results
data['adhd_risk'] = predictions
data.to_csv("results.csv", index=False)
```

### Use Case 2: Real-Time API

```python
from fastapi import FastAPI
from src.ml_models.efficient_inference import EfficientInference

app = FastAPI()

# Models loaded once at startup
adhd_model = EfficientInference("models/adhd_risk_model.pkl", "ADHD")

@app.post("/predict")
def predict(features: dict):
    import pandas as pd
    df = pd.DataFrame([features])
    
    # Fast prediction (cached models)
    result = adhd_model.predict(df)[0]
    return {"risk": result}
```

### Use Case 3: Batch Processing with Caching

```python
from src.ml_models.efficient_inference import (
    cached_predict,
    store_prediction,
    load_model_cached
)

model = load_model_cached("models/adhd_risk_model.pkl")

for user_features in users:
    # Check cache first
    cached_result = cached_predict(model, user_features)
    
    if cached_result is not None:
        result = cached_result
    else:
        # Compute and cache
        result = model.predict([user_features])[0]
        store_prediction(user_features, result)
```

## Troubleshooting

### Issue: Slow Predictions

**Solution**: Ensure models are cached

```python
from src.ml_models.efficient_inference import load_model_cached

# Verify model is loaded and cached
model = load_model_cached("model_path.pkl")
model2 = load_model_cached("model_path.pkl")  # Should be instant
```

### Issue: High Memory Usage

**Solution**: Clear caches if needed

```python
from src.ml_models.efficient_inference import unload_model_cache

# Free memory
unload_model_cache()

# Reload models (fresh cache)
model = load_model_cached("model_path.pkl")
```

### Issue: Thread Conflicts

**Solution**: Ensure single-threaded inference

```python
# Check model settings
print(model.n_jobs)  # Should be 1 or None
print(model.thread_count)  # Should be 1 or None
```

## Performance Expectations

### Typical Performance

- **Model Load** (first): 50-100ms
- **Model Load** (cached): <1ms
- **Single Prediction**: 10-15ms
- **Batch Prediction** (100): 500-800ms
- **API Response**: 50-100ms

### Scaling

- **Single Worker**: 20-30 req/sec
- **4 Workers**: 80-120 req/sec
- **Max Throughput**: Limited by CPU cores

## Configuration

### Adjust Cache Size

Edit `src/ml_models/efficient_inference.py`:

```python
# Line ~45
_model_cache_instance = ModelCache(max_size=10)  # More models in cache

# Line ~46
_feature_cache_instance = ModelCache(max_size=1000)  # More feature alignments

# Line ~49
_cache_size = 1000  # Max predictions to cache
```

### Adjust Batch Size

```python
from src.ml_models.efficient_inference import BatchPredictor

# Larger batch = better throughput but more memory
batch_pred = BatchPredictor(model, batch_size=64)

# Smaller batch = lower latency
batch_pred = BatchPredictor(model, batch_size=8)
```

## Next Steps

1. **Deploy**: Follow [deployment guide](./DEPLOYMENT.md)
2. **Monitor**: Set up performance monitoring
3. **Scale**: Use load balancing for higher throughput
4. **Optimize**: Consider ONNX conversion for 2-3x speedup

## Support

For issues or questions:
1. Check logs: `logs/app.log`
2. Run tests: `pytest tests/test_pipeline.py -v`
3. Validate setup: `python test_optimizations.py`
