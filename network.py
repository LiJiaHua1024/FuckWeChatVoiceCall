import socket
import threading
import time

class NetworkStreamer:
    def __init__(self, local_ip, local_port, outgoing_queue, incoming_queue, comm_manager):
        self.local_ip = local_ip
        self.local_port = local_port
        self.outgoing_queue = outgoing_queue
        self.incoming_queue = incoming_queue
        self.comm_manager = comm_manager

        self.peer_address = None

        # Try creating an IPv6 socket first, with a fallback to IPv4
        try:
            self.sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0) # For dual-stack
            print("Socket created with AF_INET6 (IPv6).")
        except OSError:
            print("IPv6 not supported, falling back to AF_INET (IPv4).")
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.sock.setblocking(False)

        try:
            # For IPv4, local_ip might need to be adjusted if it's '::'
            bind_ip = self.local_ip
            if self.sock.family == socket.AF_INET and bind_ip == '::':
                bind_ip = '0.0.0.0' # Bind to all interfaces for IPv4

            self.sock.bind((bind_ip, self.local_port))
            print(f"Socket bound to {self.local_ip}:{self.local_port}")
        except OSError as e:
            print(f"Error binding socket: {e}")
            self.comm_manager.status_changed.emit(f"Error: Port {self.local_port} in use.")
            raise

        self.is_running = False
        self.thread = None

    def set_peer(self, peer_ip, peer_port):
        self.peer_address = (peer_ip, peer_port)
        print(f"Peer address set to {self.peer_address}")

    def start(self):
        self.is_running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print("Network streamer started")

    def stop(self):
        self.is_running = False
        if self.thread:
            # Add a small delay to allow the loop to exit gracefully
            self.thread.join(timeout=0.1)
        self.sock.close()
        print("Network streamer stopped")

    def _run(self):
        while self.is_running:
            # Send data if a peer is set
            if self.peer_address:
                try:
                    data = self.outgoing_queue.get_nowait()
                    self.sock.sendto(data, self.peer_address)
                except Exception: # queue empty
                    pass

            # Receive data
            try:
                data, addr = self.sock.recvfrom(4096)

                # If we don't have a peer, this is an incoming call.
                if not self.peer_address:
                    self.set_peer(addr[0], addr[1])
                    # Emit signal to update GUI
                    self.comm_manager.peer_connected.emit(addr[0], addr[1])

                # Only accept data from the connected peer
                if self.peer_address and addr[0] == self.peer_address[0] and addr[1] == self.peer_address[1]:
                    self.incoming_queue.put(data)

            except BlockingIOError:
                # No data, sleep briefly to prevent high CPU usage
                time.sleep(0.001)
                pass
            except Exception as e:
                if self.is_running:
                    print(f"Error in network loop: {e}")
                    break
