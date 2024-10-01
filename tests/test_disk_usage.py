import unittest
from unittest.mock import MagicMock, patch

from disk_usage import (CalculatingFilesCount, CalculatingMemoryUsage, File,
                        UpdatingFoldersSize)


class TestDiskUsage(unittest.TestCase):

    def test_file_init(self):
        file = File("test.txt")
        self.assertEqual(file.name, "test.txt")
        self.assertEqual(file.size, 0)

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

    @patch('os.walk')
    def test_calculating_files_count(self, mock_walk):
        task = CalculatingFilesCount("root")
        mock_walk.return_value = [('root', ['dir1', 'dir2'], []),
                                  ('root\\dir1', [], ['file1']),
                                  ('root\\dir2', [], ['file2'])]
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