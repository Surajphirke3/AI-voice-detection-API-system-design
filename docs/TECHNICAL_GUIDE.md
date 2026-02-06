# 🔧 Technical Implementation Guide

## 📋 SYSTEM ARCHITECTURE

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│  (Web Apps, Mobile Apps, Third-party Integrations)          │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     API Gateway (Nginx)                      │
│              (Load Balancing, SSL, Rate Limiting)            │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  FastAPI      │   │  FastAPI      │   │  FastAPI      │
│  Instance 1   │   │  Instance 2   │   │  Instance 3   │
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   Redis       │   │  PostgreSQL   │   │   S3/Object   │
│  (Caching)    │   │  (Logs/Data)  │   │   Storage     │
└───────────────┘   └───────────────┘   └───────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │  ML Model Service     │
                │  (Inference Server)   │
                └───────────────────────┘
```

---

## 🛠️ DETAILED COMPONENT DESIGN

### 1. Audio Processing Pipeline

```python
class AudioProcessor:
    """
    Complete audio processing pipeline
    """
    
    def __init__(self, target_sr=22050):
        self.target_sr = target_sr
        self.min_duration = 1.0  # seconds
        self.max_duration = 60.0  # seconds
    
    def preprocess(self, audio_bytes: bytes) -> Tuple[np.ndarray, int]:
        """
        Preprocess audio for feature extraction
        
        Steps:
        1. Decode MP3 to raw audio
        2. Convert to mono if stereo
        3. Resample to target sample rate
        4. Normalize amplitude
        5. Remove silence (optional)
        6. Validate duration
        """
        # Load audio from bytes
        audio, sr = librosa.load(
            io.BytesIO(audio_bytes),
            sr=self.target_sr,
            mono=True
        )
        
        # Validate duration
        duration = librosa.get_duration(y=audio, sr=sr)
        if duration < self.min_duration or duration > self.max_duration:
            raise ValueError(f"Audio duration {duration:.2f}s out of range")
        
        # Normalize amplitude (-1 to 1)
        audio = librosa.util.normalize(audio)
        
        # Optional: Remove leading/trailing silence
        audio, _ = librosa.effects.trim(audio, top_db=30)
        
        return audio, sr
    
    def extract_features(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """
        Extract all features for detection
        """
        features = []
        
        # 1. Spectral features
        features.extend(self._spectral_features(audio, sr))
        
        # 2. MFCC features
        features.extend(self._mfcc_features(audio, sr))
        
        # 3. Prosodic features
        features.extend(self._prosodic_features(audio, sr))
        
        # 4. Voice quality features
        features.extend(self._voice_quality_features(audio, sr))
        
        # 5. Temporal features
        features.extend(self._temporal_features(audio, sr))
        
        return np.array(features)
    
    def _spectral_features(self, audio, sr):
        """Spectral characteristics"""
        # Spectral centroid
        centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
        
        # Spectral rolloff
        rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)[0]
        
        # Spectral bandwidth
        bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=sr)[0]
        
        # Spectral contrast
        contrast = librosa.feature.spectral_contrast(y=audio, sr=sr)
        
        # Spectral flatness
        flatness = librosa.feature.spectral_flatness(y=audio)[0]
        
        return [
            np.mean(centroid), np.std(centroid),
            np.mean(rolloff), np.std(rolloff),
            np.mean(bandwidth), np.std(bandwidth),
            np.mean(contrast), np.std(contrast),
            np.mean(flatness), np.std(flatness)
        ]
    
    def _mfcc_features(self, audio, sr):
        """Mel-frequency cepstral coefficients"""
        mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=40)
        
        # Statistics across time
        mfcc_mean = np.mean(mfccs, axis=1)
        mfcc_std = np.std(mfccs, axis=1)
        mfcc_delta = np.mean(librosa.feature.delta(mfccs), axis=1)
        
        return np.concatenate([mfcc_mean, mfcc_std, mfcc_delta])
    
    def _prosodic_features(self, audio, sr):
        """Pitch, energy, and rhythm"""
        # Fundamental frequency (F0) using PYIN algorithm
        f0, voiced_flag, voiced_probs = librosa.pyin(
            audio,
            fmin=librosa.note_to_hz('C2'),
            fmax=librosa.note_to_hz('C7'),
            sr=sr
        )
        
        # Filter out unvoiced frames
        f0_voiced = f0[voiced_flag]
        
        if len(f0_voiced) > 0:
            pitch_mean = np.mean(f0_voiced)
            pitch_std = np.std(f0_voiced)
            pitch_range = np.ptp(f0_voiced)
        else:
            pitch_mean = pitch_std = pitch_range = 0
        
        # Energy/RMS
        rms = librosa.feature.rms(y=audio)[0]
        energy_mean = np.mean(rms)
        energy_std = np.std(rms)
        
        # Zero-crossing rate (correlates with speaking rate)
        zcr = librosa.feature.zero_crossing_rate(audio)[0]
        zcr_mean = np.mean(zcr)
        
        return [
            pitch_mean, pitch_std, pitch_range,
            energy_mean, energy_std,
            zcr_mean
        ]
    
    def _voice_quality_features(self, audio, sr):
        """Jitter, shimmer, HNR"""
        # Jitter (pitch perturbation)
        f0, _, _ = librosa.pyin(audio, fmin=50, fmax=400, sr=sr)
        f0_clean = f0[~np.isnan(f0)]
        
        if len(f0_clean) > 1:
            jitter = np.mean(np.abs(np.diff(f0_clean)) / f0_clean[:-1])
        else:
            jitter = 0
        
        # Shimmer (amplitude perturbation)
        rms = librosa.feature.rms(y=audio)[0]
        if len(rms) > 1:
            shimmer = np.mean(np.abs(np.diff(rms)) / rms[:-1])
        else:
            shimmer = 0
        
        # Harmonic-to-Noise Ratio (HNR)
        harmonic, percussive = librosa.effects.hpss(audio)
        hnr = 10 * np.log10(
            np.sum(harmonic**2) / (np.sum(percussive**2) + 1e-10)
        )
        
        return [jitter, shimmer, hnr]
    
    def _temporal_features(self, audio, sr):
        """Timing and rhythm patterns"""
        # Speech/silence ratio
        intervals = librosa.effects.split(audio, top_db=30)
        
        if len(intervals) > 0:
            speech_duration = sum([end - start for start, end in intervals])
            silence_ratio = 1 - (speech_duration / len(audio))
            
            # Average pause duration
            if len(intervals) > 1:
                pauses = [intervals[i+1][0] - intervals[i][1] 
                         for i in range(len(intervals)-1)]
                avg_pause = np.mean(pauses) / sr if pauses else 0
            else:
                avg_pause = 0
        else:
            silence_ratio = 1.0
            avg_pause = 0
        
        # Onset strength (speech rhythm)
        onset_env = librosa.onset.onset_strength(y=audio, sr=sr)
        onset_mean = np.mean(onset_env)
        onset_std = np.std(onset_env)
        
        return [silence_ratio, avg_pause, onset_mean, onset_std]
