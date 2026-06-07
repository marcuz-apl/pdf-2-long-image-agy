# PDF-2-Long-Image Web Application & Batch Converter

by marcuz-apl | 4 June 2026



## Intro

A premium web application and command-line tool to stitch multiple PDF pages into single long images (TIFF, PNG, or JPEG).

---



## Features

- **Modern Web Interface**: Beautiful, responsive Single-Page Application (SPA) with a premium dark glass morphism UI.
- **Batch Processing**: Convert multiple PDF files simultaneously.
- **Format Options**: Convert to TIFF (LZW compression), PNG (lossless), or JPEG (high-quality).
- **Resolution Control**: Select conversion resolution (100, 200, or 300 DPI).
- **50MB Size Checking**: Real-time client-side and backend size validation to restrict total payload sizes to 50MB.
- **Zip Archiving**: Download all successful conversions at once in a single ZIP file.
- **Automatic Server Cleanup**: A background thread running on the server purges temporary upload and output files older than 15 minutes.
- **CLI Mode**: Retains standard batch execution command-line tool.

---



## Pre-requisites

Both CLI and Web app require the `poppler` utility.

### Linux / WSL setup
```shell
sudo apt update && sudo apt install -y imagemagick poppler-utils
```

### Windows setup

To run the application on Windows, you need the pre-built Poppler binaries. You can configure Poppler in one of the following ways:

1. **Download Poppler**: Download the latest pre-built Windows binaries package (e.g. `poppler-...-x64.zip`) from the [poppler-windows releases page](https://github.com/oschwartz10612/poppler-windows/releases).
2. **Option A (Local Folder - Recommended)**:
   - Extract the downloaded ZIP file.
   - Rename the extracted folder to `poppler` and place/copy it directly inside the project root folder (so the directory `poppler/bin` exists).
   - The application is pre-configured to automatically check for this local directory first.
3. **Option B (Environment Variable)**:
   - Extract the ZIP file to any directory on your system (e.g., `C:\poppler`).
   - Add a user or system environment variable named `POPPLER_PATH` pointing to the `bin` subdirectory inside the extracted poppler folder (e.g., `C:\poppler\Library\bin`).
4. **Option C (System PATH)**:
   - Add the `bin` directory path of poppler directly to your system's `PATH` environment variable.


### Virtual Environment setup (using uv)
```shell
# Recreate the virtual environment and install dependencies
rm -rf .venv
uv venv
uv pip install -r requirements.txt
```

---



## Running the Web Application (Recommended)

Launch the web application:
```shell
# Run in virtual environment: source .venv/bin/activate
python app.py
```
Or if using `uv`:
```shell
uv run python app.py
```
Then open your browser and navigate to:
```text
http://127.0.0.1:5000
```

---



## Running with Docker

You can easily build and run this application inside a Docker container. Docker simplifies setup as it automatically packages all necessary dependencies, including `poppler-utils`.

### 1. Build the Docker Image
```shell
docker build -t pdf-2-long-image .
```

### 2. Run the Container
```shell
docker run -p 5000:5000 pdf-2-long-image
```

### 3. Open your browser and navigate to

```text
http://127.0.0.1:5000
```

---



## Running the Command-Line Tool


Place one or more PDF files in the `./inputs` folder, then run:
```shell
python app-cli.py
```
Or if using `uv`:
```shell
uv run python app-cli.py
```
By default, conversions will be saved in the `./outputs` folder in the format `{original_name}_long_image.tiff`.

You can customize the CLI execution using optional flags:
```shell
# Run batch conversion with 300 DPI resolution and PNG output format
python app-cli.py --dpi 300 --format png --input-dir ./custom_inputs --output-dir ./custom_outputs
```

---



## Technical Stack

- **Backend**: Python 3.12+, Flask (web server), pdf2image (PDF parsing), Pillow (image stitching)
- **Frontend**: HTML5, Vanilla JavaScript (asynchronous AJAX requests, drag-and-drop validation), Vanilla CSS (glass morphic styling, background glow blobs)
- **Package Manager**: UV (Astral)



## License

This project is licensed under the [MIT License](LICENSE.md).
