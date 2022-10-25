import shutil
import tempfile
from pathlib import Path

from models.sync import sync


class TestSyncFiles:
    def test_when_a_file_exists_in_the_source_but_not_the_destination(self):
        """
        1. Создадим в source файл
        2. Начнем синхронизацию директорий
        ОР: файл появится в destination
        """
        try:
            source = tempfile.mkdtemp()
            dest = tempfile.mkdtemp()
            content = "Я — очень полезный файл"
            (Path(source) / 'my-file').write_text(content)
            sync(source, dest)
            expected_path = Path(dest) / 'my-file'
            assert expected_path.exists()
            assert expected_path.read_text() == content
        finally:
            shutil.rmtree(source)
            shutil.rmtree(dest)

    def test_when_a_file_has_been_renamed_in_the_source(self):
        """
        1. Создадим в source файл
        2. Создадим этот же файл в destination, но с другим именем
        3. Синхронизируем директории
        ОР: файл с другим названием в destination удален, в destination скопирован файл из source
        """
        try:
            source = tempfile.mkdtemp()
            dest = tempfile.mkdtemp()
            content = "Я — файл, который переименовали"
            source_path = Path(source) / 'source-filename'
            old_dest_path = Path(dest) / 'dest-filename'
            expected_dest_path = Path(dest) / 'source-filename'
            source_path.write_text(content)
            old_dest_path.write_text(content)
            sync(source, dest)
            assert old_dest_path.exists() is False
            assert expected_dest_path.read_text() == content
        finally:
            shutil.rmtree(source)
            shutil.rmtree(dest)