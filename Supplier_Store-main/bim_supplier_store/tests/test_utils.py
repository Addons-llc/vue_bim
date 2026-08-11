from unittest import TestCase

from bim_supplier_store.utils import normalize_hostname, normalize_store_code, validate_store_code


class TestSupplierStoreUtils(TestCase):
	def test_store_code_normalization(self):
		self.assertEqual(normalize_store_code("  Bucket Sadya  "), "bucket-sadya")
		self.assertTrue(validate_store_code("bucket-sadya"))
		self.assertFalse(validate_store_code("Bucket Sadya"))

	def test_hostname_normalization(self):
		self.assertEqual(normalize_hostname("HTTPS://WWW.Example.COM:443/path"), "www.example.com")
		self.assertEqual(normalize_hostname("store.example.com."), "store.example.com")

