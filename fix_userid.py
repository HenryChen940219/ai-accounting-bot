import sqlite3
conn = sqlite3.connect("accounting.db")
cur = conn.execute("UPDATE records SET user_id='Uf6bdf97ea1ab27618bd43a6408525cbd' WHERE user_id='unknown'")
conn.commit()
print(f"更新了 {cur.rowcount} 筆記錄")
conn.close()
