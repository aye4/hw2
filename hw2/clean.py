from re import sub
from pathlib import Path
from shutil import unpack_archive, ReadError
from hashlib import md5

# file extensions to sort
FOLDERS = {
    "images": ("JPEG", "PNG", "JPG", "SVG"),
    "video": ("AVI", "MP4", "MOV", "MKV"),
    "documents": ("DOC", "DOCX", "TXT", "PDF", "XLSX", "PPTX"),
    "audio": ("MP3", "OGG", "WAV", "AMR"),
    "archives": ("ZIP", "GZ", "TAR"),
}
RENAME_PATTERN = "_renamed_{:0>3}_"


class Normalize:
    @classmethod
    def __call__(cls, string: str) -> str:
        if not hasattr(cls, 'tran_dict'):
            CYRILLIC = [i for i in range(1072, 1112)] + [1169]
            LATIN = (
                "a", "b", "v", "g", "d", "e", "zh", "z", "i", "j",
                "k", "l", "m", "n", "o", "p", "r", "s", "t", "u",
                "f", "h", "ts", "ch", "sh", "sch", "", "y", "", "e",
                "yu", "ya", "_", "e", "_", "_", "je", "_", "i", "ji", "g",
            )
            cls.tran_dict = {}
            for cyrillic, latin in zip(CYRILLIC, LATIN):
                cls.tran_dict[cyrillic] = latin
                cls.tran_dict[ord(chr(cyrillic).upper())] = latin.upper()
        return sub(r"\W", "_", string.translate(cls.tran_dict))


class Counters:
    @classmethod
    def inc(cls, name: str):
        if not hasattr(cls, "counters"):
            cls.counters = {}
        cls.counters[name] = cls.counters.get(name, 0) + 1

    @classmethod
    def __getitem__(cls, name: str):
        return cls.counters.get(name, 0) if hasattr(cls, "counters") else 0

    @classmethod
    def __str__(cls):
        output = "-" * 60 + "\n"
        if not hasattr(cls, "counters") or len(cls.counters) == 0:
            return output + "0 files/folders found."
        for name, value in sorted((k, v) for k, v in cls.counters.items()):
            output += f"{name:<40}: {value}\n"
        return output


class Archives:
    @classmethod
    def append(cls, path: Path):
        if not hasattr(cls, "archives"):
            cls.archives = []
        cls.archives.append(path)

    @classmethod
    def unpack(cls, folder: Path):
        if hasattr(cls, "archives"):
            for archive in cls.archives:
                try:
                    unpack_archive(archive, folder / "archives" / archive.stem)
                except ReadError:
                    print(f"Warning: could not unpack the file '{archive}'.")
                else:
                    Counters().inc("Archives unpacked")
                    archive.unlink()


class FileWithHash:
    def __init__(self, path, calc_hash: bool = False):
        self.path = Path(path)
        self.md5_hash = None
        if calc_hash:
            self.calc_hash()

    def __getattr__(self, attr):
        return getattr(self.path, attr)

    def calc_hash(self):
        BUFFER_SIZE = 128 * 1024
        if self.path.is_file():
            md5_hash = md5()
            with open(self.path, "rb") as f:
                while True:
                    data = f.read(BUFFER_SIZE)
                    if not data:
                        break
                    md5_hash.update(data)
            self.md5_hash = md5_hash.hexdigest()

    def is_duplicate(self):
        if self.path.exists():
            return True
        if self.path.parent.stem == "archives":
            if (self.path.parent / self.path.stem).exists():
                return True
            if list(self.path.parent.glob(self.path.stem + ".*")):
                return True
        return False

    def __EQ__(self, other):
        if self.path.is_file() and other.path.is_file():
            if self.path.stat().st_size == other.path.stat().st_size:
                if not self.md5_hash:
                    self.calc_hash()
                if not other.md5_hash:
                    other.calc_hash()
                if self.md5_hash == other.md5_hash:
                    return True
        return False

    def update_name(self, name: str):
        self.path = self.path.parent / name
        self.md5_hash = None


class SortFolder:
    def __init__(self, folder: Path):
        if not folder.exists():
            raise ValueError(f"ERROR: '{folder}' does not exist.")
        if not folder.is_dir():
            raise ValueError(f"ERROR: '{folder}' is a file (not a folder).")
        self.folder = folder

    def start(self):
        print(f"Processing folder '{self.folder.resolve()}'...")
        self.process_folder(self.folder, 0)
        Archives().unpack(self.folder)
        print(Counters())

    def process_folder(self, folder: Path, level: int) -> bool:
        # returns True for an empty folder
        delete_empty_folder = bool(level)
        for f in folder.iterdir():
            if f.is_dir():
                if level or f.suffix or not f.stem.lower() in FOLDERS:
                    delete_empty_folder &= self.process_folder(f, level + 1)
            else:
                for name, ext in FOLDERS.items():
                    if f.suffix[1:].upper() in ext:
                        self.process_file(f, f.parents[level] / name)
                        break
                else:
                    Counters().inc("Unsupported extension")
                    delete_empty_folder = False
                    self.normalize_and_rename(f)
        if delete_empty_folder:
            folder.rmdir()
            Counters().inc("Empty folders deleted")
        else:
            self.normalize_and_rename(folder)
        return delete_empty_folder

    def process_file(self, file_path: Path, target: Path):
        new_name = Normalize()(file_path.stem)
        new_file = FileWithHash(target / (new_name + file_path.suffix))
        folder_counter = f"Files moved to '{target.stem}' folder"
        if not Counters()[folder_counter]:              # first file of a kind?
            self.prepare_target_folder(target)
        elif new_file.is_duplicate():
            main_file = FileWithHash(file_path)
            attempt = 0
            rename_pattern = new_name + RENAME_PATTERN + file_path.suffix
            while True:
                if new_file == main_file:               # checks size and hash
                    file_path.unlink()
                    Counters().inc("Duplicates deleted")
                    return
                else:
                    attempt += 1
                    new_file.update_name(rename_pattern.format(attempt))
                    if not new_file.is_duplicate():
                        Counters().inc("Duplicates renamed")
                        break
        file_path.replace(new_file.path)                # move to target folder
        Counters().inc(folder_counter)
        if target.stem == "archives":
            Archives().append(new_file.path)

    def prepare_target_folder(self, target: Path):
        if not target.exists():
            self.create_target_folder(target)
        elif target.is_file():                          # folder name occupied?
            tmp_file = self.get_unique_path(target, target.stem)
            target.replace(tmp_file)                    # temporary renaming
            self.create_target_folder(target)
            tmp_file.replace(target / target.stem)
            print(f"Warning: file '{target}' was moved into that folder.")

    def create_target_folder(self, target: Path):
        target.mkdir()
        print(f"Folder '{target}' has been created.")

    def normalize_and_rename(self, path: Path):
        new_name = Normalize()(path.stem)
        if new_name != path.stem:
            path.rename(self.get_unique_path(path, new_name))

    def get_unique_path(self, path: Path, new_name: str) -> Path:
        new_file = path.parent / (new_name + path.suffix)
        attempt = 0
        rename_pattern = new_name + RENAME_PATTERN + path.suffix
        while new_file.exists():
            attempt += 1
            new_file = path.parent / rename_pattern.format(attempt)
        return new_file
