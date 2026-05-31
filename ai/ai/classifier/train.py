import os
import json
import torch
import numpy as np
import pandas as pd
import random

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
from sklearn.utils.class_weight import compute_class_weight

from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
    Trainer,
    TrainingArguments,
    EarlyStoppingCallback
)

# =====================================
# Reproducibility
# =====================================

SEED = 42
torch.manual_seed(SEED)
np.random.seed(SEED)
random.seed(SEED)

# =====================================
# Paths
# =====================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data.csv")
MODEL_DIR = os.path.join(BASE_DIR, "model")

os.makedirs(MODEL_DIR, exist_ok=True)

# =====================================
# Load Dataset
# =====================================

df = pd.read_csv(DATA_PATH)

if "text" not in df.columns or "emotion" not in df.columns:
    raise ValueError("Dataset must contain 'text' and 'emotion' columns.")

df = df.dropna(subset=["text", "emotion"])
df["text"] = df["text"].astype(str)

labels = sorted(df["emotion"].unique())
label2id = {l: i for i, l in enumerate(labels)}
id2label = {i: l for l, i in label2id.items()}

df["label"] = df["emotion"].map(label2id)

# =====================================
# Stratified Split
# =====================================

train_texts, val_texts, train_labels, val_labels = train_test_split(
    df["text"],
    df["label"],
    test_size=0.2,
    random_state=SEED,
    stratify=df["label"]
)

# =====================================
# Tokenization
# =====================================

tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")

train_encodings = tokenizer(
    train_texts.tolist(),
    truncation=True,
    padding=True,
    max_length=128
)

val_encodings = tokenizer(
    val_texts.tolist(),
    truncation=True,
    padding=True,
    max_length=128
)

# =====================================
# Dataset Class
# =====================================

class EmotionDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels.tolist()

    def __getitem__(self, idx):
        item = {k: torch.tensor(v[idx]) for k, v in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)


train_dataset = EmotionDataset(train_encodings, train_labels)
val_dataset = EmotionDataset(val_encodings, val_labels)

# =====================================
# Compute Class Weights
# =====================================

class_weights = compute_class_weight(
    class_weight="balanced",
    classes=np.unique(train_labels),
    y=train_labels
)

class_weights = torch.tensor(class_weights, dtype=torch.float)

# =====================================
# Model
# =====================================

model = DistilBertForSequenceClassification.from_pretrained(
    "distilbert-base-uncased",
    num_labels=len(labels),
    id2label=id2label,
    label2id=label2id
)

# =====================================
# Custom Trainer (Weighted Loss)
# =====================================

class WeightedTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False):
        labels = inputs.get("labels")
        outputs = model(**inputs)
        logits = outputs.get("logits")

        loss_fct = torch.nn.CrossEntropyLoss(
            weight=class_weights.to(model.device)
        )

        loss = loss_fct(
            logits.view(-1, model.config.num_labels),
            labels.view(-1)
        )

        return (loss, outputs) if return_outputs else loss

# =====================================
# Metrics
# =====================================

def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)

    acc = accuracy_score(labels, preds)
    f1 = f1_score(labels, preds, average="weighted")

    return {
        "accuracy": round(acc, 4),
        "f1": round(f1, 4)
    }

# =====================================
# Training Arguments
# =====================================

training_args = TrainingArguments(
    output_dir=MODEL_DIR,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=5,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    logging_steps=25,
    load_best_model_at_end=True,
    metric_for_best_model="f1",
    greater_is_better=True,
    weight_decay=0.01,
    warmup_ratio=0.1,
    max_grad_norm=1.0,
    fp16=torch.cuda.is_available(),
    seed=SEED,
    report_to="none"
)

# =====================================
# Trainer
# =====================================

trainer = WeightedTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    compute_metrics=compute_metrics,
    callbacks=[EarlyStoppingCallback(early_stopping_patience=2)]
)

# =====================================
# Train
# =====================================

trainer.train()

# =====================================
# Save Model + Tokenizer
# =====================================

model.save_pretrained(MODEL_DIR)
tokenizer.save_pretrained(MODEL_DIR)

with open(os.path.join(MODEL_DIR, "label_mapping.json"), "w") as f:
    json.dump({
        "label2id": label2id,
        "id2label": id2label
    }, f)

print("✅ Advanced Emotion Model trained successfully")