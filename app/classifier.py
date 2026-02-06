"""
Voice Classifier for AI/Human Detection
Supports both mock classifier (MVP) and trained ensemble models
"""

import numpy as np
import joblib
import json
from pathlib import Path
from typing import Tuple, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class MockVoiceClassifier:
    """
    Mock classifier for MVP testing
    Uses heuristic-based classification before trained models are available
    """
    
    def __init__(self):
        self.model_version = "1.0.0-mock"
        self.is_mock = True
        logger.info("Initialized mock classifier")
    
    def predict(self, features: np.ndarray, language: str) -> Tuple[str, float]:
        """
        Predict if voice is AI-generated or human using heuristics
        
        AI-generated voices typically have:
        - Lower pitch variance (features[81] - pitch_std)
        - More consistent MFCC patterns
        - Higher spectral flatness
        - Lower jitter and shimmer
        """
        # Feature indices (based on audio_processor.py extraction order):
        # 0-79: MFCC (40 mean + 40 std)
        # 80-89: Spectral (10 features)
        # 90-95: Prosodic (pitch_mean, pitch_std, pitch_range, energy_mean, energy_std, zcr)
        # 96-98: Voice quality (jitter, shimmer, hnr)
        # 99-102: Temporal (silence_ratio, avg_pause, onset_mean, onset_std)
        # 103-126: Chroma (24 features)
        
        ai_score = 0.0
        
        # 1. Check pitch variance (index 91 = pitch_std)
        pitch_std = features[91] if len(features) > 91 else 0
        if pitch_std < 30:  # Low pitch variation suggests AI
            ai_score += 0.25
        elif pitch_std > 100:  # High variation suggests human
            ai_score -= 0.1
        
        # 2. Check MFCC consistency (std of MFCC std values)
        if len(features) >= 80:
            mfcc_std_values = features[40:80]  # MFCC std values
            mfcc_consistency = np.std(mfcc_std_values)
            if mfcc_consistency < 2:  # Very consistent MFCCs suggest AI
                ai_score += 0.2
        
        # 3. Check jitter (index 96)
        jitter = features[96] if len(features) > 96 else 0
        if jitter < 0.02:  # Very low jitter suggests AI
            ai_score += 0.15
        elif jitter > 0.05:  # High jitter suggests human
            ai_score -= 0.1
        
        # 4. Check shimmer (index 97)
        shimmer = features[97] if len(features) > 97 else 0
        if shimmer < 0.03:  # Very low shimmer suggests AI
            ai_score += 0.15
        
        # 5. Check HNR (index 98) - Harmonic to Noise Ratio
        hnr = features[98] if len(features) > 98 else 0
        if hnr > 15:  # Very clean audio suggests AI
            ai_score += 0.15
        
        # 6. Check onset patterns (speech rhythm)
        onset_std = features[101] if len(features) > 101 else 0
        if onset_std < 0.5:  # Very consistent rhythm suggests AI
            ai_score += 0.1
        
        # Normalize score to 0-1 range
        ai_score = max(0, min(1, 0.5 + ai_score))
        
        # Add slight randomness for demo variety (remove in production)
        import random
        ai_score += random.uniform(-0.1, 0.1)
        ai_score = max(0.05, min(0.95, ai_score))
        
        # Determine prediction
        is_ai = ai_score > 0.5
        prediction = "AI_GENERATED" if is_ai else "HUMAN"
        confidence = ai_score if is_ai else (1 - ai_score)
        
        return prediction, round(confidence, 3)


class EnsembleVoiceClassifier:
    """
    Production ensemble classifier using trained models
    Combines Random Forest, Gradient Boosting, and SVM
    """
    
    def __init__(self, model_dir: str):
        self.model_dir = Path(model_dir)
        self.models: Dict = {}
        self.scaler = None
        self.weights: Dict = {}
        self.model_version = "1.0.0"
        self.is_mock = False
        
        self._load_models()
    
    def _load_models(self):
        """Load all trained models from disk"""
        try:
            # Load individual models
            model_names = ['random_forest', 'gradient_boosting', 'svm']
            
            for name in model_names:
                model_path = self.model_dir / f"{name}.pkl"
                if model_path.exists():
                    self.models[name] = joblib.load(model_path)
                    logger.info(f"Loaded model: {name}")
            
            # Load scaler
            scaler_path = self.model_dir / "scaler.pkl"
            if scaler_path.exists():
                self.scaler = joblib.load(scaler_path)
                logger.info("Loaded feature scaler")
            
            # Load ensemble weights
            weights_path = self.model_dir / "weights.json"
            if weights_path.exists():
                with open(weights_path, 'r') as f:
                    self.weights = json.load(f)
                logger.info(f"Loaded weights: {self.weights}")
            else:
                # Equal weights if no optimization was done
                self.weights = {name: 1/len(self.models) for name in self.models.keys()}
            
            if not self.models:
                raise FileNotFoundError("No models found")
                
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise
    
    def predict(self, features: np.ndarray, language: str) -> Tuple[str, float]:
        """
        Predict using weighted ensemble voting
        """
        # Reshape if needed
        if features.ndim == 1:
            features = features.reshape(1, -1)
        
        # Scale features
        if self.scaler:
            features_scaled = self.scaler.transform(features)
        else:
            features_scaled = features
        
        # Get predictions from all models
        predictions = {}
        for name, model in self.models.items():
            try:
                proba = model.predict_proba(features_scaled)[0, 1]
                predictions[name] = proba
            except Exception as e:
                logger.warning(f"Model {name} prediction failed: {e}")
        
        if not predictions:
            raise RuntimeError("All models failed to predict")
        
        # Weighted ensemble
        ensemble_score = sum(
            self.weights.get(name, 0) * score 
            for name, score in predictions.items()
        )
        
        # Determine prediction
        is_ai = ensemble_score > 0.5
        prediction = "AI_GENERATED" if is_ai else "HUMAN"
        confidence = ensemble_score if is_ai else (1 - ensemble_score)
        
        return prediction, round(confidence, 3)


def get_classifier(model_dir: Optional[str] = None) -> MockVoiceClassifier | EnsembleVoiceClassifier:
    """
    Factory function to get appropriate classifier
    Returns ensemble if models exist, otherwise mock
    """
    if model_dir:
        model_path = Path(model_dir)
        required_files = ['random_forest.pkl', 'scaler.pkl']
        
        if all((model_path / f).exists() for f in required_files):
            try:
                return EnsembleVoiceClassifier(model_dir)
            except Exception as e:
                logger.warning(f"Failed to load ensemble models: {e}")
    
    logger.info("Using mock classifier (no trained models found)")
    return MockVoiceClassifier()
