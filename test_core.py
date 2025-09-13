import time
import queue
from main import CommunicationManager # We can reuse this for signaling
from audio import AudioStreamer
from network import NetworkStreamer

def run_test():
    print("--- Starting Core Logic Test ---")

    # 1. Setup components, simulating the main window
    outgoing_queue = queue.Queue()
    incoming_queue = queue.Queue()
    comm_manager = CommunicationManager()

    # Mock the GUI methods that would be connected to signals
    def on_status_changed(status):
        print(f"[GUI] Status updated: {status}")

    def on_peer_connected(ip, port):
        print(f"[GUI] Peer connected: {ip}:{port}")

    comm_manager.status_changed.connect(on_status_changed)
    comm_manager.peer_connected.connect(on_peer_connected)

    local_ip = '127.0.0.1' # Use IPv4 for the test
    port = 12345

    # 2. Instantiate streamers
    print("\n--- Initializing Streamers ---")

    # In a real scenario, two separate applications would run.
    # Here, we'll create two sets of streamers to talk to each other.

    # --- Peer A ---
    print("Creating Peer A...")
    peer_a_out_q = queue.Queue()
    peer_a_in_q = queue.Queue()
    peer_a_comm = CommunicationManager()
    peer_a_comm.status_changed.connect(lambda s: print(f"[Peer A] Status: {s}"))
    peer_a_net = NetworkStreamer(local_ip, port, peer_a_out_q, peer_a_in_q, peer_a_comm)
    # Peer A will send to Peer B
    peer_a_net.set_peer(local_ip, port + 1)
    # We can't use real audio devices in the headless environment, so we pass None
    # and expect it to fail gracefully, but the network part should work.
    # Let's mock the audio part for the test.

    # --- Peer B ---
    print("Creating Peer B...")
    peer_b_out_q = queue.Queue()
    peer_b_in_q = queue.Queue()
    peer_b_comm = CommunicationManager()
    peer_b_comm.status_changed.connect(lambda s: print(f"[Peer B] Status: {s}"))
    # Peer B listens on port+1
    peer_b_net = NetworkStreamer(local_ip, port + 1, peer_b_out_q, peer_b_in_q, peer_b_comm)
    # Peer B will send back to Peer A
    peer_b_net.set_peer(local_ip, port)

    # 3. Start network streamers
    print("\n--- Starting Network Communication ---")
    peer_a_net.start()
    peer_b_net.start()

    # 4. Simulate sending data
    print("\n--- Simulating Audio Data Transfer ---")
    # Peer A sends a message to Peer B
    test_message_a = b"hello from peer a"
    print("[Peer A] Sending message...")
    peer_a_out_q.put(test_message_a)

    # Give it a moment to be received
    time.sleep(1)

    # Check if Peer B received it
    try:
        received_message_b = peer_b_in_q.get_nowait()
        print(f"[Peer B] Received message: {received_message_b.decode()}")
        if received_message_b == test_message_a:
            print("--> Test 1 SUCCESS: Peer B received Peer A's message.")
        else:
            print("--> Test 1 FAILED: Mismatched message.")
    except queue.Empty:
        print("--> Test 1 FAILED: Peer B did not receive the message.")

    # Peer B sends a message to Peer A
    test_message_b = b"hello from peer b"
    print("[Peer B] Sending message...")
    peer_b_out_q.put(test_message_b)

    time.sleep(1)

    # Check if Peer A received it
    try:
        received_message_a = peer_a_in_q.get_nowait()
        print(f"[Peer A] Received message: {received_message_a.decode()}")
        if received_message_a == test_message_b:
            print("--> Test 2 SUCCESS: Peer A received Peer B's message.")
        else:
            print("--> Test 2 FAILED: Mismatched message.")
    except queue.Empty:
        print("--> Test 2 FAILED: Peer A did not receive the message.")


    # 5. Stop streamers
    print("\n--- Stopping Streamers ---")
    peer_a_net.stop()
    peer_b_net.stop()

    print("\n--- Test Finished ---")


if __name__ == "__main__":
    run_test()
