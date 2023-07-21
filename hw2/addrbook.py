import json
from collections import UserDict
from pathlib import Path
from datetime import datetime, timedelta
from re import search

DATE_FORMAT = "%Y-%m-%d"
TEXT_FORMAT = "%d %b %Y"
MIN_YEAR = 1812


class Field:
    def __init__(self, value: str = None):
        self.value = value

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value: str):
        self.__value = value

    def __str__(self) -> str:
        return self.value


class Phone(Field):
    @Field.value.setter
    def value(self, value: str):
        if len(value := str(value)) == 12 and value.isdigit():
            Field.value.fset(self, value)
        else:
            raise ValueError(f"'{value}' is not a valid phone number")


class Email(Field):
    @Field.value.setter
    def value(self, value: str):
        if search(r"^\w+([-+.']\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$", value):
            Field.value.fset(self, value)
        else:
            raise ValueError(f"'{value}' is not a valid e-mail")


class Name(Field):
    ...


class Birthday(Field):
    @Field.value.setter
    def value(self, value: str):
        try:
            birthday = datetime.strptime(value, DATE_FORMAT)
        except ValueError:
            raise ValueError(
                f"'{value}' does not match the expected format ('yyyy-mm-dd')"
            )
        if not datetime.today().year > birthday.year >= MIN_YEAR:
            raise ValueError(f"'{value}' is not a valid date")
        Field.value.fset(self, birthday)

    def replace_year(self, year: int) -> datetime:
        try:
            return self.value.replace(year=year)
        except ValueError:
            return datetime(year=year, month=2, day=28)

    def days_to_birthday(self) -> int:
        today = datetime.today()
        birthday = self.replace_year(today.year)
        if today > birthday:
            birthday = self.replace_year(today.year + 1)
        return (birthday - today).days

    def to_date_str(self) -> str:
        return self.value.strftime(DATE_FORMAT)

    def to_text_str(self) -> str:
        return self.value.strftime(TEXT_FORMAT)

    def __str__(self) -> str:
        return f"{self.to_text_str()} ({self.days_to_birthday()} days left)"

    def __contains__(self, days: int) -> bool:
        return self.days_to_birthday() <= days


class Record:
    def __init__(self, name: Name, birthday=None, email=None, phone=None):
        self.name = name
        self.birthday = birthday
        self.email = email
        self.phone: list[Phone] = []
        self.add_phone(phone)

    def is_phone(self, phone: Phone) -> bool:
        if self.phone:
            if phone.value in set(p.value for p in self.phone):
                return True
        return False

    def add_phone(self, phone) -> int:
        counter = 0
        if isinstance(phone, (list, tuple)):
            for p in phone:
                if not self.is_phone(p):
                    self.phone.append(p)
                    counter += 1
        elif isinstance(phone, Phone) and not self.is_phone(phone):
            self.phone.append(phone)
            counter = 1
        return counter

    def delete_phone(self, phone: Phone) -> bool:
        if self.is_phone(phone):
            self.phone.remove(phone)
            return True
        return False

    def __contains__(self, search_str: str) -> bool:
        if search_str.lower() in self.name.value.lower():
            return True
        if search_str.isdigit():
            if search_str in "!".join(p.value for p in self.phone):
                return True
        return False

    def to_str_list(self) -> list[str]:
        return [
            self.name.value,
            str(self.birthday) if self.birthday else "",
            self.email.value if self.email else "",
            ", ".join(str(p) for p in self.phone)
        ]


class AddressBook(UserDict):
    def __init__(self, filename="ab.json"):
        super().__init__()
        self.file_path = Path(filename)
        self.read_from_file()

    def add_record(self, record: Record):
        if record.name.value in self.data:
            raise KeyError(f"Cannot duplicate '{record.name.value}'")
        self.data[record.name.value] = record
        self.save_changes = True

    def delete_record(self, name: str) -> bool:
        if name in self.data:                         # !!!
            del self.data[name]
            self.save_changes = True
            return True
        return False

    def add_phone(self, name: str, phone: Phone) -> bool:
        if self.data[name].add_phone(phone):
            self.save_changes = True
            return True

    def delete_phone(self, name: str, phone: Phone):
        if self.data[name].delete_phone(phone):
            self.save_changes = True

    def update_birthday(self, name: str, birthday: Birthday):
        self.data[name].birthday = birthday
        self.save_changes = True

    def update_email(self, name: str, email: Email):
        self.data[name].email = email
        self.save_changes = True

    def search_birthday(self, days: int) -> list[str]:
        today = datetime.today()
        new_date = (today + timedelta(days=days)).replace(year=today.year)
        if new_date < today:
            new_date = new_date.replace(year=today.year + 1)
        days = (new_date - today).days                # standardize days
        return sorted(
            name for name, record in self.data.items()
            if record.birthday and days in record.birthday
        )

    def search(self, search_str=None) -> list[str]:
        if search_str:
            return sorted(
                name for name, record in self.data.items()
                if search_str in record
            )
        else:
            return sorted(self.data.keys())

    def from_dict(self, source: dict):
        for k, v in source.items():
            self.data[k] = Record(
                Name(v["name"]),
                birthday=Birthday(v["birthday"]) if v["birthday"] else None,
                email=Email(v["email"]) if v["email"] else None,
                phone=[Phone(x) for x in v["phone"]],
            )

    def read_from_file(self):
        self.save_changes = False
        if self.file_path.exists():
            with open(self.file_path, "r", encoding="utf-8") as f:
                try:
                    self.from_dict(json.load(f))
                except json.decoder.JSONDecodeError:
                    print(f"ERROR: File {self.file_path} could not be decoded")

    def to_dict(self) -> dict:
        return {
            k: {
                "name": v.name.value,
                "birthday": v.birthday.to_date_str() if v.birthday else None,
                "email": v.email.value if v.email else None,
                "phone": [p.value for p in v.phone],
            }
            for k, v in self.data.items()
        }

    def write_to_file(self):
        if self.save_changes:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f)
                self.save_changes = False
