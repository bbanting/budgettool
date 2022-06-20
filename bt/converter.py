import csv
import db
import entry
import datetime

def main():
    filename = input("Enter the name of your entry file: ")
    with open(filename, "r") as f:
        lines = f.readlines()
        reader = csv.DictReader(lines)
        for l in reader:
            attrs = []
            attrs.append(0)
            attrs.append(datetime.date.fromisoformat(l["date"].replace("/", "-")))
            attrs.append(entry.dollars_to_cents(l["amount"]))
            attrs.append(l["category"])
            attrs.append(l["note"])
            e = entry.Entry(*attrs)
            db.insert_entry(e)


if __name__ == "__main__":
    main()
        