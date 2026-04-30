import logging

import pandas as pd


logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def log(message):
    logging.info(message)


def get_model_feature_names(model):
    """Extract feature names from model"""
    for attr_name in ("feature_names_", "feature_names_in_"):
        feature_names = getattr(model, attr_name, None)
        if feature_names is not None:
            return [str(name) for name in feature_names]
    return None


def align_features_to_model(df, model, fill_value=0):
    """Align dataframe features to model requirements"""
    feature_names = get_model_feature_names(model)
    if not feature_names:
        return df

    aligned_df = df.copy()
    missing_columns = [name for name in feature_names if name not in aligned_df.columns]
    if missing_columns:
        missing_df = pd.DataFrame(fill_value, index=aligned_df.index, columns=missing_columns)
        aligned_df = pd.concat([aligned_df, missing_df], axis=1)

    return aligned_df[feature_names]


def prepare_model_for_inference(model):
    """Prepare model for efficient single-threaded inference"""
    if hasattr(model, "n_jobs") and getattr(model, "n_jobs") not in (None, 1):
        try:
            model.n_jobs = 1
        except Exception:
            pass
    
    if hasattr(model, "thread_count") and getattr(model, "thread_count") not in (None, 1):
        try:
            model.thread_count = 1
        except Exception:
            pass
    
    return model
