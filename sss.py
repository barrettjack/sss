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

# dylib handling for zbar on macos
if sys.platform == "darwin":
    zbar_path = "/opt/homebrew/opt/zbar/lib"
    if os.path.exists(zbar_path):
        current_dyld_path = os.environ.get('DYLD_LIBRARY_PATH', '')
        if zbar_path not in current_dyld_path:
            os.environ['DYLD_LIBRARY_PATH'] = f"{zbar_path}:{current_dyld_path}".rstrip(':')

try:
    # this can fail if pyzbar is not installed, or cannot be found
    from pyzbar.pyzbar import decode
    HAS_PYZBAR = True
except ImportError:
    HAS_PYZBAR = False

_tmp = secrets.randbits(512)
_prime = nextprime(_tmp)

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

    assert message_int < _prime, "The inputted message must be utf-8-encodable in fewer than 512 bits."
    assert threshold <= num_shares, "The chosen threshold must be <= the number of shares to generate. Aborting."

    coeffs = [secrets.randbelow(_prime) for _ in range(threshold)]
    poly = lambda x: message_int + int(sum([x**j * coeffs[j] for j in range(1, threshold)]))
    
    shares = [(i, poly(i) % _prime) for i in range(1, num_shares + 1)]
    return shares, _prime


def reconstruct(shares: list[tuple[int, int]], prime: int = _prime):
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


def encode_share_base64(share, prime_value=_prime):
    """Convert a share (x, y) to a base64 string for human readability"""
    x, y = share
    # Pack the x and y values together, including prime if provided
    if prime_value:
        combined = f"{x}:{y}:{prime_value}"
    else:
        combined = f"{x}:{y}:{_prime}"
    # Encode to bytes and then to base64
    return base64.b64encode(combined.encode('utf-8')).decode('utf-8')


def decode_share_base64(encoded_share):
    """Convert a base64 encoded share back to (x, y) tuple and optionally prime"""
    # Decode from base64 to bytes and then to string
    decoded = base64.b64decode(encoded_share).decode('utf-8')
    # Split the string to get x, y and optionally prime
    parts = decoded.split(':')
    return (int(parts[0]), int(parts[1])), int(parts[2])



def generate_share_qrcode(share, filename=None, prime_value=_prime):
    """
    Generate a QR code for a share and save it to a file or return the image
    
    Args:
        share: The (x, y) tuple share
        filename: Optional filename to save the QR code image
        prime_value: Optional prime value to include with the share
        
    Returns:
        PIL Image object if filename is None, otherwise None
    """
    # Convert share to base64 first for better QR code efficiency
    encoded_share = encode_share_base64(share, prime_value)
    
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


def generate_all_share_qrcodes(shares, directory="shares_qr", prime_value=_prime):
    """Generate QR codes for all shares and save them to files"""
    # Create directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    # Generate QR code for each share
    for i, share in enumerate(shares):
        filename = os.path.join(directory, f"share_{i+1}.png")
        generate_share_qrcode(share, filename, prime_value)
        print(f"QR code for share {i+1} saved to {filename}")


def scan_share_qrcode(image_path):
    """
    Scan a QR code image to extract a share
    
    Args:
        image_path: Path to the QR code image
        
    Returns:
        Tuple containing (share, prime) where share is the (x, y) tuple and prime is the prime value
        or None if decoding fails. Share data is decoded from base64
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
        share, prime = decode_share_base64(qr_data)
        return share, prime
    except Exception as e:
        print(f"Error decoding share from QR code: {e}")
        return None


def reconstruct_from_qrcodes(image_paths):
    """
    Reconstruct the secret from a list of QR code image paths
    
    Args:
        image_paths: List of paths to QR code images

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
        result = scan_share_qrcode(path)
        all_equal_primes = True
        prime_value = None
        if result:
            share, share_prime = result
            if prime_value is None:
                prime_value = share_prime
            elif prime_value != share_prime:
                all_equal_primes = False
                break
            print(f"Successfully decoded share from {path}: {share}")
            shares.append(share)
        else:
            print(f"Failed to decode share from {path}")
    
    # Reconstruct the secret from the shares
    if shares:
        if all_equal_primes:
            return reconstruct(shares)
        else:
            return "Error: The shares have different prime values. Reconstruction failed."
    else:
        return "Error: Could not extract any valid shares from QR codes."


