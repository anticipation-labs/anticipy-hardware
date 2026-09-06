# Assembly, like you are two

An adult does all soldering and every battery step.

## First: build the little board sandwich

1. Put the microSD BFF behind the XIAO.
2. Use the included short headers or short insulated wires.
3. Match every printed pin label exactly.  Do not guess.
4. Keep the XIAO microphone facing the three tiny lid holes.
5. Put the 32 GB card in the BFF.

## Second: make the tiny motor switch

The XIAO pin cannot safely power the motor by itself.  The transistor is a tiny
electronic finger that turns the motor on.

1. Lay the PN2222 transistor flat.
2. Wire the 1 kOhm resistor from the XIAO haptic pin to the transistor base.
3. Wire the 100 kOhm resistor from base to ground.
4. Wire the motor through the transistor as a low-side switch.
5. Put the diode across the motor; the marked end points to positive power.
6. Put the 100 nF capacitor across the motor.
7. Put the 100 uF capacitor across the motor supply, matching plus and minus.
8. Heat-shrink every bare joint.  The finished flat bundle must stay inside
   the printed 12 x 8 x 4 mm driver pocket.

## Third: put things in their homes

1. Cut a thin foam pad for the bottom of the battery pocket.
2. Set the protected battery in the large left pocket.  Do not fold, puncture,
   squeeze, screw into or hot-glue the pouch.
3. Add tiny foam strips only at loose battery edges.
4. Put the XIAO/microSD sandwich in the right pocket with USB facing the USB
   opening and the card facing the card opening.
5. Add a soft lid pad over the board.  It should touch gently, not crush it.
6. Stick the motor inside its round lid pocket with thin tape; add a Kapton
   strap across it as backup.
7. Put the insulated motor-switch bundle in its rectangular lid pocket and
   hold it with Kapton tape.
8. Insert the printed button from inside the lid, then place the real switch
   below it.  Use the shortest plunger that clicks and releases freely.
9. Route all wires through the open channels.  Nothing crosses a screw post.

## Fourth: test before closing

1. With the case open, flash the firmware by USB.
2. Test microphone recording.
3. Test Bluetooth to the iPhone.
4. Walk away from the phone and record to microSD.
5. Reconnect and verify backlog transfer.
6. Press the button 100 times.
7. Buzz the motor 100 times.
8. Charge it while it sits on a nonflammable surface.  Never charge it while
   worn or unattended.
9. Run one complete 16-hour recording test with the case loosely closed.

## Last: close it so it cannot rattle

1. Shake the open unit gently.  If a part clicks, add one tiny foam shim at an
   edge—not on top of a connector and not across the antenna.
2. Place the lid lip inside the base.
3. Install exactly two M1.4 x 5 mm screws.
4. Stop turning as soon as the lid is seated.  Do not overtighten PLA.
5. Shake it again.  Silence means the parts are captured.  A rattle means open
   it and add a foam edge shim; do not simply tighten harder.

