# Using the result tools

## Rattle audio

Export the quiet marker windows as PCM WAV. Use at least three qualified golden recordings from the same cassette index, sensor position and fixed input gain:

```bash
python3 rattle_audio_score.py \
  --golden golden_01_A.wav \
  --golden golden_02_A.wav \
  --golden golden_03_A.wav \
  --dut DUT123_A.wav \
  --output reports/DUT123_A_audio.json
```

Exit code `0` means pass, `1` means the DUT exceeded the qualified envelope by more than 6 dB, and `2` means the recording was invalid. A clipped file is invalid, not a pass or fail.

## Acceptance sheet

Copy `acceptance_test_template.csv`, replace `ENTER_SERIAL`, and fill only `actual`, `notes`, and `evidence`. Text checks take exactly `PASS`; numeric checks take a number without its unit.

```bash
python3 qa_acceptance.py DUT123_acceptance.csv \
  --output-csv reports/DUT123_evaluated.csv \
  --output-json reports/DUT123_summary.json
```

Exit code `0` is a complete pass, `1` contains a failure, `2` is incomplete/invalid, and `3` means the file itself could not be read. Never turn a blank into `PASS` just to make the report green.
