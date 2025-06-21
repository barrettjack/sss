import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sss import *

# TODO: add tests for the CLI

class TestShamirSecretSharing(unittest.TestCase):
    
    def setUp(self):
        self.message = "This is a secret message"
        self.threshold = 3
        self.num_shares = 5
    
    def test_share_and_reconstruct_basic(self):
        """Test basic sharing and reconstruction functionality"""
        shares, prime = share(self.message, self.threshold, self.num_shares)
        
        # Test reconstruction with exact threshold
        reconstructed = reconstruct(shares[:self.threshold], prime)
        self.assertEqual(reconstructed, self.message)
        
        # Test reconstruction with more than threshold
        reconstructed_extra = reconstruct(shares[:self.threshold+1], prime)
        self.assertEqual(reconstructed_extra, self.message)
    
    def test_base64_encoding_decoding(self):
        """Test base64 encoding and decoding of shares"""
        shares, prime = share(self.message, self.threshold, self.num_shares)
        encoded_shares = [encode_share_base64(s, prime) for s in shares]
        
        # Test decoding
        decoded_shares = [decode_share_base64(es)[0] for es in encoded_shares[:self.threshold]]
        reconstructed = reconstruct(decoded_shares, prime)
        self.assertEqual(reconstructed, self.message)
    
    def test_qr_code_generation(self):
        """Test QR code generation"""
        shares, prime = share(self.message, self.threshold, self.num_shares)
        
        try:
            generate_all_share_qrcodes(shares, prime_value=prime)
            # Check if QR code files were created
            import os
            qr_files = [f"shares_qr/share_{i+1}.png" for i in range(self.num_shares)]
            for qr_file in qr_files:
                self.assertTrue(os.path.exists(qr_file), f"QR code file {qr_file} was not created")
        except Exception as e:
            self.fail(f"QR code generation failed: {e}")
    
    def test_qr_code_reconstruction(self):
        """Test reconstruction from QR codes if pyzbar is available"""
        if not HAS_PYZBAR:
            print("\nQR code scanning not available. Install pyzbar to enable this feature.")
            print("pip install pyzbar")
            self.skipTest("pyzbar not available")
            return
        
        shares, prime = share(self.message, self.threshold, self.num_shares)
        
        # Generate QR codes
        generate_all_share_qrcodes(shares, prime_value=prime)
        
        qr_paths = [f"shares_qr/share_{i+1}.png" for i in range(self.threshold)]
        reconstructed_from_qr = reconstruct_from_qrcodes(qr_paths)
        
        self.assertEqual(reconstructed_from_qr, self.message)
    
    def test_insufficient_shares(self):
        """Test that reconstruction fails with insufficient shares"""
        shares, prime = share(self.message, self.threshold, self.num_shares)
        
        # Try to reconstruct with fewer than threshold shares
        for num_shares_to_use in range(self.threshold):
            with self.subTest(num_shares=num_shares_to_use):
                insufficient_shares = shares[:num_shares_to_use]
                if num_shares_to_use == 0:
                    # With 0 shares, reconstruction should fail or return empty
                    try:
                        reconstructed = reconstruct(insufficient_shares, prime)
                        # If it doesn't raise an exception, it should not equal the original
                        self.assertNotEqual(reconstructed, self.message)
                    except:
                        # It's acceptable for reconstruction to fail with 0 shares
                        pass
                else:
                    reconstructed = reconstruct(insufficient_shares, prime)
                    # Should not equal the original message
                    self.assertNotEqual(reconstructed, self.message)
    
    def test_globals_not_reinitialized(self):
        """Test that globals aren't re-initialized when invoking the function share()"""
        # This addresses the question in the original test file
        shares1, prime1 = share("message1", 2, 3)
        shares2, prime2 = share("message2", 2, 3)
        
        # The prime should be the same global value
        self.assertEqual(prime1, prime2, "Prime values should be the same (using global _prime)")

if __name__ == '__main__':
    unittest.main(verbosity=2)
