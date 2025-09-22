import json
import requests
import os
from urllib.parse import quote, urlparse
import time
import sys
import re

# Add the current directory to Python path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_filename(product_name, url):
    """Create a safe filename from product name and URL"""
    # Clean product name
    clean_name = re.sub(r'[^\w\s-]', '', product_name)
    clean_name = clean_name.replace(' ', '_').replace('"', '').replace("'", '')

    # Try to get file extension from URL
    parsed_url = urlparse(url)
    _, ext = os.path.splitext(parsed_url.path)

    if not ext:
        ext = '.jpg'  # Default extension

    return f"{clean_name}{ext}"

def download_image(url, filename, download_dir='static/images'):
    """Download image from URL to specified directory"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(download_dir, exist_ok=True)

        filepath = os.path.join(download_dir, filename)

        # Skip if file already exists
        if os.path.exists(filepath):
            print(f"✓ Already exists: {filename}")
            return True

        # Download image
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            f.write(response.content)

        print(f"✓ Downloaded: {filename}")
        return True

    except Exception as e:
        print(f"✗ Failed to download {filename}: {str(e)}")
        return False

def main():
    try:
        from app import app, db, Product

        print("Starting image download process from database...")

        with app.app_context():
            products = Product.query.all()
            print(f'Total products found in database: {len(products)}')

            if not products:
                print("No products found in database!")
                return

            print('\nCurrent product images:')
            external_urls = []

            for p in products[:5]:  # Show first 5
                print(f'{p.id}: {p.name} -> {p.image}')
                if p.image.startswith('http'):
                    external_urls.append((p.id, p.name, p.image))

            if len(products) > 5:
                print(f'... and {len(products) - 5} more products')

            print(f'\nFound {len(external_urls)} products with external URLs')

            if not external_urls:
                print("All products already use local images!")
                return

            downloaded_count = 0
            failed_count = 0
            updated_count = 0

            for product_id, product_name, url in external_urls:
                print(f"\nProcessing: {product_name}")

                # Create filename
                filename = create_filename(product_name, url)

                # Download image
                if download_image(url, filename):
                    downloaded_count += 1

                    # Update database to use local file
                    product = Product.query.get(product_id)
                    if product:
                        product.image = f'static/images/{filename}'
                        updated_count += 1
                        print(f"✓ Updated database: {product_name}")
                else:
                    failed_count += 1

                # Add delay to be respectful to the server
                time.sleep(1)

            # Commit all database changes
            db.session.commit()

            print("\n=== DOWNLOAD SUMMARY ===")
            print(f"✓ Successfully downloaded: {downloaded_count}")
            print(f"✓ Database updated: {updated_count}")
            print(f"✗ Failed downloads: {failed_count}")
            print(f"Total processed: {len(external_urls)}")

            if failed_count > 0:
                print("\nSome images failed to download. You may want to:")
                print("1. Check your internet connection")
                print("2. Try downloading failed images manually")
                print("3. Use alternative image sources")

            print("\n✅ All images downloaded and database updated!")
            print("✅ Your website should now display local images instead of external URLs!")

    except ImportError as e:
        print(f"Error importing app: {e}")
        print("Make sure you're running this script from the ANORLD directory")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
