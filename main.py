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
       
def main():
    from pprint import pprint
    pprint(search_movie_by_genre("Thriller"))
    pass
if __name__ == "__main__":
    main()