# Seedance Video Generator

A Python wrapper for BytePlus ModelArk's Seedance video generation API. Generate high-quality videos from text prompts and images using state-of-the-art AI models.

## Features

- 🎬 Text-to-video generation
- 🖼️ Image-to-video generation
- 📊 Automatic task polling and status tracking
- 🎨 Support for multiple video styles and parameters
- 🔧 Easy-to-use Python API

## Prerequisites

- Python 3.7+
- BytePlus ModelArk API Key

## Setup

### 1. Get Your API Key

1. Visit [BytePlus ModelArk Console](https://console.byteplus.com/ark/region:ark+ap-southeast-1/apikey)
2. Create or copy your API key

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API Key

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your API key:

```
ARK_API_KEY=your_actual_api_key_here
```

Alternatively, export it as an environment variable:

```bash
export ARK_API_KEY=your_actual_api_key_here
```

## Usage

### Basic Usage

```python
from seedance_video_generator import SeedanceVideoGenerator

generator = SeedanceVideoGenerator()

prompt = """A serene sunset over the ocean. 
--ratio 16:9 --resolution 720p --duration 5"""

result = generator.generate_video(prompt)

if result:
    print(f"Video URL: {result.output}")
```

### Run the Main Script

```bash
python seedance_video_generator.py
```

### Run Examples

```bash
# Basic text-to-video
python examples/basic_video.py

# Image-to-video (update image URL first)
python examples/image_to_video.py

# Interactive prompt selection
python examples/advanced_prompts.py
```

## Prompt Parameters

Enhance your videos with these parameters:

- `--ratio`: Aspect ratio (16:9, 1:1, 9:16, 21:9)
- `--resolution`: Video quality (720p, 1080p)
- `--duration`: Video length in seconds (1-10)
- `--camerafixed`: Camera movement (true/false)

### Example Prompts

**Photorealistic:**
```
Photorealistic style: Under a clear blue sky, a vast expanse of white daisy fields stretches out. 
The camera gradually zooms in and finally fixates on a close-up of a single daisy. 
--ratio 16:9 --resolution 720p --duration 5 --camerafixed false
```

**Cinematic:**
```
Cinematic style: A bustling city street at night, neon lights reflecting on wet pavement. 
--ratio 21:9 --resolution 1080p --duration 5 --camerafixed false
```

**Abstract:**
```
Abstract art style: Colorful paint swirling in water, creating mesmerizing patterns. 
--ratio 1:1 --resolution 720p --duration 5 --camerafixed true
```

## Available Models

- `seedance-1-5-pro-251215` (default) - Latest Seedance 1.5 Pro model
- `seedance-2-0-lite-260228` - Seedance 2.0 Lite (faster, lower cost)
- `seedance-2-0-pro-260228` - Seedance 2.0 Pro (highest quality)

Check [Model List](https://docs.byteplus.com/en/docs/ModelArk/1330310) for the latest models.

## API Reference

### SeedanceVideoGenerator

#### `__init__(api_key=None, base_url="https://ark.ap-southeast.bytepluses.com/api/v3")`

Initialize the generator.

**Parameters:**
- `api_key` (str, optional): API key. Defaults to `ARK_API_KEY` environment variable.
- `base_url` (str, optional): API base URL.

#### `generate_video(prompt, model="seedance-1-5-pro-251215", poll_interval=3)`

Generate a video from a text prompt.

**Parameters:**
- `prompt` (str): Text description with optional parameters
- `model` (str, optional): Model ID to use
- `poll_interval` (int, optional): Polling interval in seconds

**Returns:**
- Task result object with video URL or None if failed

#### `generate_video_with_image(prompt, image_url, model="seedance-1-5-pro-251215", poll_interval=3)`

Generate a video from an image and text prompt.

**Parameters:**
- `prompt` (str): Text description with optional parameters
- `image_url` (str): URL of the input image
- `model` (str, optional): Model ID to use
- `poll_interval` (int, optional): Polling interval in seconds

**Returns:**
- Task result object with video URL or None if failed

## Project Structure

```
newSeedance/
├── seedance_video_generator.py  # Main generator class
├── requirements.txt              # Python dependencies
├── .env.example                  # Example environment file
├── README.md                     # This file
└── examples/
    ├── basic_video.py           # Simple text-to-video example
    ├── image_to_video.py        # Image-to-video example
    └── advanced_prompts.py      # Multiple prompt examples
```

## Documentation

- [BytePlus ModelArk Quick Start](https://docs.byteplus.com/en/docs/ModelArk/1399008)
- [Seedance 2.0 Tutorial](https://docs.byteplus.com/en/docs/ModelArk/2291680)
- [Video Generation API](https://docs.byteplus.com/en/docs/ModelArk/1520757)
- [Prompt Guide](https://docs.byteplus.com/en/docs/ModelArk/2222480)

## Pricing

Check current pricing at [BytePlus ModelArk Pricing](https://docs.byteplus.com/en/docs/ModelArk/1544106)

## Troubleshooting

### API Key Issues
- Ensure `ARK_API_KEY` is set correctly
- Verify your API key is active in the console

### Task Failures
- Check your prompt format and parameters
- Ensure image URLs are publicly accessible
- Verify you have sufficient credits

### Import Errors
- Run `pip install -r requirements.txt`
- Ensure you're using Python 3.7+

## License

This project is for educational and development purposes. Please refer to BytePlus ModelArk's terms of service for API usage.

## Support

For API-related issues, contact BytePlus support or visit the [documentation](https://docs.byteplus.com/en/docs/ModelArk).
