import sqlite3
import time
import os
from discord.utils import get
SUCCESSIVE_FAILS = 10


class WatchDb:
    async def safe_send_message(self, recipient, message, bot):
        try:
            await bot.send_message(recipient, message)
        except Exception as e:
            print(e)

    def __init__(self, db_path="data/watch.db"):
        os.makedirs("data", exist_ok=True)
        
        self.db = sqlite3.connect(db_path)
        self.cursor = self.db.cursor()

        self.cursor.execute("CREATE TABLE IF NOT EXISTS users_info (user_id TEXT, short_id TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS verifiers_info (short_id TEXT PRIMARY KEY, nickname TEXT, "
                            "status INTEGER, timestamp INTEGER, in_mesh INTEGER DEFAULT 0)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS user_id on users_info(user_id);")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS short_id on users_info(short_id);")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS timestamp on verifiers_info(timestamp);")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS verifiers on verifiers_info(short_id, status);")
        self.cursor.execute("UPDATE verifiers_info SET timestamp=?;", (int(time.time()), ))
        self.db.commit()

    def stop(self):
        self.db.close()

    def watch(self, user_id, short_id, verifiers_info):
        self.cursor.execute("INSERT into users_info values(?,?)", (user_id, short_id))
        self.cursor.execute("INSERT OR IGNORE into verifiers_info values(?,?,?,?,?)",
                            (short_id, verifiers_info[short_id][1], 0, int(time.time()), verifiers_info[short_id][2]))
        self.db.commit()

    def unwatch(self, user_id, short_id):
        self.cursor.execute("DELETE FROM users_info where user_id=? and short_id=?", (user_id, short_id))
        self.db.commit()

    async def update_verifiers_status(self, verifiers_data, bot):
        self.cursor.execute("select user_id, users_info.short_id from users_info join verifiers_info where"
                            " users_info.short_id=verifiers_info.short_id and timestamp < ?",
                            (int(time.time() - 100 * 60 * SUCCESSIVE_FAILS),))
        """
        removed_verifiers = self.cursor.fetchall()
        ip_list = "("
        for verifier in removed_verifiers:
            member = get(bot.get_all_members(), id=verifier[0])
            await self.safe_send_message(member, "verifier {} has been removed from the watch list because it has been "
                                                 "removed from the cycle.".format(verifier[1]), bot)
            ip_list += "'{}',".format(verifier[1])
        if removed_verifiers:
            ip_list = ip_list[:-1]
        ip_list += ")"
        self.cursor.execute("DELETE FROM users_info WHERE short_id in {}".format(ip_list))
        self.cursor.execute("DELETE FROM verifiers_info WHERE timestamp < ?",
                            (int(time.time() - 100 * 60 * SUCCESSIVE_FAILS),))
        self.db.commit()
        """
        self.cursor.execute("select user_id, users_info.short_id from users_info join verifiers_info where"
                            " users_info.short_id=verifiers_info.short_id and in_mesh = 0")
        queue_verifiers = self.cursor.fetchall()
        for verifier in queue_verifiers:
            if verifiers_data[verifier[1]][2] == 1:
                member = get(bot.get_all_members(), id=verifier[0])
                await self.safe_send_message(member, "verifier {} just joined the cycle!".format(verifier[1]), bot)

        self.cursor.execute("SELECT distinct(short_id) FROM users_info")
        short_ids = self.cursor.fetchall()
        current_time = int(time.time())
        for short_id in short_ids:
            if short_id[0] not in verifiers_data:
                continue
            verifier = verifiers_data[short_id[0]]
            if verifier[0] >= 2:
                verifier[0] = 1
            else:
                verifier[0] = 0

            self.cursor.execute("INSERT OR IGNORE into verifiers_info values(?,?,?,?,0)", (short_id[0], verifier[1], 0,
                                                                                           current_time))
            self.cursor.execute("UPDATE verifiers_info SET status=cast(status/10 as int)+?, timestamp=?, in_mesh=?"
                                " WHERE short_id=?", ((10**SUCCESSIVE_FAILS)*verifier[0], current_time, verifier[2],
                                                      short_id[0]))
        self.db.commit()

    async def get_verifiers_status(self, bot):
        self.cursor.execute("select user_id, users_info.short_id, nickname from users_info join verifiers_info where"
                            " users_info.short_id=verifiers_info.short_id and status=?",
                            (int("1"*(SUCCESSIVE_FAILS)+"0"),))
        stopped_verifiers = self.cursor.fetchall()
        for verifier in stopped_verifiers:
            member = get(bot.get_all_members(), id=verifier[0])
            await self.safe_send_message(member, "verifier {} ({}) just stopped, you should check what happened"
                                         .format(verifier[1], verifier[2]).replace(" () ", ""), bot)

    def get_list(self, user_id, param=""):
        query = "SELECT users_info.short_id, status, nickname FROM users_info join verifiers_info WHERE " \
                "user_id=? and users_info.short_id=verifiers_info.short_id"
        if param == "queue":
            query += " and in_mesh = 0"
        elif param == "cycle":
            query += " and in_mesh = 1"
        self.cursor.execute(query, (user_id,))
        return self.cursor.fetchall()
