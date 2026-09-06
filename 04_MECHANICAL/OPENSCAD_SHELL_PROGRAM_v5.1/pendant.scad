// =====================================================================
// Anticipy pendant shell  v4 — FLAT TAG
//
// v3 was wrong: board stacked BEHIND battery -> 23.8mm deep on a 26.5mm
// width (T/W = 0.90, a near-square block). v4 lays the board and battery
// END-TO-END in a single layer -> 12.6mm deep (T/W = 0.45). Half as thick.
//
// Also fixed from v3:
//   - front dot CENTERED (v3 welded it to the mic's true x = 5.5mm off
//     centre; unnecessary — there is 2-3mm of air over the board, so a
//     centred port still reaches the mic)
//   - squarer, "bulkier" silhouette: corner radii cut from a full
//     semicircle (R13.25) to R9 top / R7 bottom, edge roll R5 -> R2.6
//   - halves now actually CLICK: tongue-and-groove lip + friction pads
//     (v3 had a flat butt joint and two loose dowels)
//
// Electronics (Seeed STEP/DXF/KiCad + measured):
//   XIAO nRF52840 Sense  PCB 20.955 x 17.78 x 1.24, USB-C 8.94w x 3.21h
//   overhanging the edge 1.53, plug axis 1.60 above PCB top.
//   Headers CLIPPED FLUSH -> 3.4 below PCB.  Board stack = 7.85 thick.
//   BLL 752042 LiPo  20.5 x 43.0 x 8.0 max as-shipped.
//
// Frame: X width, Y height (+Y bail, -Y USB), Z depth, +Z FRONT.
// Parting plane Z=0. Halves print parting-face-down. No supports.
// =====================================================================

VARIANT = 1;       // 1 FIT · 2 ROOMY · 3 NOCUT(uncut pins) · 4 FIT-LOOSE
HALF = "assembly";

// v5 (2026-08-18) — fixes + options over the shipped v4:
//   FIX: battery bay bottom was clipped by the rounded bottom corners
//        (test_batfit left a 20 x 0.9 x 8.2 sliver — battery jammed 0.9mm
//        short of seating). Bottom margin 1.2 -> 2.6.
//   STORAGE=1: +SD_T depth, flat pocket for a microSD socket lying on the
//        battery's front face near its top end, wired to the board. The
//        pocket connects to the battery bay so it closes over the socket.
//   Bail widened 5.6 -> 6.2 (4mm chain / 1.6mm-wire jump ring passes).
//   USB landing relief widened for magnetic USB-C tip base plates.
STORAGE = 0;
SD_W = 19.2;  SD_L = 19.2;  SD_T = 3.6;   // pocket for Adafruit 4682 3V
                                           // microSD breakout (~18x18mm) laid
                                           // flat on the battery, + wire room

// v5.1 (2026-08-19) — additions after the Devin-night P2S print failures:
//   BATTERY=200: smaller-cell preset (502025-class). MEASURE the real cell
//        with calipers and set BAT200_* before printing — the 200 build is
//        ~33.4 x 62.7 x 12.4 and its fit proofs run against these numbers.
//   LIP_CLR_OVERRIDE >= 0 replaces the variant's lip clearance — used with
//        the coupon to regenerate halves at the measured clicking fit.
//   HALF="coupon_front"/"coupon_back" (+COUPON_NOTCH 1/2/3): ~12x22mm slices
//        of the REAL joint at a friction pad. Print coupon_back once plus
//        coupon_front at 0.16/0.22/0.28 (notch count marks which is which),
//        ~10 min total, and learn THIS printer+filament's clicking clearance
//        before committing a 3h plate. That is the fix for the "zero
//        tolerance, doesn't even try to lock" print of 2026-08-18.
BATTERY = 500;
BAT200_W = 20.4; BAT200_L = 25.4; BAT200_T = 5.4;   // 502025 nominal + wrap
LIP_CLR_OVERRIDE = -1;
COUPON_NOTCH = 0;

