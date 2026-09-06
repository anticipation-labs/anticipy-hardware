# Welcome back

Written 2026-07-24, while you were away. Read the first two sections and you have the state.

**Short version:** the software side got a lot done and most of it survived hard checking. The
pendant did not move at all, because it cannot move without you. One button press is the whole
blocker.

---

## 1. The one thing only you can do

**Press the pendant's RESET button twice, quickly.**

That is it. Everything else is waiting on that.

### Finding the button

Bottom-left corner of the board, right next to the USB-C connector. The silkscreen (the white
printing on the board) says **`RST`**. It is a tiny round silver button, fully exposed — the board is
bare, so there is no case to open and nothing to pry.

### Pressing it without breaking anything

The risk is not the button, it is bending the board. Header pins are soldered straight through it,
and the battery wires are on the underside. If the board flexes, something tears.

So do not press it against a table. Do this instead:

1. Put your **thumb underneath the board**, directly below the button, on the opposite face.
2. Press down **from above with a fingernail**, so you are effectively **pinching** the button toward
   your thumb.
3. The force cancels out between your finger and thumb. The board cannot flex.

### The rhythm

**Two presses, about a quarter of a second apart.** Roughly the speed of a double-click on a mouse.
Leave the **USB cable connected** the whole time.

### How you know it worked

A **disk appears on your Mac named `XIAO-SENSE`** — like plugging in a USB stick. It shows up in
Finder.

(If you want to confirm it by hand, it enumerates as vendor `0x2886`, product `0x0045`.)

### If nothing appears

Nothing is broken. It just did not register the double-press. **Wait a second and try again** —
slightly faster, or slightly slower. Failing this is harmless and you can repeat it as many times as
you like. There is no way to make things worse by trying.

---

## 2. Why this is necessary

The firmware currently on the pendant **freezes before it ever switches the radio on**, so there is
no Bluetooth to talk to and nothing can be delivered wirelessly. That same firmware also **does not
have the cable trick** — the escape hatch where setting the USB serial port to 1200 baud drops the
chip into its bootloader — so the cable cannot get us in either. With both software doors missing,
**the RESET button is the only remaining way to make the chip listen.**

---

## 3. What is ready and waiting

Once `XIAO-SENSE` appears, you are dragging one file onto it. That is the whole flashing procedure.

### The two images — try A first

`/Users/omarebrahim/anticipation-builds/pendant-recovery-images-20260724/`

| file | what it is |
|---|---|
| `A-TRY-FIRST-dual-hatch-rc-internal-RC.uf2` | **Drag this one first.** Same firmware as B, except it stops relying on the external timing crystal we suspect is dead, and uses the chip's own built-in one instead. |
| `B-dual-hatch-xtal-crystal.uf2` | The control. The original verified image, still using the crystal. Keep it to compare against. |

Both also exist as `.zip` packages in the same folder for the over-the-air route, if the drive route
is ever not available.

Both images contain **both** escape hatches — the cable trick and a wireless one — so whichever you
flash, you will not be locked out again.

The folder's own `README.md` explains how to read the result, including **what it means if A fails
too** (short version: the crystal is not the fault, stop tuning clock settings, go look at power and
the antenna). I checked the file hashes in that folder today: **4 of 4 match.**

### The backup kit

`/Users/omarebrahim/anticipy-pendant-restore/` — this folder. Holds the image the pendant is
currently running, plus its full build provenance, so you can always go back.

I re-verified it today: **13 of 13 files match their recorded hashes.** One entry in
`MANIFEST.sha256` — `dfu-package/restore-to-current.zip` — points at a file that **does not exist**.
That is a known gap, not corruption; see the red list below.

### The flasher

```
/Users/omarebrahim/anticipation-builds/firmware-authorized-flash-20260723-07/macos-nordic-dfu-flasher/dist/Anticipy DFU Flasher.app/Contents/MacOS/anticipy-dfu
```

Only needed for the wireless route. Dragging a `.uf2` onto the `XIAO-SENSE` drive needs no tools at
all.

---

## 4. What actually got done

Only things that were observed. Where something was checked by deliberately breaking it and watching
it fail, I say so — that is the only kind of "it works" worth much.

### The iOS pendant work: verified, and it held up

The uncommitted iOS work (persistent Bluetooth link, background survival, first audio-path tests) was
attacked on five specific fronts and passed all five.

- **Builds clean, tests pass.** 134 tests, 3 skipped, 0 failures — against a baseline of 131/3/0. The
  count went **up by exactly 3**, and those 3 are precisely the three new tests that were added. No
  test was deleted or quietly disabled. A second test framework in the same suite reports 181 more
  tests, all passing.
- **The Bluetooth contract is untouched.** The device identifiers are byte-for-byte identical to the
  committed version. Nothing about how the phone and pendant recognise each other changed.
- **Nothing was dropped from the app's configuration.** The `anticipy` URL scheme, all three backend
  settings, and the background-audio and Bluetooth permissions were read back **out of the built
  app**, not just out of the source.
- **The "always connected" link is genuinely always connected.** Ending a recording no longer cancels
  the pending reconnect — that is the actual behavioural change, and it is wired up at app launch.
  This is not the old per-recording behaviour moved to a new file.
- **The audio gap-filling is correct, and the test that proves it has teeth.** A deliberate 10
  millisecond error was injected into the padding maths; the suite failed, off by exactly 160 audio
  samples — which is exactly 10 ms. So the check is real, not decorative. The file was then restored
  and the suite re-run clean.

