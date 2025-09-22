import json
import requests
import os
from urllib.parse import quote
import time

# Product data from user
products_data = [
    {'name': 'HP ProBook 445 14" G11 Notebook', 'price': 85000, 'old_price': 95000, 'rating': 4.5, 'description': ['AMD R5-7535U', '8GB RAM', '512GB SSD'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=HP+ProBook', 'category': 'Laptops'},
    {'name': 'HP EliteBook 630 G10 Core i7', 'price': 95000, 'old_price': 110000, 'rating': 4.8, 'description': ['Intel Core i7', '16GB RAM', '512GB SSD'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=HP+EliteBook', 'category': 'Laptops'},
    {'name': 'Lenovo V14 Gen2 14" Intel', 'price': 75000, 'old_price': 82000, 'rating': 4.2, 'description': ['Intel Core i5', '8GB RAM', '256GB SSD'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Lenovo+V14', 'category': 'Laptops'},
    {'name': 'TP-Link Archer C6 WiFi Router', 'price': 5000, 'old_price': 6500, 'rating': 4.6, 'description': ['Dual Band', '4 Antennas', 'Gigabit Ports'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=TP-Link+Router', 'category': 'Accessories'},
    {'name': 'Office Gadgets Set', 'price': 3000, 'old_price': 3500, 'rating': 4.1, 'description': ['Desk Organizer', 'Phone Stand', 'Cable Clips'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Office+Gadgets', 'category': 'Accessories'},
    {'name': 'Gaming PC Pro', 'price': 120000, 'old_price': 135000, 'rating': 4.9, 'description': ['Ryzen 7', '32GB RAM', '1TB NVMe SSD', 'RTX 4060'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Gaming+PC', 'category': 'Desktops'},
    {'name': 'Laptop Accessory Kit', 'price': 2500, 'old_price': 3000, 'rating': 4.3, 'description': ['Laptop Sleeve', 'USB Hub', 'Mini Mouse'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Accessory+Kit', 'category': 'Accessories'},
    {'name': 'Logitech MX Master 3S Mouse', 'price': 12000, 'old_price': 15000, 'rating': 4.9, 'description': ['Ergonomic Design', '8K DPI Sensor', 'Quiet Clicks'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Logitech+Mouse', 'category': 'Accessories'},
    {'name': 'Keychron K2 Mechanical Keyboard', 'price': 9500, 'old_price': 11000, 'rating': 4.8, 'description': ['Wireless/Wired', 'Gateron Switches', 'Mac & Windows'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Keychron+K2', 'category': 'Accessories'},
    {'name': 'SanDisk Ultra 128GB USB Drive', 'price': 1500, 'old_price': 2000, 'rating': 4.9, 'description': ['USB 3.0', '130MB/s Speed', 'Portable'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=SanDisk+USB', 'category': 'Accessories'},
    {'name': 'Samsung T7 1TB External SSD', 'price': 11000, 'old_price': 13000, 'rating': 4.8, 'description': ['USB-C', 'Portable SSD', '1,050 MB/s Speed'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Samsung+SSD', 'category': 'Accessories'},
    {'name': 'Logitech C920 HD Pro Webcam', 'price': 8000, 'old_price': 9500, 'rating': 4.7, 'description': ['1080p Full HD', 'Stereo Audio', 'Light Correction'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Logitech+Webcam', 'category': 'Accessories'},
    {'name': 'Sony WH-1000XM5 Headphones', 'price': 45000, 'old_price': 52000, 'rating': 4.9, 'description': ['Noise Cancelling', 'Wireless', '30-Hour Battery'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Sony+Headphones', 'category': 'Accessories'},
    {'name': 'Dell XPS 15', 'price': 180000, 'old_price': 200000, 'rating': 4.9, 'description': ['Intel Core i9', '32GB RAM', '1TB SSD', 'OLED Display'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Dell+XPS+15', 'category': 'Laptops'},
    {'name': 'Apple MacBook Air M2', 'price': 150000, 'old_price': 165000, 'rating': 4.9, 'description': ['Apple M2 Chip', '8GB RAM', '256GB SSD', 'Liquid Retina'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=MacBook+Air', 'category': 'Laptops'},
    {'name': 'Lenovo ThinkPad X1 Carbon', 'price': 165000, 'old_price': 180000, 'rating': 4.7, 'description': ['Intel Core i7', '16GB RAM', '1TB SSD', 'Lightweight'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=ThinkPad+X1', 'category': 'Laptops'},
    {'name': 'Asus ROG Zephyrus G14', 'price': 190000, 'old_price': 210000, 'rating': 4.8, 'description': ['AMD Ryzen 9', '16GB RAM', '1TB SSD', 'RTX 3060'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Asus+ROG', 'category': 'Laptops'},
    {'name': 'Microsoft Surface Laptop 5', 'price': 130000, 'old_price': 140000, 'rating': 4.6, 'description': ['Intel Core i5', '8GB RAM', '512GB SSD', 'Touchscreen'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Surface+Laptop', 'category': 'Laptops'},
    {'name': 'Acer Swift 3', 'price': 88000, 'old_price': 98000, 'rating': 4.4, 'description': ['AMD Ryzen 7', '8GB RAM', '512GB SSD', '14" FHD IPS'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Acer+Swift+3', 'category': 'Laptops'},
    {'name': 'HP Spectre x360', 'price': 145000, 'old_price': 160000, 'rating': 4.7, 'description': ['Intel Core i7', '16GB RAM', '512GB SSD', '2-in-1 Convertible'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=HP+Spectre', 'category': 'Laptops'},
    {'name': 'Apple iMac 24"', 'price': 180000, 'old_price': 195000, 'rating': 4.8, 'description': ['Apple M1 Chip', '8GB RAM', '256GB SSD', '4.5K Retina'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=iMac+24', 'category': 'Desktops'},
    {'name': 'HP Pavilion Gaming Desktop', 'price': 98000, 'old_price': 110000, 'rating': 4.6, 'description': ['Intel Core i5', '16GB RAM', '512GB SSD', 'GTX 1660 Super'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=HP+Pavilion', 'category': 'Desktops'},
    {'name': 'Dell Inspiron Compact Desktop', 'price': 65000, 'old_price': 75000, 'rating': 4.3, 'description': ['Intel Core i5', '12GB RAM', '256GB SSD', 'Small Form Factor'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Dell+Inspiron', 'category': 'Desktops'},
    {'name': 'Lenovo IdeaCentre AIO 3', 'price': 85000, 'old_price': 95000, 'rating': 4.5, 'description': ['AMD Ryzen 5', '8GB RAM', '512GB SSD', '24" FHD Display'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Lenovo+AIO', 'category': 'Desktops'},
    {'name': 'Alienware Aurora R15', 'price': 250000, 'old_price': 280000, 'rating': 4.9, 'description': ['Intel Core i9', '32GB RAM', '2TB SSD', 'RTX 4080'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Alienware', 'category': 'Desktops'},
    {'name': 'Intel NUC Mini PC', 'price': 55000, 'old_price': 62000, 'rating': 4.7, 'description': ['Intel Core i7', '16GB RAM', '512GB NVMe', 'Ultra Compact'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Intel+NUC', 'category': 'Desktops'},
    {'name': 'HP Envy All-in-One 34"', 'price': 220000, 'old_price': 240000, 'rating': 4.8, 'description': ['Intel Core i7', '16GB RAM', '1TB SSD', '5K Display'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=HP+Envy+AIO', 'category': 'Desktops'},
    {'name': 'Office Workstation PC', 'price': 78000, 'old_price': 85000, 'rating': 4.4, 'description': ['Intel Core i7', '16GB RAM', '1TB HDD + 256GB SSD'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Office+PC', 'category': 'Desktops'},
    {'name': 'Mac Mini M2', 'price': 90000, 'old_price': 100000, 'rating': 4.8, 'description': ['Apple M2 Chip', '8GB RAM', '256GB SSD', 'Compact Power'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Mac+Mini+M2', 'category': 'Desktops'},
    {'name': 'Dell UltraSharp 27" 4K Monitor', 'price': 65000, 'old_price': 75000, 'rating': 4.8, 'description': ['27-inch 4K UHD', 'IPS Panel', 'USB-C Hub'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Dell+Monitor', 'category': 'Accessories'},
    {'name': 'Anker 737 Power Bank', 'price': 15000, 'old_price': 18000, 'rating': 4.9, 'description': ['24,000mAh', '140W Output', 'Smart Display'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Anker+Power+Bank', 'category': 'Accessories'},
    {'name': 'SteelSeries QcK Mousepad', 'price': 2000, 'old_price': 2500, 'rating': 4.8, 'description': ['Large Size', 'Micro-Woven Cloth', 'Non-slip Base'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Mousepad', 'category': 'Accessories'},
    {'name': 'HP LaserJet Pro M404dn', 'price': 35000, 'old_price': 40000, 'rating': 4.6, 'description': ['Monochrome Laser', 'Fast Printing', 'Network Ready'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=HP+LaserJet', 'category': 'Accessories'},
    {'name': 'Logitech Z407 Bluetooth Speakers', 'price': 9000, 'old_price': 11000, 'rating': 4.5, 'description': ['80W Peak Power', 'Subwoofer', 'Wireless Control'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Logitech+Speakers', 'category': 'Accessories'},
    {'name': 'Rain Design mStand Laptop Stand', 'price': 5500, 'old_price': 6500, 'rating': 4.9, 'description': ['Ergonomic', 'Aluminum Design', 'Cable Organizer'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Laptop+Stand', 'category': 'Accessories'},
    {'name': 'Razer Blade 15', 'price': 220000, 'old_price': 240000, 'rating': 4.8, 'description': ['Intel Core i7', '16GB RAM', '1TB SSD', 'RTX 3070Ti'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Razer+Blade', 'category': 'Laptops'},
    {'name': 'LG Gram 17', 'price': 160000, 'old_price': 175000, 'rating': 4.6, 'description': ['Intel Core i7', '16GB RAM', '1TB SSD', 'Ultra-lightweight'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=LG+Gram', 'category': 'Laptops'},
    {'name': 'Samsung Galaxy Book3 Pro', 'price': 155000, 'old_price': 170000, 'rating': 4.7, 'description': ['Intel Core i7', '16GB RAM', '512GB SSD', 'AMOLED 2X'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Galaxy+Book3', 'category': 'Laptops'},
    {'name': 'Framework Laptop 13', 'price': 140000, 'old_price': 150000, 'rating': 4.9, 'description': ['Intel Core i5', '16GB RAM', '512GB SSD', 'Repairable'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Framework', 'category': 'Laptops'},
    {'name': 'Google Pixelbook Go', 'price': 95000, 'old_price': 110000, 'rating': 4.5, 'description': ['Intel Core i5', '8GB RAM', '128GB SSD', 'ChromeOS'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Pixelbook+Go', 'category': 'Laptops'},
    {'name': 'Corsair Vengeance i7400', 'price': 280000, 'old_price': 310000, 'rating': 4.9, 'description': ['Intel Core i7', '32GB DDR5', '2TB NVMe SSD', 'RTX 4070'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Corsair+PC', 'category': 'Desktops'},
    {'name': 'MSI Trident AS', 'price': 210000, 'old_price': 230000, 'rating': 4.7, 'description': ['Intel Core i7', '16GB RAM', '1TB SSD', 'RTX 3060Ti'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=MSI+Trident', 'category': 'Desktops'},
    {'name': 'HP Omen 45L', 'price': 260000, 'old_price': 290000, 'rating': 4.8, 'description': ['AMD Ryzen 9', '32GB RAM', '1TB SSD + 1TB HDD', 'RTX 4070Ti'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=HP+Omen', 'category': 'Desktops'},
    {'name': 'NZXT Player: Two', 'price': 190000, 'old_price': 205000, 'rating': 4.7, 'description': ['AMD Ryzen 5', '16GB RAM', '1TB NVMe SSD', 'RTX 3070'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=NZXT+Player', 'category': 'Desktops'},
    {'name': 'Lenovo Legion Tower 5i', 'price': 175000, 'old_price': 190000, 'rating': 4.6, 'description': ['Intel Core i7', '16GB RAM', '512GB SSD + 1TB HDD'], 'image': 'https://placehold.co/400x300/f4f4f4/333?text=Lenovo+Legion', 'category': 'Desktops'}
]

def create_filename(product_name):
    """Create a safe filename from product name"""
    return product_name.lower().replace(' ', '_').replace('"', '').replace("'", '').replace('/', '_') + '.jpg'

def download_image(url, filename, download_dir='static/images'):
    """Download image from URL to specified directory"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(download_dir, exist_ok=True)

        filepath = os.path.join(download_dir, filename)

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
    print("Starting image download process...")
    print(f"Total products to process: {len(products_data)}")

    downloaded_count = 0
    failed_count = 0

    for i, product in enumerate(products_data, 1):
        print(f"\nProcessing {i}/{len(products_data)}: {product['name']}")

        # Create filename
        filename = create_filename(product['name'])

        # Download image
        if download_image(product['image'], filename):
            downloaded_count += 1
        else:
            failed_count += 1

        # Add delay to be respectful to the server
        time.sleep(1)

    print("\n=== DOWNLOAD SUMMARY ===")
    print(f"✓ Successfully downloaded: {downloaded_count}")
    print(f"✗ Failed downloads: {failed_count}")
    print(f"Total processed: {len(products_data)}")

    if failed_count > 0:
        print("\nSome images failed to download. You may want to:")
        print("1. Check your internet connection")
        print("2. Try downloading failed images manually")
        print("3. Use alternative image sources")

if __name__ == "__main__":
    main()