```

---

### 2. Model Architecture

#### Ensemble Classifier Design

```python
class DetectionEnsemble:
    """
    Multi-model ensemble for robust detection
    """
    
    def __init__(self):
        self.models = {}
        self.weights = {}
        self.scaler = StandardScaler()
        
    def build_models(self):
        """
        Initialize all models in the ensemble
        """
        # Model 1: Random Forest (captures complex interactions)
        self.models['rf'] = RandomForestClassifier(
            n_estimators=200,
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',
            bootstrap=True,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        )
        
        # Model 2: Gradient Boosting (sequential learning)
        self.models['gbm'] = GradientBoostingClassifier(
            n_estimators=150,
            learning_rate=0.1,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            subsample=0.8,
            max_features='sqrt',
            random_state=42
        )
        
        # Model 3: SVM (margin-based classification)
        self.models['svm'] = SVC(
            kernel='rbf',
            C=10.0,
            gamma='scale',
            class_weight='balanced',
            probability=True,
            random_state=42
        )
        
        # Model 4: XGBoost (high performance)
        self.models['xgb'] = xgb.XGBClassifier(
            n_estimators=150,
            max_depth=10,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=1,
            random_state=42
        )
        
        # Initial equal weights
        self.weights = {name: 0.25 for name in self.models.keys()}
