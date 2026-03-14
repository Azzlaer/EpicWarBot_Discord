import mysql.connector
import yaml

with open("config.yml", "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)


def get_connection():
    return mysql.connector.connect(
        host=CONFIG["database"]["host"],
        user=CONFIG["database"]["user"],
        password=CONFIG["database"]["password"],
        database=CONFIG["database"]["name"]
    )


def map_hash_exists(map_hash):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM discord_maps WHERE map_hash=%s LIMIT 1", (map_hash,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row is not None


def save_map(user, name, file, url, size, map_hash):
    conn = get_connection()
    cur = conn.cursor()
    sql = """
    INSERT INTO discord_maps
    (discord_user, map_name, map_file, source_url, file_size, map_hash)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    cur.execute(sql, (user, name, file, url, size, map_hash))
    conn.commit()
    cur.close()
    conn.close()


def search_maps(term="", limit=100):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    if term.strip():
        like = f"%{term.strip()}%"
        cur.execute("""
            SELECT id, discord_user, map_name, map_file, source_url, file_size, map_hash, created_at
            FROM discord_maps
            WHERE map_name LIKE %s
               OR map_file LIKE %s
               OR discord_user LIKE %s
               OR source_url LIKE %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (like, like, like, like, limit))
    else:
        cur.execute("""
            SELECT id, discord_user, map_name, map_file, source_url, file_size, map_hash, created_at
            FROM discord_maps
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_stats():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    stats = {}

    cur.execute("SELECT COUNT(*) AS total FROM discord_maps")
    stats["total_maps"] = cur.fetchone()["total"] or 0

    cur.execute("SELECT COALESCE(SUM(file_size), 0) AS total_size FROM discord_maps")
    stats["total_size"] = cur.fetchone()["total_size"] or 0

    cur.execute("""
        SELECT discord_user, COUNT(*) AS total
        FROM discord_maps
        GROUP BY discord_user
        ORDER BY total DESC
        LIMIT 5
    """)
    stats["top_users"] = cur.fetchall()

    cur.execute("""
        SELECT map_name, created_at
        FROM discord_maps
        ORDER BY created_at DESC
        LIMIT 5
    """)
    stats["latest_maps"] = cur.fetchall()

    cur.close()
    conn.close()
    return stats