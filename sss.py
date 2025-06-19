import secrets
import argparse
import math
import base64
import qrcode
import os
import sys
from io import BytesIO
from PIL import Image
from sympy import nextprime

# Set up library path for macOS zbar (assumed to be installed via homebrew)
if sys.platform == "darwin":
    zbar_path = "/opt/homebrew/opt/zbar/lib"
    if os.path.exists(zbar_path):
        current_dyld_path = os.environ.get('DYLD_LIBRARY_PATH', '')
        if zbar_path not in current_dyld_path:
            os.environ['DYLD_LIBRARY_PATH'] = f"{zbar_path}:{current_dyld_path}".rstrip(':')

try:
    # Optional dependency for QR code scanning
    from pyzbar.pyzbar import decode
    HAS_PYZBAR = True
except ImportError:
    HAS_PYZBAR = False

tmp = secrets.randbits(512)
prime = nextprime(tmp)

def share(message: str, threshold: int, num_shares: int):
    """
    Split a secret message into shares using Shamir's Secret Sharing scheme.
    
    Args:
        message: The secret message to be shared (must be UTF-8 encodable)
        threshold: The minimum number of shares required to reconstruct the secret
        num_shares: The total number of shares to generate
        
    Returns:
        A list of (x, y) tuples representing the shares, where x is the share index
        and y is the share value
        
    Raises:
        AssertionError: If the message is too large (>512 bits when encoded) or 
                       if threshold > num_shares
    """
    message_bytes = message.encode('utf-8')
    message_int = int.from_bytes(message_bytes, byteorder='big')

    assert message_int < prime, "The inputted message must be utf-8-encodable in fewer than 512 bits."
    assert threshold <= num_shares, "The chosen threshold must be <= the number of shares to generate. Aborting."

    coeffs = [secrets.randbelow(prime) for _ in range(threshold)]
    poly = lambda x: message_int + int(sum([x**j * coeffs[j] for j in range(1, threshold)]))
    
    shares = [(i, poly(i) % prime) for i in range(1, num_shares + 1)]
    return shares, prime


def reconstruct(shares: list[tuple[int, int]], prime: int = prime):
    """
    Reconstruct the secret from a list of shares using Lagrange interpolation.
    
    Args:
        shares: List of (x, y) tuples representing shares
        prime: The prime modulus used during sharing
        
    Returns:
        The reconstructed secret as a string, or an error message if reconstruction fails
    """
    if len(shares) == 0:
        return "Error: an empty set of shares was provided for decoding."

    x_values = [x for x, _ in shares]
    y_values = [y for _, y in shares]
    
    def mod_inverse(a, m):
        # It follows from Fermat's little theorem that a^(p-2) ≡ a^(-1) (mod p) when p is prime
        return pow(a, m - 2, m)
    
    lagrange_polynomials = []
    for i, xi in enumerate(x_values):
        def lagrange_basis(x, i=i, xi=xi):
            numerator = 1
            denominator = 1
            for j, xj in enumerate(x_values):
                if i != j:
                    numerator = (numerator * (x - xj)) % prime
                    denominator = (denominator * (xi - xj)) % prime

            denominator_inv = mod_inverse(denominator, prime)
            return (numerator * denominator_inv) % prime
        
        lagrange_polynomials.append(lagrange_basis)
    
    # Return f(0) where f = y1 * l1(x) + ... + yt * lt(x)
    secret = 0
    for i, (_, yi) in enumerate(shares):
        li_at_0 = lagrange_polynomials[i](0)
        term = (yi * li_at_0) % prime
        secret = (secret + term) % prime
    
    secret_bytes = secret.to_bytes(math.ceil(secret.bit_length() / 8), byteorder='big')
    try:
        return secret_bytes.decode('utf-8')
    except UnicodeDecodeError:
        return "Error: Could not decode the reconstructed secret. This likely means not enough valid shares were provided."


