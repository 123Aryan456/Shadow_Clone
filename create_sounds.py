import numpy as np
from scipy.io import wavfile

def create_shoot_sound():
    sample_rate = 44100
    duration = 0.1
    t = np.linspace(0, duration, int(sample_rate * duration))
    frequency = 440
    waveform = np.sin(2 * np.pi * frequency * t) * np.exp(-10 * t)
    waveform = np.int16(waveform * 32767)
    wavfile.write('sounds/shoot.wav', sample_rate, waveform)

def create_hit_sound():
    sample_rate = 44100
    duration = 0.1
    t = np.linspace(0, duration, int(sample_rate * duration))
    frequency = 220
    waveform = np.sin(2 * np.pi * frequency * t) * np.exp(-20 * t)
    waveform = np.int16(waveform * 32767)
    wavfile.write('sounds/hit.wav', sample_rate, waveform)

def create_powerup_sound():
    sample_rate = 44100
    duration = 0.2
    t = np.linspace(0, duration, int(sample_rate * duration))
    frequency = np.linspace(440, 880, len(t))
    waveform = np.sin(2 * np.pi * frequency * t) * np.exp(-5 * t)
    waveform = np.int16(waveform * 32767)
    wavfile.write('sounds/powerup.wav', sample_rate, waveform)

def create_explosion_sound():
    sample_rate = 44100
    duration = 0.3
    t = np.linspace(0, duration, int(sample_rate * duration))
    noise = np.random.normal(0, 1, len(t))
    waveform = noise * np.exp(-10 * t)
    waveform = np.int16(waveform * 32767)
    wavfile.write('sounds/explosion.wav', sample_rate, waveform)

def create_background_music():
    sample_rate = 44100
    duration = 10.0  # 10 seconds
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Create a simple melody
    frequencies = [440, 523.25, 659.25, 783.99]  # A4, C5, E5, G5
    waveform = np.zeros_like(t)
    
    for freq in frequencies:
        waveform += np.sin(2 * np.pi * freq * t)
    
    # Add some harmonics
    waveform += 0.5 * np.sin(4 * np.pi * frequencies[0] * t)
    waveform += 0.25 * np.sin(6 * np.pi * frequencies[0] * t)
    
    # Normalize and convert to 16-bit integer
    waveform = waveform / np.max(np.abs(waveform))
    waveform = np.int16(waveform * 32767)
    
    wavfile.write('sounds/background.wav', sample_rate, waveform)

if __name__ == "__main__":
    create_shoot_sound()
    create_hit_sound()
    create_powerup_sound()
    create_explosion_sound()
    create_background_music()
    print("Sound files created successfully!") 