from PIL import Image, UnidentifiedImageError, ImageOps
import pyzbar.pyzbar as pyzbar
import os
import time
from pdf_qr2img import qr2img

# --- Configuration for Debugging ---
DEBUG_SAVE_IMAGES = False  # Set to True to save processed images for inspection
DEBUG_FOLDER = "debug_images_direct"

if DEBUG_SAVE_IMAGES and not os.path.exists(DEBUG_FOLDER):
    os.makedirs(DEBUG_FOLDER)

def extract_qr_data_from_image(image_path, upscale_factor=1, try_threshold=False):
    """
    Extracts QR code data directly from an image file.

    Args:
        image_path (str): The file path to the image (PNG, JPG, etc.).
        upscale_factor (int): Factor by which to increase the image size
                              before attempting QR code decoding. Can help if the
                              QR code within the image is small/low-res.
                              Defaults to 1 (no upscaling).
        try_threshold (bool): Whether to attempt thresholding (converting to B&W)
                              during preprocessing. Can help with contrast issues.

    Returns:
        list: A list of unique strings, where each string is the data decoded
              from a found QR code. Returns an empty list if no QR codes
              are found or an error occurs.
    """
    found_qr_data = set() # Use set for auto-uniqueness
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {image_path}")
        return []

    print(f"Processing image: {image_path}")
    base_filename = os.path.splitext(os.path.basename(image_path))[0]

    try:
        # --- 1. Load Image with Pillow ---
        pil_image = Image.open(image_path)
        img_width, img_height = pil_image.size
        print(f"  Image size: {img_width}x{img_height}")

        if DEBUG_SAVE_IMAGES:
             ts = int(time.time() * 1000)
             debug_path = os.path.join(DEBUG_FOLDER, f"{base_filename}_original_{ts}.png")
             try:
                 pil_image.save(debug_path)
                 print(f"  [Debug] Saved Original image to: {debug_path}")
             except Exception as save_e:
                 print(f"  [Debug] Failed to save original image: {save_e}")


        # --- 2. Preprocessing ---
        # Convert to Grayscale first (almost always beneficial for QR)
        pil_image_gray = pil_image.convert('L')

        # Attempt decoding on original grayscale first
        print("  Attempt 1: Decoding original grayscale...")
        decoded_objects = pyzbar.decode(pil_image_gray)
        if decoded_objects:
             print(f"  Found {len(decoded_objects)} barcode(s) in original grayscale.")
             for obj in decoded_objects:
                  if obj.type == 'QRCODE':
                      try:
                           data = obj.data.decode('utf-8')
                           print(f"    SUCCESS (Original Gray): Found QR Code!")
                           found_qr_data.add(data)
                      except UnicodeDecodeError:
                           print(f"    WARNING (Original Gray): Found QR but couldn't decode UTF-8. Data: {obj.data}")


        # --- 3. Optional Upscaling and Thresholding ---
        if upscale_factor > 1 or try_threshold:
            print(f"\n  Attempt 2: Preprocessing (U={upscale_factor}, T={try_threshold})...")
            image_to_process = pil_image_gray # Start with grayscale

            # Apply Upscaling if needed
            if upscale_factor > 1:
                new_size = (img_width * upscale_factor, img_height * upscale_factor)
                print(f"    Upscaling by {upscale_factor}x to {new_size} using LANCZOS...")
                try:
                    image_to_process = image_to_process.resize(new_size, Image.LANCZOS)
                except Exception as resize_e:
                     print(f"    Error during resize: {resize_e}")
                     # Continue with non-upscaled image if resize fails

            # Apply Thresholding if needed
            if try_threshold:
                print("    Applying autocontrast and thresholding...")
                try:
                    # Autocontrast might help first
                    image_processed = ImageOps.autocontrast(image_to_process, cutoff=5)
                    # Simple threshold - adjust 128 if needed
                    image_processed = image_processed.point(lambda x: 0 if x < 128 else 255, '1')
                    image_to_process = image_processed # Use the thresholded image
                except Exception as thresh_e:
                     print(f"    Error during thresholding: {thresh_e}")
                     # Continue with potentially only upscaled image if threshold fails

            if DEBUG_SAVE_IMAGES:
                 ts = int(time.time() * 1000)
                 debug_path = os.path.join(DEBUG_FOLDER, f"{base_filename}_processed_U{upscale_factor}_T{try_threshold}_{ts}.png")
                 try:
                    image_to_process.save(debug_path)
                    print(f"    [Debug] Saved Processed image to: {debug_path}")
                 except Exception as save_e:
                    print(f"    [Debug] Failed to save processed image: {save_e}")

            # Decode the processed (upscaled/thresholded) image
            print("    Decoding processed image...")
            decoded_objects_processed = pyzbar.decode(image_to_process)

            if decoded_objects_processed:
                 print(f"    Found {len(decoded_objects_processed)} barcode(s) in processed image.")
                 for obj in decoded_objects_processed:
                    if obj.type == 'QRCODE':
                        try:
                            data = obj.data.decode('utf-8')
                            print(f"      SUCCESS (Processed): Found QR Code!")
                            found_qr_data.add(data) # Add to set (handles duplicates)
                        except UnicodeDecodeError:
                            print(f"      WARNING (Processed): Found QR but couldn't decode UTF-8. Data: {obj.data}")

    except UnidentifiedImageError:
        print(f"Error: Pillow cannot identify image file format for {image_path}")
    except Exception as e:
        print(f"An error occurred processing image {image_path}: {e}")

    return list(found_qr_data) # Convert set back to list

