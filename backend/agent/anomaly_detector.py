"""
Anomaly Detection Engine
Uses Isolation Forest (unsupervised ML) for statistical anomaly detection,
combined with rule-based heuristics for known IoT attack patterns.
The ML model is trained on normal traffic features and flags deviations.
"""

import logging
import numpy as np
from datetime import datetime
from typing import Optional
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os

logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "isolation_forest.joblib")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "models", "scaler.joblib")

# Known IoT attack signatures (rule-based detection layer)
ATTACK_SIGNATURES = [
    {
        "name": "Port Scan",
        "description": "Device is scanning multiple ports — typical reconnaissance behaviour",
        "condition": lambda f: f.get("unique_dest_ports", 0) > 15,
        "severity": "high",
        "attack_type": "reconnaissance",
        "mitre_tactic": "TA0043 - Reconnaissance",
    },
    {
        "name": "Botnet C2 Beacon",
        "description": "Extremely regular periodic connections suggest C2 heartbeat",
        "condition": lambda f: f.get("connection_regularity", 0) > 0.95 and f.get("connection_count", 0) > 20,
        "severity": "critical",
        "attack_type": "c2_communication",
        "mitre_tactic": "TA0011 - Command and Control",
    },
    {
        "name": "Data Exfiltration",
        "description": "Abnormally high outbound traffic to unknown destination",
        "condition": lambda f: (
            f.get("bytes_transferred", 0) > f.get("max_bytes_per_minute", 1) * 3
            and f.get("outbound_ratio", 0) > 0.9
        ),
        "severity": "critical",
        "attack_type": "exfiltration",
        "mitre_tactic": "TA0010 - Exfiltration",
    },
    {
        "name": "Credential Brute Force",
        "description": "Repeated failed connection attempts to common service ports",
        "condition": lambda f: (
            f.get("failed_connections", 0) > 10
            and any(p in f.get("dest_ports", []) for p in [22, 23, 80, 443, 8080])
        ),
        "severity": "high",
        "attack_type": "brute_force",
        "mitre_tactic": "TA0006 - Credential Access",
    },
    {
        "name": "DNS Tunnelling",
        "description": "Unusually high DNS query volume — possible covert channel",
        "condition": lambda f: f.get("dns_query_count", 0) > 100 and f.get("avg_dns_payload_size", 0) > 150,
        "severity": "high",
        "attack_type": "dns_tunnelling",
        "mitre_tactic": "TA0011 - Command and Control",
    },
    {
        "name": "Lateral Movement",
        "description": "Device communicating with other internal network devices abnormally",
        "condition": lambda f: f.get("internal_connections", 0) > 20 and f.get("unique_internal_ips", 0) > 5,
        "severity": "critical",
        "attack_type": "lateral_movement",
        "mitre_tactic": "TA0008 - Lateral Movement",
    },
    {
        "name": "Firmware Injection Attempt",
        "description": "Inbound connection on management port from external IP",
        "condition": lambda f: (
            f.get("inbound_mgmt_connections", 0) > 0
            and not f.get("source_is_local", True)
        ),
        "severity": "critical",
        "attack_type": "firmware_attack",
        "mitre_tactic": "TA0001 - Initial Access",
    },
]


