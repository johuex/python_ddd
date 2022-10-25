import hashlib
import os
import shutil
from pathlib import Path

BLOCKSIZE = 65536
def hash_file(path):
    hasher = hashlib.sha1()
    with path.open("rb") as file:
        buf = file.read(BLOCKSIZE)
        while buf:
            hasher.update(buf)
            buf = file.read(BLOCKSIZE)
    return hasher.hexdigest()

def sync(source, dest):
# Обойти исходную папку и создать словарь имен и их хешей
    source_hashes = {}
    for folder, _, files in os.walk(source):
        for fn in files:
            source_hashes[hash_file(Path(folder) / fn)] = fn
    seen = set() # отслеживать файлы, найденные в целевой папке

# Обойти целевую папку и получить имена файлов и хеши
    for folder, _, files in os.walk(dest):
        for fn in files:
            dest_path = Path(folder) / fn
            dest_hash = hash_file(dest_path)
            seen.add(dest_hash)
        # если в целевой папке есть файл, которого нет
        # в источнике, то удалить его
            if dest_hash not in source_hashes:
                dest_path.remove()
            # если в целевой папке есть файл, который имеет другой
            # путь в источнике, то переместить его в правильный путь
            elif dest_hash in source_hashes and fn != source_hashes[dest_hash]:
                shutil.move(dest_path, Path(folder) / source_hashes[dest_hash])

    # каждый файл, который появляется в источнике, но не в месте
    # назначения, скопировать в целевую папку
    for src_hash, fn in source_hashes.items():
        if src_hash not in seen:
            shutil.copy(Path(source) / fn, Path(dest) / fn)