def qrcode_data(input_pdf,output_image_file):
    image_file_path=qr2img(input_pdf,output_image_file)
    resize_factor = 1  # Start with 1 (no upscale), maybe increase (e.g., 2, 3) if needed.
    # If contrast is poor, try enabling thresholding
    use_thresholding = False  # Try setting to True if decoding fails

    # --- Run Extraction ---
    print("=" * 30)
    print(" Starting QR Code Extraction from Image ".center(30, "="))
    print(f"  File: {image_file_path}")
    print(f"  Upscale: {resize_factor}x")
    print(f"  Threshold: {use_thresholding}")
    print("=" * 30)

    extracted_data = extract_qr_data_from_image(
        image_file_path,
        upscale_factor=resize_factor,
        try_threshold=use_thresholding
    )

    # --- Print Results ---
    print("\n" + "=" * 30)
    print(" Extraction Results ".center(30, "="))
    print("=" * 30)
    if extracted_data:
        # Extract and process the QR code data
        qr_data = extracted_data[0]
        lines = qr_data.split('\n')
        
        # Extract address parts
        address_parts = []
        language = None
        
        for line in lines:
            if line.startswith('ADDR:'):
                address_parts.append(line[5:].strip())  # Remove 'ADDR:' prefix
            elif line.startswith('LANGUAGE:'):
                language = line[9:].strip()  # Remove 'LANGUAGE:' prefix
        
        # Combine address parts
        full_address = ' '.join(address_parts)
        
        # Return combined information
        return f"Address: {full_address}"
    else:
        print("\nNo QR codes found in the image or failed to decode.")
        if not DEBUG_SAVE_IMAGES:
            print("Consider setting DEBUG_SAVE_IMAGES = True at the top to inspect images.")

    print("\nProcessing complete.")

# --- How to Use ---
if __name__ == "__main__":
    # --- Configuration ---
    # Use the path to your PNG or other image file
    image_file_path = 'cropped_enlarged_image.png' # <<< USE YOUR IMAGE PATH
    # image_file_path = 'test/assets/some_other_image.jpg'

    # --- Tuning Parameters (Adjust as needed) ---
    # If the QR code *within* the image is small or blurry, increase upscale_factor
    resize_factor = 1        # Start with 1 (no upscale), maybe increase (e.g., 2, 3) if needed.
    # If contrast is poor, try enabling thresholding
    use_thresholding = False # Try setting to True if decoding fails

    # --- Run Extraction ---
    print("="*30)
    print(" Starting QR Code Extraction from Image ".center(30, "="))
    print(f"  File: {image_file_path}")
    print(f"  Upscale: {resize_factor}x")
    print(f"  Threshold: {use_thresholding}")
    print("="*30)

    extracted_data = extract_qr_data_from_image(
        image_file_path,
        upscale_factor=resize_factor,
        try_threshold=use_thresholding
        )

    # --- Print Results ---
    print("\n" + "="*30)
    print(" Extraction Results ".center(30, "="))
    print("="*30)
    if extracted_data:
        # print(f"\nSuccessfully extracted {len(extracted_data)} unique QR Code(s):")
        # for i, data in enumerate(extracted_data):
        #     print(f"\n--- QR Code #{i+1} ---")
        #     print(data)
        #     print("-" * (len(f"--- QR Code #{i+1} ---")))
        print(extracted_data[0])
    else:
        print("\nNo QR codes found in the image or failed to decode.")
        if not DEBUG_SAVE_IMAGES:
             print("Consider setting DEBUG_SAVE_IMAGES = True at the top to inspect images.")

    print("\nProcessing complete.")