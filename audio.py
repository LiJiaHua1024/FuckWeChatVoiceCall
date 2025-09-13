import pyaudio
import threading
import queue
import audioop

class AudioStreamer:
    def __init__(self, input_device_index, output_device_index, outgoing_queue, incoming_queue):
        # Audio parameters
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 8000

        # Device indices
        self.input_device_index = input_device_index
        self.output_device_index = output_device_index

        # Queues for thread-safe data transfer
        self.outgoing_queue = outgoing_queue
        self.incoming_queue = incoming_queue

        # PyAudio instance
        self.p = pyaudio.PyAudio()

        # NOTE: We are not using any encoder/decoder for simplicity with audioop
        # self.encoder = opuslib.Encoder(self.RATE, self.CHANNELS, opuslib.APPLICATION_VOIP)
        # self.decoder = opuslib.Decoder(self.RATE, self.CHANNELS)

        # Streams
        self.input_stream = None
        self.output_stream = None

        # Threading control
        self.is_running = False
        self.thread = None

    def start(self):
        self.is_running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print("Audio streamer started")

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join() # Wait for the thread to finish
        self.close_streams()
        print("Audio streamer stopped")

    def _run(self):
        self.open_streams()

        # Start two threads: one for sending, one for receiving
        send_thread = threading.Thread(target=self._send_audio, daemon=True)
        receive_thread = threading.Thread(target=self._receive_audio, daemon=True)

        send_thread.start()
        receive_thread.start()

        send_thread.join()
        receive_thread.join()

    def _send_audio(self):
        """ Reads from microphone, encodes, and puts data into the outgoing queue. """
        while self.is_running:
            try:
                data = self.input_stream.read(self.CHUNK, exception_on_overflow=False)
                # Compress data using G.711 μ-law
                compressed_data = audioop.lin2ulaw(data, self.p.get_sample_size(self.FORMAT))
                self.outgoing_queue.put(compressed_data)
            except Exception as e:
                print(f"Error in sending audio: {e}")
                break

    def _receive_audio(self):
        """ Gets data from the incoming queue, decodes, and plays it. """
        while self.is_running:
            try:
                compressed_data = self.incoming_queue.get()
                if compressed_data is None: # Sentinel value to stop
                    break
                # Decompress data using G.711 μ-law
                decoded_data = audioop.ulaw2lin(compressed_data, self.p.get_sample_size(self.FORMAT))
                self.output_stream.write(decoded_data)
            except Exception as e:
                print(f"Error in receiving audio: {e}")
                break

    def open_streams(self):
        try:
            self.input_stream = self.p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK,
                input_device_index=self.input_device_index
            )
            self.output_stream = self.p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                output=True,
                frames_per_buffer=self.CHUNK,
                output_device_index=self.output_device_index
            )
            print("Audio streams opened")
        except Exception as e:
            print(f"Error opening audio streams: {e}")
            self.is_running = False

    def close_streams(self):
        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()
        if self.output_stream:
            self.output_stream.stop_stream()
            self.output_stream.close()
        self.p.terminate()
        print("Audio streams closed")
