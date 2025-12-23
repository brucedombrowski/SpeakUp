#!/usr/bin/env python3
"""
Long-Duration DTN Transfer Test with LOS/AOS Simulation

Simulates a realistic deep-space data transfer scenario:
- Very low bandwidth (simulating DSN constraints)
- Loss of Signal (LOS) / Acquisition of Signal (AOS) periods
- Store-and-forward behavior during blackouts
- Progress tracking and estimated completion time

Scenario: Voyager-class mission data return
- Data rate: ~160 bps (20 bytes/sec) - actual Voyager downlink
- LOS periods: Simulated Earth rotation (ground station visibility)
- Transfer duration: ~5-6 hours for meaningful payload

Usage:
    python3 long_duration_test.py [--duration HOURS] [--rate BPS]

Example:
    python3 long_duration_test.py --duration 5 --rate 160
"""

import sys
import os
import time
import threading
import argparse
import hashlib
import random
import signal
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from bpv7 import Bundle, EndpointID
from bpv7.agent.tcpcl import TCPConvergenceLayer

# Configuration
DEFAULT_DURATION_HOURS = 5
DEFAULT_DATA_RATE_BPS = 160  # Voyager downlink rate
PORT = 4557  # Different port to avoid conflicts


class LinkState(Enum):
    """Link state for LOS/AOS simulation."""
    AOS = "AOS"  # Acquisition of Signal
    LOS = "LOS"  # Loss of Signal


@dataclass
class ContactWindow:
    """Represents a ground station contact window."""
    start_offset_sec: int  # Seconds from test start
    duration_sec: int      # Duration of contact
    station: str           # Ground station name

    def __str__(self):
        return f"{self.station}: +{self.start_offset_sec}s for {self.duration_sec}s"


@dataclass
class TransferStats:
    """Statistics for the ongoing transfer."""
    total_bytes: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    segments_sent: int = 0
    segments_received: int = 0
    los_events: int = 0
    aos_events: int = 0
    start_time: Optional[datetime] = None

    @property
    def progress_pct(self) -> float:
        if self.total_bytes == 0:
            return 0.0
        return (self.bytes_received / self.total_bytes) * 100

    @property
    def elapsed_sec(self) -> float:
        if not self.start_time:
            return 0.0
        return (datetime.now() - self.start_time).total_seconds()


def generate_test_payload(size_bytes: int) -> bytes:
    """Generate deterministic test payload for verification."""
    # Use repeating pattern with embedded checksums for verification
    chunk_size = 1024
    chunks = []
    remaining = size_bytes
    chunk_num = 0

    while remaining > 0:
        # Create chunk with identifiable pattern
        header = f"CHUNK{chunk_num:08d}".encode()
        pattern = bytes([(chunk_num + i) % 256 for i in range(min(chunk_size - len(header), remaining - len(header)))])
        chunk = header + pattern
        chunk = chunk[:min(len(chunk), remaining)]
        chunks.append(chunk)
        remaining -= len(chunk)
        chunk_num += 1

    return b''.join(chunks)


def create_contact_plan(duration_hours: float) -> List[ContactWindow]:
    """
    Create a realistic contact plan simulating DSN ground station passes.

    Based on typical deep-space mission operations:
    - 3 DSN complexes (Goldstone, Madrid, Canberra)
    - ~8-12 hour coverage from each complex
    - Some overlap, some gaps
    - Voyager 2 constraint: Only Canberra can see it (southern trajectory)
    """
    total_sec = int(duration_hours * 3600)
    contacts = []

    # Simulate passes every ~2 hours with ~45 min gaps (Earth rotation)
    current_time = 0
    station_cycle = ["Goldstone", "Madrid", "Canberra"]
    station_idx = 0

    while current_time < total_sec:
        # Contact window: 60-90 minutes
        contact_duration = random.randint(3600, 5400)

        # Ensure we don't exceed test duration
        if current_time + contact_duration > total_sec:
            contact_duration = total_sec - current_time

        if contact_duration > 0:
            contacts.append(ContactWindow(
                start_offset_sec=current_time,
                duration_sec=contact_duration,
                station=station_cycle[station_idx % len(station_cycle)]
            ))

        # Gap: 15-45 minutes (LOS period)
        gap = random.randint(900, 2700)
        current_time += contact_duration + gap
        station_idx += 1

    return contacts


