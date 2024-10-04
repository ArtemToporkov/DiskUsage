import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from disk_usage import (CalculatingFilesCount, CalculatingMemoryUsage, File,
                        UpdatingFoldersSize)


class TestDiskUsage(unittest.TestCase):

    def test_file_init(self):
        path = Path(__file__).parent / "test.txt"
        file = File(str(path))
        self.assertEqual(file.name, "test.txt")
        self.assertEqual(file.size, 0)
        self.assertIsNotNone(file.creation_date)
        self.assertIsNotNone(file.change_date)
        self.assertEqual(file.extension, ".txt")
        self.assertIsNotNone(file.owner)

    def test_file_is_file(self):
        path = Path(__file__).parent / "test.txt"
        file = File(str(path))
        self.assertTrue(file.is_file())

    def test_file_get_file_extension(self):
        path = Path(__file__).parent / "test.txt"
        self.assertEqual(File.get_file_extension(path), ".txt")

    def test_file_get_catalog_name(self):
        self.assertEqual(File.get_catalog_name("C:\\test"), "test")
        self.assertEqual(File.get_catalog_name("C:\\"), "C")

    def test_file_get_owner(self):
        with patch('disk_usage.win32security.GetFileSecurity') as mock_get_file_security:
            mock_get_file_security.return_value = MagicMock()
            mock_get_file_security.return_value.GetSecurityDescriptorOwner.return_value = "owner_sid"
            with patch('disk_usage.win32security.LookupAccountSid') as mock_lookup_account_sid:
                mock_lookup_account_sid.return_value = ("owner", None, None)
                self.assertEqual(File.get_owner("test.txt"), "owner")

    def test_calculating_files_count(self):
        path = Path(__file__).parent / "root"
        task = CalculatingFilesCount(path)
        task.run()
        self.assertEqual(task.result, 4)

    def test_calculating_memory_usage(self):
        with patch('disk_usage.os.scandir') as mock_scandir:
            mock_scandir.return_value = [MagicMock(path="file1"), MagicMock(path="dir1")]
            task = CalculatingMemoryUsage("C:\\", 4)
            task.run()
            self.assertIsNotNone(task.tree)

    def test_updating_folders_size(self):
        file = File("test.txt")
        file.files = [File("file1.txt"), File("file2.txt")]
        file.folders = [File("dir1")]
        task = UpdatingFoldersSize(file, 4)
        task.run()
        self.assertEqual(file.size, 0)

if __name__ == '__main__':
    unittest.main()