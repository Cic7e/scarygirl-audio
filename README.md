# scarygirl-audio

A tiny tool for converting **Scarygirl** game audio assets (`.str` files) into standard `.wav` files.

## Format

*Scarygirl* (2012, PC/Steam release) stores audio assets as `.str` files which are essentially trimmed-down WAVs.
This script reads the header and repacks the samples as a standard `.wav` file.

16-Byte Header layout (little-endian):

| Offset | Type | Field             | Meaning                      |
|--------|------|-------------------|------------------------------|
| 0      | u16  | `wFormatTag`      | format tag (`1` = plain PCM) |
| 2      | u16  | `nChannels`       | channel count                |
| 4      | u32  | `nSamplesPerSec`  | sample rate (Hz)             |
| 8      | u32  | `nAvgBytesPerSec` | bytes per second             |
| 12     | u16  | `nBlockAlign`     | bytes per frame              |
| 14     | u16  | `wBitsPerSample`  | bits per sample              |

This script tries to find and convert plain-PCM files (`wFormatTag == 1`).

Files that fail the check `nAvgBytesPerSec == nSamplesPerSec × nBlockAlign` or `nBlockAlign == nChannels × wBitsPerSample / 8` get dropped.

### Platform notes

This tool targets the PC/Steam release. The `.str` files of the console versions reportedly use a different header and are not officially supported here.

## Requirements

This script only requires Python 3.10+ and does not use any additional dependencies.

## Usage

```bash
python str_to_wav.py                      # every *.str in the current directory
python str_to_wav.py music.str            # a single file
python str_to_wav.py sounds/ music/       # every *.str inside these folders
python str_to_wav.py "assets/*.str"       # glob pattern(s)
python str_to_wav.py -o out/ sounds/      # write .wav files into ./out/
```

By default `.wav` files are copied next to their sources, keeping the same base name (`bgm01.str` -> `bgm01.wav`).

## Example Output

```
OK: sounds/88C9340E4FF71EE4.str (44100 Hz, 2ch)
SKIP: not plain PCM (tag=6): sounds/D345939E0643AB17.str
FAIL: sounds/F9E56190318A8388.str: no complete audio frames after the header

Done. Converted: 1, skipped: 1, failed: 1.
```

Exit code is `0` when everything is successfully converted (skips don't count) otherwise `1`.