class SpaceLinkSimulator:
    """Simulates space link with bandwidth limiting and LOS/AOS."""

    def __init__(
        self,
        data_rate_bps: int,
        contact_plan: List[ContactWindow],
        stats: TransferStats,
    ):
        self.data_rate_bps = data_rate_bps
        self.bytes_per_sec = data_rate_bps / 8
        self.contact_plan = contact_plan
        self.stats = stats
        self.current_state = LinkState.LOS
        self.start_time: Optional[datetime] = None
        self._stop = threading.Event()

    def start(self):
        self.start_time = datetime.now()
        self._state_thread = threading.Thread(target=self._state_monitor, daemon=True)
        self._state_thread.start()

    def stop(self):
        self._stop.set()

    def get_state(self) -> LinkState:
        """Get current link state based on contact plan."""
        if not self.start_time:
            return LinkState.LOS

        elapsed = (datetime.now() - self.start_time).total_seconds()

        for contact in self.contact_plan:
            if contact.start_offset_sec <= elapsed < (contact.start_offset_sec + contact.duration_sec):
                return LinkState.AOS

        return LinkState.LOS

    def _state_monitor(self):
        """Monitor and log state changes."""
        last_state = None
        while not self._stop.is_set():
            current = self.get_state()
            if current != last_state:
                if current == LinkState.AOS:
                    self.stats.aos_events += 1
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === AOS === Signal acquired")
                else:
                    self.stats.los_events += 1
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === LOS === Signal lost - storing data")
                last_state = current
            time.sleep(1)

    def rate_limit_send(self, data: bytes) -> bool:
        """
        Simulate bandwidth-limited send.
        Returns True if link is up, False if LOS.
        """
        if self.get_state() == LinkState.LOS:
            return False

        # Simulate transmission time
        tx_time = len(data) / self.bytes_per_sec
        time.sleep(tx_time)
        return True


class DTNNode:
    """DTN node with store-and-forward capability."""

    def __init__(
        self,
        eid: EndpointID,
        port: int,
        link_sim: SpaceLinkSimulator,
        stats: TransferStats,
        is_sender: bool = False,
    ):
        self.eid = eid
        self.port = port
        self.link_sim = link_sim
        self.stats = stats
        self.is_sender = is_sender
        self.cla: Optional[TCPConvergenceLayer] = None
        self.pending_bundles: List[Bundle] = []
        self.received_data = bytearray()
        self._stop = threading.Event()

    def start(self):
        self.cla = TCPConvergenceLayer(self.eid, listen_port=self.port)
        self.cla.add_bundle_handler(self._on_bundle_received)
        self.cla.start()

    def stop(self):
        self._stop.set()
        if self.cla:
            self.cla.stop()

    def _on_bundle_received(self, bundle: Bundle):
        """Handle received bundle."""
        self.stats.segments_received += 1
        self.stats.bytes_received += len(bundle.payload.data)
        self.received_data.extend(bundle.payload.data)

        # Progress update every 10 segments
        if self.stats.segments_received % 10 == 0:
            elapsed = self.stats.elapsed_sec
            rate = self.stats.bytes_received / elapsed if elapsed > 0 else 0
            eta_sec = (self.stats.total_bytes - self.stats.bytes_received) / rate if rate > 0 else 0
            eta = timedelta(seconds=int(eta_sec))

            print(f"\r[{datetime.now().strftime('%H:%M:%S')}] "
                  f"Progress: {self.stats.progress_pct:.1f}% | "
                  f"Received: {self.stats.bytes_received:,} / {self.stats.total_bytes:,} bytes | "
                  f"Rate: {rate*8:.0f} bps | "
                  f"ETA: {eta}", end="", flush=True)


def run_sender(
    dest_eid: EndpointID,
    payload: bytes,
    segment_size: int,
    link_sim: SpaceLinkSimulator,
    stats: TransferStats,
    stop_event: threading.Event,
):
    """Sender thread - segments and transmits data."""
    sender_eid = EndpointID.ipn(1, 1)  # Earth ground station

    time.sleep(2)  # Wait for receiver to be ready

    print(f"\n[SENDER] Starting transmission to {dest_eid}")
    print(f"[SENDER] Payload: {len(payload):,} bytes in {len(payload)//segment_size + 1} segments")
    print(f"[SENDER] Data rate: {link_sim.data_rate_bps} bps ({link_sim.bytes_per_sec:.1f} bytes/sec)")
    print()

    cla = TCPConvergenceLayer(sender_eid)
    conn = None
    offset = 0

    while offset < len(payload) and not stop_event.is_set():
        # Check link state
        if link_sim.get_state() == LinkState.LOS:
            time.sleep(1)
            continue

        # Connect if needed
        if conn is None:
            try:
                conn = cla.connect('127.0.0.1', PORT)
                print(f"\n[SENDER] Connected to receiver")
            except Exception as e:
                print(f"\n[SENDER] Connection failed: {e}")
                time.sleep(5)
                continue

        # Send next segment
        segment = payload[offset:offset + segment_size]

        bundle = Bundle.create(
            destination=dest_eid,
            source=sender_eid,
            payload=segment,
            lifetime_ms=86400000,  # 24 hours
        )

        try:
            # Rate limit
            if not link_sim.rate_limit_send(segment):
                continue  # LOS during send

            conn.send_bundle(bundle)
            stats.segments_sent += 1
            stats.bytes_sent += len(segment)
            offset += len(segment)

        except Exception as e:
            print(f"\n[SENDER] Send error: {e}")
            conn = None
            time.sleep(1)

    if conn:
        conn.stop()

    print(f"\n[SENDER] Transmission complete: {stats.segments_sent} segments sent")


