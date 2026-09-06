#!/usr/bin/env python3
"""Electrical source of truth for Anticipy ANT-PROD-R0B EVT.

``net=None`` means intentional no-connect.  The native schematic generator emits
an explicit KiCad no-connect marker for every such pin.  This is a design
checkpoint; battery, RF, enclosure, and first-article validation remain gates.
"""

from __future__ import annotations

from dataclasses import dataclass
import uuid


PROJECT = "Anticipy_PROD_R0B_EVT"
SCHEMATIC_VERSION = 20230121  # KiCad 7 native format


def uid(seed: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"https://anticipy.ai/r0b/{seed}"))


ROOT_UUID = uid("schematic-root")


@dataclass(frozen=True)
class PinSpec:
    number: str
    name: str
    net: str | None
    electrical_type: str = "passive"


@dataclass(frozen=True)
class PartSpec:
    ref: str
    value: str
    footprint: str
    mpn: str
    manufacturer: str
    datasheet: str
    description: str
    pins: tuple[PinSpec, ...]
    dnp: bool = False


def p(number: str | int, name: str, net: str | None,
      electrical_type: str = "passive") -> PinSpec:
    return PinSpec(str(number), name, net, electrical_type)


def part(ref: str, value: str, footprint: str, mpn: str, manufacturer: str,
         pins: tuple[PinSpec, ...], description: str = "", datasheet: str = "",
         dnp: bool = False) -> PartSpec:
    return PartSpec(ref, value, footprint, mpn, manufacturer, datasheet,
                    description, pins, dnp)


def passive(ref: str, value: str, footprint: str, mpn: str, manufacturer: str,
            net1: str, net2: str, description: str = "") -> PartSpec:
    return part(ref, value, footprint, mpn, manufacturer,
                (p(1, "1", net1), p(2, "2", net2)), description)


RAYTAC_PIN_NAMES = {
    1:"GND",2:"GND",3:"P1.10",4:"P1.11",5:"P1.12",6:"P1.13",
    7:"P1.14",8:"P1.15",9:"P0.03/AIN1",10:"P0.29/AIN5",
    11:"P0.02/AIN0",12:"P0.31/AIN7",13:"P0.28/AIN4",
    14:"P0.30/AIN6",15:"GND",16:"P0.27",17:"P0.00/XL1",
    18:"P0.01/XL2",19:"P0.26",20:"P0.04/AIN2",21:"P0.05/AIN3",
    22:"P0.06",23:"P0.07/TRACECLK",24:"P0.08",25:"P1.08",
    26:"P1.09/TRACEDATA3",27:"P0.11/TRACEDATA2",28:"VDD",
    29:"P0.12/TRACEDATA1",30:"VDDH",31:"DCCH",32:"VBUS",33:"GND",
    34:"D-",35:"D+",36:"P0.14",37:"P0.13",38:"P0.16",39:"P0.15",
    40:"P0.18/RESET",41:"P0.17",42:"P0.19",43:"P0.21",44:"P0.20",
    45:"P0.23",46:"P0.22",47:"P1.00/TRACEDATA0",48:"P0.24",
    49:"P0.25",50:"P1.02",51:"SWDIO",52:"P0.09/NFC1",53:"SWDCLK",
    54:"P0.10/NFC2",55:"GND",56:"P1.04",57:"P1.06",58:"P1.07",
    59:"P1.05",60:"P1.03",61:"P1.01",
}

RAYTAC_NETS = {
    1:"GND",2:"GND",15:"GND",33:"GND",55:"GND",28:"3V_MAIN",
    30:"3V_MAIN",32:"VBUSOUT",34:"USB_MCU_D-",35:"USB_MCU_D+",16:"I2C_SDA",
    19:"I2C_SCL",38:"PDM_CLK",39:"PDM_DATA",42:"FLASH_SCK",
    44:"FLASH_CS",43:"FLASH_IO0",46:"FLASH_IO1",45:"FLASH_IO2",
    47:"FLASH_IO3",40:"RESET",41:"PMIC_INT",48:"ACC_INT1",
    49:"ACC_INT2",24:"HAPTIC_PWM",21:"UART_TX",20:"UART_RX",
    51:"SWDIO",53:"SWDCLK",
}