### The browser round-trip proof: real, and falsified four ways

The test that claims to prove the whole chain — backend, gateway, extension, receipt — passes. More
importantly it was **broken on purpose four times and failed every time**, including a silent break
(the gateway accepts the connection but quietly never delivers commands) that a weak test would have
sailed straight through. The receipt it checks is read back out of the database and cannot be
produced without a real browser really navigating and the backend really verifying the evidence.

### The Chrome Web Store package: audited, passes

The release zip was built and inspected: correct flat layout, all four icons, no test files, no extra
permissions, and all the developer-only UI genuinely stripped. Every leftover reference to removed
buttons was individually checked and is safely guarded — the panel cannot crash on load. The release
gate that blocks developer tools from shipping was fired at 7 deliberately bad inputs and refused all
7. (It also has a real hole — see red list.)

### The new firmware image (A): built and verified, not flashed

Built in the pinned container, first try, zero new warnings. Verified **against the compiled binary,
not the source** — both escape hatches are present as raw bytes, and the actual machine code was read
to confirm it asks for the internal oscillator at the correct declared accuracy, with the calibration
handler genuinely linked in. Packaged and validated. **Nothing was flashed and nothing was written to
the pendant.**

### Disk

**5.90 GiB reclaimed** with a safety check first: every image and every git commit in the deleted
directories was proven to have a surviving copy elsewhere before anything was removed. Currently
**~13 GiB free (97% full)**. No `docker prune` was run; the pinned Nordic image is untouched.

### One thing that got fixed and is now confirmed clean

A temporary "break marker" was found left behind in the gateway source by a concurrent test run. It
was reverted. I re-checked the file today — the marker is gone and the file hash matches its clean
baseline.

Also worth noting: an earlier report warned that the good firmware image existed in only one place on
disk. **That is no longer true** — the side-by-side folder now holds a second, hash-verified copy.

---

## 5. What is still red

**1. The radio is still dead, and the diagnosis is still a hypothesis.** Everything above is
preparation. Nothing has been flashed, so we do not know whether the crystal is actually the fault.
Image A is a *test* of that idea, not a fix. This is what your button press unblocks.

**2. Image A sits exactly on a limit with no margin.** It declares its timing accuracy at 500 parts
per million, which is precisely the documented minimum the Bluetooth stack accepts. It is legal and
it is the standard default, but there is zero headroom, and it could not be confirmed whether the
precompiled library treats that boundary as "at or better" or "strictly better". If A fails with a
permission-type error from the Bluetooth stack, that is the first thing to change.

**3. Image A also costs battery life, and nobody has measured how much.** Fine for a diagnostic
image, not obviously fine for shipping.

**4. The backup kit is missing its wireless package.** `MANIFEST.sha256` lists
`dfu-package/restore-to-current.zip` and that file does not exist — only a note explaining how to
build it. Everything else in the kit verifies. This only matters if you ever need to restore over the
air rather than by dragging a file.

**5. The browser round-trip proof is not in CI.** It only runs when someone runs it by hand, because
it needs a real browser and a production key. So the thing it proves is exactly as unprotected
against future regressions as it was before the test existed.

**6. The store release gate promises more than it delivers.** Its own comment claims any new
developer control added outside the marked regions will fail the release. It will not — it only
catches six specific strings someone already thought of. This was proved: a new
"Restart local engine" button added outside every marked region **built cleanly with no complaint.**
Either fix the check or correct the comment.

**7. The browser proof writes to the only real backend there is.** There is no staging project, and
it never cleans up after itself. Roughly six extra task and evidence rows were created today. Nothing
is corrupted, but this needs a staging target before it runs routinely.

**8. That same test leaks a browser profile folder on every run.** Thirteen orphaned folders (61 MB)
were found and cleaned up. The fix is one line — add the profile directory to the cleanup block. It
matters because the disk is at 97%.

**9. Nothing has been committed.** 25 files are uncommitted on `feat/phone-otp-enrollment` — the iOS
work, the extension changes, the CI change, the new tests. Verified, but not saved anywhere but this
machine.

**10. One git lane is the sole surviving copy of a lot of history.**
`~/anticipation-lanes/firmware-final-integration` now holds the only on-disk history for 16 deleted
checkouts, and its own branch has never been pushed. If that folder is lost, that history is gone.
Push it.

**11. The disk is still at 97%.** 5.9 GiB was bought back; that is headroom, not a fix. Around 8.5
GiB sits in three separate firmware toolchain workspaces that are very likely redundant with each
other, but they were on the must-keep list so nobody touched them. Your call.

**12. Known, deliberate, not a bug — just so it does not surprise you later:** recorded audio does not
include the gap before the first sound arrives or any silence after the last one. Transcript timings
stay correct relative to the audio, but a file can be shorter than the wall-clock length of the
session.

---

## What to do first

1. Double-press `RST`. Watch for the `XIAO-SENSE` drive.
2. Drag `A-TRY-FIRST-dual-hatch-rc-internal-RC.uf2` onto it.
3. See whether the pendant starts advertising over Bluetooth.
4. Read the result table in
   `~/anticipation-builds/pendant-recovery-images-20260724/README.md` — including the row for
   "A also fails", which is a real and informative outcome, not a dead end.
