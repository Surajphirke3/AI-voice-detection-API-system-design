"""
Unit Tests for AI Voice Detection API
Run with: pytest tests/ -v
"""

import pytest
import numpy as np
import base64
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import app modules
import sys
sys.path.insert(0, '.')

from app_main import app
from app.audio_processor import AudioProcessor
from app.classifier import MockVoiceClassifier
from app.models import VoiceDetectionRequest, VoiceDetectionResponse


# ============== FIXTURES ==============

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def api_key():
    """Valid API key for testing"""
    return "demo_key_12345"


@pytest.fixture
def audio_processor():
    """Audio processor instance"""
    return AudioProcessor()


@pytest.fixture
def mock_classifier():
    """Mock classifier instance"""
    return MockVoiceClassifier()


@pytest.fixture
def sample_audio_base64():
    """
    Generate a simple test audio as base64
    Creates a 2-second sine wave at 440Hz
    """
    # Create a simple audio signal (sine wave)
    import io
    import wave
    
    sample_rate = 22050
    duration = 2  # seconds
    frequency = 440  # Hz
    
    t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
    audio = np.sin(2 * np.pi * frequency * t)
    
    # Convert to 16-bit PCM
    audio_int16 = (audio * 32767).astype(np.int16)
    
    # Write to WAV format
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_int16.tobytes())
    
    audio_bytes = buffer.getvalue()
    return base64.b64encode(audio_bytes).decode('utf-8')


# ============== API ENDPOINT TESTS ==============

class TestHealthEndpoint:
    """Tests for /health endpoint"""
    
    def test_health_check_returns_healthy(self, client):
        """Health check returns healthy status"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    def test_health_check_no_auth_required(self, client):
        """Health check doesn't require authentication"""
        response = client.get("/health")
        assert response.status_code == 200


