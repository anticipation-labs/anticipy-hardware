# Minimal iPhone receiver status

`AnticipyBLEClient.swift` is a source-complete CoreBluetooth transport handoff. It:

- scans and connects to the Anticipy/Omi audio service;
- triggers iOS encrypted pairing by reading the protected codec characteristic;
- subscribes to live audio, storage and button notifications;
- emits individual raw 16-kHz mono Opus frames;
- reassembles negotiated-MTU storage notifications into the firmware's 440-byte SD records;
- validates the length-prefixed Opus records;
- fsyncs every complete record before advancing the resumable byte offset;
- sends haptic commands.

It has **not** been built with Xcode or run on an iPhone in this environment. Put it in an iOS 16+ app target, add the Bluetooth usage descriptions and background mode, connect its callbacks to Anticipy's upload path, and exercise the hardware gates in `BUILD_STATUS.md` before calling the device usable.

Use `NSBluetoothAlwaysUsageDescription` in `Info.plist` and add `bluetooth-central` to `UIBackgroundModes`. Background declarations allow CoreBluetooth work; they do not prove that a two-hour locked-phone stream will survive, so that remains a physical acceptance test.

For local playback, link a maintained libopus build and initialize `opus_decoder_create(16000, 1, &error)`. Call `opus_decode(decoder, packet, packetLength, pcm, 160, 0)` once for each callback frame. The stock Omi Flutter app already accepts codec ID 20 and the same live service/characteristic, but its legacy SD downloader assumes every notification is exactly 440 bytes; this client supplies the required iPhone-MTU reassembly instead.
