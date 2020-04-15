import sqlite3


class Db:
    def __init__(self, path):
        self.db = sqlite3.connect(path, check_same_thread=False)

    def commit(self):
        self.db.commit()

    def get(self, query, params=False):
        cursor = self.db.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchall()

    def get_firsts(self, *args, amount=1, **kwargs):
        result = []
        for value in self.get(*args, **kwargs):
            result.extend(value[:amount])
        return result

    def execute(self, query, params=False, commit=True):
        cursor = self.db.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        if commit:
            self.db.commit()

    def close(self):
        self.db.close()


if __name__ == '__main__':
    print("I'm a module, I can't run!")
