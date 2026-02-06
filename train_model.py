"""
Model Training Script for AI Voice Detection
Implements ensemble approach with multiple classifiers
"""

import numpy as np
import librosa
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import joblib
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceDatasetLoader:
    """Load and preprocess voice dataset"""
    
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.languages = ['tamil', 'english', 'hindi', 'malayalam', 'telugu']
        
    def load_dataset(self):
        """
        Load dataset with structure:
        data/
          ├── ai_generated/
          │   ├── tamil/
          │   ├── english/
          │   ├── hindi/
          │   ├── malayalam/
          │   └── telugu/
          └── human/
              ├── tamil/
              ├── english/
              ├── hindi/
              ├── malayalam/
              └── telugu/
        """
        X = []
        y = []
        languages = []
        
        for label_dir in ['ai_generated', 'human']:
            label = 1 if label_dir == 'ai_generated' else 0
            
            for lang in self.languages:
                audio_dir = self.data_dir / label_dir / lang
                
                if not audio_dir.exists():
                    logger.warning(f"Directory not found: {audio_dir}")
                    continue
                
                for audio_file in audio_dir.glob('*.mp3'):
                    try:
                        features = self.extract_features(str(audio_file))
                        X.append(features)
                        y.append(label)
                        languages.append(lang)
                        logger.info(f"Processed: {audio_file.name}")
                    except Exception as e:
                        logger.error(f"Error processing {audio_file}: {e}")
        
        return np.array(X), np.array(y), languages
    
    def extract_features(self, audio_path):
        """Extract comprehensive features from audio"""
        audio, sr = librosa.load(audio_path, sr=None, duration=30)
        
        features = []
        
        # 1. MFCC features (40 coefficients)
        mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=40)
        features.extend(np.mean(mfccs, axis=1))
        features.extend(np.std(mfccs, axis=1))
        
        # 2. Chroma features
        chroma = librosa.feature.chroma_stft(y=audio, sr=sr)
        features.extend(np.mean(chroma, axis=1))
        features.extend(np.std(chroma, axis=1))
        
        # 3. Spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)[0]
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=sr)[0]
        
        features.extend([
            np.mean(spectral_centroids), np.std(spectral_centroids),
            np.mean(spectral_rolloff), np.std(spectral_rolloff),
            np.mean(spectral_bandwidth), np.std(spectral_bandwidth)
        ])
        
        # 4. Prosodic features
        pitches, magnitudes = librosa.piptrack(y=audio, sr=sr)
        pitch_values = [pitches[magnitudes[:, t].argmax(), t] 
                       for t in range(pitches.shape[1]) 
                       if pitches[magnitudes[:, t].argmax(), t] > 0]
        
        features.extend([
            np.mean(pitch_values) if pitch_values else 0,
            np.std(pitch_values) if pitch_values else 0
        ])
        
        # 5. Energy
        energy = librosa.feature.rms(y=audio)[0]
        features.extend([np.mean(energy), np.std(energy)])
        
        # 6. Zero crossing rate
        zcr = librosa.feature.zero_crossing_rate(audio)[0]
        features.extend([np.mean(zcr), np.std(zcr)])
        
        # 7. Harmonic-to-Noise Ratio (approximation)
        harmonic, percussive = librosa.effects.hpss(audio)
        hnr = np.mean(harmonic) / (np.mean(percussive) + 1e-6)
        features.append(hnr)
        
        # 8. Temporal features
        # Silence ratio
        intervals = librosa.effects.split(audio, top_db=30)
        silence_ratio = 1 - (sum([end - start for start, end in intervals]) / len(audio))
        features.append(silence_ratio)
        
        return np.array(features)


