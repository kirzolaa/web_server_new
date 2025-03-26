import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy.interpolate import interp1d
tau = 8e-15   # pulse duration in seconds , based on Otabek's plots
omega_0 = 2 * np.pi * 3e8 / (800e-9)  # carrier frequency for 800 nm light (approx)
E0 = 1.0  
dt = tau / 10000
t = np.arange(-tau, tau, dt)

E_t = E0 * np.sin(np.pi * t / tau)**2 * np.cos(omega_0 * t)
E_t[t < -tau/2] = 0
E_t[t > tau/2] = 0
E_w = np.fft.fftshift(np.fft.fft(E_t)) # numpy has a fftshift function for fast fourier transform
freq = np.fft.fftshift(np.fft.fftfreq(len(E_t), dt))


hbar = 6.582119569e-16  # Planck's constant in eV*s
energy = hbar * 2 * np.pi * freq

intensity = np.abs(E_w)**2
half_max = np.max(intensity) / 2
interp = interp1d(energy, intensity - half_max, kind='linear')
roots = interp.roots()

if len(roots) >= 2:
    fwhm = roots[-1] - roots[0]
else:
    fwhm = None

# Plot spectrum
plt.figure(figsize=(8, 5))
plt.plot(energy, intensity)
plt.axhline(half_max, color='r', linestyle='--', label='Half Max')
if fwhm is not None:
    plt.axvline(roots[0], color='g', linestyle='--')
    plt.axvline(roots[-1], color='g', linestyle='--')
    plt.title(f'Spectrum of Sin²-shaped Electric Field Pulse (FWHM: {fwhm:.3f} eV)')
else:
    plt.title('Spectrum of Sin²-shaped Electric Field Pulse (FWHM not found)')

plt.xlabel('Energy (eV)')
plt.ylabel('Spectral Intensity |E(w)|^2')
plt.grid()
plt.show()