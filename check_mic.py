import pyaudio

p = pyaudio.PyAudio()
print("=== Microphones disponibles ===")
for i in range(p.get_device_count()):
    d = p.get_device_info_by_index(i)
    if d['maxInputChannels'] > 0:
        print(f"[{i}] {d['name']} | channels={d['maxInputChannels']} | rate={int(d['defaultSampleRate'])}")

print("\nDevice par défaut:", p.get_default_input_device_info()['name'])
p.terminate()
