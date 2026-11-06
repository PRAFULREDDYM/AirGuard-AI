import numpy as np
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import classification_report, confusion_matrix

class SensorPatternClassifier:
    """
    Supervised Environmental Sensor-Pattern Classifier.
    Trained on labeled recording sessions with session-grouped cross-validation
    and out-of-distribution unknown-class rejection.
    """
    def __init__(self, confidence_threshold: float = 0.60):
        self.confidence_threshold = confidence_threshold
        self.model: Optional[RandomForestClassifier] = None
        self.classes: List[str] = []
        self.feature_names: List[str] = []
        self.is_trained = False
        self.training_metadata: Dict[str, Any] = {}

    def extract_window_features(self, readings_window: List[Dict[str, Any]]) -> np.ndarray:
        """
        Extracts multi-channel statistical features from a time window:
        mean, std, min, max, delta for each measurement type.
        """
        # Group by measurement type
        by_type: Dict[str, List[float]] = {}
        for r in readings_window:
            m = r.get("measurement_type")
            v = float(r.get("value", 0.0))
            by_type.setdefault(m, []).append(v)

        features = []
        for m_type in ["PM25", "VOC_INDEX", "TEMPERATURE", "HUMIDITY", "CO2"]:
            vals = by_type.get(m_type, [0.0])
            mean_v = float(np.mean(vals))
            std_v = float(np.std(vals))
            min_v = float(np.min(vals))
            max_v = float(np.max(vals))
            delta_v = float(vals[-1] - vals[0]) if len(vals) > 1 else 0.0
            features.extend([mean_v, std_v, min_v, max_v, delta_v])

        return np.array(features)

    def train_on_sessions(
        self,
        sessions_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Trains classifier on labeled session data using GroupKFold by session.
        Prevents temporal leakage across adjacent time windows.
        """
        X = []
        y = []
        groups = []

        for session in sessions_data:
            label = session.get("label")
            if not label:
                continue
            session_id = session.get("session_id")
            windows = session.get("windows", [])
            for w in windows:
                feats = self.extract_window_features(w)
                X.append(feats)
                y.append(label)
                groups.append(session_id)

        X = np.array(X)
        y = np.array(y)
        groups = np.array(groups)

        unique_labels = sorted(list(set(y)))
        unique_sessions = len(set(groups))

        if len(unique_labels) < 2 or unique_sessions < 2 or len(X) < 10:
            return {
                "status": "not_trained",
                "error": "Insufficient labeled sessions for training. Minimum 2 distinct classes and 2 separate sessions required."
            }

        # Train Random Forest
        rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
        rf.fit(X, y)

        # Cross-validation with GroupKFold
        n_splits = min(3, unique_sessions)
        gkf = GroupKFold(n_splits=n_splits)
        cv_scores = []
        for train_idx, test_idx in gkf.split(X, y, groups):
            rf_cv = RandomForestClassifier(n_estimators=50, max_depth=8, random_state=42)
            rf_cv.fit(X[train_idx], y[train_idx])
            score = rf_cv.score(X[test_idx], y[test_idx])
            cv_scores.append(score)

        self.model = rf
        self.classes = list(rf.classes_)
        self.is_trained = True
        self.training_metadata = {
            "training_date": datetime.utcnow().isoformat(),
            "sample_count": len(X),
            "session_count": unique_sessions,
            "classes": self.classes,
            "mean_cv_accuracy": round(float(np.mean(cv_scores)), 3),
            "limitations": "Trained only on controlled indoor ambient and benign odor examples. Odor descriptors are statistical pattern matches, NOT chemical identification."
        }

        return {
            "status": "trained",
            "metadata": self.training_metadata
        }

    def predict(self, window_readings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Classifies an observed sensor window. Rejects unknown/OOD classes if
        maximum predicted probability is below confidence_threshold.
        """
        if not self.is_trained or not self.model:
            return {
                "status": "not_trained",
                "classification": None,
                "confidence": 0.0,
                "is_unknown": True,
                "message": "Model is not trained. Classification unavailable."
            }

        feats = self.extract_window_features(window_readings).reshape(1, -1)
        probs = self.model.predict_proba(feats)[0]
        max_idx = int(np.argmax(probs))
        max_prob = float(probs[max_idx])
        predicted_class = self.classes[max_idx]

        # Unknown / Out-of-distribution rejection
        if max_prob < self.confidence_threshold:
            return {
                "status": "unidentified_anomaly",
                "classification": "unknown_pattern",
                "confidence": round(max_prob, 3),
                "is_unknown": True,
                "message": "Pattern detected but confidence below validation threshold. Labeled as unidentified pattern."
            }

        return {
            "status": "classified",
            "classification": predicted_class,
            "confidence": round(max_prob, 3),
            "is_unknown": False,
            "class_probabilities": {cls: round(float(p), 3) for cls, p in zip(self.classes, probs)},
            "warning": "Classification represents a learned sensor pattern, NOT confirmed chemical hazard."
        }

sensor_classifier = SensorPatternClassifier()