$fa = 2; $fs = 0.28;
EPS = 0.01;
BIG = 400;

// ------------------------- electronics --------------------------------
BAT_W = (BATTERY == 200) ? BAT200_W : 20.5;
BAT_L = (BATTERY == 200) ? BAT200_L : 43.0;
BAT_T = (BATTERY == 200) ? BAT200_T : 8.0;
BRD_W = 17.78;  BRD_L = 20.955; PCB_T = 1.24;
USB_SHELL_W = 8.94;  USB_SHELL_H = 3.21;
USB_OVERHANG = 1.53;        // receptacle face proud of the PCB edge
USB_AXIS_ABOVE_PCB = 1.60;
BRD_ABOVE_PCB = 3.21 + 0.25;      // USB shell + margin
BRD_UNDER_CLIPPED = 3.4;          // insulator + clipped stubs + solder
BRD_UNDER_PINS    = 9.4;          // untouched header posts
MIC_FROM_ANT_EDGE = 1.52;         // mic aperture, from the antenna end

// ------------------------- variants -----------------------------------
CLR       = (VARIANT == 2) ? 0.85 : 0.5;
DEPTH_PAD = (VARIANT == 2) ? 0.7  : 0.0;
PINS_CLIPPED = (VARIANT != 3);
LIP_CLR   = (LIP_CLR_OVERRIDE >= 0) ? LIP_CLR_OVERRIDE
          : (VARIANT == 4) ? 0.28 : 0.16;   // per side
CUT_PAD   = (VARIANT == 4) ? 0.35 : 0.0;

BRD_UNDER = PINS_CLIPPED ? BRD_UNDER_CLIPPED : BRD_UNDER_PINS;
BRD_T     = PCB_T + BRD_ABOVE_PCB + BRD_UNDER;   // full board stack

// ------------------------- shell numbers -------------------------------
WALL = 2.0;
WALL_MIN = 1.35;              // hard floor, enforced by envelope clipping

SD_PAD  = (STORAGE == 1) ? SD_T : 0;
BAY_T   = max(BRD_T, BAT_T) + 0.5 + DEPTH_PAD + SD_PAD;   // one shared layer
D       = BAY_T + 2*WALL;

// board sits LANDSCAPE (long edge across) at the TOP, battery below it.
// That puts the mic — and therefore the front dot — in the upper third,
// where the real pendant's dot is, and shortens the body by ~4mm.
BAT_BAY_W = BAT_W + 2*CLR;
BAT_BAY_L = BAT_L + 1.4 + CLR;
BRD_BAY_W = BRD_L + 1.0 + 2*CLR;      // board's LONG edge spans X
BRD_BAY_L = BRD_W + 1.4 + CLR;        // board's SHORT edge spans Y

// widen the shoulders so the silhouette is a substantial tag, not a bar.
// Real pendant measures H/W = 2.03; bare bays would give 2.97.
SHOULDER = 6.4;
W = max(BAT_BAY_W, BRD_BAY_W) + 2*WALL + SHOULDER;

BAIL_D    = 6.4 + CUT_PAD;   // 5mm curb chain (diag ~5.4) threads directly
BAIL_TOP  = 3.6;              // material above the bail hole
BAIL_GAP  = 2.1;              // bail hole to battery bay
GAP_BB    = 1.4;              // board bay to battery bay
BOT_MARGIN = 2.6;             // was 1.2 — the v4 batfit failure

H = BAT_BAY_L + GAP_BB + BRD_BAY_L + BAIL_GAP + BAIL_D + BAIL_TOP + BOT_MARGIN;

// squarer than v3's semicircle (was R = W/2). "bulky and square".
R_TOP  = 13.0;
R_BOT  = 11.0;
R_ROLL = 2.6;                 // edge roll; v3 used 5.0 and looked soft