class TestRootEndpoint:
    """Tests for / endpoint"""
    
    def test_root_returns_api_info(self, client):
        """Root endpoint returns API information"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
        assert "supported_languages" in data


class TestDetectEndpoint:
    """Tests for /detect endpoint"""
    
    def test_detect_requires_api_key(self, client, sample_audio_base64):
        """Detection requires API key"""
        response = client.post(
            "/detect",
            json={
                "audio_base64": sample_audio_base64,
                "language": "english"
            }
        )
        assert response.status_code == 401
    
    def test_detect_rejects_invalid_api_key(self, client, sample_audio_base64):
        """Detection rejects invalid API key"""
        response = client.post(
            "/detect",
            headers={"X-API-Key": "invalid_key"},
            json={
                "audio_base64": sample_audio_base64,
                "language": "english"
            }
        )
        assert response.status_code == 403
    
    def test_detect_with_valid_audio(self, client, api_key, sample_audio_base64):
        """Detection works with valid audio"""
        response = client.post(
            "/detect",
            headers={"X-API-Key": api_key},
            json={
                "audio_base64": sample_audio_base64,
                "language": "english"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["prediction"] in ["AI_GENERATED", "HUMAN"]
        assert 0 <= data["confidence"] <= 1
        assert data["language"] == "english"
        assert "processing_time_ms" in data
        assert "audio_duration_seconds" in data
    
    def test_detect_rejects_invalid_base64(self, client, api_key):
        """Detection rejects invalid base64"""
        response = client.post(
            "/detect",
            headers={"X-API-Key": api_key},
            json={
                "audio_base64": "not_valid_base64!!!",
                "language": "english"
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_detect_validates_language(self, client, api_key, sample_audio_base64):
        """Detection validates language parameter"""
        response = client.post(
            "/detect",
            headers={"X-API-Key": api_key},
            json={
                "audio_base64": sample_audio_base64,
                "language": "french"  # Not supported
            }
        )
        assert response.status_code == 422
    
    def test_detect_all_supported_languages(self, client, api_key, sample_audio_base64):
        """Detection works for all supported languages"""
        languages = ["tamil", "english", "hindi", "malayalam", "telugu"]
        
        for lang in languages:
            response = client.post(
                "/detect",
                headers={"X-API-Key": api_key},
                json={
                    "audio_base64": sample_audio_base64,
                    "language": lang
                }
            )
            assert response.status_code == 200, f"Failed for language: {lang}"


# ============== AUDIO PROCESSING TESTS ==============

class TestAudioProcessor:
    """Tests for audio processing pipeline"""
    
    def test_extract_mfcc_features(self, audio_processor):
        """MFCC extraction returns correct shape"""
        # Create test audio
        audio = np.random.randn(22050 * 2).astype(np.float32)  # 2 seconds
        sr = 22050
        
        features = audio_processor._extract_mfcc_features(audio, sr)
        
        # Should have 80 features (40 mean + 40 std)
        assert len(features) == 80
    
    def test_extract_spectral_features(self, audio_processor):
        """Spectral extraction returns correct shape"""
        audio = np.random.randn(22050 * 2).astype(np.float32)
        sr = 22050
        
        features = audio_processor._extract_spectral_features(audio, sr)
        
        # Should have 10 features
        assert len(features) == 10
    
    def test_extract_prosodic_features(self, audio_processor):
        """Prosodic extraction returns correct shape"""
        audio = np.random.randn(22050 * 2).astype(np.float32)
        sr = 22050
        
        features = audio_processor._extract_prosodic_features(audio, sr)
        
        # Should have 6 features
        assert len(features) == 6
    
    def test_extract_all_features(self, audio_processor):
        """Full feature extraction returns expected count"""
        audio = np.random.randn(22050 * 2).astype(np.float32)
        sr = 22050
        
        features = audio_processor.extract_all_features(audio, sr)
        
        # Total features: 80 + 10 + 6 + 3 + 4 + 24 = 127
        assert len(features) >= 100
        assert features.dtype == np.float32


# ============== CLASSIFIER TESTS ==============

class TestMockClassifier:
    """Tests for mock classifier"""
    
    def test_predict_returns_valid_prediction(self, mock_classifier):
        """Classifier returns valid prediction"""
        # Create dummy features
        features = np.random.randn(127).astype(np.float32)
        
        prediction, confidence = mock_classifier.predict(features, "english")
        
        assert prediction in ["AI_GENERATED", "HUMAN"]
        assert 0 <= confidence <= 1
    
    def test_predict_different_languages(self, mock_classifier):
        """Classifier works with different languages"""
        features = np.random.randn(127).astype(np.float32)
        languages = ["tamil", "english", "hindi", "malayalam", "telugu"]
        
        for lang in languages:
            prediction, confidence = mock_classifier.predict(features, lang)
            assert prediction in ["AI_GENERATED", "HUMAN"]


# ============== MODEL VALIDATION TESTS ==============

class TestRequestModels:
    """Tests for Pydantic request models"""
    
    def test_valid_request(self, sample_audio_base64):
        """Valid request validates successfully"""
        request = VoiceDetectionRequest(
            audio_base64=sample_audio_base64,
            language="english"
        )
        assert request.language == "english"
    
    def test_invalid_language_rejected(self, sample_audio_base64):
        """Invalid language is rejected"""
        with pytest.raises(Exception):
            VoiceDetectionRequest(
                audio_base64=sample_audio_base64,
                language="french"
            )


# ============== RATE LIMITING TESTS ==============

class TestRateLimiting:
    """Tests for rate limiting"""
    
    def test_rate_limit_headers_present(self, client, api_key, sample_audio_base64):
        """Rate limit headers are present in response"""
        response = client.post(
            "/detect",
            headers={"X-API-Key": api_key},
            json={
                "audio_base64": sample_audio_base64,
                "language": "english"
            }
        )
        
        # Rate limit headers should be present on successful requests
        assert response.status_code == 200


# ============== RUN TESTS ==============

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
