# Mavlink-tag

On boarding task for a hardware/software developer. This task point is to create a public python tools that are meant to help users of Mavlink based drones with debugging their setups. The user should be capable of capturing Mavlink packets using serial line. Optionally, it can support capturing on TCP/UDP socket. Traditionally, there is a tool called Mavlink Proxy that can be configured to connect serial line and then forward the Mavlink packets to the TCP/UDP endpoint, which can be captured by additional tools. The main point of this package is to make this process easier and omit the need for using custom mavlink dialects and complicated logic added by the Mavlink Proxy. There are python libraries that are capable of parsing the Mavlink packets, which can be used.

Mavlink Pcaps can be viewed inside the Wireshark with plugin to ease the development.

Use cases:
  * User should be able to open a serial line to capture all Mavlink packets to Pcap. 
    * (Optional/Future) Should be able to capture the packets from TCP/UDP socket. (Consideration for the architecture)\
      * Probably can be done by tcpdump tool, which is for normal user hard to use.
      * Can be replaced by comprehensive guide inside a Readme documentation.
      * Or by convenient invocation by the python tool. (Might interfere with windows compatibility)
  * User should be able to replay the Pcap file back to the serial line. (Used by us when customer sent us a capture of their mavlink traffic)
    * (Optional/Future) Should be able to replay the packets to TCP/UDP destination. (Consideration for the architecture)
      * Usually would be done using a tcpreplay tool, which is for normal user hard to use.
      * Can be replaced by comprehensive guide inside a Readme documentation.
      * Or by convenient invocation by the python tool. (Might interfere with windows compatibility)
  * User should be able to specify filter based on traditional mavlink addressing, or a set of mavlink packet types.
  * User should be able to install and use the tool according to comprehensive Readme and help of the CLI tools. (PyPI)
  * Tool should be compatible with Linux/Windows/MacOS
  * Tool should meet standard programmer requirements for maintainable package. 



Links:
 * https://ardupilot.org/mavproxy/
 * https://github.com/ArduPilot/MAVProxy
 * https://mavlink.io/en/guide/wireshark.html
 * https://github.com/Parrot-Developers/mavlink/blob/master/pymavlink/examples/mav2pcap.py
 * https://mavlink.io/en/guide/serialization.html