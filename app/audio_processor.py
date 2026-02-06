"""
Audio Processing Pipeline
Comprehensive feature extraction for AI/Human voice detection
"""

import numpy as np
import librosa
import io
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class AudioProcessor:
    """
    Complete audio processing pipeline with feature extraction
    Based on TECHNICAL_GUIDE specifications
    """
    
    def __init__(self, target_sr: int = 22050):
        self.target_sr = target_sr
        self.min_duration = 1.0
        self.max_duration = 60.0
    
    def preprocess(self, audio_bytes: bytes) -> Tuple[np.ndarray, int, float]:
        """
        Preprocess audio for feature extraction
        
        Returns:
            audio: Preprocessed audio array
            sr: Sample rate
            duration: Audio duration in seconds
        """
        # Load audio from bytes - librosa handles MP3, WAV, OGG, etc.
        audio, sr = librosa.load(
            io.BytesIO(audio_bytes),
            sr=self.target_sr,
            mono=True
        )
        
        # Calculate duration
        duration = librosa.get_duration(y=audio, sr=sr)
        
        # Validate duration
        if duration < self.min_duration:
            raise ValueError(f"Audio too short: {duration:.2f}s (min: {self.min_duration}s)")
        if duration > self.max_duration:
            raise ValueError(f"Audio too long: {duration:.2f}s (max: {self.max_duration}s)")
        
        # Normalize amplitude
        audio = librosa.util.normalize(audio)
        
        # Remove leading/trailing silence
        audio, _ = librosa.effects.trim(audio, top_db=30)
        
        return audio, sr, duration
    
    def extract_all_features(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """
        Extract comprehensive features for voice detection
        Total: ~113 features
        """
        features = []
        
        # 1. MFCC Features (80 features)
        mfcc_features = self._extract_mfcc_features(audio, sr)
        features.extend(mfcc_features)
        
        # 2. Spectral Features (10 features)
        spectral_features = self._extract_spectral_features(audio, sr)
        features.extend(spectral_features)
        
        # 3. Prosodic Features (6 features)
        prosodic_features = self._extract_prosodic_features(audio, sr)
        features.extend(prosodic_features)
        
        # 4. Voice Quality Features (3 features)
        voice_quality = self._extract_voice_quality_features(audio, sr)
        features.extend(voice_quality)
        
        # 5. Temporal Features (4 features)
        temporal_features = self._extract_temporal_features(audio, sr)
        features.extend(temporal_features)
        
        # 6. Chroma Features (24 features)
        chroma_features = self._extract_chroma_features(audio, sr)
        features.extend(chroma_features)
        
        return np.array(features, dtype=np.float32)
    
    def _extract_mfcc_features(self, audio: np.ndarray, sr: int) -> list:
        """
        Extract MFCC features (80 features)
        - 40 MFCC coefficients (mean)
        - 40 MFCC coefficients (std)
        """
        mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=40)
        
        mfcc_mean = np.mean(mfccs, axis=1)
        mfcc_std = np.std(mfccs, axis=1)
        
        return list(np.concatenate([mfcc_mean, mfcc_std]))
    
    def _extract_spectral_features(self, audio: np.ndarray, sr: int) -> list:
        """
        Extract spectral features (10 features)
        - Spectral centroid (mean, std)
        - Spectral rolloff (mean, std) 
        - Spectral bandwidth (mean, std)
        - Spectral contrast (mean, std)
        - Spectral flatness (mean, std)
        """
        # Spectral Centroid
        centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
        
        # Spectral Rolloff
        rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)[0]
        
        # Spectral Bandwidth
        bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=sr)[0]
        
        # Spectral Contrast
        contrast = librosa.feature.spectral_contrast(y=audio, sr=sr)
        
        # Spectral Flatness
        flatness = librosa.feature.spectral_flatness(y=audio)[0]
        
        return [
            np.mean(centroid), np.std(centroid),
            np.mean(rolloff), np.std(rolloff),
            np.mean(bandwidth), np.std(bandwidth),
            np.mean(contrast), np.std(contrast),
            np.mean(flatness), np.std(flatness)
        ]
    
    def _extract_prosodic_features(self, audio: np.ndarray, sr: int) -> list:
        """
        Extract prosodic features (6 features)
        - Pitch (mean, std, range)
        - Energy (mean, std)
        - Zero-crossing rate (mean)
        """
        # Pitch extraction using piptrack
        pitches, magnitudes = librosa.piptrack(y=audio, sr=sr)
        
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                pitch_values.append(pitch)
        
        if pitch_values:
            pitch_mean = np.mean(pitch_values)
            pitch_std = np.std(pitch_values)
            pitch_range = np.ptp(pitch_values)
        else:
            pitch_mean = pitch_std = pitch_range = 0.0
        
        # Energy/RMS
        rms = librosa.feature.rms(y=audio)[0]
        energy_mean = np.mean(rms)
        energy_std = np.std(rms)
        
        # Zero-crossing rate
        zcr = librosa.feature.zero_crossing_rate(audio)[0]
        zcr_mean = np.mean(zcr)
        
        return [pitch_mean, pitch_std, pitch_range, energy_mean, energy_std, zcr_mean]
    
    def _extract_voice_quality_features(self, audio: np.ndarray, sr: int) -> list:
        """
        Extract voice quality features (3 features)
        - Jitter (pitch perturbation)
        - Shimmer (amplitude perturbation)
        - Harmonic-to-Noise Ratio (HNR)
        """
        # Jitter approximation
        pitches, magnitudes = librosa.piptrack(y=audio, sr=sr)
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                pitch_values.append(pitch)
        
        if len(pitch_values) > 1:
            pitch_values = np.array(pitch_values)
            jitter = np.mean(np.abs(np.diff(pitch_values)) / (pitch_values[:-1] + 1e-10))
        else:
            jitter = 0.0
        
        # Shimmer approximation
        rms = librosa.feature.rms(y=audio)[0]
        if len(rms) > 1:
            shimmer = np.mean(np.abs(np.diff(rms)) / (rms[:-1] + 1e-10))
        else:
            shimmer = 0.0
        
        # Harmonic-to-Noise Ratio
        harmonic, percussive = librosa.effects.hpss(audio)
        hnr = 10 * np.log10(
            (np.sum(harmonic**2) + 1e-10) / (np.sum(percussive**2) + 1e-10)
        )
        
        return [jitter, shimmer, hnr]
    
    def _extract_temporal_features(self, audio: np.ndarray, sr: int) -> list:
        """
        Extract temporal features (4 features)
        - Silence ratio
        - Average pause duration
        - Onset strength (mean, std)
        """
        # Speech/silence intervals
        intervals = librosa.effects.split(audio, top_db=30)
        
        if len(intervals) > 0:
            speech_duration = sum([end - start for start, end in intervals])
            silence_ratio = 1 - (speech_duration / len(audio))
            
            # Average pause duration
            if len(intervals) > 1:
                pauses = [intervals[i+1][0] - intervals[i][1] 
                         for i in range(len(intervals)-1)]
                avg_pause = np.mean(pauses) / sr if pauses else 0.0
            else:
                avg_pause = 0.0
        else:
            silence_ratio = 1.0
            avg_pause = 0.0
        
        # Onset strength (rhythm)
        onset_env = librosa.onset.onset_strength(y=audio, sr=sr)
        onset_mean = np.mean(onset_env)
        onset_std = np.std(onset_env)
        
        return [silence_ratio, avg_pause, onset_mean, onset_std]
    
    def _extract_chroma_features(self, audio: np.ndarray, sr: int) -> list:
        """
        Extract chroma features (24 features)
        - 12 chroma bins (mean)
        - 12 chroma bins (std)
        """
        chroma = librosa.feature.chroma_stft(y=audio, sr=sr)
        
        chroma_mean = np.mean(chroma, axis=1)
        chroma_std = np.std(chroma, axis=1)
        
        return list(np.concatenate([chroma_mean, chroma_std]))


# Singleton instance
audio_processor = AudioProcessor()