class AnomalyDetector:
    """
    Two-layer anomaly detection:
    1. Isolation Forest ML model for statistical outlier detection
    2. Rule-based signature matching for known attack patterns
    """

    def __init__(self):
        self.model: Optional[IsolationForest] = None
        self.scaler: Optional[StandardScaler] = None
        self._training_buffer: list = []
        self.MIN_TRAINING_SAMPLES = 30
        self.is_trained = False
        self._load_or_initialise_model()

    def _load_or_initialise_model(self) -> None:
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
                self.scaler = joblib.load(SCALER_PATH)
                self.is_trained = True
                logger.info("Loaded pre-trained Isolation Forest model")
                return
            except Exception as e:
                logger.warning(f"Could not load saved model: {e}")

        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42,
            n_jobs=-1,
        )
        self.scaler = StandardScaler()
        logger.info("Initialised new Isolation Forest model (awaiting training data)")

    def _extract_features(self, traffic_sample: dict) -> list[float]:
        """Extract numerical features from a traffic sample."""
        return [
            float(traffic_sample.get("bytes_transferred", 0)),
            float(traffic_sample.get("connection_count", 0)),
            float(traffic_sample.get("unique_dest_ips", 1)),
            float(traffic_sample.get("unique_dest_ports", 1)),
            float(traffic_sample.get("avg_packet_size", 500)),
            float(traffic_sample.get("outbound_ratio", 0.5)),
            float(traffic_sample.get("dns_query_count", 0)),
            float(traffic_sample.get("failed_connections", 0)),
            float(traffic_sample.get("internal_connections", 0)),
            float(datetime.now().hour),
        ]

    def train(self, normal_samples: list[dict]) -> None:
        """Train (or retrain) the model on normal traffic samples."""
        if len(normal_samples) < self.MIN_TRAINING_SAMPLES:
            logger.warning(f"Insufficient training samples: {len(normal_samples)}")
            return

        features = np.array([self._extract_features(s) for s in normal_samples])
        self.scaler.fit(features)
        features_scaled = self.scaler.transform(features)
        self.model.fit(features_scaled)
        self.is_trained = True

        try:
            joblib.dump(self.model, MODEL_PATH)
            joblib.dump(self.scaler, SCALER_PATH)
            logger.info(f"Model trained on {len(normal_samples)} samples and saved")
        except Exception as e:
            logger.warning(f"Could not save model: {e}")

    def add_training_sample(self, traffic_sample: dict) -> None:
        """Buffer a normal traffic sample for future training."""
        self._training_buffer.append(traffic_sample)
        if len(self._training_buffer) >= self.MIN_TRAINING_SAMPLES and not self.is_trained:
            self.train(self._training_buffer)

    def detect(self, traffic_sample: dict, baseline_score: dict) -> dict:
        """
        Run full detection pipeline on a traffic sample.
        Returns comprehensive detection result with severity and details.
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "device_id": traffic_sample.get("device_id", "unknown"),
            "ml_anomaly": False,
            "ml_score": 0.0,
            "rule_matches": [],
            "baseline_anomaly": baseline_score.get("is_anomalous", False),
            "baseline_score": baseline_score.get("composite_score", 0.0),
            "is_threat": False,
            "severity": "low",
            "attack_types": [],
            "description": "Normal traffic pattern",
            "recommended_action": "monitor",
        }

        # Layer 1: ML-based detection
        if self.is_trained:
            try:
                features = np.array([self._extract_features(traffic_sample)])
                features_scaled = self.scaler.transform(features)
                prediction = self.model.predict(features_scaled)[0]
                score = self.model.score_samples(features_scaled)[0]
                # Isolation Forest: -1 = anomaly, 1 = normal; score closer to -1 = more anomalous
                normalised_score = max(0.0, min(1.0, (-score + 0.5) * 2))
                result["ml_anomaly"] = prediction == -1
                result["ml_score"] = round(normalised_score, 4)
            except Exception as e:
                logger.warning(f"ML detection failed: {e}")
        else:
            self.add_training_sample(traffic_sample)

        # Layer 2: Rule-based signature matching
        for sig in ATTACK_SIGNATURES:
            try:
                if sig["condition"](traffic_sample):
                    result["rule_matches"].append({
                        "name": sig["name"],
                        "description": sig["description"],
                        "severity": sig["severity"],
                        "attack_type": sig["attack_type"],
                        "mitre_tactic": sig["mitre_tactic"],
                    })
                    result["attack_types"].append(sig["attack_type"])
            except Exception:
                pass

        # Combine results to determine final threat assessment
        has_critical_rule = any(m["severity"] == "critical" for m in result["rule_matches"])
        has_high_rule = any(m["severity"] == "high" for m in result["rule_matches"])
        high_baseline = result["baseline_score"] >= 0.55
        ml_anomaly = result["ml_anomaly"] and result["ml_score"] > 0.6

        if has_critical_rule or (ml_anomaly and high_baseline):
            result["is_threat"] = True
            result["severity"] = "critical"
            result["recommended_action"] = "isolate"
        elif has_high_rule or (result["baseline_score"] >= 0.75):
            result["is_threat"] = True
            result["severity"] = "high"
            result["recommended_action"] = "block_traffic"
        elif result["baseline_anomaly"] or ml_anomaly:
            result["is_threat"] = True
            result["severity"] = "medium"
            result["recommended_action"] = "alert"
        else:
            result["is_threat"] = False
            result["severity"] = "low"
            result["recommended_action"] = "monitor"

        if result["rule_matches"]:
            primary = result["rule_matches"][0]
            result["description"] = primary["description"]
        elif result["baseline_anomaly"]:
            details = baseline_score.get("anomaly_details", [])
            result["description"] = details[0] if details else "Statistical deviation from learned baseline"

        return result


# Singleton
anomaly_detector = AnomalyDetector()
