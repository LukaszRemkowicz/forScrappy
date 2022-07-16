import os
import pathlib

from django.conf import settings


class FileDumper:
    def __init__(self,  logger, force_overwrite=True):
        self.force_overwrite = force_overwrite
        self.logger = logger

    def dump(self, filename: str, content) -> None:
        filepath = self._build_path(filename)
        self._ensure_path_exists(filepath)
        self._save_to_file(filepath, content)

    @staticmethod
    def _build_path(filename: str) -> str:
        path_to_dump = settings.MAIN_DIRECTORY_PATH
        return os.path.join(path_to_dump, filename)

    def load(self, filename: str):
        filepath = self._build_path(filename)
        if os.path.exists(filepath):
            with open(filepath, 'rb+') as f:
                content = f.read()
            return content
        raise FileNotFoundError(f"File {filepath} does not exist!")

    def path(self, filename: str) -> str:
        return self._build_path(filename)

    def file_exists(self, filename: str) -> bool:
        filepath = self._build_path(filename)
        return os.path.exists(filepath)

    def _save_to_file(self, filepath: str, content) -> None:
        self._check_force_overwrite(filepath)
        try:
            with open(filepath, 'wb+') as f:
                f.write(content)
            self.logger.info(f'Content saved to {filepath}')
        except (Exception, IOError) as e:
            self.logger.critical(e, f"\nTried saving to file {filepath}")

    @staticmethod
    def _ensure_path_exists(path: str) -> None:
        path = pathlib.Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

    def _check_force_overwrite(self, filepath: str) -> None:
        if os.path.exists(filepath) and not self.force_overwrite:
            self.logger.critical(f"FileExistsError: File {filepath} already exists! Overwrite forbidden by flag.")
            raise FileExistsError(f"File {filepath} already exists! Overwrite forbidden by flag.")
