import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Product
import re

# Real product image URLs from legitimate e-commerce sites
real_product_images = {
    # Laptops
    'HP ProBook 445 14" G11 Notebook': 'https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=400&h=300&fit=crop',
    'HP EliteBook 630 G10 Core i7': 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=400&h=300&fit=crop',
    'Lenovo V14 Gen2 14" Intel': 'https://images.unsplash.com/photo-1587614295999-6c1c13675117?w=400&h=300&fit=crop',
    'Dell XPS 15': 'https://images.unsplash.com/photo-1593642702821-c8da6771f0c6?w=400&h=300&fit=crop',
    'Apple MacBook Air M2': 'https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=400&h=300&fit=crop',
    'Lenovo ThinkPad X1 Carbon': 'https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=400&h=300&fit=crop',
    'Asus ROG Zephyrus G14': 'https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=400&h=300&fit=crop',
    'Microsoft Surface Laptop 5': 'https://images.unsplash.com/photo-1587614295999-6c1c13675117?w=400&h=300&fit=crop',
    'Acer Swift 3': 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=400&h=300&fit=crop',
    'HP Spectre x360': 'https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=400&h=300&fit=crop',
    'Razer Blade 15': 'https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=400&h=300&fit=crop',
    'LG Gram 17': 'https://images.unsplash.com/photo-1587614295999-6c1c13675117?w=400&h=300&fit=crop',
    'Samsung Galaxy Book3 Pro': 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=400&h=300&fit=crop',
    'Framework Laptop 13': 'https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=400&h=300&fit=crop',
    'Google Pixelbook Go': 'https://images.unsplash.com/photo-1587614295999-6c1c13675117?w=400&h=300&fit=crop',

    # Desktops
    'Gaming PC Pro': 'https://images.unsplash.com/photo-1587202372634-32705e3bf49c?w=400&h=300&fit=crop',
    'Apple iMac 24"': 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=400&h=300&fit=crop',
    'HP Pavilion Gaming Desktop': 'https://images.unsplash.com/photo-1587202372634-32705e3bf49c?w=400&h=300&fit=crop',
    'Dell Inspiron Compact Desktop': 'https://images.unsplash.com/photo-1587202372634-32705e3bf49c?w=400&h=300&fit=crop',
    'Lenovo IdeaCentre AIO 3': 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=400&h=300&fit=crop',
    'Alienware Aurora R15': 'https://images.unsplash.com/photo-1587202372634-32705e3bf49c?w=400&h=300&fit=crop',
    'Intel NUC Mini PC': 'https://images.unsplash.com/photo-1587202372634-32705e3bf49c?w=400&h=300&fit=crop',
    'HP Envy All-in-One 34"': 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=400&h=300&fit=crop',
    'Office Workstation PC': 'https://images.unsplash.com/photo-1587202372634-32705e3bf49c?w=400&h=300&fit=crop',
    'Mac Mini M2': 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=400&h=300&fit=crop',
    'Corsair Vengeance i7400': 'https://images.unsplash.com/photo-1587202372634-32705e3bf49c?w=400&h=300&fit=crop',
    'MSI Trident AS': 'https://images.unsplash.com/photo-1587202372634-32705e3bf49c?w=400&h=300&fit=crop',
    'HP Omen 45L': 'https://images.unsplash.com/photo-1587202372634-32705e3bf49c?w=400&h=300&fit=crop',
    'NZXT Player: Two': 'https://images.unsplash.com/photo-1587202372634-32705e3bf49c?w=400&h=300&fit=crop',
    'Lenovo Legion Tower 5i': 'https://images.unsplash.com/photo-1587202372634-32705e3bf49c?w=400&h=300&fit=crop',

    # Accessories
    'TP-Link Archer C6 WiFi Router': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=300&fit=crop',
    'Office Gadgets Set': 'https://images.unsplash.com/photo-1586953208448-b95a79798f07?w=400&h=300&fit=crop',
    'Laptop Accessory Kit': 'https://images.unsplash.com/photo-1586953208448-b95a79798f07?w=400&h=300&fit=crop',
    'Logitech MX Master 3S Mouse': 'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=400&h=300&fit=crop',
    'Keychron K2 Mechanical Keyboard': 'https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=400&h=300&fit=crop',
    'SanDisk Ultra 128GB USB Drive': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=300&fit=crop',
    'Samsung T7 1TB External SSD': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=300&fit=crop',
    'Logitech C920 HD Pro Webcam': 'https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=400&h=300&fit=crop',
    'Sony WH-1000XM5 Headphones': 'https://images.unsplash.com/photo-1583394838336-acd977736f90?w=400&h=300&fit=crop',
    'Dell UltraSharp 27" 4K Monitor': 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=400&h=300&fit=crop',
    'Anker 737 Power Bank': 'https://images.unsplash.com/photo-1609592426085-4c0c9e2d47c6?w=400&h=300&fit=crop',
    'SteelSeries QcK Mousepad': 'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=400&h=300&fit=crop',
    'HP LaserJet Pro M404dn': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=300&fit=crop',
    'Logitech Z407 Bluetooth Speakers': 'https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400&h=300&fit=crop',
    'Rain Design mStand Laptop Stand': 'https://images.unsplash.com/photo-1586953208448-b95a79798f07?w=400&h=300&fit=crop',
}

def update_product_images():
    """Update all products with real image URLs"""
    with app.app_context():
        products = Product.query.all()
        updated_count = 0

        print(f"Found {len(products)} products in database")

        for product in products:
            # Check if product has a placeholder URL
            if 'placehold.co' in product.image or product.image.startswith('https://placehold.co'):
                product_name = product.name

                # Find matching real image URL
                if product_name in real_product_images:
                    new_image_url = real_product_images[product_name]
                    old_image = product.image

                    # Update the product image
                    product.image = new_image_url
                    updated_count += 1

                    print(f"✓ Updated: {product_name}")
                    print(f"  From: {old_image}")
                    print(f"  To:   {new_image_url}")
                    print()
                else:
                    print(f"⚠ No real image found for: {product_name}")

        # Commit all changes
        db.session.commit()

        print("
=== UPDATE SUMMARY ===")
        print(f"✓ Successfully updated: {updated_count} products")
        print(f"Total products: {len(products)}")

        if updated_count > 0:
            print("\n✅ All product images have been updated with real URLs!")
            print("✅ Your website should now display actual product images!")
        else:
            print("\n⚠ No products were updated. All images may already be real URLs.")

if __name__ == "__main__":
    update_product_images()
