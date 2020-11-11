import socket
import json
import netifaces


class Finder:
    broadcast_ip = '255.255.255.255'
    broadcast_port = 5055
    broadcast_hosts = []

    listen_socket = None
    listen_ip = '0.0.0.0'
    listen_port = 5055

    broadcast_string = json.dumps({
        'Command': 'SendDeviceData',
        'Caller': {
            'SupportedProtocolVersions': [1, 2, 3],
            'Port': listen_port
        }
    })

    detected_cameras = {}

    def __init__(self):
        self.broadcast_hosts = self.get_ips_of_interfaces()
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listen_socket.bind((self.listen_ip, self.listen_port))
        self.listen_socket.listen()

        self.on_change_callback = None

    @staticmethod
    def get_ips_of_interfaces():
        ips = []
        for interface in netifaces.interfaces():
            data = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in data:
                addr = [data[netifaces.AF_INET][0]['addr']]
                if addr != ['127.0.0.1']:
                    ips += addr
        return ips

    def broadcast(self):
        for ip in self.broadcast_hosts:
            broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            broadcast_socket.bind((ip, 0))
            broadcast_socket.sendto(
                self.broadcast_string.encode("utf-8"),
                (self.broadcast_ip, self.broadcast_port)
            )

    def accept(self):
        try:
            self.listen_socket.settimeout(0.5)
            connection, address = self.listen_socket.accept()
            output = ''
            while True:
                data = connection.recv(1280).decode("utf-8")
                output += data
                if not data:
                    break
            connection.close()
            j_data = json.loads(output)
            return {str(address[0]): j_data}
        except socket.timeout:
            return None

    def detect(self, hold=False):
        if not hold:
            self.detected_cameras = {}
        self.broadcast()

        while True:
            msg = self.accept()
            if msg is None:
                break
            self.detected_cameras.update(msg)

        return self.detected_cameras

    def get_detected_cameras(self):
        return self.detected_cameras

    def get_detected_ips(self):
        return self.detected_cameras.keys()

    @staticmethod
    def get_mock_data():
        return {
            "NXT-MOCK.254.44.35":
                {"Command": "DeviceDataResponse",
                 "DeviceData": {"FWVersion": "1.0.0.44", "Location": "", "Model": "rio GS29016C", "Name": "NXT",
                                "Serialnumber": "TEST3800000031",
                                "Type": "IDS NXT rio", "UniqueID": "5C:67:76:80:00:5C"},
                 "ProtocolVersion": 1},
            "NXT-MOCK.254.48.55":
                {"Command": "DeviceDataResponse",
                 "DeviceData": {"FWVersion": "1.0.0.44", "Location": "", "Model": "rio GS29016C", "Name": "NXT",
                                "Serialnumber": "TEST3800000103",
                                "Type": "IDS NXT rio", "UniqueID": "5C:67:76:80:00:BB"},
                 "ProtocolVersion": 1},
            "NXT-MOCK.254.25.16": {"Command": "DeviceDataResponse",
                                   "DeviceData": {"FWVersion": "1.0.0.61", "Location": "", "Model": "rio GS29016C",
                                                  "Name": "NXT", "Serialnumber": "TEST4103735819",
                                                  "Type": "IDS NXT rio", "UniqueID": "5C:67:76:80:00:E7"},
                                   "ProtocolVersion": 1}
        }
