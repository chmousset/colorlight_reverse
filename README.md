# Colorlight pinout reverse

This repo contains tools used to reverse engineer the Colorlight I9+ LED receiver card to use it as a general-purpose Artix7 SOM.

The main tool is the `PinoutFinder` LiteX design. It simply instanciates UART that continuously send the IO name.
Then, using a simple serial port, it's possible to probe every interesting peripheral pins to determine on which FPGA IO they are connected.

JTAG boundary scan was also used to guess the pinout, as it was possible to identify patterns in IO signals (level, but also Input or Output types) to identify which pin corresponds to which function.

# i9+

https://docs.google.com/spreadsheets/d/1LuqJX827LIg408SDM6qgPPfoHgTK5UOQPo3P7uLQvb8/edit#gid=795288376

# i5a 907
Another receiver card closely related to the i5a-75 series. The Ethernet and SDRAM pinouts are identical; only the IO change.
This card is slightly more interesting than the i5a-75 as they provide a couple more headers directly connected to the FPGA IOs, a bit more buffered IOs, but it's also easier to swap the buffers as they are on the underside of the PCB.

## Manufacturer documentation
https://www.ledcontrollercard.com/media/wysiwyg/ColorLight/i5A-907%20.pdf

# Related reverse works
https://github.com/wuxx/Colorlight-FPGA-Projects/blob/master/colorlight_i9_v7.2.md

# Components
http://reverse.0cpm.org/grandstream/datasheet/W9816G6CH.pdf
https://www.esmt.com.tw/upload/pdf/ESMT/datasheets/M12L16161A(2Q).pdf
https://www.esmt.com.tw/upload/pdf/ESMT/datasheets/M12L64322A(2S).pdf
