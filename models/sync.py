import hashlib
import os
import shutil
from pathlib import Path
from typing import List, Any, Dict

BLOCKSIZE = 65536


def hash_file(path):
    """
    Получаем hash файла
    """
    hasher = hashlib.sha1()
    with path.open("rb") as file:
        buf = file.read(BLOCKSIZE)
        while buf:
            hasher.update(buf)
            buf = file.read(BLOCKSIZE)
    return hasher.hexdigest()


def read_paths_and_hashes(root):
    """
    Читаем содержимое директории и считаем hash файла
    """
    hashes = {}
    for folder, _, files in os.walk(root):
        for fn in files:
            hashes[hash_file(Path(folder) / fn)] = fn
    return hashes


def determine_actions(src_hashes, dst_hashes, src_folder, dst_folder):
    """
    Возвращаем абстрактные операции, которые нужно выполнить для синхронизации
    """
    for sha, filename in src_hashes.items():
        if sha not in dst_hashes:
            sourcepath = Path(src_folder) / filename
            destpath = Path(dst_folder) / filename
            yield 'copy', sourcepath, destpath
        elif dst_hashes[sha] != filename:
            olddestpath = Path(dst_folder) / dst_hashes[sha]
            newdestpath = Path(dst_folder) / filename
            yield 'move', olddestpath, newdestpath
    for sha, filename in dst_hashes.items():
        if sha not in src_hashes:
            yield 'delete', dst_folder / filename


def sync(source: Dict[str, Any], dest: Dict[str, Any]):
    # шаг 1 с императивным ядром: собрать входные данные
    # изолируем операции связанные с I/O
    source_hashes = read_paths_and_hashes(source)
    dest_hashes = read_paths_and_hashes(dest)

    # шаг 2: вызвать функциональное ядро
    # тут у нас бизнес-логика
    actions = determine_actions(source_hashes, dest_hashes, source, dest)

    # шаг 3 с императивным ядром: применить операции ввода-вывода данных
    for action, *paths in actions:
        if action == 'copy':
            shutil.copyfile(*paths)
        if action == 'move':
            shutil.move(*paths)
        if action == 'delete':
            os.remove(paths[0])
