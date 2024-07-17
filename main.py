from collections import UserDict
import re
from datetime import datetime, date, timedelta
import pickle


class LengthPhoneNumberError(Exception):
    pass


class NotNumberError(Exception):
    pass


class IncorectNameError(Exception):
    pass


def get_phone(func):
    def inner(self, phone):
        pattern = r"\d+"
        if len(phone) != 10:
            raise LengthPhoneNumberError("Incorrectly entered phone number")
        if not re.fullmatch(pattern, phone):
            raise NotNumberError("Need to enter a phone number with digits only")

        return func(self, phone)

    return inner


def check_name(func):
    def inner(self, name):
        pattern = r"[a-zA-Z]+"
        if not re.fullmatch(pattern, name):
            raise IncorectNameError("Name must contain at least one letter")

        return func(self, name)

    return inner


def input_error(func):
    def inner(self, *args):
        try:
            return func(self, *args)
        except ValueError:
            return "Give me name, old phone and new phone please."
        except KeyError:
            return "There is no such contact!"

    return inner


def find_next_weekday(start_date, weekday):
    days_ahead = weekday - start_date.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return start_date + timedelta(days=days_ahead)


def adjust_for_weekend(birthday):
    if birthday.weekday() >= 5:
        return find_next_weekday(birthday, 0)
    return birthday


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    @check_name
    def __init__(self, value):
        super().__init__(value)


class Phone(Field):
    @get_phone
    def __init__(self, value):
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value):
        super().__init__(value)
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    @get_phone
    def add_phone(self, phone_number):
        self.phones.append(Phone(phone_number))

    @get_phone
    def remove_phone(self, phone_number):
        self.phones = [phone for phone in self.phones if phone_number != phone.value]

    def check_phone_is_found(self, number):
        for phone in self.phones:
            if phone.value == number:
                return self.phones.index(phone)
        raise ValueError("Not found phone number")

    def edit_phone(self, args: list):
        old_phone, new_phone = args
        try:
            index = self.check_phone_is_found(old_phone)
            self.phones[index] = Phone(new_phone)
            return "Contact was changed successfully"
        except ValueError as e:
            raise KeyError("There is no such contact!") from e

    def find_phone(self, phone):
        for item in self.phones:
            if item.value == phone:
                return item
        return None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)
        return "Birthday was added successful!"

    def __str__(self):
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}"


class AddressBook(UserDict):

    def add_record(self, contact: Record):
        self.data[contact.name.value] = contact

    def delete(self, name):
        self.data.pop(name)
        return f"Contact {name} was deleted!"

    def find(self, name: str):
        return self.data.get(name, None)

    def get_upcoming_birthdays(self):
        today = date.today()

        for record in self.data.values():
            if record.birthday:
                birthday_this_year = record.birthday.value.replace(year=today.year)
                if birthday_this_year < today:
                    birthday_this_year = record.birthday.value.replace(year=today.year + 1)

                if 0 <= (birthday_this_year - today).days <= 7:
                    birthday_this_year = adjust_for_weekend(birthday_this_year)
                    yield f"{record.name} - {birthday_this_year.strftime('%d.%m.%Y')}"
            return None

    def __str__(self):
        return '\n'.join(str(record) for record in self.data.values())


@input_error
def add_contact(args, book: AddressBook):
    try:
        name, phone, *_ = args
        record = book.find(name)
        message = "Contact updated."
        if not record:
            record = Record(name)
            book.add_record(record)
            message = "Contact added."
        if phone:
            record.add_phone(phone)
        return message
    except Exception as e:
        return e


@input_error
def edit_contact(args, book: AddressBook):
    try:
        name, *phones = args
        record = book.find(name)
        message = record.edit_phone(phones)
        return message
    except Exception as e:
        return e


@input_error
def add_birthday(args, book: AddressBook):
    try:
        name, birthday = args
        record = book.find(name)
        message = record.add_birthday(birthday)
        return message
    except Exception as e:
        return e


@input_error
def show_birthday(name, book: AddressBook):
    if book.find(name):
        return f"{name.title()} - {book.find(name).birthday}"
    return book.find(name)


@input_error
def birthdays(book: AddressBook):
    for person in book.get_upcoming_birthdays():
        print(person)


def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()  # Повернення нової адресної книги, якщо файл не знайдено


def main():
    book = load_data()
    print("Welcome to the assistant bot!")
    while True:
        command = input("Enter a command: ").strip().casefold()
        match command.split(" "):
            case ['hello']:
                print("How can I help you?")
            case ['all']:
                print(book)
            case "add", *info:
                print(add_contact(info, book))
            case "change", *info:
                print(edit_contact(info, book))
            case "add-birthday", *info:
                print(add_birthday(info, book))
            case "show-birthday", name:
                print(show_birthday(name, book))
            case ["birthdays"]:
                birthdays(book)
            case "phone", name:
                print(book.find(name))
            case "delete", name:
                print(book.delete(name))
            case ["close"] | ["exit"]:
                print("Good bye!")
                save_data(book)
                break
            case _:
                print("Invalid command.")


if __name__ == "__main__":
    main()