def encode_share_base64(share):
    """Convert a share (x, y) to a base64 string for human readability"""
    x, y = share
    # Pack the x and y values together
    combined = f"{x}:{y}"
    # Encode to bytes and then to base64
    return base64.b64encode(combined.encode('utf-8')).decode('utf-8')

def decode_share_base64(encoded_share):
    """Convert a base64 encoded share back to (x, y) tuple"""
    # Decode from base64 to bytes and then to string
    decoded = base64.b64decode(encoded_share).decode('utf-8')
    # Split the string to get x and y
    x_str, y_str = decoded.split(':')
    return (int(x_str), int(y_str))

def encode_share_hex(share):
    """Convert a share (x, y) to a hex string for human readability"""
    x, y = share
    # Format as hex with a separator
    return f"{x:x}:{y:x}"

def decode_share_hex(encoded_share):
    """Convert a hex encoded share back to (x, y) tuple"""
    x_str, y_str = encoded_share.split(':')
    return (int(x_str, 16), int(y_str, 16))

def generate_share_qrcode(share, filename=None):
    """
    Generate a QR code for a share and save it to a file or return the image
    
    Args:
        share: The (x, y) tuple share
        filename: Optional filename to save the QR code image
        
    Returns:
        PIL Image object if filename is None, otherwise None
    """
    # Convert share to base64 first for better QR code efficiency
    encoded_share = encode_share_base64(share)
    
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    # Add data to the QR code
    qr.add_data(encoded_share)
    qr.make(fit=True)
    
    # Create an image from the QR code
    img = qr.make_image(fill_color="black", back_color="white")
    
    if filename:
        img.save(filename)
        return None
    else:
        return img

def generate_all_share_qrcodes(shares, directory="shares_qr"):
    """Generate QR codes for all shares and save them to files"""
    # Create directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    # Generate QR code for each share
    for i, share in enumerate(shares):
        filename = os.path.join(directory, f"share_{i+1}.png")
        generate_share_qrcode(share, filename)
        print(f"QR code for share {i+1} saved to {filename}")

def scan_share_qrcode(image_path):
    """
    Scan a QR code image to extract a share
    
    Args:
        image_path: Path to the QR code image
        
    Returns:
        The (x, y) tuple share extracted from the QR code
    """
    if not HAS_PYZBAR:
        print("Error: pyzbar package is required for QR code scanning.")
        print("Install it with: pip install pyzbar")
        return None
    
    # Open the image
    img = Image.open(image_path)
    
    # Decode the QR code
    decoded_objects = decode(img)
    if not decoded_objects:
        print(f"Error: Could not decode QR code in {image_path}")
        return None
    
    # Extract the data
    qr_data = decoded_objects[0].data.decode('utf-8')
    
    # Convert from base64 to share
    try:
        return decode_share_base64(qr_data)
    except Exception as e:
        print(f"Error decoding share from QR code: {e}")
        return None

def reconstruct_from_qrcodes(image_paths, prime):
    """
    Reconstruct the secret from a list of QR code image paths
    
    Args:
        image_paths: List of paths to QR code images
        prime: The prime modulus used during sharing
        
    Returns:
        The reconstructed secret as a string
    """
    if not HAS_PYZBAR:
        print("Error: pyzbar package is required for QR code scanning.")
        print("Install it with: pip install pyzbar")
        return None
    
    # Scan each QR code to get the shares
    shares = []
    for path in image_paths:
        share = scan_share_qrcode(path)
        if share:
            shares.append(share)
    
    # Reconstruct the secret from the shares
    if shares:
        return reconstruct(shares, prime)
    else:
        return "Error: Could not extract any valid shares from QR codes."

def main():
    # TODO: implement the CLI
    # TODO: the prime used should be attached to the shares, since without it, reconstruction is impossible
    # TODO: implement message splitting for messages larger than 512 bits:
    # - split the message into chunks of 512 bits
    # - share each chunk separately
    # - they should be labeled in a way that allows them to be distributed appropriately
    # print("this should only run if the script is invoked as a standalone application")

    pass


if __name__ == "__main__":
    main()
