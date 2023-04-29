from migen import *

from litex.gen import *

from litex.build.generic_platform import *

from litex.soc.cores.clock import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *

from litex.soc.cores.uart import RS232PHYTX
# Pinout finder. Generates a UART stream on each spare IO

all_pins = "A8 C11 A10 C9 B8 D11 B10 D9 A4 C5 A6 C7 B4 D5 B6 D7 E6 F6 E10 F10 A1 A13 A14 A15 A16 A18 A19 A20 A21 B1 B2 B13 B15 B16 B17 B18 B20 B21 B22 C2 C13 C14 C15 C17 C18 C19 C20 C22 D1 D2 D14 D15 D16 D17 D19 D20 D21 D22 E1 E2 E3 E13 E14 E16 E17 E18 E19 E21 E22 F1 F3 F4 F13 F14 F15 F16 F18 F19 F20 F21 G1 G2 G3 G4 G13 G15 G16 G17 G18 G20 G21 G22 H2 H3 H4 H5 H13 H14 H15 H17 H18 H19 H20 H22 J1 J2 J4 J5 J6 J14 J15 J16 J17 J19 J20 J21 J22 K1 K2 K3 K4 K6 K13 K14 K16 K17 K18 K19 K21 K22 L1 L3 L4 L5 L6 L13 L14 L15 L16 L18 L19 L20 L21 M1 M2 M3 M5 M6 M13 M15 M16 M17 M18 M20 M21 M22 N2 N3 N4 N5 N13 N14 N15 N17 N18 N19 N20 N22 P1 P2 P4 P5 P6 P14 P15 P16 P17 P19 P20 P21 P22 R1 R2 R3 R4 R6 R14 R16 R17 R18 R19 R21 R22 T1 T3 T4 T5 T6 T18 T19 T20 T21 U1 U2 U3 U5 U6 U7 U17 U18 U20 U21 U22 V2 V3 V4 V5 V7 V8 V9 V17 V18 V19 V20 V22 W1 W2 W4 W5 W6 W7 W9 W17 W19 W20 W21 W22 Y1 Y2 Y3 Y4 Y6 Y7 Y8 Y9 Y18 Y19 Y21 Y22 AA1 AA3 AA4 AA5 AA6 AA8 AA18 AA19 AA20 AA21 AB1 AB2 AB3 AB5 AB6 AB7 AB8 AB18 AB20 AB21 AB22"
known_pins = "K4"
avoid_pins = "A8 C11 A10 C9 B8 D11 B10 D9 A4 C5 A6 C7 B4 D5 B6 D7 E6 F6 E10 F10 "

import re
all_pins = re.findall("[A-Z0-9]+", all_pins)
known_pins = re.findall("[A-Z0-9]+", known_pins)
avoid_pins = re.findall("[A-Z0-9]+", avoid_pins)

unkwnon_pins = []
for pin  in all_pins:
    if pin not in known_pins and pin not in avoid_pins:
        unkwnon_pins += [pin]

unkwnon_pins = " ".join(unkwnon_pins)

class PinoutFinder(Module):
    def __init__(self, platform, free_ios):
        # uart
        uart_pads = Record([("tx", 1)])
        tuning_word = int((115200/60E6)*2**32)
        self.submodules.uart = RS232PHYTX(uart_pads, tuning_word)

        # list the IOS we want to discover
        pads = re.findall("[A-Z0-9]+", free_ios)
        print(free_ios)
        print(pads)
        pin_count = len(pads)
        print(pin_count)
        platform.add_extension([("free_ios", 0, Pins(free_ios), IOStandard("LVCMOS33")),])

        # This memory will be used to send pin name on UART
        # pins_init = [ord(c) for c in free_ios]
        pins_init = []
        for pad in pads:
            pins_init += [ord(c) for c in pad] + [ord("\r"), ord("\n") | 0x100]
        pins_init[-1] |= 0x200
        print(pins_init)
        self.specials.mem_pinname = Memory(10, len(pins_init), init=pins_init)
        self.specials.rport = rport = self.mem_pinname.get_port()

        # Pin mux: either choose default_pin_value or the UART TX pin
        pin = platform.request("free_ios")
        print(pin.nbits)
        pin_sel = Signal(max=pin_count + 1)  # select Signal for pin mux
        default_pin_value = Signal(reset=1)
        cases = {}
        for i in range(pin_count):
            self.comb += pin[i].eq(default_pin_value)
            cases[i] = pin[i].eq(uart_pads.tx)
        self.comb += Case(pin_sel, cases)


        self.comb += self.uart.sink.data.eq(rport.dat_r[0:7]),
        self.sync += [
            self.uart.sink.valid.eq(1),
            If(self.uart.sink.ready,  # byte was sent
                If(rport.dat_r & 0x200,  # all pins sent
                    rport.adr.eq(0),
                    pin_sel.eq(0),
                # ).Elif(rport.dat_r == ord(" "),
                ).Elif(rport.dat_r & 0x100,
                    pin_sel.eq(pin_sel + 1),
                ),
                rport.adr.eq(rport.adr + 1),
            )
        ]


