from __future__ import annotations

import base64
import io
import logging
from datetime import datetime, timezone

try:
    from PIL import Image, ImageDraw, ImageFont
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False

logger = logging.getLogger(__name__)


class DynamicWatermark:
    def __init__(self, user_id: str, session_id: str) -> None:
        self.user_id = user_id
        self.session_id = session_id

    def get_watermark_text(self) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        return f"ZeroTraceFW Secure Viewer\nUser: {self.user_id}\nSession: {self.session_id}\nTime: {timestamp}"

    def get_html_watermark_overlay(self) -> str:
        """Returns CSS and HTML div to overlay on top of web-based or rich text content."""
        text = self.get_watermark_text().replace("\n", "<br>")
        return f"""
        <style>
            .ztfw-watermark-overlay {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                pointer-events: none;
                z-index: 999999;
                display: flex;
                align-items: center;
                justify-content: center;
                opacity: 0.15;
                font-family: monospace;
                font-size: 24px;
                color: #ff0000;
                text-align: center;
                transform: rotate(-30deg);
                user-select: none;
            }}
        </style>
        <div class="ztfw-watermark-overlay">
            <div>{text}</div>
        </div>
        """

    def apply_to_image_bytes(self, image_data: bytes) -> bytes:
        """Applies a visible watermark to raw image bytes and returns the modified bytes."""
        if not _HAS_PIL:
            logger.warning("Pillow not installed. Cannot apply image watermark.")
            return image_data

        try:
            image = Image.open(io.BytesIO(image_data)).convert("RGBA")
            
            # Create a transparent layer for the watermark
            txt_layer = Image.new("RGBA", image.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(txt_layer)
            
            # Try to load a nice font, fallback to default
            try:
                # Use a larger font size relative to image width
                font_size = max(12, int(image.width * 0.05))
                font = ImageFont.truetype("arial.ttf", font_size)
            except IOError:
                font = ImageFont.load_default()
            
            text = self.get_watermark_text()
            
            # Use textbbox to get size instead of textsize (deprecated)
            left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
            text_width = right - left
            text_height = bottom - top
            
            # Position at center
            x = (image.width - text_width) // 2
            y = (image.height - text_height) // 2
            
            # Draw semi-transparent red text
            draw.text((x, y), text, fill=(255, 0, 0, 128), font=font, align="center")
            
            # Rotate the text layer by 30 degrees
            txt_layer = txt_layer.rotate(30, resample=Image.Resampling.BICUBIC, expand=1)
            
            # Paste centered on original image
            paste_x = (image.width - txt_layer.width) // 2
            paste_y = (image.height - txt_layer.height) // 2
            
            watermarked = Image.new("RGBA", image.size)
            watermarked.paste(image, (0, 0))
            watermarked.paste(txt_layer, (paste_x, paste_y), mask=txt_layer)
            
            # Convert back to original format (we'll assume PNG or JPEG)
            out_format = image.format or "PNG"
            if out_format.upper() == "JPEG":
                watermarked = watermarked.convert("RGB")
                
            out = io.BytesIO()
            watermarked.save(out, format=out_format)
            return out.getvalue()
        except Exception as e:
            logger.error(f"Failed to apply image watermark: {e}")
            return image_data
