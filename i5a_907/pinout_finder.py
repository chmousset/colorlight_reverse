from migen import *

from litex.gen import *

from litex.build.generic_platform import *
from litex_boards.platforms import colorlight_i5a_907
from litex_boards.targets.colorlight_5a_75x import _CRG

from litex.soc.cores.clock import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *

from litex.soc.cores.uart import RS232PHYTX
# Pinout finder. Generates a UART stream on each spare IO

all_pins = "B1 B2 C3 D3 C1 E3 C2 F3 D1 F4 E2 F5 G5 F2 G4 E1 F1 G3 G2 H3 H5 J4 H4 J5 G1 J3 H2 K3 J1 K1 J2 K2 L1 M1 L2 M2 K4 L4 K5 L5 N1 L3 P2 M3 P1 M4 R1 N3 N4 R2 P3 T2 P4 R4 R3 T3 R5 M5 T4 N5 M6 N6 P6 P5 T6 R7 R6 P7 N7 T7 M7 T8 R8 N8 P8 M8 M9 T9 N9 R9 P9 CFG_P10 CFG_R10 CFG_N10 M10 T10 R11 T11 P12 P11 N11 M11 N12 T13 M12 R12 T14 R14 R13 P13 T15 P14 R15 N13 N14 R16 M13 P16 M14 P15 L14 N16 L12 K12 L13 K13 M15 L15 M16 L16 K15 J15 K16 J16 K14 H15 J14 G16 J12 H13 J13 H12 H14 G15 G14 F16 E16 G13 F15 G12 F12 E15 F13 D16 F14 C15 E14 C16 D14 C14 B15 B16 A15 A14 B14 A13 E13 C13 D13 B13 E12 C12 D12 B12 A12 E11 A11 D11 C11 E10 B11 D10 C10 A10 B10 A9 E9 C9 D9 B9 B8 D8 C8 E8 A8 B7 A7 C7 D7 B6 E7 C6 D6 A6 E6 A5 B5 D5 C5 E5 B4 D4 C4 E4 A4 B3 A3 A2"

known_pins = "P6 P11 M13 P11 M13 N8 T8 T7 C6 B13 C11 C10 A11 C9 E8  B6  B9 A6  B5  A5  B4  B3 C3  A2  B2 E2  D3  A4  E4  D4 C4  E5  D5 E6  D6  D8  A8  B8 B10 B11 E11 A9 E10 B12 D13 C12 D11 D10 E9 D9 B7 C8 C7 D7 E7 A7 M2 M1 P5 T2 P3 N6 N1 M5 N5 M6 M3 L1 L3 P2 L4 M12 M16 P5 T2 P3 L15 P13 N13 P14 M15 R15 T14 R12 R13 R14 M8 R2 P4"

avoid_pins = "T11 R11 T10 M10 N10 CFG R10 P10 P9 R9 N9 T9"

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
    def __init__(self, platform, pins):
        # uart
        uart_pads = Record([("tx", 1)])
        tuning_word = int((115200/60E6)*2**32)
        self.submodules.uart = RS232PHYTX(uart_pads, tuning_word)

        # list the IOS we want to discover
        # free_ios = "B1 C1 E3 C2 F3 D1 F4 F5 G5 F2 G4 E1 F1 G3 G2 H3 H5 J4 H4 J5 G1 J3 H2 K3 J1 K1 J2 K2 L2 K4 K5 L5 P1 M4 R1 N3 N4 R4 R3 T3 R5 T4 T6 R7 R6 P7 N7 M7 R8 P8 M9 T9 N9 R9 P9 CFG P10 CFG R10 CFG N10 M10 T10 R11 P12 N11 M11 N12 T13 T15 N14 R16 P16 M14 P15 L14 N16 L12 K12 L13 K13 L16 K15 J15 K16 J16 K14 H15 J14 G16 J12 H13 J13 H12 H14 G15 G14 F16 E16 G13 F15 G12 F12 E15 F13 D16 F14 C15 E14 C16 D14 C14 B15 B16 A15 A14 B14 A13 E13 C13 E12 D12 A12 A10 C5 A3"
        free_ios = " ".join(unkwnon_pins)
        free_ios = free_ios.replace("-", "")
        for _ in range(10):
            free_ios = free_ios.replace("  ", " ")
        pads = free_ios.split(" ")
        free_ios = " ".join(pads)
        import re
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


class SoC(SoCCore):
    def __init__(self, sys_clk_freq=60e6, toolchain="trellis",
        use_internal_osc = False, **kwargs):

        platform = colorlight_i5a_907.Platform()
        self.crg = _CRG(platform, sys_clk_freq,
            use_internal_osc = use_internal_osc,
            with_usb_pll     = False,
            with_rst         = True,
            sdram_rate       = "1:1"
        )

        # SoCCore ----------------------------------------------------------------------------------
        SoCCore.__init__(self, platform, int(sys_clk_freq), ident="LiteX SoC on Colorlight ", **kwargs)

        self.submodules += PinoutFinder(platform, unkwnon_pins)


def main():
    from litex.build.parser import LiteXArgumentParser
    parser = LiteXArgumentParser(platform=colorlight_i5a_907.Platform, description="LiteX SoC on Colorlight 5A-75X.")
    args = parser.parse_args()

    soc = SoC(
        **parser.soc_argdict
    )
    builder = Builder(soc, **parser.builder_argdict)

    if args.build:
        builder.build(**parser.toolchain_argdict)

    if args.load:
        prog = soc.platform.create_programmer()
        prog.load_bitstream(builder.get_bitstream_filename(mode="sram", ext=".svf")) # FIXME

if __name__ == "__main__":
    main()