def print_summary(stats: TransferStats, payload: bytes, received_data: bytes):
    """Print final test summary."""
    print("\n")
    print("=" * 70)
    print("LONG-DURATION DTN TRANSFER TEST - FINAL SUMMARY")
    print("=" * 70)
    print()

    elapsed = timedelta(seconds=int(stats.elapsed_sec))

    print(f"Duration:           {elapsed}")
    print(f"Payload size:       {stats.total_bytes:,} bytes")
    print(f"Bytes sent:         {stats.bytes_sent:,} bytes")
    print(f"Bytes received:     {stats.bytes_received:,} bytes")
    print(f"Segments sent:      {stats.segments_sent}")
    print(f"Segments received:  {stats.segments_received}")
    print(f"LOS events:         {stats.los_events}")
    print(f"AOS events:         {stats.aos_events}")
    print()

    # Verify data integrity
    if len(received_data) == len(payload):
        if received_data == payload:
            print("DATA INTEGRITY:     VERIFIED (MD5 match)")
            print(f"  Expected MD5:     {hashlib.md5(payload).hexdigest()}")
            print(f"  Received MD5:     {hashlib.md5(received_data).hexdigest()}")
        else:
            print("DATA INTEGRITY:     FAILED (content mismatch)")
    else:
        print(f"DATA INTEGRITY:     INCOMPLETE ({len(received_data)} of {len(payload)} bytes)")

    print()
    print(f"Effective rate:     {stats.bytes_received * 8 / stats.elapsed_sec:.1f} bps")
    print()
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Long-duration DTN transfer test")
    parser.add_argument("--duration", type=float, default=DEFAULT_DURATION_HOURS,
                        help=f"Test duration in hours (default: {DEFAULT_DURATION_HOURS})")
    parser.add_argument("--rate", type=int, default=DEFAULT_DATA_RATE_BPS,
                        help=f"Data rate in bps (default: {DEFAULT_DATA_RATE_BPS})")
    parser.add_argument("--segment-size", type=int, default=256,
                        help="Bundle segment size in bytes (default: 256)")
    args = parser.parse_args()

    # Calculate payload size for desired duration
    # Account for ~60% duty cycle due to LOS periods
    duty_cycle = 0.6
    effective_rate = (args.rate / 8) * duty_cycle
    payload_size = int(effective_rate * args.duration * 3600)

    print("=" * 70)
    print("LONG-DURATION DTN TRANSFER TEST")
    print("=" * 70)
    print()
    print("Simulating deep-space data transfer with realistic constraints:")
    print()
    print(f"  Target duration:  {args.duration} hours")
    print(f"  Data rate:        {args.rate} bps (Voyager-class)")
    print(f"  Payload size:     {payload_size:,} bytes")
    print(f"  Segment size:     {args.segment_size} bytes")
    print(f"  Duty cycle:       {duty_cycle*100:.0f}% (LOS/AOS simulation)")
    print()

    # Generate contact plan
    contact_plan = create_contact_plan(args.duration)
    print("Contact Plan (Ground Station Passes):")
    for i, contact in enumerate(contact_plan[:10]):  # Show first 10
        print(f"  {i+1}. {contact}")
    if len(contact_plan) > 10:
        print(f"  ... and {len(contact_plan) - 10} more passes")
    print()

    # Initialize
    stats = TransferStats(total_bytes=payload_size)
    link_sim = SpaceLinkSimulator(args.rate, contact_plan, stats)

    # Generate payload
    print("Generating test payload...")
    payload = generate_test_payload(payload_size)
    print(f"  Payload MD5: {hashlib.md5(payload).hexdigest()}")
    print()

    # Setup receiver
    receiver_eid = EndpointID.ipn(2, 1)  # Deep space probe
    receiver = DTNNode(receiver_eid, PORT, link_sim, stats, is_sender=False)

    # Stop handler
    stop_event = threading.Event()

    def signal_handler(sig, frame):
        print("\n\nInterrupted - generating summary...")
        stop_event.set()

    signal.signal(signal.SIGINT, signal_handler)

    # Start test
    print("Starting test...")
    print("Press Ctrl+C to stop early and see summary")
    print()

    stats.start_time = datetime.now()
    link_sim.start()
    receiver.start()

    # Start sender thread
    sender_thread = threading.Thread(
        target=run_sender,
        args=(receiver_eid, payload, args.segment_size, link_sim, stats, stop_event),
        daemon=True
    )
    sender_thread.start()

    # Wait for completion or interrupt
    try:
        while sender_thread.is_alive() and not stop_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        stop_event.set()

    # Cleanup
    time.sleep(2)
    link_sim.stop()
    receiver.stop()

    # Summary
    print_summary(stats, payload, bytes(receiver.received_data))


if __name__ == "__main__":
    main()
