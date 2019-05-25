import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine('postgres://igewbtyjdnqqxn:d5fdc749fe483d76e3d7219cc9a4285196b5a7b0f72ea57d45809f14c0e5d8aa@ec2-107-20-230-70.compute-1.amazonaws.com:5432/d54an3ap8fb3o1')
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv", "r")  # needs to be opened during reading csv
    reader = csv.reader(f)
    next(reader)
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
               {"isbn": isbn, "title": title, "author": author, "year": year})
        db.commit()
        #print(f"Added book with ISBN: {isbn} Title: {title}  Author: {author}  Year: {year}")

if __name__ == '__main__':
    main()
