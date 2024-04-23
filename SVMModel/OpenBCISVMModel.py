import sys
import getopt
import numpy as np
import time
from random import random as rand
from pylsl import StreamInfo, StreamOutlet, local_clock
import pyOpenBCI
import mne
from mne.preprocessing import ICA, corrmap
import matplotlib.pyplot as plt
from scipy.signal import welch, iirnotch
from scipy.stats import ttest_rel
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, f1_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

def initialize_stream(argv):
    """ Initialize the LSL stream based on command line arguments. """
    srate = 250  # Default sampling rate.
    name = 'OpenBCI_Cython_8_LSL'  # Default stream name.
    type = 'EEG'  # Default stream type.
    n_channels = 8  # Default number of channels.
    eeg_port = '/dev/ttyUSB0'  # Default EEG device port
    help_string = 'Usage: SendData.py -s <sampling_rate> -n <stream_name> -c <channels> -t <stream_type> -p <eeg_port>'
    
    try:
        opts, args = getopt.getopt(argv, "hs:c:n:t:p:", ["srate=", "channels=", "name=", "type=", "port="])
    except getopt.GetoptError:
        print(help_string)
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print(help_string)
            sys.exit()
        elif opt in ("-s", "--srate"):
            srate = float(arg)
        elif opt in ("-c", "--channels"):
            n_channels = int(arg)
        elif opt in ("-n", "--name"):
            name = arg
        elif opt in ("-t", "--type"):
            type = arg
        elif opt in ("-p", "--port"):
            eeg_port = arg

    return StreamInfo(name, type, n_channels, srate, 'float32', 'someuuid1234'), eeg_port

def preprocess_eeg(raw, srate):
    """ Preprocess the EEG data using common techniques. """
    # Apply notch filtering to remove 60 Hz power line interference
    raw = mne.filter.notch_filter(raw, srate, 60.0, trans_bandwidth=2.0, filter_length='auto', phase='zero')

    # Apply common-average referencing
    raw.set_eeg_reference("average", projection=False, verbose=False)

    # Apply bandpass filtering
    raw.filter(l_freq=0.1, h_freq=45, fir_design="firwin", verbose=False)

    # Apply ICA to remove artifacts
    ica = ICA(n_components=15, random_state=97, max_iter=800)
    ica.fit(raw)

    # Identify and remove eye blink and muscle artifacts using corrmap
    target_components, _ = corrmap(ica, template=(0, 1), threshold=0.85)
    ica.exclude = target_components
    ica.apply(raw)

    # Construct epochs
    event_id = {
        "10hz": 1010,
        "15hz": 1015,
        "20hz": 1020,
        "25hz": 1025,
        "30hz": 1030,
        "35hz": 1035,
        "40hz": 1040
    }
    events, _ = mne.events_from_annotations(raw, verbose=False)
    tmin, tmax = -1.0, 20.0  # in s
    baseline = None
    epochs = mne.Epochs(raw, events=events, event_id=list(event_id.values()), tmin=tmin, tmax=tmax, baseline=baseline, verbose=False)

    return epochs

def analyze_ssvep(epochs, outlet):
    """ Analyze the SSVEP responses in the preprocessed EEG data. """
    # Frequency-domain analysis
    fft_freqs = np.fft.fftfreq(len(epochs.times), 1 / epochs.info["sfreq"])
    fft_freqs = fft_freqs[:len(fft_freqs) // 2]

    # Compute power spectral density (PSD)
    psds, freqs = mne.time_frequency.psd_welch(epochs, fmin=0, fmax=45, n_fft=len(epochs.times), verbose=False)
    psds = 10 * np.log10(psds)  # Convert to decibels

    # Compute signal-to-noise ratio (SNR)
    snr = np.zeros((len(epochs), len(fft_freqs)))
    for i, epoch in enumerate(epochs):
        fft = np.fft.fft(epoch, axis=-1)
        fft = fft[:len(fft) // 2]
        snr[i] = 10 * np.log10(np.abs(fft) ** 2 / np.var(fft))

    # Compute statistical significance of SSVEP responses
    ssvep_detected = False
    ssvep_frequency = None
    for freq in [10, 15, 20, 25, 30, 35, 40]:
        t_stats, p_values = ttest_rel(snr[:, int(freq * len(fft_freqs) / 45)], snr[:, int(freq * len(fft_freqs) / 45)])
        print(f"Frequency: {freq} Hz, t-statistic: {t_stats:.2f}, p-value: {p_values:.4f}")
        if p_values < 0.05:
            ssvep_detected = True
            ssvep_frequency = freq
            outlet.push_sample([1, ssvep_frequency])  # Send a marker to the PhysioLabMarkerIn script with the detected frequency
            break
    if not ssvep_detected:
        outlet.push_sample([0, 0])

    # Plot PSD and SNR
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    ax1.plot(freqs, np.mean(psds, axis=0))
    ax1.set_xlabel("Frequency (Hz)")
    ax1.set_ylabel("Power (dB)")
    ax1.set_title("Power Spectral Density")

    ax2.plot(fft_freqs, np.mean(snr, axis=0))
    ax2.set_xlabel("Frequency (Hz)")
    ax2.set_ylabel("SNR (dB)")
    ax2.set_title("Signal-to-Noise Ratio")
    plt.show()

    return ssvep_detected, ssvep_frequency

def train_ssvep_classifier(epochs):
    """ Train a machine learning model to detect SSVEP responses. """
    X = epochs.get_data()
    y = epochs.events[:, -1]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Use a more robust Random Forest Classifier with hyperparameter tuning
    param_grid = {
        'n_estimators': [50, 100, 150],
        'max_depth': [5, 10, 15],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4]
    }
    clf = RandomForestClassifier(random_state=42)
    grid_search = GridSearchCV(clf, param_grid, cv=5, scoring='f1_macro')
    grid_search.fit(X_train, y_train)

    y_pred = grid_search.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='macro')
    print(f"SSVEP classification accuracy: {accuracy:.2f}")
    print(f"SSVEP classification F1-score: {f1:.2f}")

    return grid_search.best_estimator_

def send_data(outlet, srate, eeg_port):
    print("Now sending EEG data...")
    start_time = local_clock()
    sent_samples = 0

    # Initialize the EEG device
    board = pyOpenBCI.OpenBCIBoard(port=eeg_port)
    board.start_stream()

    # Initialize the raw EEG data
    raw = mne.io.RawArray(np.zeros((board.info['nchan'], 0)), mne.create_info(board.info['nchan'], srate, 'eeg'))

    # Train the SSVEP classifier
    epochs = preprocess_eeg(raw, srate)
    ssvep_classifier = train_ssvep_classifier(epochs)

    while True:
        elapsed_time = local_clock() - start_time
        required_samples = int(srate * elapsed_time) - sent_samples

        # Read EEG data from the device
        eeg_data = board.read_sample()
        raw._data = np.hstack((raw._data, np.array([eeg_data]).T))

        # Push the EEG data to the LSL stream
        outlet.push_sample(eeg_data)

        # Preprocess and analyze the EEG data
        if len(raw._data) >= srate * 20:  # Analyze every 20 seconds of data
            epochs = preprocess_eeg(raw, srate)
            ssvep_detected, ssvep_frequency = analyze_ssvep(epochs, outlet)
            raw._data = np.zeros((board.info['nchan'], 0))

        sent_samples += 1
        time.sleep(1 / srate)

def main(argv):
    info, eeg_port = initialize_stream(argv)
    outlet = StreamOutlet(info)
    send_data(outlet, info.nominal_srate(), eeg_port)

if __name__ == '__main__':
    main(sys.argv[1:])