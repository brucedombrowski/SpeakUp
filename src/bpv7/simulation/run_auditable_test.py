#!/usr/bin/env python3
"""
Auditable DTN Transfer Test with OQE Artifacts

Produces verifiable, auditable evidence of DTN protocol operation:
- Timestamped log files
- SHA-256 checksums of all artifacts
- Transfer statistics JSON
- Test manifest for reproducibility

Usage:
    python3 run_auditable_test.py [--duration HOURS] [--output-dir DIR]

Outputs:
    output_dir/
    ├── test-manifest.json       # Test configuration and parameters
    ├── test-log.txt             # Complete timestamped log
    ├── transfer-stats.json      # Statistics and metrics
    ├── payload-sent.bin         # Original payload (for verification)
    ├── payload-received.bin     # Received payload
    ├── checksums.sha256         # SHA-256 of all artifacts
    └── test-summary.txt         # Human-readable summary
"""

import sys
import os
import time
import json
import hashlib
import argparse
import threading
import signal
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from bpv7 import Bundle, EndpointID
from bpv7.agent.tcpcl import TCPConvergenceLayer

PORT = 4558


class LinkState(Enum):
    AOS = "AOS"
    LOS = "LOS"


@dataclass
class TestConfig:
    """Test configuration - recorded for reproducibility."""
    test_id: str
    start_time: str
    duration_hours: float
    data_rate_bps: int
    segment_size: int
    payload_size: int
    payload_sha256: str
    hostname: str
    python_version: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TransferStats:
    """Transfer statistics - updated during test."""
    bytes_sent: int = 0
    bytes_received: int = 0
    segments_sent: int = 0
    segments_received: int = 0
    los_events: int = 0
    aos_events: int = 0
    errors: int = 0
    start_time: Optional[str] = None
    end_time: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AuditableLogger:
    """Logger that writes to both console and file with timestamps."""

    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_file = open(log_path, 'w')
        self._lock = threading.Lock()

    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().isoformat()
        line = f"[{timestamp}] [{level}] {message}"

        with self._lock:
            print(line)
            self.log_file.write(line + "\n")
            self.log_file.flush()

    def close(self):
        self.log_file.close()


class ContactPlan:
    """Manages contact windows for LOS/AOS simulation."""

    def __init__(self, duration_hours: float, logger: AuditableLogger):
        self.logger = logger
        self.windows = self._generate_plan(duration_hours)
        self.start_time: Optional[datetime] = None

    def _generate_plan(self, duration_hours: float) -> List[Dict]:
        """Generate deterministic contact plan."""
        import random
        random.seed(42)  # Deterministic for reproducibility

        windows = []
        total_sec = int(duration_hours * 3600)
        current = 0
        stations = ["Goldstone", "Madrid", "Canberra"]
        idx = 0

        while current < total_sec:
            duration = random.randint(3600, 5400)  # 60-90 min contact
            if current + duration > total_sec:
                duration = total_sec - current

            if duration > 0:
                windows.append({
                    "station": stations[idx % 3],
                    "start_sec": current,
                    "duration_sec": duration
                })

            gap = random.randint(900, 2700)  # 15-45 min gap
            current += duration + gap
            idx += 1

        return windows

    def start(self):
        self.start_time = datetime.now()
        self.logger.log(f"Contact plan started with {len(self.windows)} windows")

    def get_state(self) -> LinkState:
        if not self.start_time:
            return LinkState.LOS

        elapsed = (datetime.now() - self.start_time).total_seconds()

        for w in self.windows:
            if w["start_sec"] <= elapsed < (w["start_sec"] + w["duration_sec"]):
                return LinkState.AOS

        return LinkState.LOS


def generate_payload(size: int) -> bytes:
    """Generate deterministic test payload."""
    import random
    random.seed(12345)  # Deterministic

    chunks = []
    remaining = size
    chunk_num = 0

    while remaining > 0:
        header = f"CHUNK{chunk_num:08d}|".encode()
        pattern_size = min(1024 - len(header), remaining - len(header))
        if pattern_size > 0:
            pattern = bytes([random.randint(0, 255) for _ in range(pattern_size)])
            chunk = header + pattern
        else:
            chunk = header[:remaining]
        chunks.append(chunk[:remaining])
        remaining -= len(chunk)
        chunk_num += 1

    return b''.join(chunks)