```

#### Deep Learning Model (Future Enhancement)

```python
class CNNVoiceDetector(nn.Module):
    """
    CNN-based detector for spectrogram analysis
    """
    
    def __init__(self):
        super().__init__()
        
        # Convolutional layers
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        
        # Batch normalization
        self.bn1 = nn.BatchNorm2d(32)
        self.bn2 = nn.BatchNorm2d(64)
        self.bn3 = nn.BatchNorm2d(128)
        
        # Pooling
        self.pool = nn.MaxPool2d(2, 2)
        
        # Dropout for regularization
        self.dropout = nn.Dropout(0.5)
        
        # Fully connected layers
        self.fc1 = nn.Linear(128 * 16 * 16, 512)
        self.fc2 = nn.Linear(512, 128)
        self.fc3 = nn.Linear(128, 2)  # Binary: AI vs Human
        
    def forward(self, x):
        # Conv block 1
        x = self.pool(F.relu(self.bn1(self.conv1(x))))
        
        # Conv block 2
        x = self.pool(F.relu(self.bn2(self.conv2(x))))
        
        # Conv block 3
        x = self.pool(F.relu(self.bn3(self.conv3(x))))
        
        # Flatten
        x = x.view(-1, 128 * 16 * 16)
        
        # FC layers
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        
        return x
```

---

### 3. API Design Patterns

#### Request Validation

```python
class AudioValidator:
    """Validate audio input"""
    
    @staticmethod
    def validate_base64(data: str) -> bool:
        """Check if valid base64"""
        try:
            decoded = base64.b64decode(data)
            return len(decoded) > 0
        except:
            return False
    
    @staticmethod
    def validate_audio_format(audio_bytes: bytes) -> bool:
        """Check if valid MP3"""
        # Check MP3 header
        if audio_bytes[:3] == b'ID3' or audio_bytes[:2] == b'\xff\xfb':
            return True
        return False
    
    @staticmethod
    def validate_file_size(audio_bytes: bytes, max_mb: int = 10) -> bool:
        """Check file size"""
        return len(audio_bytes) <= max_mb * 1024 * 1024
```

#### Response Caching

```python
class ResponseCache:
    """Cache detection results"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl = 3600  # 1 hour
    
    def get_cached_result(self, audio_hash: str) -> Optional[dict]:
        """Retrieve cached result"""
        cached = self.redis.get(f"detection:{audio_hash}")
        if cached:
            return json.loads(cached)
        return None
    
    def cache_result(self, audio_hash: str, result: dict):
        """Store result in cache"""
        self.redis.setex(
            f"detection:{audio_hash}",
            self.ttl,
            json.dumps(result)
        )
    
    @staticmethod
    def compute_hash(audio_bytes: bytes) -> str:
        """Compute SHA-256 hash of audio"""
        return hashlib.sha256(audio_bytes).hexdigest()
```

---

### 4. Database Schema

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    api_key VARCHAR(64) UNIQUE NOT NULL,
    tier VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- API usage tracking
CREATE TABLE api_calls (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    endpoint VARCHAR(100),
    language VARCHAR(50),
    prediction VARCHAR(20),
    confidence FLOAT,
    processing_time_ms FLOAT,
    audio_duration_s FLOAT,
    timestamp TIMESTAMP DEFAULT NOW(),
    audio_hash VARCHAR(64),
    INDEX idx_user_timestamp (user_id, timestamp),
    INDEX idx_timestamp (timestamp)
);

-- Rate limiting
CREATE TABLE rate_limits (
    user_id UUID PRIMARY KEY REFERENCES users(id),
    calls_this_minute INT DEFAULT 0,
    calls_this_hour INT DEFAULT 0,
    calls_this_day INT DEFAULT 0,
    minute_reset TIMESTAMP,
    hour_reset TIMESTAMP,
    day_reset TIMESTAMP
);

-- Analytics aggregations
CREATE TABLE daily_stats (
    date DATE PRIMARY KEY,
    total_calls INT,
    ai_detected INT,
    human_detected INT,
    avg_confidence FLOAT,
    avg_processing_time_ms FLOAT,
    by_language JSONB
);
```

---

### 5. Deployment Configuration

#### Docker Compose

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://user:pass@postgres:5432/voicedb
    depends_on:
      - redis
      - postgres
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
  
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: voicedb
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api

volumes:
  redis_data:
  postgres_data:
```

---

### 6. Monitoring & Observability

```python
from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics
api_requests_total = Counter(
    'api_requests_total',
    'Total API requests',
    ['endpoint', 'method', 'status']
)

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['endpoint']
)

detection_confidence = Histogram(
    'detection_confidence',
    'Detection confidence scores',
    ['prediction', 'language']
)

active_users = Gauge(
    'active_users',
    'Number of active users'
)

# Middleware
@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    api_requests_total.labels(
        endpoint=request.url.path,
        method=request.method,
        status=response.status_code
    ).inc()
    
    api_request_duration.labels(
        endpoint=request.url.path
    ).observe(duration)
    
    return response
```

---

This technical implementation provides a solid foundation for building a production-ready AI voice detection system. Each component is designed for scalability, reliability, and maintainability.