// ------------------------- positions -----------------------------------
// bottom -> top: battery, gap, board (landscape), gap, bail
Y_BOT   = -H/2;
BAT_Y0  = Y_BOT + BOT_MARGIN;
BAT_Y1  = BAT_Y0 + BAT_BAY_L;
BRD_Y0  = BAT_Y1 + GAP_BB;                   // board bay bottom edge
BRD_Y1  = BRD_Y0 + BRD_BAY_L;
BAIL_Y  = BRD_Y1 + BAIL_GAP + BAIL_D/2;
// USB-C exits the RIGHT side (board's long edge runs across the pendant)
USB_SIDE_X = W/2;

// one shared depth layer, everything referenced to the FRONT inner face
Z_FRONT_IN = D/2 - WALL;
BRD_ZTOP   = Z_FRONT_IN - 0.4;               // top of USB shell
BRD_ZPCB   = BRD_ZTOP - BRD_ABOVE_PCB;       // PCB top face
BAT_ZF     = Z_FRONT_IN - 0.4 - SD_PAD;      // battery front face
                                             // (pushed back when STORAGE=1)

USB_HOLE_W = USB_SHELL_W + 0.75 + CUT_PAD;   // spans Y (pendant length)
USB_HOLE_H = USB_SHELL_H + 0.75 + CUT_PAD;   // spans Z (pendant depth)
USB_Z      = BRD_ZPCB + USB_AXIS_ABOVE_PCB;
BRD_CY     = BRD_Y0 + BRD_BAY_L/2;           // board centre line
USB_Y      = BRD_CY;

// Board landscape, USB to the right: the mic maps to x = -8.96, and sits
// 5.52 below the board centre. The dot is CENTRED in x for looks — there
// is an open cavity over the board, so the port still reaches the mic.
DOT_X = 0;
DOT_Y = BRD_CY - 5.52;
DOT_D = 2.0;

// ------------------------- checks --------------------------------------
assert(BAT_Y1 <= BAIL_Y - BAIL_D/2 - 1.0, "battery bay hits the bail");
assert(BAY_T >= BAT_T + 0.4, "bay too shallow for the cell");
assert(BAY_T >= BRD_T + 0.3, "bay too shallow for the board");
echo(str("V",VARIANT,"  W=",W," H=",H," D=",D,
  "  H/W=",round(H/W*100)/100,"  T/W=",round(D/W*100)/100,
  " | board bay ",BRD_BAY_W,"x",BRD_BAY_L," y ",BRD_Y0,"..",BRD_Y1,
  " | batt bay ",BAT_BAY_W,"x",BAT_BAY_L," y ",BAT_Y0,"..",BAT_Y1,
  " | bay depth ",BAY_T," | bail y ",BAIL_Y," d ",BAIL_D,
  " | dot (",DOT_X,",",round(DOT_Y*10)/10,")"));

// ------------------------- body ----------------------------------------
module outline2d(inset) {
    hull() {
        for (s=[-1,1]) {
            translate([s*(W/2 - R_TOP), H/2 - R_TOP]) circle(R_TOP - inset);
            translate([s*(W/2 - R_BOT), -H/2 + R_BOT]) circle(R_BOT - inset);
        }
    }
}
module body(d = 0) {           // exact inward offset by d
    minkowski() {
        translate([0,0,-(D/2 - R_ROLL)])
            linear_extrude(2*(D/2 - R_ROLL)) outline2d(R_ROLL);
        sphere(R_ROLL - d);
    }
}
module rbox(s, r) {
    hull() for (x=[r, s[0]-r], y=[r, s[1]-r], z=[r, s[2]-r])
        translate([x,y,z]) sphere(r);
}