def sha256_file(path: Path) -> str:
    """Calculate SHA-256 of a file."""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    """Calculate SHA-256 of bytes."""
    return hashlib.sha256(data).hexdigest()


class DTNTestRunner:
    """Runs the DTN test with full audit trail."""

    def __init__(self, output_dir: Path, config: TestConfig, logger: AuditableLogger):
        self.output_dir = output_dir
        self.config = config
        self.logger = logger
        self.stats = TransferStats()
        self.contact_plan: Optional[ContactPlan] = None
        self.received_data = bytearray()
        self.stop_event = threading.Event()
        self._current_state = LinkState.LOS

    def run(self, payload: bytes) -> bool:
        """Run the test and return success status."""
        self.logger.log("=" * 60)
        self.logger.log("AUDITABLE DTN TRANSFER TEST")
        self.logger.log("=" * 60)
        self.logger.log(f"Test ID: {self.config.test_id}")
        self.logger.log(f"Duration: {self.config.duration_hours} hours")
        self.logger.log(f"Data rate: {self.config.data_rate_bps} bps")
        self.logger.log(f"Payload: {self.config.payload_size:,} bytes")
        self.logger.log(f"Payload SHA-256: {self.config.payload_sha256}")

        # Save original payload
        payload_sent_path = self.output_dir / "payload-sent.bin"
        with open(payload_sent_path, 'wb') as f:
            f.write(payload)
        self.logger.log(f"Saved payload to {payload_sent_path}")

        # Setup contact plan
        self.contact_plan = ContactPlan(self.config.duration_hours, self.logger)

        # Log contact windows
        self.logger.log("Contact Plan:")
        for i, w in enumerate(self.contact_plan.windows[:10]):
            self.logger.log(f"  {i+1}. {w['station']}: +{w['start_sec']}s for {w['duration_sec']}s")
        if len(self.contact_plan.windows) > 10:
            self.logger.log(f"  ... and {len(self.contact_plan.windows) - 10} more")

        # Start receiver
        self.logger.log("Starting receiver node (ipn:2.1)...")
        receiver_eid = EndpointID.ipn(2, 1)
        receiver_cla = TCPConvergenceLayer(receiver_eid, listen_port=PORT)
        receiver_cla.add_bundle_handler(self._on_bundle)
        receiver_cla.start()

        # Start test
        self.stats.start_time = datetime.now().isoformat()
        self.contact_plan.start()

        # State monitor thread
        state_thread = threading.Thread(target=self._monitor_state, daemon=True)
        state_thread.start()

        # Sender thread
        sender_thread = threading.Thread(
            target=self._sender_loop,
            args=(payload, receiver_eid),
            daemon=True
        )
        sender_thread.start()

        # Wait for completion
        try:
            while sender_thread.is_alive() and not self.stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.log("Test interrupted by user", "WARN")
            self.stop_event.set()

        # Cleanup
        time.sleep(2)
        receiver_cla.stop()
        self.stats.end_time = datetime.now().isoformat()

        # Save received payload
        payload_recv_path = self.output_dir / "payload-received.bin"
        with open(payload_recv_path, 'wb') as f:
            f.write(bytes(self.received_data))
        self.logger.log(f"Saved received payload to {payload_recv_path}")

        # Verify
        received_sha256 = sha256_bytes(bytes(self.received_data))
        success = (received_sha256 == self.config.payload_sha256)

        self.logger.log("=" * 60)
        self.logger.log("TEST COMPLETE")
        self.logger.log("=" * 60)
        self.logger.log(f"Bytes sent: {self.stats.bytes_sent:,}")
        self.logger.log(f"Bytes received: {self.stats.bytes_received:,}")
        self.logger.log(f"Segments sent: {self.stats.segments_sent}")
        self.logger.log(f"Segments received: {self.stats.segments_received}")
        self.logger.log(f"LOS events: {self.stats.los_events}")
        self.logger.log(f"AOS events: {self.stats.aos_events}")
        self.logger.log(f"Errors: {self.stats.errors}")
        self.logger.log(f"Expected SHA-256: {self.config.payload_sha256}")
        self.logger.log(f"Received SHA-256: {received_sha256}")
        self.logger.log(f"VERIFICATION: {'PASS' if success else 'FAIL'}")

        return success

    def _on_bundle(self, bundle: Bundle):
        """Handle received bundle."""
        self.stats.segments_received += 1
        self.stats.bytes_received += len(bundle.payload.data)
        self.received_data.extend(bundle.payload.data)

        if self.stats.segments_received % 50 == 0:
            pct = (self.stats.bytes_received / self.config.payload_size) * 100
            self.logger.log(f"Progress: {pct:.1f}% ({self.stats.bytes_received:,}/{self.config.payload_size:,} bytes)")

    def _monitor_state(self):
        """Monitor link state changes."""
        last_state = None
        while not self.stop_event.is_set():
            state = self.contact_plan.get_state()
            if state != last_state:
                if state == LinkState.AOS:
                    self.stats.aos_events += 1
                    self.logger.log("=== AOS === Signal acquired")
                else:
                    self.stats.los_events += 1
                    self.logger.log("=== LOS === Signal lost")
                self._current_state = state
                last_state = state
            time.sleep(1)

    def _sender_loop(self, payload: bytes, dest_eid: EndpointID):
        """Sender thread."""
        time.sleep(2)

        sender_eid = EndpointID.ipn(1, 1)
        cla = TCPConvergenceLayer(sender_eid)
        conn = None
        offset = 0
        segment_size = self.config.segment_size
        bytes_per_sec = self.config.data_rate_bps / 8

        self.logger.log(f"Sender starting: {len(payload):,} bytes to transmit")

        while offset < len(payload) and not self.stop_event.is_set():
            # Wait for AOS
            if self._current_state == LinkState.LOS:
                time.sleep(1)
                continue

            # Connect
            if conn is None:
                try:
                    conn = cla.connect('127.0.0.1', PORT)
                    self.logger.log("Sender connected to receiver")
                except Exception as e:
                    self.stats.errors += 1
                    self.logger.log(f"Connection error: {e}", "ERROR")
                    time.sleep(5)
                    continue

            # Send segment
            segment = payload[offset:offset + segment_size]
            bundle = Bundle.create(
                destination=dest_eid,
                source=sender_eid,
                payload=segment,
                lifetime_ms=86400000,
            )

            try:
                # Rate limit
                tx_time = len(segment) / bytes_per_sec
                time.sleep(tx_time)

                if self._current_state == LinkState.LOS:
                    continue

                conn.send_bundle(bundle)
                self.stats.segments_sent += 1
                self.stats.bytes_sent += len(segment)
                offset += len(segment)

            except Exception as e:
                self.stats.errors += 1
                self.logger.log(f"Send error: {e}", "ERROR")
                conn = None
                time.sleep(1)

        if conn:
            conn.stop()

        self.logger.log(f"Sender complete: {self.stats.segments_sent} segments sent")