def raytac_pins() -> tuple[PinSpec, ...]:
    power = {1,2,15,28,30,32,33,55}
    return tuple(p(n, RAYTAC_PIN_NAMES[n], RAYTAC_NETS.get(n),
                   "power_in" if n in power else "bidirectional")
                 for n in range(1, 62))


PARTS: tuple[PartSpec, ...] = (
    part("U1", "MDBT50Q-1MV2", "Anticipy_R0B:Raytac_MDBT50Q_R0B",
         "MDBT50Q-1MV2", "Raytac", raytac_pins(),
         "Certified nRF52840 module; rotation 0 puts antenna at the top board edge",
         "https://www.raytac.com/download/index.php?index_id=43"),
    part("U2", "nPM1300", "Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm_EP3.45x3.45mm",
         "NPM1300-QEAA-R", "Nordic Semiconductor", (
        p(1,"BUCK1OUT","3V_MAIN","power_out"),p(2,"PVSS1","PVSS1","power_in"),
        p(3,"SW1","SW1","power_out"),p(4,"PVDD1","VSYS","power_in"),
        p(5,"SW2","SW2","power_out"),p(6,"PVSS2","PVSS2","power_in"),
        p(7,"GPIO0","PMIC_INT","bidirectional"),p(8,"GPIO1",None,"bidirectional"),
        p(9,"GPIO2",None,"bidirectional"),p(10,"GPIO3",None,"bidirectional"),
        p(11,"GPIO4",None,"bidirectional"),p(12,"VDDGPIO","3V_MAIN","power_in"),
        p(13,"SDA","I2C_SDA","bidirectional"),p(14,"SCL","I2C_SCL","input"),
        p(15,"SHPHLD","SHPHLD_BTN","bidirectional"),p(16,"VSET2","VSET2","input"),
        p(17,"VSET1","VSET1","input"),p(18,"NTC","NTC","input"),
        p(19,"VBAT","VBAT","power_in"),p(20,"VSYS","VSYS","power_out"),
        p(21,"VBUS","VBUS","power_in"),p(22,"VBUSOUT","VBUSOUT","power_out"),
        p(23,"CC1","USB_CC1","bidirectional"),p(24,"CC2","USB_CC2","bidirectional"),
        p(25,"LED0","LED_BLUE_K","open_collector"),p(26,"LED1","LED_RED_K","open_collector"),
        p(27,"LED2",None,"open_collector"),p(28,"LDO1IN","VSYS","power_in"),
        p(29,"LDO1OUT","3V_MIC","power_out"),p(30,"LDO2IN",None,"power_in"),
        p(31,"LDO2OUT",None,"power_out"),p(32,"BUCK2OUT","3V_FLASH","power_out"),
        p(33,"EP","GND","power_in")),
         "PMIC, USB charger, two bucks, two LDO/load switches",
         "https://docs.nordicsemi.com/bundle/ps_npm1300/"),
    part("U3", "LIS2DW12TR", "Package_LGA:LGA-12_2x2mm_P0.5mm",
         "LIS2DW12TR", "STMicroelectronics", (
        p(1,"SCL/SPC","I2C_SCL","input"),p(2,"CS","3V_MAIN","input"),
        p(3,"SDO/SA0","GND","bidirectional"),p(4,"SDA/SDI/SDO","I2C_SDA","bidirectional"),
        p(5,"RES",None),p(6,"GND","GND","power_in"),p(7,"GND","GND","power_in"),
        p(8,"GND","GND","power_in"),p(9,"VDD_IO","3V_MAIN","power_in"),
        p(10,"VDD","3V_MAIN","power_in"),p(11,"INT2","ACC_INT2","output"),
        p(12,"INT1","ACC_INT1","output")), "Low-power accelerometer, I2C, SA0 low",
         "https://www.st.com/resource/en/datasheet/lis2dw12.pdf"),
    part("U4", "TPD2EUSB30DRTR", "Anticipy_R0B:Texas_DRT-3_R0B",
         "TPD2EUSB30DRTR", "Texas Instruments", (
        p(1,"IO1","USB_D+","bidirectional"),p(2,"IO2","USB_D-","bidirectional"),
        p(3,"GND","GND","power_in")), "USB 2.0 data-line ESD protection",
         "https://www.ti.com/lit/ds/symlink/tpd2eusb30.pdf"),
    part("U6", "TPD2E2U06DCKR", "Package_TO_SOT_SMD:SOT-323_SC-70",
         "TPD2E2U06DCKR", "Texas Instruments", (
        p(1,"IO1","USB_CC1","bidirectional"),
        p(2,"IO2","USB_CC2","bidirectional"),
        p(3,"GND","GND","power_in")),
         "Connector-side 5.5-V CC1/CC2 shunt ESD protection; no series impedance",
         "https://www.ti.com/lit/gpn/TPD2E2U06"),
    part("U5", "MX35LF4GE4AD-Z4I",
         "Package_SON:WSON-8-1EP_8x6mm_P1.27mm_EP3.4x4.3mm",
         "MX35LF4GE4AD-Z4I", "Macronix", (
        p(1,"CS#","FLASH_CS","input"),p(2,"SO/SIO1","FLASH_IO1","bidirectional"),
        p(3,"WP#/SIO2","FLASH_IO2","bidirectional"),p(4,"GND","GND","power_in"),
        p(5,"SI/SIO0","FLASH_IO0","bidirectional"),p(6,"SCLK","FLASH_SCK","input"),
        p(7,"HOLD#/SIO3","FLASH_IO3","bidirectional"),p(8,"VCC","3V_FLASH","power_in"),
        p(9,"EP","GND","power_in")),
         "4-Gbit SLC serial NAND; firmware needs ECC, bad-block and power-loss handling",
         "https://www.macronix.com/Lists/Datasheet/Attachments/9047/MX35LF4GE4AD%2C%203V%2C%204Gb%2C%20v1.6.pdf"),
    part("MIC1", "CMM-3424DT-26165-TR", "Anticipy_R0B:SameSky_CMM-3424DT-26165-TR_TopPort_PDM",
         "CMM-3424DT-26165-TR", "Same Sky", (
        p(1,"VDD","3V_MIC","power_in"),p(2,"SELECT","GND","input"),
        p(3,"CLOCK","PDM_CLK","input"),p(4,"DATA","PDM_DATA_MIC1","output"),
        p(5,"GND","GND","power_in"),p(6,"GND","GND","power_in"),
        p(7,"GND","GND","power_in"),p(8,"GND","GND","power_in")),
         "Front-side top-port IP67 PDM microphone; SELECT low",
         "https://www.sameskydevices.com/product/resource/cmm-3424dt-26165-tr.pdf"),
    part("MIC2", "CMM-3424DT-26165-TR", "Anticipy_R0B:SameSky_CMM-3424DT-26165-TR_TopPort_PDM",
         "CMM-3424DT-26165-TR", "Same Sky", (
        p(1,"VDD","3V_MIC","power_in"),p(2,"SELECT","3V_MIC","input"),
        p(3,"CLOCK","PDM_CLK","input"),p(4,"DATA","PDM_DATA_MIC2","output"),
        p(5,"GND","GND","power_in"),p(6,"GND","GND","power_in"),
        p(7,"GND","GND","power_in"),p(8,"GND","GND","power_in")),
         "Front-side top-port IP67 PDM microphone; SELECT high",
         "https://www.sameskydevices.com/product/resource/cmm-3424dt-26165-tr.pdf"),
    part("J1", "USB4500-03-1-A", "Anticipy_R0B:USB_C_Receptacle_GCT_USB4500-03-1-A_MidMount",
         "USB4500-03-1-A", "GCT", (
        p(1,"GND_A1_B12","GND","power_in"),p(2,"VBUS_A4_B9","VBUS","power_out"),
        p(3,"SBU2_B8",None,"bidirectional"),p(4,"CC1_A5","USB_CC1","bidirectional"),
        p(5,"D-_B7","USB_D-","bidirectional"),p(6,"D+_A6","USB_D+","bidirectional"),
        p(7,"D-_A7","USB_D-","bidirectional"),p(8,"D+_B6","USB_D+","bidirectional"),
        p(9,"SBU1_A8",None,"bidirectional"),p(10,"CC2_B5","USB_CC2","bidirectional"),
        p(11,"VBUS_B4_A9","VBUS","power_out"),p(12,"GND_B1_A12","GND","power_in"),
        p("S1","SHIELD","GND"),p("S2","SHIELD","GND"),
        p("S3","SHIELD","GND"),p("S4","SHIELD","GND")),
         "0.8-mm mid-mount USB-C; 12 grouped contacts plus four plated shell stakes",
         "https://gct.co/connector/usb4500"),
    part("BT1", "PROVISIONAL <=26x15.5x4.8mm PROTECTED 10kNTC",
         "Anticipy_R0B:Battery_LiPo_3Wire_Solder_26x15.5", "BATTERY-TBD-3WIRE",
         "TBD", (p(1,"VBAT+","VBAT","power_out"),
        p(2,"NTC_10K","NTC","output"),p(3,"VBAT-","GND","power_out")),
         "DO NOT SOURCE: exact protected three-wire pack, controlled max-tolerance drawing, polarity, 10k NTC configuration, UN38.3/IEC62133/MSDS, stock and runtime are release gates"),
    part("SW1", "B3U-1000P", "Button_Switch_SMD:SW_SPST_B3U-1000P",
         "B3U-1000P", "Omron", (p(1,"A","SHPHLD_BTN"),p(2,"B","GND")),
         "Hard reset / ship-hold button; intentionally not tied to MCU"),
    part("LED1", "APHB1608LVBDSEKJ3C", "Anticipy_R0B:LED_Kingbright_APHB1608LVBDSEKJ3C",
         "APHB1608LVBDSEKJ3C", "Kingbright", (
        p(1,"BLUE_K","LED_BLUE_K","input"),p(2,"BLUE_A","VSYS","power_in"),
        p(3,"RED_K","LED_RED_K","input"),p(4,"RED_A","VSYS","power_in")),
         "Red/blue status LED on nPM1300 fixed 5-mA sinks; blue low-battery brightness is a first-article gate",
         "https://www.kingbrightusa.com/images/catalog/SPEC/APHB1608LVBDSEKJ3C.pdf"),
    part("Q1", "AO3400A", "Package_TO_SOT_SMD:SOT-23", "AO3400A",
         "Alpha & Omega Semiconductor", (p(1,"G","HAPTIC_GATE","input"),
        p(2,"S","GND","power_in"),p(3,"D","HAPTIC_NEG","open_collector")),
         "Low-side haptic MOSFET"),
    part("D1", "1N4148WS-7-F", "Diode_SMD:D_SOD-323", "1N4148WS-7-F",
         "Diodes Incorporated", (p(1,"K","3V_MAIN"),p(2,"A","HAPTIC_NEG")),
         "Active-lifecycle haptic flyback diode; KiCad pad 1 is cathode",
         "https://www.diodes.com/assets/Datasheets/ds12019.pdf"),
    part("D2", "ESD441DPYR", "Anticipy_R0B:TI_DPY0002A_X1SON",
         "ESD441DPYR", "Texas Instruments", (
        p(1,"IO","VBUS","power_in"),p(2,"GND","GND","power_in")),
         "Connector-side 5.5-V VBUS shunt ESD/surge protector; TI DPY0002A land pattern",
         "https://www.ti.com/lit/gpn/ESD441"),
    part("M1", "VCLP1020B002L", "Anticipy_R0B:Haptic_VCLP1020B002L_WirePads",
         "VCLP1020B002L", "Vybronics", (p(1,"+","3V_MAIN","power_in"),
        p(2,"-","HAPTIC_NEG","power_in")), "10-mm coin haptic, hand soldered"),
    part("NT1", "PVSS1-GND", "NetTie:NetTie-2_SMD_Pad0.5mm", "NETTIE",
         "Anticipy", (p(1,"PVSS1","PVSS1"),p(2,"GND","GND")),
         "Single-point buck-1 power-ground tie"),
    part("NT2", "PVSS2-GND", "NetTie:NetTie-2_SMD_Pad0.5mm", "NETTIE",
         "Anticipy", (p(1,"PVSS2","PVSS2"),p(2,"GND","GND")),
         "Single-point buck-2 power-ground tie"),
    passive("L1","2.2uH","Inductor_SMD:L_Murata_DFE201610P","CIGT201610EH2R2MNE",
            "Samsung Electro-Mechanics","3V_MAIN","SW1","Buck-1 inductor"),
    passive("L2","2.2uH","Inductor_SMD:L_Murata_DFE201610P","CIGT201610EH2R2MNE",
            "Samsung Electro-Mechanics","3V_FLASH","SW2","Buck-2 inductor"),
    passive("R1","10k 1%","Resistor_SMD:R_0201_0603Metric","RC0201FR-0710KL",
            "Yageo","3V_MAIN","I2C_SCL","I2C pull-up"),
    passive("R2","10k 1%","Resistor_SMD:R_0201_0603Metric","RC0201FR-0710KL",
            "Yageo","3V_MAIN","I2C_SDA","I2C pull-up"),
    passive("R3","330k 1%","Resistor_SMD:R_0201_0603Metric","RC0201FR-07330KL",
            "Yageo","VSET1","GND","Buck-1 starts at 2.7 V; firmware raises 3V_MAIN to 3.0 V"),
    passive("R4","150k 1%","Resistor_SMD:R_0201_0603Metric","RC0201FR-07150KL",
            "Yageo","VSET2","GND","Buck-2 starts at 3.0 V"),
    passive("R5","100R 1%","Resistor_SMD:R_0402_1005Metric","RC0402FR-07100RL",
            "Yageo","HAPTIC_PWM","HAPTIC_GATE","MOSFET gate resistor"),
    passive("R6","100k 1%","Resistor_SMD:R_0402_1005Metric","RC0402FR-07100KL",
            "Yageo","HAPTIC_GATE","GND","MOSFET gate pulldown"),
    passive("R7","100k 1%","Resistor_SMD:R_0402_1005Metric","RC0402FR-07100KL",
            "Yageo","3V_FLASH","FLASH_CS","Flash chip-select default high"),
    passive("R8","100R 1%","Resistor_SMD:R_0402_1005Metric","RC0402FR-07100RL",
            "Yageo","PDM_DATA_MIC1","PDM_DATA","PDM source isolation"),
    passive("R9","100R 1%","Resistor_SMD:R_0402_1005Metric","RC0402FR-07100RL",
            "Yageo","PDM_DATA_MIC2","PDM_DATA","PDM source isolation"),
    passive("R10","27R 1%","Resistor_SMD:R_0201_0603Metric","CRCW020127R0FNED",
            "Vishay Dale","USB_D+","USB_MCU_D+","Raytac-recommended USB D+ series resistor"),
    passive("R11","27R 1%","Resistor_SMD:R_0201_0603Metric","CRCW020127R0FNED",
            "Vishay Dale","USB_D-","USB_MCU_D-","Raytac-recommended USB D- series resistor"),
    passive("C1","1uF 16V X7R","Capacitor_SMD:C_0603_1608Metric","C1608X7R1C105K080AC",
            "TDK","VBUS","GND","PMIC VBUS input"),
    passive("C2","10uF 25V X5R","Capacitor_SMD:C_0603_1608Metric","GRM188R61E106MA73J",
            "Murata","VSYS","PVSS1","Buck-1 PVDD local return"),
    passive("C3","10uF 25V X5R","Capacitor_SMD:C_0603_1608Metric","GRM188R61E106MA73J",
            "Murata","VSYS","PVSS2","Buck-2 PVDD local return"),
    passive("C4","10uF 25V X5R","Capacitor_SMD:C_0603_1608Metric","GRM188R61E106MA73J",
            "Murata","VSYS","GND","System rail bulk"),
    passive("C5","1uF 16V X7R","Capacitor_SMD:C_0603_1608Metric","C1608X7R1C105K080AC",
            "TDK","VBUSOUT","GND","Protected USB output bypass"),
    passive("C6","2.2uF 16V X7R","Capacitor_SMD:C_0603_1608Metric","EMK107BB7225KA-T",
            "Taiyo Yuden","VBAT","GND","Battery input bypass"),
    passive("C7","10uF 25V X5R","Capacitor_SMD:C_0603_1608Metric","GRM188R61E106MA73J",
            "Murata","3V_MAIN","PVSS1","Buck-1 output"),
    passive("C8","10uF 25V X5R","Capacitor_SMD:C_0603_1608Metric","GRM188R61E106MA73J",
            "Murata","3V_FLASH","PVSS2","Buck-2 output"),
    passive("C9","10uF 25V X5R","Capacitor_SMD:C_0603_1608Metric","GRM188R61E106MA73J",
            "Murata","VSYS","GND","System rail second bulk"),
    passive("C10","10uF 25V X5R","Capacitor_SMD:C_0603_1608Metric","GRM188R61E106MA73J",
            "Murata","3V_MIC","GND","Microphone LDO output"),
    passive("C13","100nF 16V X5R","Capacitor_SMD:C_0201_0603Metric","C0603X5R1C104K030BC",
            "TDK","3V_MAIN","GND","PMIC logic bypass; Nordic QEAA 0201 assembler gate"),
    passive("C14","100nF 16V X7R","Capacitor_SMD:C_0402_1005Metric","C0402C104M4RAC7867",
            "KEMET","VSYS","PVSS1","Buck-1 high-frequency input bypass; Nordic QEAA ref 1.2"),
    passive("C15","100nF 16V X7R","Capacitor_SMD:C_0402_1005Metric","C0402C104M4RAC7867",
            "KEMET","VSYS","PVSS2","Buck-2 high-frequency input bypass; Nordic QEAA ref 1.2"),
    passive("C16","100nF 16V X7R","Capacitor_SMD:C_0402_1005Metric","C0402C104M4RAC7867",
            "KEMET","VSYS","GND","System high-frequency bypass; Nordic QEAA ref 1.2"),
    passive("C17","100nF 10V X7R","Capacitor_SMD:C_0402_1005Metric","C1005X7R1A104K050BC",
            "TDK","3V_FLASH","GND","Flash local bypass"),
    passive("C18","1uF 16V X7R","Capacitor_SMD:C_0603_1608Metric","C1608X7R1C105K080AC",
            "TDK","3V_FLASH","GND","Flash local bulk"),
    passive("C19","100nF 10V X7R","Capacitor_SMD:C_0402_1005Metric","C1005X7R1A104K050BC",
            "TDK","3V_MIC","GND","MIC1 local bypass"),
    passive("C20","100nF 10V X7R","Capacitor_SMD:C_0402_1005Metric","C1005X7R1A104K050BC",
            "TDK","3V_MIC","GND","MIC2 local bypass"),
    passive("C21","100nF 16V X5R","Capacitor_SMD:C_0201_0603Metric","C0603X5R1C104K030BC",
            "TDK","3V_MAIN","GND","Accelerometer VDD local bypass"),
    passive("C22","100nF 10V X7R","Capacitor_SMD:C_0402_1005Metric","C1005X7R1A104K050BC",
            "TDK","3V_MAIN","HAPTIC_NEG","Motor brush-noise capacitor"),
    passive("C23","47uF 6.3V X5R","Capacitor_SMD:C_0805_2012Metric","CC0805MKX5R5BB476",
            "Yageo","3V_MAIN","GND","Haptic rail bulk"),
    passive("C24","10uF 25V X5R","Capacitor_SMD:C_0603_1608Metric","GRM188R61E106MA73J",
            "Murata","3V_MAIN","GND","Accelerometer local bulk"),
    passive("C25","10uF 6.3V X5R","Capacitor_SMD:C_0402_1005Metric","GRM155R60J106ME15D",
            "Murata","3V_MAIN","GND","Raytac VDD/VDDH local bulk; effective capacitance is a first-article gate"),
    passive("C26","10uF 6.3V X5R","Capacitor_SMD:C_0402_1005Metric","GRM155R60J106ME15D",
            "Murata","VBUSOUT","GND","Raytac VBUS local bulk; effective capacitance is a first-article gate"),
    passive("C27","100nF 16V X5R","Capacitor_SMD:C_0201_0603Metric","C0603X5R1C104K030BC",
            "TDK","3V_MAIN","GND","Accelerometer VDDIO local bypass"),
)


