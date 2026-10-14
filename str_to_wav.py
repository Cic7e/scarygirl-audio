import argparse
import struct
import sys
import wave
from pathlib import Path

HEADER_SIZE = 16
PCM_TAG = 1
BYTES_PER_SAMPLE = 2  # 16-bit

OK, SKIP, FAIL = "OK", "SKIP", "FAIL"


def read_header(path: Path) -> tuple[int, int, int] | None:
    """Return (tag, channels, rate) from a .str header, or None if truncated"""
    with path.open("rb") as f:
        header = f.read(HEADER_SIZE)
    if len(header) < HEADER_SIZE:
        return None
    tag, channels = struct.unpack_from("<HH", header)
    (rate,) = struct.unpack_from("<I", header, 4)
    return tag, channels, rate

def convert(path: Path, outdir: Path | None) -> tuple[str, str]:
    """Convert one .str file to .wav, returns (status, message)"""
    size = path.stat().st_size
    header = read_header(path)
    if header is None:
        return FAIL, f"{path}: file smaller than the {HEADER_SIZE}-byte header"
    tag, channels, rate = header
    if tag != PCM_TAG:
        return SKIP, f"not plain PCM (tag={tag}): {path}"
    if channels == 0 or rate == 0:
        return FAIL, f"{path}: invalid header (rate={rate}, ch={channels})"
    bytes_per_frame = channels * BYTES_PER_SAMPLE
    # Keep only complete frames
    payload = (size - HEADER_SIZE) // bytes_per_frame * bytes_per_frame
    if payload <= 0:
        return FAIL, f"{path}: no complete audio frames after the header"
    with path.open("rb") as src:
        src.seek(HEADER_SIZE)
        pcm = src.read(payload)
    out_path = (outdir or path.parent) / path.with_suffix(".wav").name
    with wave.open(str(out_path), "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(BYTES_PER_SAMPLE)
        wav.setframerate(rate)
        wav.writeframes(pcm)
    return OK, f"{path} ({rate} Hz, {channels}ch)"

def collect_inputs(inputs: list[str]) -> tuple[list[Path], list[str]]:
    """Expand files, folders, and globs into an ordered list"""
    found: dict[Path, None] = {}  # insertion-ordered set
    problems: list[str] = []
    targets = [Path(i) for i in inputs] or [Path(".")]
    for target in targets:
        if target.is_dir():
            matches = sorted(target.glob("*.str"))
        elif target.is_file():
            matches = [target]
        else:
            # Not an existing directory
            matches = sorted(Path().glob(str(target)))
        for match in matches:
            if match.is_file():
                found.setdefault(match, None)
        if not matches and not target.exists():
            problems.append(f"no .str files matched '{target}'")
    return list(found), problems

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert Scarygirl .str audio assets to .wav files")
    parser.add_argument("inputs", nargs="*",
                        help=".str files, folders or glob patterns (default: every *.str in the current directory)")
    parser.add_argument("-o", "--outdir", type=Path,
                        help="write .wav files here instead of next to their source files")
    args = parser.parse_args(argv)
    files, problems = collect_inputs(args.inputs)
    for problem in problems:
        print(f"WARN: {problem}", file=sys.stderr)
    if not files:
        print("No .str files found", file=sys.stderr)
        return 1
    if args.outdir:
        args.outdir.mkdir(parents=True, exist_ok=True)
    counts = {OK: 0, SKIP: 0, FAIL: 0}
    for path in files:
        if path.suffix.lower() != ".str":
            status, message = SKIP, f"not a .str file: {path}"
        else:
            try:
                status, message = convert(path, args.outdir)
            except Exception as exc:  # report and keep going
                status, message = FAIL, f"{path}: {exc}"
        counts[status] += 1
        print(f"{status}: {message}")
    print(f"\nDone. Converted: {counts[OK]}, skipped: {counts[SKIP]}, failed: {counts[FAIL]}.")
    return 1 if counts[FAIL] else 0

if __name__ == "__main__":
    sys.exit(main())
