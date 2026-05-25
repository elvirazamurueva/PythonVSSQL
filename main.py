import database
def search_movie_by_genre(genre: str):
    db = database.DatabaseManager("base.db")
    with db:
        results = db.select_records(
            table_name="movies",
            where_clause="genre LIKE ?",
            params=(f"%{genre}%",)
        )
        return results
def search_movies_by_title(word: str):
    db = database.DatabaseManager("base.db")

    with db:
        results = db.select_records(
            table_name="movies",
            where_clause="title LIKE ?",
            params=(f"%{word}%",)
        )

        return results





       
def main():
    from pprint import pprint
    pprint (search_movies_by_title("dark"))

    pass
if __name__ == "__main__":
    main()
