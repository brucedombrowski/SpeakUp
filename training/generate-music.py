#!/usr/bin/env python3
"""
SpeakUp Background Music Generator

Generates simple, royalty-free ambient/elevator music for video backgrounds.
All music generated is original and owned by the project.

Dependencies:
    pip install midiutil
    brew install fluidsynth

Usage:
    python generate-music.py --duration 60 --style ambient --output background.mp3
"""

import argparse
import random
import subprocess
import tempfile
from pathlib import Path

from midiutil import MIDIFile


def generate_ambient_melody(duration_seconds: int, tempo: int = 72) -> MIDIFile:
    """
    Generate calming ambient background music.

    Uses simple chord progressions and arpeggios in major keys.
    Designed to be unobtrusive and professional-sounding.
    """
    midi = MIDIFile(2)  # 2 tracks: pad + melody

    # Track 0: Sustained pad chords
    track_pad = 0
    channel_pad = 0
    midi.addTrackName(track_pad, 0, "Ambient Pad")
    midi.addTempo(track_pad, 0, tempo)
    midi.addProgramChange(track_pad, channel_pad, 0, 89)  # Warm Pad

    # Track 1: Gentle melody/arpeggio
    track_melody = 1
    channel_melody = 1
    midi.addTrackName(track_melody, 0, "Melody")
    midi.addTempo(track_melody, 0, tempo)
    midi.addProgramChange(track_melody, channel_melody, 0, 88)  # New Age pad

    # Calculate beats
    beats_per_second = tempo / 60
    total_beats = int(duration_seconds * beats_per_second)

    # Chord progression: I - V - vi - IV (classic pleasant progression)
    # In C major: C - G - Am - F
    chords = [
        [60, 64, 67],      # C major (C E G)
        [55, 59, 62],      # G major (G B D)
        [57, 60, 64],      # A minor (A C E)
        [53, 57, 60],      # F major (F A C)
    ]

    # Add pad chords (sustained, changing every 8 beats)
    chord_duration = 8  # beats
    current_beat = 0
    chord_index = 0
    pad_volume = 50  # Quiet background

    while current_beat < total_beats:
        chord = chords[chord_index % len(chords)]
        for note in chord:
            # Lower octave for warmth
            midi.addNote(track_pad, channel_pad, note - 12, current_beat,
                        chord_duration, pad_volume)
        chord_index += 1
        current_beat += chord_duration

    # Add gentle arpeggio melody
    melody_volume = 40  # Even quieter
    current_beat = 0
    chord_index = 0
    note_duration = 2  # beats per note

    while current_beat < total_beats:
        chord = chords[chord_index % len(chords)]
        # Arpeggio through chord notes
        for i, note in enumerate(chord + [chord[0] + 12]):  # Up an octave at end
            if current_beat + i * note_duration < total_beats:
                midi.addNote(track_melody, channel_melody, note + 12,
                           current_beat + i * note_duration,
                           note_duration, melody_volume)
        chord_index += 1
        current_beat += chord_duration

    return midi


def generate_corporate_music(duration_seconds: int, tempo: int = 100) -> MIDIFile:
    """
    Generate upbeat but professional corporate background music.
    Think: tech presentation, startup pitch.
    """
    midi = MIDIFile(3)

    # Track 0: Bass
    midi.addTrackName(0, 0, "Bass")
    midi.addTempo(0, 0, tempo)
    midi.addProgramChange(0, 0, 0, 33)  # Fingered Bass

    # Track 1: Pad
    midi.addTrackName(1, 0, "Pad")
    midi.addTempo(1, 0, tempo)
    midi.addProgramChange(1, 1, 0, 91)  # Pad (Bowed)

    # Track 2: Bells/Melody
    midi.addTrackName(2, 0, "Bells")
    midi.addTempo(2, 0, tempo)
    midi.addProgramChange(2, 2, 0, 8)  # Celesta

    beats_per_second = tempo / 60
    total_beats = int(duration_seconds * beats_per_second)

    # Major key progression
    bass_notes = [48, 43, 45, 41]  # C, G, A, F (bass)
    chords = [
        [60, 64, 67],  # C
        [55, 59, 62],  # G
        [57, 60, 64],  # Am
        [53, 57, 60],  # F
    ]

    current_beat = 0
    chord_index = 0

    while current_beat < total_beats:
        # Bass (quarter notes)
        bass_note = bass_notes[chord_index % len(bass_notes)]
        for i in range(4):
            if current_beat + i * 2 < total_beats:
                midi.addNote(0, 0, bass_note, current_beat + i * 2, 1.5, 60)

        # Pad chord
        chord = chords[chord_index % len(chords)]
        for note in chord:
            midi.addNote(1, 1, note, current_beat, 8, 45)

        # Occasional bell accent
        if chord_index % 2 == 0:
            midi.addNote(2, 2, chord[2] + 12, current_beat, 4, 35)

        chord_index += 1
        current_beat += 8

    return midi


