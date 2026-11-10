"""Unit tests for Photo & Passport Scanner Validator."""
import io
import unittest
from PIL import Image
from photo_validator import validate_biometric_photo, validate_passport_scan


def create_test_image(width: int, height: int, color=(255, 255, 255), fmt="JPEG", mode="RGB") -> bytes:
    img = Image.new(mode, (width, height), color=color)
    bio = io.BytesIO()
    img.save(bio, format=fmt)
    return bio.getvalue()


class PhotoValidatorTests(unittest.TestCase):
    def test_valid_600x600_biometric_photo(self):
        # White background, 600x600, RGB, JPEG
        data = create_test_image(600, 600, color=(245, 245, 245), fmt="JPEG", mode="RGB")
        res = validate_biometric_photo(data, "photo.jpg")
        self.assertTrue(res["valid"])
        self.assertTrue(res["is_jpeg"])
        self.assertTrue(res["is_exact_dim"])
        self.assertTrue(res["is_size_ok"])
        self.assertTrue(res["is_rgb"])
        self.assertIn("TEKNİK UYGUNLUK: GEÇTİ", res["formatted_report"])

    def test_invalid_dimensions(self):
        data = create_test_image(800, 600, color=(255, 255, 255), fmt="JPEG")
        res = validate_biometric_photo(data, "photo.jpg")
        self.assertFalse(res["valid"])
        self.assertFalse(res["is_exact_dim"])
        self.assertIn("600x600 veya 1200x1200", res["formatted_report"])

    def test_pdf_rejection(self):
        res = validate_biometric_photo(b"%PDF-1.4...", "photo.pdf")
        self.assertFalse(res["valid"])
        self.assertIn("PDF Formatı Kabul Edilmez", res["formatted_report"])

    def test_non_rgb_mode(self):
        # Grayscale image (mode L)
        img = Image.new("L", (600, 600), color=255)
        bio = io.BytesIO()
        img.save(bio, format="JPEG")
        res = validate_biometric_photo(bio.getvalue(), "photo.jpg")
        self.assertFalse(res["valid"])
        self.assertFalse(res["is_rgb"])
        self.assertIn("Siyah-Beyaz / Gri Tonlama Kabul Edilmez", res["formatted_report"])

    def test_passport_scan_valid(self):
        data = create_test_image(1200, 800, color=(200, 200, 200), fmt="JPEG")
        res = validate_passport_scan(data, "passport_scan.jpg")
        self.assertTrue(res["valid"])
        self.assertIn("Pasaport taramanız yükleme kriterlerine uygun", res["formatted_report"])

    def test_passport_scan_pdf_rejection(self):
        res = validate_passport_scan(b"%PDF-1.4...", "passport.pdf")
        self.assertFalse(res["valid"])
        self.assertIn("PDF Formatı Kabul Edilmez", res["formatted_report"])


if __name__ == "__main__":
    unittest.main()