// ------------------------- cavities -------------------------------------
module cavity_raw() {
    // board bay — opens through the parting plane so the halves close over it
    translate([-BRD_BAY_W/2, BRD_Y0 - 0.05, BRD_ZTOP - BRD_T - 0.3])
        rbox([BRD_BAY_W, BRD_BAY_L, BRD_T + 0.3 + 0.4 + 1.0], 0.8);
    // battery bay
    translate([-BAT_BAY_W/2, BAT_Y0, BAT_ZF - BAT_T - 0.5])
        rbox([BAT_BAY_W, BAT_BAY_L, BAT_T + 0.5 + 0.4 + 1.0], 0.8);
    // wire tunnel between the two bays (battery below -> board above)
    translate([-7, BAT_Y1 - 1.2, BAT_ZF - BAT_T - 0.2])
        rbox([14, GAP_BB + 2.4, BAT_T + SD_PAD], 0.8);
    // microSD socket pocket: lies flat on the battery's front face near its
    // top end, opens into the battery bay below and reaches the front
    // inner wall above; wires run through the widened tunnel to the board.
    if (STORAGE == 1)
        translate([-SD_W/2, BAT_Y1 - SD_L - 1.0, BAT_ZF - 0.1])
            rbox([SD_W, SD_L, SD_T + 0.5], 0.8);
}
module cavity() { intersection() { cavity_raw(); body(WALL_MIN); } }

// ------------------------- features --------------------------------------
module bail_hole() {
    translate([0, BAIL_Y, 0]) {
        cylinder(h = D + 4, d = BAIL_D, center = true);
        for (s = [-1,1])
            translate([0,0,s*(D/2)]) rotate([90 + s*90, 0, 0])
                translate([0,0,-0.01])
                cylinder(h = 1.0, d1 = BAIL_D + 2.0, d2 = BAIL_D);
    }
}
// port exits the RIGHT side. local z -> global +x, local y -> global y.
module usb_hole() {
    r = 0.9;
    translate([W/2 - 3, USB_Y, USB_Z]) rotate([0,90,0]) {
        hull() for (sx=[-1,1], sy=[-1,1])
            translate([sx*(USB_HOLE_H/2 - r), sy*(USB_HOLE_W/2 - r), 0])
                cylinder(h = 12, r = r, center = true);
        hull() for (sx=[-1,1], sy=[-1,1])   // outward lead-in flare
            translate([sx*(USB_HOLE_H/2 - r), sy*(USB_HOLE_W/2 - r), 3 - 1.5])
                cylinder(h = 1.55, r1 = r, r2 = r + 1.0);
    }
    // landing relief so a seated overmold clears the rolled side edge —
    // widened to 14.8 x 8.4 so magnetic USB-C tip base plates also seat.
    intersection() {
        translate([W/2 - 0.45, -20, -20]) cube([25, 40, 40]);
        translate([W/2 - 3, USB_Y, USB_Z]) rotate([0,90,0])
            hull() for (sx=[-1,1], sy=[-1,1])
                translate([sx*(8.4/2 - 2.2), sy*(14.8/2 - 2.2), 0])
                    cylinder(h = 16.2, r = 2.2, center = true);
    }
}
module dot() {
    translate([DOT_X, DOT_Y, D/2 - WALL - 1]) cylinder(h = WALL + 2, d = DOT_D);
    translate([DOT_X, DOT_Y, D/2 - 0.7]) cylinder(h = 1.6, d1 = DOT_D, d2 = DOT_D + 1.6);
}
TEXT_DEPTH = 0.5;
module text_back() {
    intersection() {
        translate([0, (BAT_Y0 + BAT_Y1)/2, -D/2 - 1])
            mirror([1,0,0]) rotate([0,0,90])
            linear_extrude(D, convexity = 10)
                text("Anticipy", size = 5.6, font = "Avenir Next:style=Medium",
                     halign = "center", valign = "center", spacing = 1.06);
        difference() { body(-0.02); body(TEXT_DEPTH); }
        translate([-BIG/2, -BIG/2, -BIG]) cube(BIG);
    }
}

