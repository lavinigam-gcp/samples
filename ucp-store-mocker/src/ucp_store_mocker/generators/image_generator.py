"""Product image generator using Gemini API."""

import asyncio
import os
from pathlib import Path
from typing import Any, Optional

from ucp_store_mocker.config.schema import StoreConfig


class ProductImageGenerator:
    """Generate product images using Gemini API."""

    def __init__(self, config: StoreConfig):
        self.config = config.catalog.images
        self.api_key = os.getenv("GEMINI_API_KEY")
        self._client = None

    @property
    def client(self):
        """Lazy-load Gemini client."""
        if self._client is None:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "google-genai package is required for image generation. "
                    "Install with: pip install google-genai"
                )
        return self._client

    async def generate_product_image(self, product: dict, output_dir: Path) -> Optional[str]:
        """Generate an image for a single product."""
        if not self.api_key:
            # Return placeholder path when no API key
            return self._create_placeholder(product, output_dir)

        try:
            prompt = self._build_prompt(product)

            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.config.model,
                contents=[prompt],
                config={
                    "response_modalities": ["IMAGE"],
                }
            )

            # Save image
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        image_path = output_dir / f"{product['id']}.png"
                        with open(image_path, 'wb') as f:
                            f.write(part.inline_data.data)
                        return str(image_path)

            return self._create_placeholder(product, output_dir)

        except Exception as e:
            print(f"Warning: Image generation failed for {product['id']}: {e}")
            return self._create_placeholder(product, output_dir)

    def _build_prompt(self, product: dict) -> str:
        """Build image generation prompt from product data."""
        style_descriptions = {
            "product-photography": "professional product photography, studio lighting",
            "lifestyle": "lifestyle product shot, natural setting",
            "minimal": "minimalist product shot, clean composition",
        }

        style = style_descriptions.get(self.config.style, self.config.style)
        background = self.config.background

        return f"""Professional e-commerce product image of {product['title']}.
Category: {product.get('category', 'General')}.
Style: {style}.
Background: {background}.
High quality, centered product shot, suitable for online store.
No text or watermarks."""

    async def generate_batch(
        self,
        products: list[dict],
        output_dir: Path
    ) -> dict[str, str]:
        """Generate images for multiple products with rate limiting."""
        results = {}
        output_dir.mkdir(parents=True, exist_ok=True)

        batch_size = self.config.batch_size

        for i in range(0, len(products), batch_size):
            batch = products[i:i + batch_size]

            # Process batch concurrently
            tasks = [
                self.generate_product_image(product, output_dir)
                for product in batch
            ]
            paths = await asyncio.gather(*tasks, return_exceptions=True)

            for product, path in zip(batch, paths):
                if isinstance(path, Exception):
                    path = self._create_placeholder(product, output_dir)
                if path:
                    results[product['id']] = path

            # Rate limiting between batches
            if i + batch_size < len(products):
                await asyncio.sleep(1)

        return results

    def _create_placeholder(self, product: dict, output_dir: Path) -> str:
        """Create a placeholder image when generation fails or is disabled."""
        # Create a simple SVG placeholder
        product_id = product['id']
        title = product.get('title', 'Product')[:30]
        category = product.get('category', 'General')

        svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400">
  <rect width="400" height="400" fill="#f0f0f0"/>
  <rect x="50" y="100" width="300" height="200" fill="#e0e0e0" rx="10"/>
  <text x="200" y="190" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" fill="#666">{title}</text>
  <text x="200" y="220" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#999">{category}</text>
  <text x="200" y="350" text-anchor="middle" font-family="Arial, sans-serif" font-size="10" fill="#ccc">{product_id}</text>
</svg>'''

        image_path = output_dir / f"{product_id}.svg"
        with open(image_path, 'w') as f:
            f.write(svg_content)

        return str(image_path)
