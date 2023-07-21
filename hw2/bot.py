from re import search
from pathlib import Path
from addrbook import AddressBook, Record, Phone, Birthday, Name, Email
from notebook import NoteBook
from clean import SortFolder
from abc import abstractmethod, ABCMeta
from os import system

LINE = "-" * 60


def yellow(string: str) -> str:
    return "\033[93m" + string + "\033[0m"


def red(string: str) -> str:
    return "\033[91m" + string + "\033[0m"


def white(string: str) -> str:
    return "\033[97m" + string + "\033[0m"


class Helper(metaclass=ABCMeta):
    @abstractmethod
    def loop(self):
        pass

    @abstractmethod
    def add_contact(self):
        pass

    @abstractmethod
    def edit_contact(self):
        pass

    @abstractmethod
    def search_contacts(self):
        pass

    @abstractmethod
    def show_contacts(self):
        pass

    @abstractmethod
    def add_note(self):
        pass

    @abstractmethod
    def edit_note(self):
        pass

    @abstractmethod
    def search_notes(self):
        pass

    @abstractmethod
    def show_notes(self):
        pass

    @abstractmethod
    def sort_folder(self):
        pass


class BotHelper(Helper):
    def __init__(self):
        self.contacts = AddressBook()
        self.notes = NoteBook()
        self.print_main_menu = True
        system("")

    def loop(self):
        while True:
            self.show_menu()
            if not self.get_user_input("Enter an option: "):
                self.exit()
            self.process_user_input()

    def show_menu(self):
        if not self.print_main_menu:
            return
        message = "\n[ Contacts: {} ] [ Notes: {} ]"
        print(yellow(message.format(len(self.contacts), len(self.notes))))
        print(LINE)
        print("1 = Add new contact")
        print("2 = Add new note")
        print("3 = Show all contacts")
        print("4 = Search contacts by birthday")
        print("5 = Search contacts using name and/or phone")
        print("6 = Show all notes")
        print("7 = Search notes using text")
        print("8 = Search notes using hashtag")
        print("9 = Sort files")
        print("0 = Exit (Ctrl+C)")
        print(LINE)
        print("NB: Options from 3 to 8 allow to select one item for update")
        print(LINE)

    def get_user_input(self, message: str) -> bool:
        self.user_input = None
        try:
            self.user_input = input(message).strip()
        except EOFError:           # F6/Ctrl-Z + Enter
            return False
        except KeyboardInterrupt:  # Ctrl-C
            print()
            return False
        return True

    def process_user_input(self):
        self.print_main_menu = True
        if self.user_input == "0":
            self.exit()
        elif self.user_input == "1":            # = Add new contact
            self.add_contact()
        elif self.user_input == "2":            # = Add new note
            self.add_note()
        elif self.user_input == "3":            # = Show all contacts
            self.show_contacts(self.contacts.search())
        elif self.user_input == "4":            # = Search by birthday
            self.search_contacts_by_birthday()
        elif self.user_input == "5":            # = Search name & phone
            self.search_contacts()
        elif self.user_input == "6":            # = Show all notes
            self.show_notes(self.notes.search_text())
        elif self.user_input == "7":            # = Search notes (text)
            self.search_notes()
        elif self.user_input == "8":            # = Search notes (hashtag)
            self.search_notes_by_hashtag()
        elif self.user_input == "9":            # = Sort folder
            self.sort_folder()
        else:
            print(red("Unrecognized command"))
            self.print_main_menu = False

    def exit(self):
        self.contacts.write_to_file()
        self.notes.write_to_file()
        print(yellow("Good bye!"))
        exit()

    def add_contact(self):
        print(yellow("\n[ ADD NEW CONTACT ]"))
        print(LINE)
        print("You may leave the birthday/email/phone fields blank")
        print("Ctrl+C to exit")
        print(LINE)
        if not self.get_user_input("Enter a name (required): "):
            return
        if not self.user_input or self.user_input in self.contacts:
            print(red("\nCannot add duplicate or empty name"))
            return
        name = Name(self.user_input)
        if not self.get_user_input("Enter birthday (e.g. '1999-10-22'): "):
            return
        try:
            birthday = Birthday(self.user_input)
        except ValueError as e:
            birthday = None
            if self.user_input:
                print(red(f"{e}"))
        if not self.get_user_input("Enter e-mail: "):
            return
        try:
            email = Email(self.user_input)
        except ValueError as e:
            email = None
            if self.user_input:
                print(red(f"{e}"))
        print(LINE)
        print("Every phone number consists of 12 digits, e.g. 380501234567")
        print("You may enter a list of phone numbers separated by ' '")
        print(LINE)
        if not self.get_user_input("Enter phone number(s): "):
            return
        phones = []
        for phone in self.user_input.split():
            try:
                phones.append(Phone(phone.strip()))
            except ValueError as e:
                print(red(f"{e}"))
            else:
                print(f"Phone '{phones[-1]}' added.")
        self.contacts.add_record(Record(name, birthday, email, phones))
        print(f"\nContact '{name}' successfully added.")

    def add_note(self):
        print(yellow("\n[ ADD NEW NOTE ]"))
        print(LINE)
        print("Ctrl+C to exit")
        print(LINE)
        if not self.get_user_input("Enter a note text (required): "):
            return
        if not self.user_input:
            print(red("\nCannot add an empty note"))
            return
        text = self.user_input
        print("You may leave the tags blank (press 'Enter'),")
        message = "Enter list of tags separated by ' ' (e.g. #world #bus): "
        if not self.get_user_input(message):
            return
        tags = []
        for tag in self.user_input.split():
            if search(r"^#\w+$", tag):
                if tag in tags:
                    print(red(f"Duplicate tag '{tag}'"))
                else:
                    print(f"Hashtag '{tag}' added")
                    tags.append(tag)
            else:
                print(red(f"'{tag}' is not a hashtag"))
        self.notes.add_note(text, tags)
        print("\nNote successfully added.")

    def search_contacts_by_birthday(self):
        while self.get_user_input("Enter number of days to birthday: "):
            try:
                days = int(self.user_input)
            except ValueError:
                print(red("Integer number expected"))
            else:
                self.show_contacts(self.contacts.search_birthday(days))
                return

    def search_contacts(self):
        if self.get_user_input("Enter a pattern to search contacts: "):
            self.show_contacts(self.contacts.search(self.user_input))

    def show_contacts(self, name_list: list[str], select=True):
        if name_list:
            headers = [" Row", "User", "Birthday", "e-mail", "Phone number(s)"]
            format_str = "{:>5} {:<40} {:<27} {:<30} {:<20}"
            print()
            print(format_str.format(*headers))
            line = " ".join("-" * i for i in [5, 40, 27, 30, 20])
            print(line)
            for i, name in enumerate(name_list):
                print(format_str.format(i, *self.contacts[name].to_str_list()))
            print(line)
            if select:
                row_list = list(range(len(name_list)))
                row = self.get_row_number(row_list, "contact")
                if row is None:
                    print("\nNo contacts selected")
                else:
                    self.edit_contact(name_list[row])
        else:
            print(white("\n0 contacts found"))

    def get_row_number(self, rows: list[int], item: str) -> int:
        message = f"Type row number to select a {item} ('Enter' to skip): "
        while self.get_user_input(white(message)):
            try:
                row_number = int(self.user_input)
            except ValueError:
                if self.user_input:
                    print(red("Integer number expected"))
                else:
                    return None
            else:
                if row_number in rows:
                    return row_number
                else:
                    print(red("Please enter a valid row number"))

    def edit_contact(self, name: str):
        self.print_edit_menu = True
        while True:
            self.show_edit_contact_menu(name)
            if self.get_user_input("Enter an option: "):
                self.print_edit_menu = True
                if self.user_input == "0":
                    break
                if self.user_input == "1":
                    self.add_phone(name)
                elif self.user_input == "2":
                    self.delete_phone(name)
                elif self.user_input == "3":
                    self.update_email(name)
                elif self.user_input == "4":
                    self.update_birthday(name)
                elif self.user_input == "5":
                    self.delete_email(name)
                elif self.user_input == "6":
                    self.delete_birthday(name)
                elif self.user_input == "7":
                    if self.delete_contact(name):
                        break
                elif self.user_input == "8":
                    self.show_contacts([name], select=False)
                else:
                    print(red("Unrecognized command"))
                    self.print_edit_menu = False
            else:
                break

    def show_edit_contact_menu(self, name: str):
        if self.print_edit_menu:
            print(yellow(f"\n[ Contact '{name}' selected ]"))
            print(LINE)
            print("1 = Add new phone(s)")
            print("2 = Delete existing phone")
            print("3 = Update e-mail")
            print("4 = Update birthday")
            print("5 = Delete e-mail")
            print("6 = Delete birthday")
            print("7 = Delete contact")
            print("8 = Show contact")
            print("0 = Main menu (Ctrl+C)")
            print(LINE)

    def add_phone(self, name: str):
        message = "Enter 12-digit phone, e.g. 380501234567: "
        while self.get_user_input(message):
            try:
                phone = Phone(self.user_input)
            except ValueError as e:
                print(red(f"{e}"))
            else:
                if self.contacts.add_phone(name, phone):
                    print(f"\nContact '{name}' successfully updated.")
                    return
                else:
                    print(red("Duplicate phone number"))

    def delete_phone(self, name: str):
        if self.contacts[name].phone:
            print(LINE)
            for i, phone in enumerate(self.contacts[name].phone):
                print(f"{i} = {phone}")
            print(LINE)
            message = "Enter row number for the phone to delete: "
            while self.get_user_input(yellow(message)):
                try:
                    phone_id = int(self.user_input)
                except ValueError:
                    print(red("Integer number expected"))
                    continue
                try:
                    phone = self.contacts[name].phone[phone_id]
                except KeyError:
                    print(red(f"Use integer from 0 to {i}."))
                else:
                    self.contacts.delete_phone(name, phone)
                    print(white(f"\nPhone '{phone}' has been deleted."))
                    return
        else:
            print(f"Contact '{name}' has 0 phone numbers")

    def update_email(self, name: str):
        while self.get_user_input("Enter e-mail: "):
            try:
                email = Email(self.user_input)
            except ValueError as e:
                print(red(f"{e}"))
            else:
                self.contacts.update_email(name, email)
                print(f"\nContact '{name}' successfully updated.")
                return

    def update_birthday(self, name: str):
        message = "Enter birthday (format is 'yyyy-mm-dd', e.g.'1999-10-22'): "
        while self.get_user_input(message):
            try:
                birthday = Birthday(self.user_input)
            except ValueError as e:
                print(red(f"{e}"))
            else:
                self.contacts.update_birthday(name, birthday)
                print(f"\nContact '{name}' successfully updated.")
                return

    def delete_email(self, name: str):
        if self.contacts[name].email:
            self.contacts.update_email(name, None)
            print(f"\nContact '{name}' successfully updated.")

    def delete_birthday(self, name: str):
        if self.contacts[name].birthday:
            self.contacts.update_birthday(name, None)
            print(f"\nContact '{name}' successfully updated.")

    def delete_contact(self, name: str) -> bool:
        if self.get_user_input(yellow(f"Delete contact '{name}'?(Y)")):
            if self.user_input.lower()[0] == "y":
                self.contacts.delete_record(name)
                print(white(f"\nContact '{name}' successfully deleted."))
                return True
        return False

    def search_notes(self):
        if self.get_user_input("Enter a text pattern to search notes: "):
            self.show_notes(self.notes.search_text(self.user_input))

    def search_notes_by_hashtag(self):
        if self.get_user_input("Enter a text pattern to search tags: "):
            self.show_notes(self.notes.search_tag(self.user_input))

    def show_notes(self, note_id_list: list[int], select=True):
        if note_id_list:
            headers = ["Row ", "Date   ", "Note", "[Hashtags]"]
            format_str = "{:>5} {:>10} {:<60} {:<1}"
            print()
            print(format_str.format(*headers))
            line = " ".join("-" * i for i in [5, 10, 60])
            print(line)
            for i in note_id_list:
                note = self.notes.to_list(i)
                if len(note[2]) > 60:
                    note[3] += "\n" + " " * 17 + note[2][60:]
                    note[2] = note[2][:60]
                print(format_str.format(*note))
            print(line)
            if select:
                row = self.get_row_number(note_id_list, "note")
                if row is None:
                    print(white("\nNo notes selected"))
                else:
                    self.edit_note(row)
        else:
            print(white("\n0 notes found"))

    def edit_note(self, note_id: int):
        self.print_edit_menu = True
        while True:
            self.show_edit_note_menu(note_id)
            if self.get_user_input("Enter an option: "):
                self.print_edit_menu = True
                if self.user_input == "0":
                    break
                if self.user_input == "1":
                    self.update_note_text(note_id)
                elif self.user_input == "2":
                    self.delete_note_tag(note_id)
                elif self.user_input == "3":
                    self.add_note_tag(note_id)
                elif self.user_input == "4":
                    if self.delete_note(note_id):
                        break
                elif self.user_input == "5":
                    self.show_notes([note_id], select=False)
                else:
                    print(red("Unrecognized command"))
                    self.print_edit_menu = False
            else:
                break

    def show_edit_note_menu(self, note_id: int):
        if self.print_edit_menu:
            print(yellow(f"\n[ Note {note_id} selected ]"))
            print(LINE)
            print("1 = Update text")
            print("2 = Delete existing hashtag")
            print("3 = Add new hashtag")
            print("4 = Delete note")
            print("5 = Show note")
            print("0 = Main menu (Ctrl+C)")
            print(LINE)

    def update_note_text(self, note_id: int):
        if self.get_user_input("Enter new text: "):
            self.notes.update_text(note_id, self.user_input)
            print(f"\nNote {note_id} successfully updated.")

    def delete_note_tag(self, note_id: int):
        tags = self.notes[note_id]["tags"]
        if not tags:
            print(white("\nThere are 0 hashtags in the selected note"))
            return
        print(LINE)
        for i, tag in enumerate(tags):
            print(f"{i} = {tag}")
        print(LINE)
        message = "Enter row number for the tag to delete: "
        while self.get_user_input(yellow(message)):
            try:
                tag_id = int(self.user_input)
            except ValueError:
                print(red("Integer number expected"))
                continue
            try:
                self.notes.delete_tag(note_id, tags[tag_id])
            except KeyError:
                print(red(f"Use integer from 0 to {len(tags) - 1}."))
            else:
                print(white(f"\nHashtag '{tag}' has been deleted."))
                return

    def add_note_tag(self, note_id: int):
        while self.get_user_input("Enter hashtag (e.g. #world): "):
            try:
                self.notes.add_tag(note_id, self.user_input)
            except (ValueError, KeyError) as e:
                print(red(f"{e}"))
            else:
                print(f"\nNote {note_id} successfully updated.")
                break

    def delete_note(self, note_id: int) -> bool:
        if self.get_user_input(yellow(f"Delete note {note_id}?(Y)")):
            if self.user_input.lower()[0] == "y":
                self.notes.delete_note(note_id)
                print(white(f"\nNote {note_id} successfully deleted."))
                return True
        return False

    def sort_folder(self):
        print(yellow("\n[ SORT FILES ]"))
        print(LINE)
        print("Please specify folder name or leave it blank and press Enter")
        print(f"to use the current folder ({Path('.').parent.resolve()})")
        print(LINE)
        if self.get_user_input(white("Enter folder name: ")):
            path = Path(self.user_input) if self.user_input else Path(".")
            try:
                sort_files = SortFolder(path)
                sort_files.start()
            except ValueError as e:
                print(red(f"\n{e}\n"))


def run():
    menu = BotHelper()
    menu.loop()


if __name__ == "__main__":
    run()
