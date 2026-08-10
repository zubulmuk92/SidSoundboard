import miniaudio

devices = miniaudio.Devices()
playbacks = devices.get_playbacks()
print("Playback devices:")
for p in playbacks:
    print(f"- {p['name']} ({p['id']})")
