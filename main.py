"""
AI Voice Detection API
Detects whether audio is AI-generated or human speech
Supports: Tamil, English, Hindi, Malayalam, Telugu
"""

from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, validator
import base64
import io
import librosa
import numpy as np
from typing import Literal
import logging
from datetime import datetime
import hashlib

# Initialize app
app = FastAPI(
    title="AI Voice Detection API",
    description="Multilingual AI vs Human Voice Classification",
    version="1.0.0"
)

# API Key authentication
API_KEY_HEADER = APIKeyHeader(name="X-API-Key")
VALID_API_KEYS = {"demo_key_12345"}  # In production, use secure storage

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Request/Response Models
class VoiceDetectionRequest(BaseModel):
    audio_base64: str = Field(..., description="Base64-encoded MP3 audio")
    language: Literal["tamil", "english", "hindi", "malayalam", "telugu"] = Field(
        ..., description="Language of the audio sample"
    )
    
    @validator('audio_base64')
    def validate_base64(cls, v):
        try:
            base64.b64decode(v)
            return v
        except Exception:
            raise ValueError("Invalid base64 encoding")


class VoiceDetectionResponse(BaseModel):
    prediction: Literal["AI_GENERATED", "HUMAN"]
    confidence: float = Field(..., ge=0.0, le=1.0)
    language: str
    processing_time_ms: float
    timestamp: str
    audio_duration_seconds: float
    model_version: str = "1.0.0"
    

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str


# Authentication
async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    if api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=403,
            detail="Invalid API Key"
        )
    return api_key


# Feature Extraction Functions
class AudioFeatureExtractor:
    """Extract features for AI/Human classification"""
    
    @staticmethod
    def extract_mfcc_features(audio, sr):
        """Extract MFCC features"""
        mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=40)
        mfcc_mean = np.mean(mfccs, axis=1)
        mfcc_std = np.std(mfccs, axis=1)
        return np.concatenate([mfcc_mean, mfcc_std])
    
    @staticmethod
    def extract_prosodic_features(audio, sr):
        """Extract prosodic features (pitch, energy)"""
        # Pitch (F0)
        pitches, magnitudes = librosa.piptrack(y=audio, sr=sr)
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                pitch_values.append(pitch)
        
        pitch_mean = np.mean(pitch_values) if pitch_values else 0
        pitch_std = np.std(pitch_values) if pitch_values else 0
        
        # Energy
        energy = librosa.feature.rms(y=audio)[0]
        energy_mean = np.mean(energy)
        energy_std = np.std(energy)
        
        # Speaking rate (zero crossing rate)
        zcr = librosa.feature.zero_crossing_rate(audio)[0]
        zcr_mean = np.mean(zcr)
        
        return np.array([pitch_mean, pitch_std, energy_mean, energy_std, zcr_mean])
    
    @staticmethod
    def extract_spectral_features(audio, sr):
        """Extract spectral features"""
        spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)[0]
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=sr)[0]
        
        return np.array([
            np.mean(spectral_centroids),
            np.std(spectral_centroids),
            np.mean(spectral_rolloff),
            np.std(spectral_rolloff),
            np.mean(spectral_bandwidth),
            np.std(spectral_bandwidth)
        ])
    
    @staticmethod
    def extract_all_features(audio, sr):
        """Combine all features"""
        mfcc = AudioFeatureExtractor.extract_mfcc_features(audio, sr)
        prosody = AudioFeatureExtractor.extract_prosodic_features(audio, sr)
        spectral = AudioFeatureExtractor.extract_spectral_features(audio, sr)
        
        return np.concatenate([mfcc, prosody, spectral])


# Mock Classifier (Replace with trained model)
class VoiceClassifier:
    """AI/Human voice classifier"""
    
    def __init__(self):
        # In production, load actual trained models here
        self.model_loaded = True
        
    def predict(self, features, language):
        """
        Predict if voice is AI or Human
        
        In production, this would:
        1. Use language-specific models
        2. Employ ensemble voting
        3. Apply calibrated confidence scores
        """
        
        # MOCK IMPLEMENTATION
        # Replace with actual model inference
        
        # Simple heuristic for demo:
        # Check pitch variance and MFCC patterns
        pitch_variance = features[80] if len(features) > 80 else 0  # pitch_std
        mfcc_variance = np.std(features[:40])
        
        # AI voices typically have:
        # - Lower pitch variance
        # - More consistent MFCC patterns
        ai_score = 0.0
        
        if pitch_variance < 20:  # Low pitch variation
            ai_score += 0.3
        if mfcc_variance < 5:  # Consistent MFCCs
            ai_score += 0.3
        
        # Random component for demo (remove in production)
        import random
        ai_score += random.uniform(0, 0.4)
        
        # Determine prediction
        is_ai = ai_score > 0.5
        confidence = ai_score if is_ai else (1 - ai_score)
        
        prediction = "AI_GENERATED" if is_ai else "HUMAN"
        
        return prediction, confidence


# Initialize classifier
classifier = VoiceClassifier()
feature_extractor = AudioFeatureExtractor()


# API Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0"
    )


@app.post("/detect", response_model=VoiceDetectionResponse)
async def detect_voice(
    request: VoiceDetectionRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Detect if voice is AI-generated or human
    
    Args:
        audio_base64: Base64-encoded MP3 audio
        language: Language of audio (tamil/english/hindi/malayalam/telugu)
        
    Returns:
        prediction: AI_GENERATED or HUMAN
        confidence: Confidence score (0.0 to 1.0)
    """
    start_time = datetime.utcnow()
    
    try:
        # Decode base64 audio
        audio_bytes = base64.b64decode(request.audio_base64)
        
        # Load audio with librosa
        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=None)
        audio_duration = librosa.get_duration(y=audio, sr=sr)
        
        # Validate audio duration (1-60 seconds)
        if audio_duration < 1 or audio_duration > 60:
            raise HTTPException(
                status_code=400,
                detail=f"Audio duration must be between 1-60 seconds. Got {audio_duration:.2f}s"
            )
        
        # Extract features
        features = feature_extractor.extract_all_features(audio, sr)
        
        # Classify
        prediction, confidence = classifier.predict(features, request.language)
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Log request
        logger.info(f"Detection: {prediction} | Confidence: {confidence:.3f} | Language: {request.language}")
        
        return VoiceDetectionResponse(
            prediction=prediction,
            confidence=round(confidence, 3),
            language=request.language,
            processing_time_ms=round(processing_time, 2),
            timestamp=datetime.utcnow().isoformat(),
            audio_duration_seconds=round(audio_duration, 2),
            model_version="1.0.0"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing audio: {str(e)}"
        )


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "AI Voice Detection API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "detect": "/detect (POST)",
            "docs": "/docs"
        },
        "supported_languages": ["tamil", "english", "hindi", "malayalam", "telugu"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