// ------------------------- the click joint --------------------------------
// tongue on the BACK half, groove in the FRONT half, 4 friction pads so it
// snaps and holds itself closed for dry-fitting before any glue.
LIP_H = 1.7;  LIP_T = 1.0;  LIP_RELIEF = 0.35;
PAD_T = 0.18;                               // interference at the pads
module lip_ring(grow) {
    difference() {
        body(WALL/2 - LIP_T/2 - grow);
        body(WALL/2 + LIP_T/2 + grow);
    }
}
module lip_keepout() {                       // no lip across the port or bail
    union() {
        translate([W/2 - 2.5, USB_Y, USB_Z]) cube([12, USB_HOLE_W + 6, 30], center = true);
        translate([0, BAIL_Y, 0]) cylinder(h = 40, d = BAIL_D + 4.5, center = true);
    }
}
module friction_pads(grow) {
    for (p = [[-1, 0.30], [1, 0.30], [-1, 0.70], [1, 0.70]])
        intersection() {
            lip_ring(grow);
            translate([p[0]*W/2, Y_BOT + p[1]*H, 0])
                cylinder(h = LIP_H*2, d = 7, center = true);
        }
}
module tongue() {
    difference() {
        union() {
            intersection() {
                lip_ring(0);
                translate([-BIG/2,-BIG/2,0]) cube([BIG,BIG,LIP_H]);
            }
            intersection() {                 // pads stand slightly proud
                friction_pads(-PAD_T);
                translate([-BIG/2,-BIG/2,0]) cube([BIG,BIG,LIP_H - 0.45]);
            }
        }
        lip_keepout();
        cavity_raw();
        bail_hole();
    }
}
module groove() {
    difference() {
        intersection() {
            lip_ring(LIP_CLR);
            translate([-BIG/2,-BIG/2,-EPS]) cube([BIG,BIG,LIP_H + LIP_RELIEF]);
        }
        lip_keepout();
    }
}

// ------------------------- coupon (joint calibration) -----------------------
// A ~12x22 slice of the REAL parts through the left 0.30-height friction pad:
// coupon_back = tongue + pad, coupon_front = the groove over the same window
// (flip it over by hand to mate, exactly like closing the pendant).
// Print one back + three fronts at LIP_CLR_OVERRIDE 0.16/0.22/0.28; the
// snuggest front that still clicks home by hand = this printer's number.
// COUPON_NOTCH edge-notches (1/2/3) mark which front is which. Notches cut
// only 0.45mm into the 2.0 wall — they never reach the joint ring (0.5 in).
module coupon_box() {
    yc = Y_BOT + 0.30*H;
    translate([-W/2 - 3, yc - 11, -D]) cube([12, 22, 2*D]);
}
module coupon_notches(n) {
    yc = Y_BOT + 0.30*H;
    if (n > 0) for (i = [0:n-1])
        translate([-W/2 - 0.15, yc - 9 + 3.2*i, 0])
            cylinder(h = 3*D, d = 1.2, center = true);
}

// ------------------------- halves ------------------------------------------
module shell_common() {
    difference() {
        body(0);
        cavity();
        bail_hole();
        usb_hole();
        dot();
        text_back();
    }
}
module half_back()  {
    union() {
        intersection() { shell_common(); translate([-BIG/2,-BIG/2,-BIG]) cube(BIG); }
        tongue();
    }
}
module half_front() {
    difference() {
        intersection() { shell_common(); translate([-BIG/2,-BIG/2,0]) cube(BIG); }
        groove();
    }
}

// ------------------------- dummies -----------------------------------------
module dummies() {
    color("silver",0.65)
        translate([-BAT_W/2, BAT_Y0 + 0.5, BAT_ZF - BAT_T]) cube([BAT_W, BAT_L, BAT_T]);
    color("green",0.75)                                   // board, landscape
        translate([-BRD_L/2, BRD_CY - BRD_W/2, BRD_ZPCB - PCB_T])
            cube([BRD_L, BRD_W, PCB_T]);
    color("dimgray",0.85)                                 // USB-C, facing +x
        translate([BRD_L/2 - 7.3 + USB_OVERHANG, USB_Y - USB_SHELL_W/2, BRD_ZPCB])
            cube([7.3, USB_SHELL_W, USB_SHELL_H]);
}