from litex.build.generic_platform import *
from litex.build.xilinx import Xilinx7SeriesPlatform
from litex.build.openocd import OpenOCD

_io = [
    ("clk25", 0, Pins("K4"), IOStandard("LVCMOS33")),
    ("user_led", 0, Pins("A18")),

    # RGMII Ethernet (B50612D)
    ("eth_clocks", 1,  # U5
        Subsignal("tx", Pins("A1")),
        Subsignal("rx", Pins("H4")),
        IOStandard("LVCMOS33")
    ),
    ("eth", 1,
        #Subsignal("rst_n",   Pins("H2")),
        Subsignal("mdio",    Pins("G2")),
        Subsignal("mdc",     Pins("G1")),
        Subsignal("rx_ctl",  Pins("F1")),
        Subsignal("rx_data", Pins("E3 E2 E1 F3")),
        Subsignal("tx_ctl",  Pins("D1")),
        Subsignal("tx_data", Pins("B2 B2 C2 D2")),
        IOStandard("LVCMOS33")
    ),
    ("eth_clocks", 0,  # U9
        Subsignal("tx", Pins("M6")),
        Subsignal("rx", Pins("L3")),
        IOStandard("LVCMOS33")
    ),
    ("eth", 0,
        #Subsignal("rst_n",   Pins("H2")),
        Subsignal("mdio",    Pins("G2")),
        Subsignal("mdc",     Pins("G1")),
        Subsignal("rx_ctl",  Pins("R1")),
        Subsignal("rx_data", Pins("N2 N3 P1 P2")),
        Subsignal("tx_ctl",  Pins("N5")),
        Subsignal("tx_data", Pins("M5 M2 N4 P4")),
        IOStandard("LVCMOS33")
    ),
    ("sdram_clock", 0, Pins("E14"), IOStandard("LVCMOS33")),
    ("sdram", 0,
        Subsignal("a", Pins(
            "C20 C19 C13 F13 G13 G15 "
            "F14 F18 E13 E18 C14 A13")),  # address pin A11 routed but NC on M12L64322A
        Subsignal("dq", Pins(
            "F21 E22 F20 E21 F19 D22 E19 D21 "
            "K21 L21 K22 M21 L20 M22 N20 M20 "
            "B18 D20 A19 A21 A20 B21 C22 B22 "
            "G21 G22 H20 H22 J20 J22 G20 J21 "
            )),
        Subsignal("we_n",  Pins("D17")),
        Subsignal("ras_n", Pins("A14")),
        Subsignal("cas_n", Pins("D14")),
        #Subsignal("cs_n", Pins("")), # gnd
        #Subsignal("cke",  Pins("")), # 3v3
        Subsignal("ba",    Pins("D19 B13")),
        #Subsignal("dm",   Pins("")), # gnd
        IOStandard("LVCMOS33"),
        Misc("SLEWRATE=FAST")
    ),
]

