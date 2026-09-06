# Primary-source ledger

Retrieved and checked 2026-08-27/28. Manufacturer sources are primary unless the status column says otherwise.

| Block | Primary source | Used for | Status |
|---|---|---|---|
| nPM1300-CAAA | [Nordic product specification](https://docs.nordicsemi.com/r/bundle/ps_npm1300/page/keyfeatures_html5.html) | Limits, rails and supported functions | Checked |
| nPM1300-CAAA pins | [Nordic pin assignments](https://docs.nordicsemi.com/r/bundle/ps_npm1300/page/pin.html) | All 35 ball names/numbers | Checked |
| nPM1300 reference | [Nordic CAAA Reference Layout 1.1 ZIP](https://nsscprodmedia.blob.core.windows.net/prod/software-and-other-downloads/reference-layouts/npm1300/wlcsp/npm1300-caaa-reference-layout-1_1.zip) | Config 4 topology, Gerber land, BOM values/order codes | Checked; exact source for L1/L2 and selected capacitors |
| nPM1300 mechanical | [Nordic mechanical specification](https://docs.nordicsemi.com/r/bundle/ps_npm1300/page/chapters/hw_layout/mech_spec/frontpage.html) | WLCSP body limits | Checked |
| W25N04KV | [Winbond product family](https://www.winbond.com/hq/product/code-storage-flash/qspi-nand/w25n-kv/?__locale=en) and [official document entry](https://www.winbond.com/hq/support/documentation/downloadV2022.jsp?__locale=en&xmlPath=/support/resources/.content/item/DA00-W25N04KV.html&level=1) | Pin map, voltage, raw capacity, WSON dimensions | Checked; document delivery was mirrored by Mouser because Winbond’s download UI is gated |
| IM69D128S | [Infineon datasheet](https://www.infineon.com/assets/row/public/documents/24/49/infineon-im69d128s-datasheet-en.pdf) | Pin map, body, PCB sound-hole and copper geometry | Checked |
| DRV2605L | [Texas Instruments SLOS854D](https://www.ti.com/lit/ds/symlink/drv2605l.pdf) | Pin map, supply range, bypass requirements, DSBGA body | Checked |
| Charge ESD | [Texas Instruments TPD1E10B06 datasheet](https://www.ti.com/lit/ds/symlink/tpd1e10b06.pdf) | Bidirectional protection and DPY package | Checked; assembler land review remains |
| RF antenna | [Johanson 2450AT18A0100001E Rev 4.0](https://www.johansontechnology.com/docs/3827/Antenna-2450AT18A0100001E-Rev4.0.pdf) | Body, pin orientation, 6.5 mm reference region and evaluation network | Checked; evaluation values are tune candidates only |
| Radio module | [Ezurio BL54L15U support page](https://www.ezurio.com/support/series/bl54l15u) | Public body size and list of official design files | Body checked; footprint/symbol/pin map account-gated, therefore held |
| Button | [Alps Alpine SKSCLCE010 product page](https://tech.alpsalpine.com/e/products/detail/SKSCLCE010/) | Standard supply status, side-push direction, 3.5 × 3.55 × 1.25 mm body, 1.6 N force, 0.2 mm travel, no bosses | Body/orientation checked; formal product/delivery drawing remains members-only, therefore copper held |
| FPC haptic motor | [JIE YI JYC0720/JYC0720FDRL catalog](https://jyelectronics.com.cn/coin-vibration-motors) and [DigiKey JYC720FDRL order page](https://www.digikey.ca/en/products/detail/jie-yi-electronics-limited/JYC720FDRL/21850246) | Selected off-board motor identity; 7 × 2 mm can, 3 V rating, FPC double-sided welding pads and hot-bar attachment intent | Catalog identity/electrical family checked; controlled FPC geometry, land pattern and hot-bar process are not public, therefore J3 copper held |

## Source-handling rule

No package pad, module pin or reference network is accepted from a search snippet, distributor drawing or AI memory when a manufacturer file exists. If the primary drawing cannot be obtained, the copper stays absent and the part remains a fabrication gate.
