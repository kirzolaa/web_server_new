import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

# Pulse parameters
tau = 8e-15  # pulse duration in seconds (e.g., 8 fs)
omega_0 = 2 * np.pi * 3e8 / (800e-9)  # carrier frequency for 800 nm light (approx)
E0 = 1.0  # amplitude

# Time grid
dt = tau / 10000  # finer time resolution
t = np.arange(-tau, tau, dt)

# Electric field with sin^2 envelope
E_t = E0 * np.sin(np.pi * t / tau)**2 * np.cos(omega_0 * t)
E_t[t < -tau/2] = 0
E_t[t > tau/2] = 0

# Fourier transform
E_w = np.fft.fftshift(np.fft.fft(E_t))
freq = np.fft.fftshift(np.fft.fftfreq(len(E_t), dt))

# Convert frequency to energy in eV
hbar = 6.582119569e-16  # Planck's constant in eV*s
energy = hbar * 2 * np.pi * freq

# Spectral intensity
intensity = np.abs(E_w)**2

# Find FWHM
half_max = np.max(intensity) / 2

# Interpolation for better root finding
interp_func = interp1d(energy, intensity - half_max, kind='linear', fill_value="extrapolate")
fine_energy = np.linspace(energy[0], energy[-1], 10000)
fine_intensity = interp_func(fine_energy)

# Find crossings of half maximum
crossings = np.where(np.diff(np.sign(fine_intensity)))[0]
if len(crossings) >= 2:
    fwhm = fine_energy[crossings[-1]] - fine_energy[crossings[0]]
else:
    fwhm = None

# Plot spectrum
plt.figure(figsize=(8, 5))
plt.plot(energy, intensity, label='Spectrum')
plt.axhline(half_max, color='r', linestyle='--', label='Half Max')

if fwhm is not None:
    plt.axvline(fine_energy[crossings[0]], color='g', linestyle='--', label='FWHM Start')
    plt.axvline(fine_energy[crossings[-1]], color='g', linestyle='--', label='FWHM End')
    plt.title(f'Spectrum of Sin²-shaped Electric Field Pulse (FWHM: {fwhm:.3f} eV)')
else:
    plt.title('Spectrum of Sin²-shaped Electric Field Pulse (FWHM not found)')

plt.xlabel('Energy (eV)')
plt.ylabel('Spectral Intensity |E(w)|^2')
plt.legend()
plt.xlim([1.5, 4.5])  # Adjust as needed
plt.grid()
plt.show()
