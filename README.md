## BCI and Gaze-Controlled VR Game

### Overview
This project explores the integration of gaze tracking and steady-state visually evoked potential (SSVEP) technology to create an immersive and accessible virtual reality gaming experience. Players engage with moving targets - robots adorned with flickering dots - by fixating their gaze on a target, causing their brain signals to synchronize with the flickering frequency and triggering the destruction of the object in-game.

### Key Features
- Seamless integration of gaze tracking and SSVEP detection for enhanced accuracy and reliability
- Customization options to adjust flickering light frequencies and colors for individual accessibility
- Advanced signal processing techniques like notch filtering, Fast Fourier Transform, and Recursive Least Squares adaptive filtering to enhance SSVEP detection from EEG data
- Support Vector Machine model for supervised learning to differentiate SSVEP signals from background EEG activity

### Tools and APIs
- Unity Game Engine, Version 2022.3.14f1
- Varjo VR Headset with Varjo Unity Package and Varjo Base
- OpenBCI Cyton 8-Channel EEG Cap
- PhysiolabXR and Lab Streaming Layer (LSL)

### Installation and Setup
1. Clone the repository
2. Install Unity Game Engine 2022.3.14f1
3. Set up Varjo VR Headset and OpenBCI Cyton 8-Channel EEG Cap
4. Install required packages (Varjo Unity Package, PhysiolabXR, Lab Streaming Layer)
5. Build and run the Unity project

### Usage
1. Start the Unity game
2. Wear the VR headset and EEG cap
3. Fixate your gaze on the flickering targets to destroy them
4. Adjust frequencies and colors in the settings for personalized accessibility

### Acknowledgments
- Xing, X., Wang, Y., Pei, W., Guo, J., & Liu, S. (2018). A high-speed SSVEP-based BCI using low-frequency stimuli: Design and evaluation. International Journal of Neural Systems, 28(07), 1850019[1].
- Bin, G., Gao, X., Yan, Z., Hong, B., & Gao, S. (2009). An online multi-channel SSVEP-based brain–computer interface using a canonical correlation analysis method. Journal of neural engineering, 6(4), 046002.
- Multi-Frequency SSVEP Dataset. (n.d.). Retrieved from [https://github.com/xdjiang/SSVEP-Dataset](https://doi.org/10.26188/22015694.v5).