TEST_NETS = (
    ("TP1","SWDIO"),("TP2","SWDCLK"),("TP3","RESET"),
    ("TP4","3V_MAIN"),("TP5","GND"),("TP6","UART_TX"),
    ("TP7","UART_RX"),("TP8","VBAT"),("TP9","VBUS"),
    ("TP10","VSYS"),("TP11","VBUSOUT"),("TP12","3V_FLASH"),
    ("TP13","3V_MIC"),("TP14","PMIC_INT"),
)

PARTS += tuple(part(ref, net, "Anticipy_R0B:PogoPad_D1.0mm", "TESTPAD",
                    "Anticipy", (p(1,net,net),), f"Factory test point: {net}")
               for ref, net in TEST_NETS)

PART_BY_REF = {item.ref: item for item in PARTS}
NETS = tuple(sorted({pin.net for item in PARTS for pin in item.pins
                     if pin.net is not None}))


def expected_nodes() -> dict[str, set[tuple[str, str]]]:
    nodes = {net: set() for net in NETS}
    for item in PARTS:
        for pin in item.pins:
            if pin.net is not None:
                nodes[pin.net].add((item.ref, pin.number))
    return nodes


def validate_spec() -> list[str]:
    errors: list[str] = []
    refs: set[str] = set()
    for item in PARTS:
        if item.ref in refs:
            errors.append(f"duplicate reference {item.ref}")
        refs.add(item.ref)
        numbers: set[str] = set()
        for pin in item.pins:
            if pin.number in numbers:
                errors.append(f"{item.ref}: duplicate pin {pin.number}")
            numbers.add(pin.number)
    if RAYTAC_NETS[32] != "VBUSOUT":
        errors.append("U1 pin 32 must use protected VBUSOUT")
    if RAYTAC_NETS[34] != "USB_MCU_D-" or RAYTAC_NETS[35] != "USB_MCU_D+":
        errors.append("U1 USB pins must be behind the 27-ohm series resistors")
    if PART_BY_REF["D1"].pins[0].net != "3V_MAIN":
        errors.append("D1 pad 1/K must connect to 3V_MAIN")
    if PART_BY_REF["SW1"].pins[0].net != "SHPHLD_BTN":
        errors.append("button must connect only to nPM1300 SHPHLD, not MCU")
    if PART_BY_REF["R10"].pins[0].net != "USB_D+" or PART_BY_REF["R10"].pins[1].net != "USB_MCU_D+":
        errors.append("R10 must bridge connector-side USB_D+ to USB_MCU_D+")
    if PART_BY_REF["R11"].pins[0].net != "USB_D-" or PART_BY_REF["R11"].pins[1].net != "USB_MCU_D-":
        errors.append("R11 must bridge connector-side USB_D- to USB_MCU_D-")
    return errors


# Board-generator-friendly, dependency-free view requested by the integration
# owner.  UUIDs and pin maps are deterministic and identical to the schematic.
COMPONENTS = tuple({
    "ref": item.ref,
    "value": item.value,
    "footprint": item.footprint,
    "mpn": item.mpn,
    "pin_nets": {pin.number: pin.net for pin in item.pins if pin.net is not None},
    "no_connect": tuple(pin.number for pin in item.pins if pin.net is None),
    "symbol_uuid": uid(f"symbol-instance-{item.ref}"),
} for item in PARTS)
COMPONENT_BY_REF = {item["ref"]: item for item in COMPONENTS}


if __name__ == "__main__":
    problems = validate_spec()
    if problems:
        raise SystemExit("\n".join(problems))
    connected = sum(pin.net is not None for item in PARTS for pin in item.pins)
    ncs = sum(pin.net is None for item in PARTS for pin in item.pins)
    print(f"{PROJECT}: {len(PARTS)} parts, {len(NETS)} nets, "
          f"{connected} connected pins, {ncs} explicit no-connect pins")
