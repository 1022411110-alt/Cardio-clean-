CARDIOCLEAN DSP — ECG NOISE REDUCTION STUDIO
================================================

WHAT'S INCLUDED
- ECG_Noise_Removal.m: MATLAB signal generation, FIR filtering, SNR and CSV export.
- cardioclean_dashboard.py: PyCharm-friendly desktop dashboard for plotting results.
- requirements.txt: Python packages needed for the dashboard.

QUICK START (recommended)
1. In MATLAB / MATLAB Online, open ECG_Noise_Removal.m.
2. Run it. It creates ECG_Results.csv and MATLAB figures.
3. Download ECG_Results.csv from MATLAB Online if you are using the browser version.
4. Put ECG_Results.csv in the same folder as cardioclean_dashboard.py, or use the app's
   "Load MATLAB CSV" button to select it.
5. In PyCharm, open this project folder.
6. Open the Terminal tab and run:
      pip install -r requirements.txt
7. Run cardioclean_dashboard.py.
8. If MATLAB CSV isn't available yet, click Demo Mode to see the dashboard with a
   built-in simulated example. For your final demo, prefer loading the MATLAB CSV.
9. Click Save Graph to save a dashboard screenshot for your report.

CSV FORMAT
The MATLAB file exports four columns without headers:
time, clean ECG, noisy ECG, filtered ECG.

IMPORTANT
This is a simulated educational DSP project. It is not real patient data and is not
intended for medical diagnosis. A simple low-pass filter can reduce some noise but
may also alter meaningful ECG features.
