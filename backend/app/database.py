import sqlite3
import json
import os
from pathlib import Path
from .seed_data import SCHEMES_SEED, SAMPLE_CASES_SEED, LEARNING_RESOURCES_SEED

DB_PATH = Path(__file__).resolve().parent.parent / "setu.db"

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Schemes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schemes (
        scheme_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        name_ta TEXT,
        state TEXT NOT NULL,
        completed_class TEXT NOT NULL,
        income_limit INTEGER NOT NULL,
        categories TEXT NOT NULL,
        gender TEXT NOT NULL,
        benefit_amount TEXT NOT NULL,
        benefit_amount_ta TEXT,
        deadline TEXT NOT NULL,
        documents TEXT NOT NULL,
        apply_steps TEXT NOT NULL,
        official_url TEXT NOT NULL,
        source_authority TEXT NOT NULL,
        last_verified TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'ACTIVE'
    )
    """)

    # Student profiles table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        student_id TEXT PRIMARY KEY,
        name TEXT,
        state TEXT,
        completed_class INTEGER,
        income INTEGER,
        category TEXT,
        gender TEXT,
        course_pursuing TEXT,
        language TEXT DEFAULT 'en',
        confirmed INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Cases tracking table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cases (
        case_id TEXT PRIMARY KEY,
        student_name TEXT NOT NULL,
        phone TEXT,
        state TEXT NOT NULL,
        scheme_id TEXT NOT NULL,
        scheme_name TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'MATCHED',
        days_inactive INTEGER DEFAULT 0,
        teacher_alert INTEGER DEFAULT 0,
        reminder_sent INTEGER DEFAULT 0,
        notes TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    # Learning resources table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS learning_resources (
        resource_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        title_ta TEXT,
        category TEXT NOT NULL,
        target_class TEXT NOT NULL,
        url TEXT NOT NULL,
        language TEXT NOT NULL,
        verified_by TEXT NOT NULL
    )
    """)

    conn.commit()

    # Seed or synchronize schemes with verified seed data
    for s in SCHEMES_SEED:
        cursor.execute("""
        INSERT OR REPLACE INTO schemes (
            scheme_id, name, name_ta, state, completed_class, income_limit,
            categories, gender, benefit_amount, benefit_amount_ta, deadline,
            documents, apply_steps, official_url, source_authority, last_verified, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            s["scheme_id"], s["name"], s.get("name_ta"), s["state"], s["completed_class"],
            s["income_limit"], s["categories"], s["gender"], s["benefit_amount"],
            s.get("benefit_amount_ta"), s["deadline"], json.dumps(s["documents"]),
            json.dumps(s["apply_steps"]), s["official_url"], s["source_authority"],
            s["last_verified"], s["status"]
        ))
    conn.commit()

    # Seed sample cases if empty
    cursor.execute("SELECT COUNT(*) FROM cases")
    if cursor.fetchone()[0] == 0:
        for c in SAMPLE_CASES_SEED:
            cursor.execute("""
            INSERT INTO cases (
                case_id, student_name, phone, state, scheme_id, scheme_name,
                status, days_inactive, teacher_alert, reminder_sent, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                c["case_id"], c["student_name"], c["phone"], c["state"], c["scheme_id"],
                c["scheme_name"], c["status"], c["days_inactive"],
                1 if c["teacher_alert"] else 0, 1 if c["reminder_sent"] else 0,
                c.get("notes"), c["created_at"], c["updated_at"]
            ))
        conn.commit()

    # Seed or synchronize learning resources
    for r in LEARNING_RESOURCES_SEED:
        cursor.execute("""
        INSERT OR REPLACE INTO learning_resources (
            resource_id, title, title_ta, category, target_class, url, language, verified_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            r["resource_id"], r["title"], r.get("title_ta"), r["category"],
            r["target_class"], r["url"], r["language"], r["verified_by"]
        ))
    conn.commit()

    conn.close()
