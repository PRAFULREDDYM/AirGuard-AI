import os
import joblib
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "samples", "sample_odor_molecules.csv")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODEL_DIR, exist_ok=True)
MODEL_PATH = os.path.join(MODEL_DIR, "pom_rf_checkpoint.joblib")

from services.ml_molecular.service import CANONICAL_ODOR_DESCRIPTORS

def extract_morgan_fp(smiles: str, n_bits: int = 1024) -> np.ndarray:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return np.zeros(n_bits, dtype=np.int8)
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=n_bits)
    arr = np.zeros((n_bits,), dtype=np.int8)
    Chem.DataStructs.ConvertToNumpyArray(fp, arr)
    return arr

def train_and_save():
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} sample molecules from {DATA_PATH}")

    # Build binary label matrix for top canonical descriptors
    top_descriptors = [
        "vanilla", "sweet", "creamy", "citrus", "orange", "fresh",
        "clove", "spicy", "warm", "banana", "fruity", "sulfurous",
        "cabbage", "gassy", "earthy", "musty", "balsamic", "phenolic",
        "medicinal", "buttery", "caramellic", "roasted", "floral", "green"
    ]

    X = []
    Y = []
    for _, row in df.iterrows():
        smiles = row["nonStereoSMILES"]
        descriptors = [d.strip().lower() for d in str(row["primary_descriptors"]).split(";")]
        fp = extract_morgan_fp(smiles)
        X.append(fp)
        y_vec = [1 if d in descriptors else 0 for d in top_descriptors]
        Y.append(y_vec)

    X = np.array(X)
    Y = np.array(Y)

    # Train multi-output Random Forest
    rf = RandomForestClassifier(n_estimators=30, max_depth=6, random_state=42)
    rf.fit(X, Y)

    # Save model and descriptor mapping
    checkpoint = {
        "model": rf,
        "descriptors": top_descriptors,
        "n_bits": 1024,
        "training_date": pd.Timestamp.now().isoformat(),
        "model_type": "Morgan_FP_RandomForest_MultiOutput",
        "sample_count": len(df)
    }
    joblib.dump(checkpoint, MODEL_PATH)
    print(f"Trained and saved baseline molecular odor model to {MODEL_PATH}")

if __name__ == "__main__":
    train_and_save()