class EnsembleVoiceClassifier:
    """Ensemble classifier combining multiple models"""
    
    def __init__(self):
        self.models = {
            'random_forest': RandomForestClassifier(
                n_estimators=200,
                max_depth=20,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1
            ),
            'gradient_boosting': GradientBoostingClassifier(
                n_estimators=150,
                learning_rate=0.1,
                max_depth=10,
                random_state=42
            ),
            'svm': SVC(
                kernel='rbf',
                C=10,
                gamma='scale',
                probability=True,
                random_state=42
            )
        }
        self.scaler = StandardScaler()
        self.weights = None
        
    def train(self, X_train, y_train, X_val, y_val):
        """Train all models and optimize ensemble weights"""
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        
        # Train individual models
        val_predictions = {}
        
        for name, model in self.models.items():
            logger.info(f"Training {name}...")
            model.fit(X_train_scaled, y_train)
            
            # Validation predictions
            val_pred = model.predict_proba(X_val_scaled)[:, 1]
            val_predictions[name] = val_pred
            
            # Evaluate
            val_acc = model.score(X_val_scaled, y_val)
            logger.info(f"{name} validation accuracy: {val_acc:.4f}")
        
        # Optimize ensemble weights using validation set
        self.weights = self._optimize_weights(val_predictions, y_val)
        logger.info(f"Optimized weights: {self.weights}")
        
        # Final ensemble evaluation
        ensemble_pred = self._ensemble_predict(val_predictions)
        ensemble_acc = np.mean((ensemble_pred > 0.5) == y_val)
        logger.info(f"Ensemble validation accuracy: {ensemble_acc:.4f}")
        
    def _optimize_weights(self, predictions_dict, y_true):
        """Optimize ensemble weights based on validation performance"""
        from scipy.optimize import minimize
        
        def objective(weights):
            weights = weights / weights.sum()  # Normalize
            ensemble = sum(w * predictions_dict[name] 
                          for w, name in zip(weights, predictions_dict.keys()))
            return -roc_auc_score(y_true, ensemble)
        
        n_models = len(predictions_dict)
        initial_weights = np.ones(n_models) / n_models
        bounds = [(0, 1)] * n_models
        
        result = minimize(objective, initial_weights, bounds=bounds)
        optimized = result.x / result.x.sum()
        
        return {name: w for name, w in zip(predictions_dict.keys(), optimized)}
    
    def _ensemble_predict(self, predictions_dict):
        """Weighted ensemble prediction"""
        ensemble = sum(self.weights[name] * predictions_dict[name] 
                      for name in predictions_dict.keys())
        return ensemble
    
    def predict_proba(self, X):
        """Predict probabilities using ensemble"""
        X_scaled = self.scaler.transform(X)
        
        predictions = {}
        for name, model in self.models.items():
            predictions[name] = model.predict_proba(X_scaled)[:, 1]
        
        return self._ensemble_predict(predictions)
    
    def predict(self, X):
        """Predict class labels"""
        proba = self.predict_proba(X)
        return (proba > 0.5).astype(int)
    
    def save(self, output_dir):
        """Save all models and scaler"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save individual models
        for name, model in self.models.items():
            joblib.dump(model, output_dir / f"{name}.pkl")
        
        # Save scaler
        joblib.dump(self.scaler, output_dir / "scaler.pkl")
        
        # Save weights
        with open(output_dir / "weights.json", 'w') as f:
            json.dump(self.weights, f)
        
        logger.info(f"Models saved to {output_dir}")
    
    @classmethod
    def load(cls, model_dir):
        """Load trained models"""
        model_dir = Path(model_dir)
        
        ensemble = cls()
        
        # Load individual models
        for name in ensemble.models.keys():
            ensemble.models[name] = joblib.load(model_dir / f"{name}.pkl")
        
        # Load scaler
        ensemble.scaler = joblib.load(model_dir / "scaler.pkl")
        
        # Load weights
        with open(model_dir / "weights.json", 'r') as f:
            ensemble.weights = json.load(f)
        
        logger.info(f"Models loaded from {model_dir}")
        return ensemble


def train_pipeline(data_dir, output_dir):
    """Complete training pipeline"""
    
    logger.info("Starting training pipeline...")
    
    # Load dataset
    loader = VoiceDatasetLoader(data_dir)
    X, y, languages = loader.load_dataset()
    
    logger.info(f"Dataset size: {len(X)} samples")
    logger.info(f"AI samples: {sum(y)}, Human samples: {len(y) - sum(y)}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.2, random_state=42, stratify=y_train
    )
    
    logger.info(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    
    # Train ensemble
    ensemble = EnsembleVoiceClassifier()
    ensemble.train(X_train, y_train, X_val, y_val)
    
    # Final evaluation
    y_pred = ensemble.predict(X_test)
    y_pred_proba = ensemble.predict_proba(X_test)
    
    logger.info("\nTest Set Results:")
    logger.info(classification_report(y_test, y_pred, 
                                     target_names=['Human', 'AI Generated']))
    logger.info(f"ROC AUC: {roc_auc_score(y_test, y_pred_proba):.4f}")
    
    # Save model
    ensemble.save(output_dir)
    
    return ensemble


if __name__ == "__main__":
    # Example usage
    DATA_DIR = "data"  # Directory with audio samples
    OUTPUT_DIR = "models"
    
    # Check if data directory exists
    if not os.path.exists(DATA_DIR):
        logger.error(f"Data directory {DATA_DIR} not found!")
        logger.info("Please organize your data as:")
        logger.info("data/")
        logger.info("  ├── ai_generated/")
        logger.info("  │   ├── tamil/")
        logger.info("  │   ├── english/")
        logger.info("  │   └── ...")
        logger.info("  └── human/")
        logger.info("      ├── tamil/")
        logger.info("      ├── english/")
        logger.info("      └── ...")
    else:
        ensemble = train_pipeline(DATA_DIR, OUTPUT_DIR)
        logger.info("Training complete!")