def generate_minimal_music(duration_seconds: int, tempo: int = 60) -> MIDIFile:
    """
    Generate minimal, sparse background music.
    Very unobtrusive, good for voiceover.
    """
    midi = MIDIFile(1)

    midi.addTrackName(0, 0, "Minimal")
    midi.addTempo(0, 0, tempo)
    midi.addProgramChange(0, 0, 0, 88)  # New Age

    beats_per_second = tempo / 60
    total_beats = int(duration_seconds * beats_per_second)

    # Simple pentatonic notes
    notes = [60, 62, 64, 67, 69, 72, 74, 76]

    current_beat = 0
    while current_beat < total_beats:
        # Sparse random notes
        if random.random() < 0.3:  # 30% chance of note
            note = random.choice(notes)
            duration = random.choice([4, 6, 8])
            volume = random.randint(30, 50)
            midi.addNote(0, 0, note, current_beat, duration, volume)

        current_beat += 2

    return midi


def midi_to_audio(midi_path: Path, output_path: Path, soundfont: Path = None) -> bool:
    """
    Convert MIDI to audio using fluidsynth.
    """
    # Find a soundfont
    if soundfont is None:
        # Common soundfont locations
        soundfont_paths = [
            Path("/opt/homebrew/share/sounds/sf2/FluidR3_GM.sf2"),
            Path("/usr/share/sounds/sf2/FluidR3_GM.sf2"),
            Path("/usr/local/share/sounds/sf2/FluidR3_GM.sf2"),
            Path.home() / ".fluidsynth/default.sf2",
        ]

        for sf in soundfont_paths:
            if sf.exists():
                soundfont = sf
                break

    if soundfont is None or not soundfont.exists():
        # Check for local soundfont first
        local_sf = Path(__file__).parent / "FluidR3_GM.sf2"
        if local_sf.exists():
            soundfont = local_sf
        else:
            print("  [WARN] No soundfont found. Download FluidR3_GM.sf2 (~141MB)")
            print("  curl -L -o FluidR3_GM.sf2 'https://github.com/urish/cinto/raw/master/media/FluidR3%20GM.sf2'")
            return False

    # Generate WAV first
    wav_path = output_path.with_suffix('.wav')

    # Note: fluidsynth argument order matters on macOS - -F must come before -ni
    result = subprocess.run([
        "fluidsynth",
        "-F", str(wav_path),  # Output file (must be first on macOS)
        "-ni",  # No interactive mode
        "-g", "0.5",  # Gain (volume)
        str(soundfont),
        str(midi_path),
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  [ERROR] fluidsynth failed: {result.stderr}")
        return False

    # Convert to MP3 with ffmpeg (lower volume for background)
    result = subprocess.run([
        "ffmpeg", "-y",
        "-i", str(wav_path),
        "-af", "volume=0.3",  # Reduce volume to 30% for background use
        "-b:a", "128k",
        str(output_path)
    ], capture_output=True, text=True)

    # Clean up WAV
    wav_path.unlink(missing_ok=True)

    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(
        description="Generate royalty-free background music for videos"
    )
    parser.add_argument(
        "--duration", type=int, default=60,
        help="Duration in seconds (default: 60)"
    )
    parser.add_argument(
        "--style", choices=["ambient", "corporate", "minimal"],
        default="ambient",
        help="Music style (default: ambient)"
    )
    parser.add_argument(
        "--output", type=str, default="background-music.mp3",
        help="Output file path (default: background-music.mp3)"
    )
    parser.add_argument(
        "--tempo", type=int, default=None,
        help="Tempo in BPM (default: varies by style)"
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Random seed for reproducibility"
    )

    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    print("========================================================")
    print("SpeakUp Background Music Generator")
    print("========================================================")
    print(f"Style: {args.style}")
    print(f"Duration: {args.duration}s")
    print()

    # Generate MIDI
    print("Generating MIDI...")

    if args.style == "ambient":
        tempo = args.tempo or 72
        midi = generate_ambient_melody(args.duration, tempo)
    elif args.style == "corporate":
        tempo = args.tempo or 100
        midi = generate_corporate_music(args.duration, tempo)
    else:  # minimal
        tempo = args.tempo or 60
        midi = generate_minimal_music(args.duration, tempo)

    # Write MIDI file
    output_path = Path(args.output)
    midi_path = output_path.with_suffix('.mid')

    with open(midi_path, 'wb') as f:
        midi.writeFile(f)
    print(f"  Created: {midi_path}")

    # Convert to audio
    print("Converting to audio...")
    if midi_to_audio(midi_path, output_path):
        print(f"  Created: {output_path}")
        # Keep MIDI for reference/editing
        print()
        print("========================================================")
        print("Music Generation Complete")
        print("========================================================")
        print()
        print(f"Output: {output_path}")
        print(f"MIDI source: {midi_path}")
        print()
        print("License: Original work, owned by SpeakUp project")
        print("Usage: Free for any purpose (we generated it)")
        print()
    else:
        print("  [ERROR] Audio conversion failed")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
