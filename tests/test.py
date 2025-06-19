from sss import *

message = "This is a secret message"
threshold = 3
num_shares = 5

shares, prime = share(message, threshold, num_shares)
print("Original shares:")
for i, s in enumerate(shares):
    print(f"Share {i+1}: {s}")

print("\nBase64 encoded shares (more human-readable):")
encoded_shares = [encode_share_base64(s) for s in shares]
for i, es in enumerate(encoded_shares):
    print(f"Share {i+1}: {es}")

print("\nHex encoded shares (more compact):")
hex_shares = [encode_share_hex(s) for s in shares]
for i, hs in enumerate(hex_shares):
    print(f"Share {i+1}: {hs}")

# Generate QR codes for all shares
print("\nGenerating QR codes for shares:")
generate_all_share_qrcodes(shares)

# Demonstrate reconstruction
print("\nReconstruction from base64 shares:")
decoded_shares = [decode_share_base64(es) for es in encoded_shares[:threshold]]
reconstructed = reconstruct(decoded_shares, prime)
print(f"Reconstructed secret: {reconstructed}")

# Demonstrate reconstruction from QR codes (if pyzbar is available)
if HAS_PYZBAR:
    print("\nReconstruction from QR codes:")
    qr_paths = [f"shares_qr/share_{i+1}.png" for i in range(threshold)]
    reconstructed_from_qr = reconstruct_from_qrcodes(qr_paths, prime)
    print(f"Reconstructed secret from QR codes: {reconstructed_from_qr}")
else:
    print("\nQR code scanning not available. Install pyzbar to enable this feature.")
    print("pip install pyzbar")