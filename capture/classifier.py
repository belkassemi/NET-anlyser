"""Layer 7 classification based on known ports and protocol hints."""

_PORT_MAP = {
    80: "Web browsing",
    8080: "Web browsing",
    443: "Web browsing",
    8443: "Web browsing",
    53: "DNS",
    67: "DHCP",
    68: "DHCP",
    20: "File transfer",
    21: "File transfer",
    22: "File transfer",
    25: "Email",
    110: "Email",
    143: "Email",
    587: "Email",
    465: "Email",
    993: "Email",
    995: "Email",
    1935: "Streaming",
    3478: "Streaming",
    3479: "Streaming",
    19302: "Streaming",
    3074: "Gaming",
    3659: "Gaming",
    9339: "Gaming",
    27015: "Gaming",
}


def classify(src_port: int | None, dst_port: int | None, protocol: str) -> str:
    if protocol in ("ARP", "ICMP", "ICMPv6"):
        return protocol
    for port in (dst_port, src_port):
        if port and port in _PORT_MAP:
            return _PORT_MAP[port]
    return "Other"
