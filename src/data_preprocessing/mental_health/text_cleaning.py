import pandas as pd
import re
import nltk
from nltk.corpus import stopwords

df = pd.read_csv("data/raw/mental_health.csv")

print("Original Shape:", df.shape)

FALLBACK_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "he", "in", "is", "it", "its", "of", "on", "that", "the",
    "to", "was", "were", "will", "with"
}


def load_stop_words():
    try:
        return set(stopwords.words("english"))
    except LookupError:
        try:
            nltk.download("stopwords", quiet=True)
            return set(stopwords.words("english"))
        except Exception:
            print("Falling back to built-in stopword list.")
            return FALLBACK_STOPWORDS


# Load stopwords once and avoid hard-failing when downloads are blocked
stop_words = load_stop_words()

def clean_text(text):
    text = str(text).lower()
    text = re.sub(r'[^a-zA-Z ]', '', text)
    words = text.split()
    words = [w for w in words if w not in stop_words]
    return " ".join(words)

# Apply cleaning
df["cleaned_text"] = df["text"].apply(clean_text)

df.to_csv("data/cleaned/mental_health_cleaned.csv", index=False)

print("Text cleaning completed")
