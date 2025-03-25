import base64
from openai import OpenAI
import sounddevice as sd
import numpy as np
import io
import wave

client = OpenAI()

while True:
    question = input("Enter a phrase to repeat: ")
    completion = client.chat.completions.create(
        model="gpt-4o-audio-preview",
        modalities=["text", "audio"],
        audio={"voice": "alloy", "format": "wav"},
        messages=[
            {
                "role": "user",
                "content": "Diga isso de um jeito elaborado e fofo: " + question
            }
        ]
    )

    # Convert base64 audio to numpy array for playback
    wav_bytes = base64.b64decode(completion.choices[0].message.audio.data)
    with io.BytesIO(wav_bytes) as wav_buffer:
        with wave.open(wav_buffer, 'rb') as wav_file:
            # Get audio parameters
            sample_width = wav_file.getsampwidth()
            channels = wav_file.getnchannels()
            framerate = wav_file.getframerate()
            # Read audio data
            audio_data = wav_file.readframes(wav_file.getnframes())
            # Convert to numpy array
            dtype_map = {1: np.int8, 2: np.int16, 4: np.int32}
            audio_np = np.frombuffer(audio_data, dtype=dtype_map[sample_width])

    # Play the audio
    sd.play(audio_np, framerate)
    sd.wait()  # Wait until the audio is finished playing