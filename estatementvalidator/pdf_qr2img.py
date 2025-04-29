import fitz  # PyMuPDF
import os

def crop_enlarge_save_png(input_pdf_path,
                          output_png_path,
                          page_number=0,
                          cut_top=50,
                          cut_bottom=50,
                          cut_left=50,
                          cut_right=50,
                          output_dpi=300): # Changed parameter for clarity
    """
    Extracts a central portion of a specific PDF page by cutting amounts
    from the edges, renders this portion at a specified DPI (effectively
    enlarging it in pixel dimensions), and saves it as a PNG image.

    Args:
        input_pdf_path (str): Path to the source PDF file.
        output_png_path (str): Path where the output PNG image will be saved.
        page_number (int): The 0-based index of the page to process.
        cut_top (float): Points to cut off from the top edge.
        cut_bottom (float): Points to cut off from the bottom edge.
        cut_left (float): Points to cut off from the left edge.
        cut_right (float): Points to cut off from the right edge.
        output_dpi (int): Resolution (dots per inch) for the output PNG.
                          Higher DPI results in a larger, clearer image from the
                          same source area. Common values: 96, 150, 300, 600.

    Returns:
        bool: True if successful, False otherwise.
    """
    if not os.path.exists(input_pdf_path):
        print(f"Error: Input PDF not found at '{input_pdf_path}'")
        return False

    # Validate cut amounts are non-negative
    if not (cut_top >= 0 and cut_bottom >= 0 and cut_left >= 0 and cut_right >= 0):
         print("Error: Cut amounts (top, bottom, left, right) cannot be negative.")
         return False

    if output_dpi <= 0:
         print("Error: Output DPI must be positive.")
         return False

    doc = None
    try:
        # --- 1. Open the Source PDF ---
        doc = fitz.open(input_pdf_path)
        if not (0 <= page_number < len(doc)):
            print(f"Error: Page number {page_number} is out of range (PDF has {len(doc)} pages).")
            return False

        # --- 2. Get the Specified Page and its Dimensions ---
        page = doc.load_page(page_number)
        source_rect = page.rect   # Get the rectangle defining the page size (x0, y0, x1, y1)
        print(f"Source page {page_number + 1} size: {source_rect.width:.2f} x {source_rect.height:.2f} points")

        # --- 3. Define the Rectangle to Keep (after cutting) ---
        clip_x0 = source_rect.x0 + cut_left
        clip_y0 = source_rect.y0 + cut_bottom
        clip_x1 = source_rect.x1 - cut_right
        clip_y1 = source_rect.y1 - cut_top

        clip_rect = fitz.Rect(clip_x0, clip_y0, clip_x1, clip_y1)
        print(f"Calculated area to keep: ({clip_rect.x0:.2f}, {clip_rect.y0:.2f}) to ({clip_rect.x1:.2f}, {clip_rect.y1:.2f})")

        # --- Validate the resulting clip_rect ---
        if clip_rect.is_empty or clip_rect.width <= 0 or clip_rect.height <= 0:
             print(f"Error: Calculated clipping rectangle is invalid or has zero/negative area.")
             print(f"  Page Width: {source_rect.width:.2f}, Total Horizontal Cut: {cut_left + cut_right:.2f}")
             print(f"  Page Height: {source_rect.height:.2f}, Total Vertical Cut: {cut_top + cut_bottom:.2f}")
             return False
        print(f"  Resulting clip area size: {clip_rect.width:.2f} x {clip_rect.height:.2f} points")


        # --- 4. Render the Clipped Area to a Pixmap (Image) at specified DPI ---
        print(f"Rendering clipped area at {output_dpi} DPI...")
        pix = page.get_pixmap(
            clip=clip_rect,    # Render *only* the clipped area
            dpi=output_dpi,    # Control the output resolution (enlargement)
            alpha=False        # Create RGB image, no transparency
        )

        if not pix.samples:
            print("Error: Failed to render the clipped area to a pixmap.")
            return False

        print(f"Rendered image size: {pix.width} x {pix.height} pixels.")

        # --- 5. Save the Pixmap as a PNG Image ---
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_png_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            print(f"Created output directory: '{output_dir}'")

        pix.save(output_png_path) # Pixmap object has a save method
        print(f"Successfully saved cropped and enlarged image to: '{output_png_path}'")
        return True

    except Exception as e:
        print(f"An error occurred: {e}")
        # Attempt to provide more specific feedback for common pixmap errors
        if "cannot render page" in str(e).lower():
             print("  Hint: This might happen with complex or damaged PDFs.")
        return False
    finally:
        # --- 6. Close Document ---
        if doc:
            doc.close()

def qr2img(input_pdf,output_image_file):
    target_page_index = 0  # Process the first page (index 0)

    # --- Define Cuts in Points (1 inch = 72 points) ---
    cut_off_top = 605.0
    cut_off_bottom = 195.0  # Make sure these are floats if needed
    cut_off_left = 525.0
    cut_off_right = 25.0

    # --- Define Output Image Resolution ---
    # Higher DPI means larger pixel dimensions for the output image.
    # 300 DPI is good print quality. Use 600 or more for very high detail.
    image_dpi = 600

    print(f"Processing '{input_pdf}'...")
    success = crop_enlarge_save_png(
        input_pdf_path=input_pdf,
        output_png_path=output_image_file,
        page_number=target_page_index,
        cut_top=cut_off_top,
        cut_bottom=cut_off_bottom,
        cut_left=cut_off_left,
        cut_right=cut_off_right,
        output_dpi=image_dpi
    )

    if success:
        print("\nImage processing complete.")
    else:
        print("\nImage processing failed.")

    return output_image_file


# --- How to Use ---
if __name__ == "__main__":
    # --- Configuration ---
    input_pdf = 'copy.pdf'      # <<< CHANGE to your source PDF file path
    # --- CHANGE output path to end in .png ---
    output_image_file = 'cropped_enlarged_image.png'
    target_page_index = 0                     # Process the first page (index 0)

    # --- Define Cuts in Points (1 inch = 72 points) ---
    cut_off_top = 605.0
    cut_off_bottom = 195.0 # Make sure these are floats if needed
    cut_off_left = 525.0
    cut_off_right = 25.0

    # --- Define Output Image Resolution ---
    # Higher DPI means larger pixel dimensions for the output image.
    # 300 DPI is good print quality. Use 600 or more for very high detail.
    image_dpi = 600

    print(f"Processing '{input_pdf}'...")
    success = crop_enlarge_save_png(
        input_pdf_path=input_pdf,
        output_png_path=output_image_file,
        page_number=target_page_index,
        cut_top=cut_off_top,
        cut_bottom=cut_off_bottom,
        cut_left=cut_off_left,
        cut_right=cut_off_right,
        output_dpi=image_dpi
    )

    if success:
        print("\nImage processing complete.")
    else:
        print("\nImage processing failed.")