def main():
    parser = argparse.ArgumentParser(description="Shamir's Secret Sharing CLI")
    
    # Create a group for the main actions
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('-s', '--share', action='store_true', help='Share a secret')
    action_group.add_argument('-r', '--reconstruct', action='store_true', help='Reconstruct a secret from shares')
    
    # Create a group for message input type (only applicable for sharing)
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument('-m', '--message', type=str, help='Secret message to share')
    input_group.add_argument('-f', '--file', type=str, help='File containing the secret to share')
    
    # Add encoding type
    parser.add_argument('--enc_type', choices=['base64', 'qr'], default='base64', 
                        help='Encoding type for shares (base64 or QR codes)')
    
    # Positional arguments - will be interpreted based on action
    parser.add_argument('args', nargs='*', help='Additional arguments based on action. For sharing, the first two arguments are the threshold and number of shares. For reconstructing, the first argument is the path to the shares.')
    
    args = parser.parse_args()
    
    # Handle share action
    if args.share:
        # Validate input method
        if not args.message and not args.file:
            parser.error("When sharing, either -m/--message or -f/--file must be specified")
        
        # Validate and parse positional arguments
        if len(args.args) != 2:
            parser.error("When sharing, exactly 2 additional arguments are required: threshold and number_of_shares")
        
        try:
            threshold = int(args.args[0])
            num_shares = int(args.args[1])
        except ValueError:
            parser.error("Threshold and number_of_shares must be integers")
        
        # Get the message to share
        if args.message:
            message = args.message
        else:  # args.file
            try:
                with open(args.file, 'r') as f:
                    message = f.read()
            except Exception as e:
                print(f"Error reading file: {e}")
                return
        
        # Generate shares
        try:
            # Use globals()['share'] to avoid name conflict with args.share
            share_func = globals()['share']
            generated_shares, prime_used = share_func(message, threshold, num_shares)
            
            # Handle different encoding types
            if args.enc_type == 'base64':
                encoded_shares = [encode_share_base64(s, prime_used) for s in generated_shares]
                for i, es in enumerate(encoded_shares):
                    print(f"Share {i+1}: {es}")
                
                # Save shares to files
                shares_dir = "shares_base64"
                if not os.path.exists(shares_dir):
                    os.makedirs(shares_dir)
                
                for i, es in enumerate(encoded_shares):
                    with open(f"{shares_dir}/share_{i+1}.txt", 'w') as f:
                        f.write(es)
                print(f"Base64 encoded shares saved to {shares_dir}/ directory")
                
            elif args.enc_type == 'qr':
                generate_all_share_qrcodes(generated_shares, prime_value=prime_used)
                print(f"QR code shares generated in shares_qr/ directory")
            
        except Exception as e:
            print(f"Error generating shares: {e}")
    
    # Handle reconstruct action
    elif args.reconstruct:
        if not args.args:
            parser.error("When reconstructing, you must provide the path to the shares")
        
        # Handle different encoding types
        if args.enc_type == 'base64':
            # Assume args.args contains paths to base64 encoded share files
            shares = []
            
            for path in args.args:
                try:
                    with open(path, 'r') as f:
                        encoded_share = f.read().strip()
                        share_result = decode_share_base64(encoded_share)
                        
                        if isinstance(share_result, tuple) and len(share_result) == 2:
                            share, prime_from_share = share_result
                            shares.append(share)
                        else:
                            print(f"Invalid share format in {path}")
                except Exception as e:
                    print(f"Error reading share from {path}: {e}")
            
            if shares:
                secret = reconstruct(shares, prime_from_share)
                print(f"Reconstructed secret: {secret}")
            else:
                print("No valid shares found. Reconstruction failed.")
                
        elif args.enc_type == 'qr':
            # Assume args.args is a directory containing QR code images
            if len(args.args) != 1:
                parser.error("When reconstructing from QR codes, provide the directory containing the QR codes")
            
            qr_dir = args.args[0]
            if not os.path.isdir(qr_dir):
                print(f"Error: {qr_dir} is not a directory")
                return
            
            # Get all image files in the directory
            image_paths = []
            for filename in os.listdir(qr_dir):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    image_paths.append(os.path.join(qr_dir, filename))
            
            if not image_paths:
                print(f"No image files found in {qr_dir}")
                return
            
            secret = reconstruct_from_qrcodes(image_paths)
            if secret:
                print(f"Reconstructed secret: {secret}")
            else:
                print("Failed to reconstruct secret from QR codes")


if __name__ == "__main__":
    main()
