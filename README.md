# ECG Digital Signal Denoising App

A web application for denoising ECG digital signals. This application enables users to upload ECGs in binary image format and a CSV file containing ECG file names, and denoise the ECGs.

## Features

- **Upload CSV Files**: Upload CSV files containing ECG file names
- **Prepare raw ECG images and ECGs in binary image format**: Upload your raw ECG images to 'raw_img' and your ECGs in binary image format to 'asset'
- **Denoise ECGs**: Denoise ECG digital signals in a convenient way
- **Track Progress**: Automatically track denoising progress with timestamps

## Required CSV Format

The CSV file should contain the following columns:
- `ecg`: Name of the ECG in binary images


A new column `last_update` will be automatically added to track when each record was last annotated.

## Installation

1. Clone this repository:
```
git clone <repository-url>
cd signal_denoising
```

2. Install the required dependencies:
```
pip install -r requirements.txt
```

3. Run the application:
```
python main.py
```

4. Open your browser and navigate to `http://localhost:5000`

## Workflow

1. **Upload Page**: Upload your CSV file containing ECG file names
2. **Table Page**: View all ECGs, check annotation status, and select ECG to denoise
3. **Denoising Page**: View raw and binary images of ECGs, and denoise signals

## Notes

- All annotations directly modify the source CSV file
- The last_update column is automatically updated with timestamps when annotations are saved