def main():
    parser = argparse.ArgumentParser(description="Auditable DTN Transfer Test")
    parser.add_argument("--duration", type=float, default=0.1,
                        help="Duration in hours (default: 0.1 = 6 minutes for quick test)")
    parser.add_argument("--rate", type=int, default=8000,
                        help="Data rate in bps (default: 8000 for faster testing)")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Output directory (default: timestamped dir)")
    args = parser.parse_args()

    # Create output directory in tracked verification/test-results
    # These artifacts become part of the system of record
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        # Store in verification/test-results for proper record retention
        output_dir = Path(__file__).parent.parent.parent.parent / "verification" / "test-results" / f"dtn-test-{timestamp}"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize logger
    logger = AuditableLogger(output_dir / "test-log.txt")

    # Calculate payload size
    duty_cycle = 0.6
    effective_rate = (args.rate / 8) * duty_cycle
    payload_size = int(effective_rate * args.duration * 3600)

    # Ensure minimum meaningful payload
    payload_size = max(payload_size, 10000)

    # Generate payload
    logger.log("Generating test payload...")
    payload = generate_payload(payload_size)
    payload_hash = sha256_bytes(payload)

    # Create config
    import socket
    config = TestConfig(
        test_id=f"DTN-{timestamp}",
        start_time=datetime.now().isoformat(),
        duration_hours=args.duration,
        data_rate_bps=args.rate,
        segment_size=256,
        payload_size=payload_size,
        payload_sha256=payload_hash,
        hostname=socket.gethostname(),
        python_version=sys.version.split()[0],
    )

    # Save manifest
    manifest_path = output_dir / "test-manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(config.to_dict(), f, indent=2)
    logger.log(f"Saved test manifest to {manifest_path}")

    # Setup signal handler
    def signal_handler(sig, frame):
        logger.log("Interrupt received - stopping test", "WARN")
        runner.stop_event.set()

    signal.signal(signal.SIGINT, signal_handler)

    # Run test
    runner = DTNTestRunner(output_dir, config, logger)
    success = runner.run(payload)

    # Save stats
    stats_path = output_dir / "transfer-stats.json"
    with open(stats_path, 'w') as f:
        json.dump(runner.stats.to_dict(), f, indent=2)

    # Close logger before computing checksums (so log file is complete)
    logger.log(f"Test artifacts saved to: {output_dir}")
    logger.log(f"Verification: {'PASS' if success else 'FAIL'}")
    logger.close()

    # Generate summary (after logger closed)
    summary_path = output_dir / "test-summary.txt"
    recv_hash = sha256_bytes(bytes(runner.received_data))
    with open(summary_path, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("DTN TRANSFER TEST - OBJECTIVE QUALITY EVIDENCE\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Test ID:        {config.test_id}\n")
        f.write(f"Date:           {config.start_time}\n")
        f.write(f"Duration:       {config.duration_hours} hours\n")
        f.write(f"Data Rate:      {config.data_rate_bps} bps\n")
        f.write(f"Payload Size:   {config.payload_size:,} bytes\n\n")
        f.write("Results:\n")
        f.write(f"  Bytes Sent:     {runner.stats.bytes_sent:,}\n")
        f.write(f"  Bytes Received: {runner.stats.bytes_received:,}\n")
        f.write(f"  Segments:       {runner.stats.segments_sent} sent / {runner.stats.segments_received} received\n")
        f.write(f"  LOS Events:     {runner.stats.los_events}\n")
        f.write(f"  AOS Events:     {runner.stats.aos_events}\n")
        f.write(f"  Errors:         {runner.stats.errors}\n\n")
        f.write("Verification:\n")
        f.write(f"  Expected SHA-256: {config.payload_sha256}\n")
        f.write(f"  Received SHA-256: {recv_hash}\n")
        f.write(f"  Status:           {'PASS' if success else 'FAIL'}\n\n")
        f.write("Artifacts:\n")
        for file in sorted(output_dir.iterdir()):
            if file.name != "checksums.sha256":  # Exclude checksums file
                f.write(f"  - {file.name}\n")
        f.write("  - checksums.sha256\n")  # Add it last
        f.write("\n")
        f.write("To verify checksums:\n")
        f.write(f"  cd {output_dir}\n")
        f.write("  shasum -a 256 -c checksums.sha256\n")

    # Generate checksums LAST (after all other files are written and closed)
    checksums_path = output_dir / "checksums.sha256"
    with open(checksums_path, 'w') as f:
        for file in sorted(output_dir.iterdir()):
            if file.name != "checksums.sha256" and file.is_file():
                h = sha256_file(file)
                f.write(f"{h}  {file.name}\n")

    print(f"\n{'='*60}")
    print(f"Test complete. Results in: {output_dir}")
    print(f"Verification: {'PASS' if success else 'FAIL'}")
    print(f"{'='*60}\n")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
