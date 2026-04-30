"""
ML Model Optimization & Efficient Inference
Optimizes model loading, inference, and caching for production performance
"""

import joblib
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import threading
from functools import lru_cache
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# GLOBAL MODEL CACHE
# ============================================================================

_model_cache = {}
_model_lock = threading.Lock()
_prediction_cache = {}
_cache_size = 1000


class ModelCache:
    """Thread-safe model cache with LRU eviction"""
    
    def __init__(self, max_size=1000):
        self.cache = {}
        self.max_size = max_size
        self.lock = threading.Lock()
        self.access_times = {}
    
    def get(self, key: str):
        """Get model from cache"""
        with self.lock:
            if key in self.cache:
                self.access_times[key] = time.time()
                return self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """Set model in cache with LRU eviction"""
        with self.lock:
            if len(self.cache) >= self.max_size:
                # Evict least recently used
                lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
                del self.cache[lru_key]
                del self.access_times[lru_key]
            
            self.cache[key] = value
            self.access_times[key] = time.time()
    
    def clear(self):
        """Clear entire cache"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()


# Global cache instances
_model_cache_instance = ModelCache(max_size=10)
_feature_cache_instance = ModelCache(max_size=1000)


# ============================================================================
# EFFICIENT MODEL LOADING
# ============================================================================

def load_model_cached(model_path: str, force_reload=False):
    """
    Load model with caching to avoid repeated disk I/O
    
    Args:
        model_path: Path to model file
        force_reload: Force reload from disk
        
    Returns:
        Loaded model
    """
    if not force_reload:
        cached = _model_cache_instance.get(model_path)
        if cached is not None:
            logger.debug(f"Loading {model_path} from cache")
            return cached
    
    logger.debug(f"Loading {model_path} from disk")
    try:
        model = joblib.load(model_path)
        _model_cache_instance.set(model_path, model)
        return model
    except Exception as e:
        logger.error(f"Failed to load {model_path}: {e}")
        return None


def unload_model_cache():
    """Clear model cache to free memory"""
    _model_cache_instance.clear()
    logger.info("Model cache cleared")


# ============================================================================
# OPTIMIZED FEATURE ALIGNMENT
# ============================================================================

def align_features_optimized(df: pd.DataFrame, model, fill_value=0):
    """
    Optimized feature alignment with caching and vectorization
    
    Args:
        df: Input dataframe
        model: Model with feature requirements
        fill_value: Value for missing features
        
    Returns:
        Aligned dataframe
    """
    # Get expected features
    expected_features = get_model_feature_names(model)
    if not expected_features:
        return df
    
    # Fast path: features already aligned
    if set(df.columns) == set(expected_features):
        return df[expected_features]
    
    # Check cache for alignment mapping
    cache_key = f"{model.__class__.__name__}_{len(expected_features)}"
    
    # Alignment with minimal copies
    aligned_df = df.copy()
    
    # Add missing features efficiently
    missing_features = [f for f in expected_features if f not in aligned_df.columns]
    if missing_features:
        aligned_df = aligned_df.assign(**{f: fill_value for f in missing_features})
    
    # Return only needed features in correct order
    return aligned_df[expected_features]


# ============================================================================
# BATCH PREDICTION OPTIMIZATION
# ============================================================================

class BatchPredictor:
    """Efficient batch prediction handler"""
    
    def __init__(self, model, batch_size=32):
        self.model = model
        self.batch_size = batch_size
    
    def predict_batch(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict on batch of data
        
        Args:
            X: Input features dataframe
            
        Returns:
            Predictions array
        """
        n_samples = len(X)
        
        if n_samples <= self.batch_size:
            return self.model.predict(X)
        
        predictions = []
        for i in range(0, n_samples, self.batch_size):
            batch = X.iloc[i:i + self.batch_size]
            batch_pred = self.model.predict(batch)
            predictions.extend(batch_pred)
        
        return np.array(predictions)
    
    def predict_proba_batch(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict probabilities on batch of data
        
        Args:
            X: Input features dataframe
            
        Returns:
            Probabilities array
        """
        if not hasattr(self.model, 'predict_proba'):
            return None
        
        n_samples = len(X)
        
        if n_samples <= self.batch_size:
            return self.model.predict_proba(X)
        
        predictions = []
        for i in range(0, n_samples, self.batch_size):
            batch = X.iloc[i:i + self.batch_size]
            batch_pred = self.model.predict_proba(batch)
            predictions.extend(batch_pred)
        
        return np.array(predictions)


# ============================================================================
# PREDICTION CACHING
# ============================================================================

def get_prediction_hash(features_dict: Dict) -> str:
    """Create hash of features for caching"""
    import hashlib
    import json
    
    # Convert to JSON for hashing (order-independent for dicts)
    json_str = json.dumps(features_dict, sort_keys=True, default=str)
    return hashlib.md5(json_str.encode()).hexdigest()


def cached_predict(model, features_dict: Dict, cache_ttl: int = 3600) -> Optional[float]:
    """
    Predict with caching (useful for repeated queries)
    
    Args:
        model: Model to use for prediction
        features_dict: Input features as dict
        cache_ttl: Cache time-to-live in seconds
        
    Returns:
        Cached prediction or None if not in cache
    """
    cache_key = get_prediction_hash(features_dict)
    
    if cache_key in _prediction_cache:
        cached_time, cached_result = _prediction_cache[cache_key]
        if time.time() - cached_time < cache_ttl:
            logger.debug(f"Returning cached prediction for {cache_key}")
            return cached_result
    
    return None


def store_prediction(features_dict: Dict, prediction: float):
    """Store prediction in cache"""
    cache_key = get_prediction_hash(features_dict)
    _prediction_cache[cache_key] = (time.time(), prediction)
    
    # Limit cache size
    if len(_prediction_cache) > _cache_size:
        # Remove oldest entries
        oldest_key = min(_prediction_cache.keys(), 
                        key=lambda k: _prediction_cache[k][0])
        del _prediction_cache[oldest_key]


def clear_prediction_cache():
    """Clear prediction cache"""
    _prediction_cache.clear()
    logger.info("Prediction cache cleared")


# ============================================================================
# MODEL HELPER FUNCTIONS
# ============================================================================

def get_model_feature_names(model) -> Optional[List[str]]:
    """Extract feature names from model"""
    for attr_name in ("feature_names_", "feature_names_in_"):
        feature_names = getattr(model, attr_name, None)
        if feature_names is not None:
            return [str(name) for name in feature_names]
    return None


def prepare_model_for_inference(model):
    """Prepare model for single-threaded inference"""
    if hasattr(model, "n_jobs"):
        try:
            model.n_jobs = 1
        except Exception as e:
            logger.warning(f"Could not set n_jobs=1: {e}")
    
    if hasattr(model, "thread_count"):
        try:
            model.thread_count = 1
        except Exception as e:
            logger.warning(f"Could not set thread_count=1: {e}")
    
    return model


# ============================================================================
# INFERENCE PROFILING
# ============================================================================

class InferenceProfiler:
    """Profile model inference performance"""
    
    def __init__(self):
        self.timings = []
        self.feature_counts = []
        self.model_names = []
    
    def profile_inference(self, model_name: str, model, X: pd.DataFrame, 
                         n_runs: int = 100) -> Dict[str, float]:
        """Profile inference speed"""
        times = []
        
        for _ in range(n_runs):
            start = time.time()
            _ = model.predict(X)
            times.append(time.time() - start)
        
        avg_time = np.mean(times)
        std_time = np.std(times)
        min_time = np.min(times)
        max_time = np.max(times)
        
        results = {
            "model": model_name,
            "n_features": len(X.columns),
            "n_samples": len(X),
            "avg_time_ms": avg_time * 1000,
            "std_time_ms": std_time * 1000,
            "min_time_ms": min_time * 1000,
            "max_time_ms": max_time * 1000,
            "throughput_samples_per_sec": len(X) / avg_time,
        }
        
        self.timings.append(results)
        return results
    
    def get_report(self) -> str:
        """Generate profiling report"""
        if not self.timings:
            return "No profiling data"
        
        report = "=" * 80 + "\n"
        report += "MODEL INFERENCE PROFILING REPORT\n"
        report += "=" * 80 + "\n\n"
        
        for timing in self.timings:
            report += f"Model: {timing['model']}\n"
            report += f"  Samples: {timing['n_samples']} | Features: {timing['n_features']}\n"
            report += f"  Avg Time: {timing['avg_time_ms']:.3f}ms ± {timing['std_time_ms']:.3f}ms\n"
            report += f"  Range: {timing['min_time_ms']:.3f}ms - {timing['max_time_ms']:.3f}ms\n"
            report += f"  Throughput: {timing['throughput_samples_per_sec']:.1f} samples/sec\n"
            report += "\n"
        
        return report


# ============================================================================
# EFFICIENT INFERENCE WRAPPER
# ============================================================================

class EfficientInference:
    """Unified efficient inference interface"""
    
    def __init__(self, model_path: str, model_name: str = "model"):
        self.model_path = model_path
        self.model_name = model_name
        self.model = None
        self.batch_predictor = None
        self._load_model()
    
    def _load_model(self):
        """Load model with optimization"""
        self.model = load_model_cached(self.model_path)
        if self.model:
            self.model = prepare_model_for_inference(self.model)
            self.batch_predictor = BatchPredictor(self.model)
            logger.info(f"Loaded optimized model: {self.model_name}")
    
    def predict(self, X: pd.DataFrame, use_batch: bool = True) -> np.ndarray:
        """Efficient single prediction"""
        if self.model is None:
            logger.error(f"Model not loaded: {self.model_name}")
            return np.array([])
        
        # Align features
        X_aligned = align_features_optimized(X, self.model)
        
        # Batch or single prediction
        if use_batch and len(X) > 1:
            return self.batch_predictor.predict_batch(X_aligned)
        else:
            return self.model.predict(X_aligned)
    
    def predict_proba(self, X: pd.DataFrame, use_batch: bool = True) -> Optional[np.ndarray]:
        """Efficient probability prediction"""
        if self.model is None or not hasattr(self.model, 'predict_proba'):
            return None
        
        X_aligned = align_features_optimized(X, self.model)
        
        if use_batch and len(X) > 1:
            return self.batch_predictor.predict_proba_batch(X_aligned)
        else:
            return self.model.predict_proba(X_aligned)
    
    def get_feature_count(self) -> int:
        """Get number of features expected by model"""
        features = get_model_feature_names(self.model)
        return len(features) if features else 0


# ============================================================================
# MODEL STATISTICS
# ============================================================================

def get_model_stats(model_path: str) -> Dict[str, Any]:
    """Get model statistics"""
    try:
        stat_info = Path(model_path).stat()
        model = joblib.load(model_path)
        
        features = get_model_feature_names(model)
        
        return {
            "path": str(model_path),
            "size_mb": stat_info.st_size / (1024 * 1024),
            "n_features": len(features) if features else "Unknown",
            "model_type": model.__class__.__name__,
            "has_predict_proba": hasattr(model, 'predict_proba'),
        }
    except Exception as e:
        logger.error(f"Could not get stats for {model_path}: {e}")
        return {}


# ============================================================================
# BATCH INFERENCE ORCHESTRATOR
# ============================================================================

class BatchInferenceOrchestrator:
    """Manage multiple model predictions efficiently"""
    
    def __init__(self):
        self.models = {}
    
    def register_model(self, name: str, model_path: str):
        """Register a model"""
        self.models[name] = EfficientInference(model_path, name)
    
    def predict_all(self, X: pd.DataFrame) -> Dict[str, np.ndarray]:
        """Get predictions from all registered models"""
        results = {}
        for name, inference in self.models.items():
            try:
                results[name] = inference.predict(X)
            except Exception as e:
                logger.error(f"Prediction failed for {name}: {e}")
        return results
    
    def get_stats(self) -> Dict[str, Dict]:
        """Get statistics for all models"""
        return {name: inf.model_path for name, inf in self.models.items()}