// ------------------------- fit proofs (must export EMPTY) -------------------
module part_battery() {
    translate([0,0,BAT_ZF - BAT_T - 0.1])
        linear_extrude(BAT_T + 0.2) hull()
            for (sx=[-1,1], sy=[0,1])
                translate([sx*((BAT_W+0.2)/2 - 2), BAT_Y0 + 0.4 + 2 + sy*(BAT_L - 4)])
                    circle(2);
}
module part_board() {          // landscape: long edge along X, USB to +X
    union() {
        translate([0,0,BRD_ZPCB - PCB_T]) linear_extrude(PCB_T) hull()
            for (sx=[-1,1], sy=[-1,1])
                translate([sx*(BRD_L/2 - 1.9), BRD_CY + sy*(BRD_W/2 - 1.9)]) circle(1.9);
        translate([0,0,BRD_ZPCB - BRD_UNDER]) linear_extrude(BRD_UNDER - PCB_T) hull()
            for (sx=[-1,1], sy=[-1,1])
                translate([sx*(BRD_L/2 - 2.1), BRD_CY + sy*(BRD_W/2 - 2.1)]) circle(1.9);
        translate([BRD_L/2 - 7.3 + USB_OVERHANG, USB_Y - USB_SHELL_W/2, BRD_ZPCB])
            cube([7.3, USB_SHELL_W, USB_SHELL_H]);
    }
}
module part_sd() {             // the microSD socket, lying on the battery
    translate([0,0,BAT_ZF + 0.05]) linear_extrude(SD_T - 0.1) hull()
        for (sx=[-1,1], sy=[0,1])
            translate([sx*((SD_W-0.3)/2 - 1.5),
                       BAT_Y1 - 1.0 - SD_L + 0.15 + 1.5 + sy*(SD_L - 0.3 - 3)])
                circle(1.5);
}

// ------------------------- top level ---------------------------------------
// PRINT ORIENTATION: both halves go OUTER-FACE-DOWN on the textured plate.
// The tongue then stands upward (self-supporting) instead of hanging below
// the bed, and both cosmetic faces get the same matte plate finish.
if      (HALF == "front")        translate([0,0,D/2]) rotate([180,0,0]) half_front();
else if (HALF == "back")         translate([0,0,D/2]) half_back();
else if (HALF == "open_back")    { half_back(); dummies(); }
else if (HALF == "open_front")   { half_front(); dummies(); }
else if (HALF == "backtext")     { half_back(); color("red") text_back(); }
else if (HALF == "test_batfit")  difference() { part_battery(); cavity(); }
else if (HALF == "test_brdfit")  difference() { part_board(); cavity(); usb_hole(); }
else if (HALF == "test_bailclear")
    intersection() { translate([0,BAIL_Y,0]) cylinder(h=D+4,d=BAIL_D+2.6,center=true); cavity_raw(); }
else if (HALF == "test_jointgap")     // tongue must sit inside its groove
    difference() { tongue(); groove(); }
else if (HALF == "test_sdfit") {      // SD socket must fit its pocket
    if (STORAGE == 1) difference() { part_sd(); cavity(); }
}
else if (HALF == "coupon_back")
    translate([0,0,D/2]) difference() {
        intersection() { half_back(); coupon_box(); }
        coupon_notches(COUPON_NOTCH);
    }
else if (HALF == "coupon_front")
    translate([0,0,D/2]) rotate([180,0,0]) difference() {
        intersection() { half_front(); coupon_box(); }
        coupon_notches(COUPON_NOTCH);
    }
else if (HALF == "section") {
    intersection() {
        union() { half_front(); half_back(); }
        translate([-BIG,-BIG/2,-BIG/2]) cube(BIG);
    }
    dummies();
}
else { half_front(); half_back(); %dummies(); }
