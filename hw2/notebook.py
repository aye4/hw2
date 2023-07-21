import json
from pathlib import Path
from datetime import datetime
from re import search

DATE_FORMAT = "%Y-%m-%d"


class NoteBook():
    def __init__(self, filename="nb.json"):
        self.file_path = Path(filename)
        self.read_from_file()

    def add_id_to_tags(self, note_id: int):
        self.save_changes = True
        if self.data[note_id]['tags']:
            for tag in self.data[note_id]['tags']:
                self.tags.setdefault(tag, []).append(note_id)
        else:
            self.tags.setdefault("#", []).append(note_id)

    def delete_id_from_tags(self, note_id: int):
        self.save_changes = True
        if self.data[note_id]['tags']:
            for tag in self.data[note_id]['tags']:
                self.tags.get(tag).remove(note_id)
        else:
            self.tags.get("#").remove(note_id)

    def delete_tag(self, note_id: int, tag: str):
        self.save_changes = True
        self.data[note_id]['tags'].remove(tag)
        if len(self.tags[tag]) == 1:
            del self.tags[tag]
        else:
            self.tags[tag].remove(note_id)
        if not self.data[note_id]['tags']:
            self.tags.setdefault("#", []).append(note_id)

    def tags_scan(self):
        self.tags = {}
        for note_id in self.data:
            self.add_id_to_tags(note_id)

    def from_dict(self, source: dict):
        for k, v in source.items():
            self.data[int(k)] = {
                "text": v['text'],
                "created": v['created'],
                "tags": v['tags']
            }

    def read_from_file(self):
        self.data: dict = {}
        self.max_id = 0
        self.save_changes = False
        if self.file_path.exists():
            with open(self.file_path, "r", encoding="utf-8") as f:
                try:
                    self.from_dict(json.load(f))
                except json.decoder.JSONDecodeError:
                    print(f"ERROR: File {self.file_path} could not be decoded")
        if self.data:
            self.max_id = max(self.data.keys()) + 1
        self.tags_scan()

    def write_to_file(self):
        if self.save_changes:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f)
                self.save_changes = False

    def add_note(self, text: str, tags: list[str] = []):
        self.data[self.max_id] = {
            "text": text,
            "created": datetime.today().strftime(DATE_FORMAT),
            "tags": tags
        }
        self.add_id_to_tags(self.max_id, tags)
        self.max_id += 1
        self.save_changes = True

    def add_tag(self, note_id: int, tag: str):
        if search(r"^#\w+$", tag):
            if self.data[note_id]['tags']:
                if tag in self.data[note_id]['tags']:
                    raise KeyError(f"Cannot duplicate tag '{tag}'")
            else:
                self.tags["#"].remove(note_id)
            self.save_changes = True
            self.data[note_id]['tags'].append(tag)
            self.tags.setdefault(tag, []).append(note_id)
        else:
            raise ValueError(f"'{tag}' is not a valid hashtag")

    def delete_note(self, note_id: int):
        self.delete_id_from_tags(note_id)
        del self.data[note_id]
        self.save_changes = True

    def update_text(self, note_id: int, text: str):
        self.data[note_id]["text"] = text
        self.save_changes = True

    def search_text(self, search_str: str = None) -> list[int]:
        if search_str:
            return sorted(
                note_id for note_id, note in self.data.items()
                if search_str.lower() in note['text'].lower()
            )
        else:
            return sorted(self.data.keys())

    def search_tag(self, search_str: str):
        if search_str in ("", "#"):
            return self.tags.get("#")
        result_set = set()
        for tag, note_id_list in self.tags.items():
            if search_str.lower() in tag.lower():
                result_set.update(note_id_list)
        return sorted(result_set)

    def __len__(self):
        return len(self.data)

    def to_list(self, note_id: int) -> list:
        if note_id in self.data:
            return [
                note_id,
                self.data[note_id]['created'],
                self.data[note_id]['text'],
                str(self.data[note_id]['tags'])
            ]
        return []

    def __getitem__(self, note_id: int):
        return self.data[note_id]

    def __contains__(self, note_id: int):
        return note_id in self.data