_connectors = [
    ("sodimm",
        "ZERO "  # zero offset
        "GND 5V GND 5V GND 5V GND 5V GND 5V "  # 1-10
        "GND 5V NC NC ETH1_1P ETH2_1P ETH1_1N ETH2_1N NC NC "  # 11-20
        "ETH1_2N ETH2_2N ETH1_2P ETH2_2P NC NC ETH1_3P ETH2_3P ETH1_3N ETH2_3N "  # 21-30
        "NC NC ETH1_4N ETH2_4N ETH1_4P ETH2_4P NC NC GND GND "  # 31-40
        "R2 P5 P6 T6 R6 U7 T1 U6 T3 U5 "  # 41-50
        "T4 V5 T4 U1 GND GND U2 H3 U3 J1 "  # 51-60
        "V2 K1 V3 L1 W1 M1 Y1 J2 AA1 K2 "  # 61-70
        "AB1 K3 W2 G3 Y2 J4 AB2 G4 AA3 F4 "  # 71-80
        "AB3 L4 Y3 R3 W4 M3 AA4 V4 Y4 R4 "  # 81-90
        "AB5 T5 AA5 J5 Y6 J6 AB6 W5 AA6 L5 "  # 91-100
        "Y7 L6 AB7 W6 GND GND GND GND AA8 V7 "  # 101-110
        "AB8 N13 Y8 N14 W7 P15 Y9 P16 V8 R16 "  # 111-120
        "W9 N17 V9 V17 R14 P17 P14 U17 W17 T18 "  # 121-130
        "Y18 R17 AA18 U18 W19 R18 AB18 N18 Y19 R19 "  # 131-140
        "AA19 N19 V18 N15 V19 M16 AB20 M15 AA20 L15 "  # 141-150
        "AA21 L16 AB21 K14 Y21 N22 GND GND AB22 J14 "  # 151-160
        "W20 J15 Y22 J19 W21 H13 W22 H14 V20 H17 "  # 161-170
        "V22 H15 U21 G18 U20 G17 T20 G16 P19 F16 "  # 171-180
        "P20 F15 M18 E17 L19 E16 J17 D16 K18 D15 "  # 181-190
        "K19 C18 K16 C17 H18 B20 H19 B17 NC NC"  # 191-200
    )
]

class Platform(Xilinx7SeriesPlatform):
    default_clk_name   = "clk25"
    default_clk_period = 1e9/25e6

    def __init__(self, toolchain="vivado"):
        Xilinx7SeriesPlatform.__init__(self, "xc7a50tfgg484-1", _io, _connectors, toolchain=toolchain)
        self.toolchain.bitstream_commands = \
            ["set_property BITSTREAM.CONFIG.SPI_BUSWIDTH 4 [current_design]"]
        self.toolchain.additional_commands = \
            ["write_cfgmem -force -format bin -interface spix4 -size 16 "
             "-loadbit \"up 0x0 {build_name}.bit\" -file {build_name}.bin"]
        self.add_platform_command("set_property INTERNAL_VREF 0.675 [get_iobanks 34]")

    def create_programmer(self):
        bscan_spi = "bscan_spi_xc7a50t.bit"
        return OpenOCD("openocd_xc7_ft2232.cfg", bscan_spi)

    def do_finalize(self, fragment):
        Xilinx7SeriesPlatform.do_finalize(self, fragment)
        self.add_period_constraint(self.lookup_request("clk25", loose=True), 1e9/25e6)


class _CRG(LiteXModule):
    def __init__(self, platform, sys_clk_freq):
        self.rst    = Signal()
        self.cd_sys = ClockDomain()

        # # #

        # Clk/Rst.
        clk25 = platform.request("clk25")
        rst    = 0

        # PLL.
        self.pll = pll = S7PLL(speedgrade=-1)
        self.comb += pll.reset.eq(rst | self.rst)
        pll.register_clkin(clk25, 25e6)
        pll.create_clkout(self.cd_sys, sys_clk_freq)
        platform.add_false_path_constraints(self.cd_sys.clk, pll.clkin) # Ignore sys_clk to pll.clkin path created by SoC's rst.


class SoC(SoCCore):
    def __init__(self, sys_clk_freq=60e6, toolchain="trellis",
        use_internal_osc = False, **kwargs):

        platform = Platform()
        self.crg = _CRG(platform, sys_clk_freq)

        # SoCCore ----------------------------------------------------------------------------------
        SoCCore.__init__(self, platform, int(sys_clk_freq), ident="LiteX SoC on Colorlight I9+", **kwargs)

        self.submodules += PinoutFinder(platform, unkwnon_pins)


def main():
    from litex.build.parser import LiteXArgumentParser
    parser = LiteXArgumentParser(platform=Platform, description="LiteX SoC on Colorlight i9+")
    args = parser.parse_args()

    soc = SoC(
        **parser.soc_argdict
    )
    builder = Builder(soc, **parser.builder_argdict)

    if args.build:
        builder.build(**parser.toolchain_argdict)

    if args.load:
        prog = soc.platform.create_programmer()
        prog.load_bitstream(builder.get_bitstream_filename(mode="sram"))

if __name__ == "__main__":
    main()
