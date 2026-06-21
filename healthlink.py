#!/usr/bin/env python3
"""
HEALTHLINK SIERRA LEONE – FINAL DEFINITIVE
Home page stats update on every patient change (add/update/delete).
Search bar moved up, visits chart transparent, total label removed.
Run: python healthlink_final.py
Login: admin / admin123
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime, timedelta
import random
import os
import sys
import csv
import re
import calendar

# ---------- Optional libraries ----------
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    import numpy as np
    MATPLOTLIB = True
except ImportError:
    MATPLOTLIB = False

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    REPORTLAB = True
except ImportError:
    REPORTLAB = False

# ---------- Theme colors ----------
class Theme:
    LIGHT = {
        'primary': '#1a5276',
        'primary_light': '#2e86c1',
        'secondary': '#1abc9c',
        'accent': '#e74c3c',
        'success': '#27ae60',
        'warning': '#f39c12',
        'background': '#f0f4f8',
        'sidebar_bg': '#0d1b2a',
        'sidebar_hover': '#1b3a5c',
        'card': '#ffffff',
        'card_border': '#d5dbdb',
        'text': '#2c3e50',
        'text_light': '#7f8c8d',
        'border': '#d5dbdb',
        'tree_bg': '#ffffff',
        'tree_fg': '#2c3e50',
        'tree_selected': '#2e86c1',
    }
    DARK = {
        'primary': '#2c3e50',
        'primary_light': '#34495e',
        'secondary': '#1abc9c',
        'accent': '#e74c3c',
        'success': '#27ae60',
        'warning': '#f39c12',
        'background': '#1e272e',
        'sidebar_bg': '#0a0f1a',
        'sidebar_hover': '#1b2a3a',
        'card': '#2d3a47',
        'card_border': '#4a5a6a',
        'text': '#ecf0f1',
        'text_light': '#b0bec5',
        'border': '#4a5a6a',
        'tree_bg': '#2d3a47',
        'tree_fg': '#ecf0f1',
        'tree_selected': '#34495e',
    }

current_theme = 'light'
COLORS = Theme.LIGHT.copy()

def apply_theme(theme_name):
    global COLORS
    if theme_name == 'dark':
        COLORS = Theme.DARK.copy()
    else:
        COLORS = Theme.LIGHT.copy()
    return COLORS

# ---------- Rounded frame helper ----------
class RoundedFrame(tk.Frame):
    def __init__(self, master, radius=10, bg=None, *args, **kwargs):
        self.radius = radius
        self.bg = bg if bg is not None else COLORS['card']
        super().__init__(master, bg=self.bg, *args, **kwargs)
        self.canvas = tk.Canvas(self, bg=self.bg, highlightthickness=0, bd=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.bind("<Configure>", self._draw)
        self._draw()

    def _draw(self, event=None):
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 2*self.radius or h < 2*self.radius:
            return
        self.canvas.delete("all")
        self.canvas.create_rounded_rectangle(0, 0, w, h, radius=self.radius,
                                             fill=self.bg, outline=COLORS['card_border'], width=2)

def _create_rounded_rect(self, x1, y1, x2, y2, radius=10, **kwargs):
    points = [x1+radius, y1,
              x2-radius, y1,
              x2, y1,
              x2, y1+radius,
              x2, y2-radius,
              x2, y2,
              x2-radius, y2,
              x1+radius, y2,
              x1, y2,
              x1, y2-radius,
              x1, y1+radius,
              x1, y1]
    return self.create_polygon(points, smooth=True, **kwargs)
tk.Canvas.create_rounded_rectangle = _create_rounded_rect

# ---------- Enhanced Calendar Picker ----------
class CalendarPicker:
    def __init__(self, master, callback, initial_date=None):
        self.master = master
        self.callback = callback
        self.initial_date = initial_date
        self.window = tk.Toplevel(master)
        self.window.title("Select Date")
        self.window.resizable(False, False)
        self.window.configure(bg=COLORS['background'])
        self.window.grab_set()

        self.year = datetime.now().year
        self.month = datetime.now().month
        if initial_date:
            try:
                dt = datetime.strptime(initial_date, '%Y-%m-%d')
                self.year = dt.year
                self.month = dt.month
            except:
                pass

        self.selected_date = initial_date

        self.build()
        self.center()

    def center(self):
        self.window.update_idletasks()
        w = self.window.winfo_width()
        h = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (w // 2)
        y = (self.window.winfo_screenheight() // 2) - (h // 2)
        self.window.geometry(f"{w}x{h}+{x}+{y}")

    def build(self):
        container = tk.Frame(self.window, bg=COLORS['background'], padx=10, pady=10)
        container.pack(fill=tk.BOTH, expand=True)

        self.date_label = tk.Label(container, text="Selected: " + (self.selected_date or "None"),
                                   font=('Tahoma',11,'bold'), bg=COLORS['background'], fg=COLORS['text'])
        self.date_label.pack(pady=(0,10))

        nav = tk.Frame(container, bg=COLORS['background'])
        nav.pack(fill=tk.X, pady=5)

        tk.Button(nav, text="◀", command=self.prev_month,
                  bg=COLORS['primary_light'], fg='white', relief=tk.FLAT, padx=10, cursor='hand2').pack(side=tk.LEFT)

        self.month_var = tk.StringVar(value=calendar.month_name[self.month])
        month_menu = ttk.Combobox(nav, textvariable=self.month_var,
                                  values=list(calendar.month_name)[1:], width=8, state='readonly')
        month_menu.pack(side=tk.LEFT, padx=5)
        month_menu.bind('<<ComboboxSelected>>', lambda e: self.change_month())

        self.year_var = tk.StringVar(value=str(self.year))
        year_menu = ttk.Combobox(nav, textvariable=self.year_var,
                                 values=[str(y) for y in range(1900, 2101)], width=6, state='readonly')
        year_menu.pack(side=tk.LEFT, padx=5)
        year_menu.bind('<<ComboboxSelected>>', lambda e: self.change_year())

        tk.Button(nav, text="▶", command=self.next_month,
                  bg=COLORS['primary_light'], fg='white', relief=tk.FLAT, padx=10, cursor='hand2').pack(side=tk.LEFT)

        tk.Button(nav, text="Today", command=self.go_today,
                  bg=COLORS['secondary'], fg='white', relief=tk.FLAT, padx=10, cursor='hand2').pack(side=tk.LEFT, padx=10)

        self.cal_frame = tk.Frame(container, bg=COLORS['background'])
        self.cal_frame.pack(pady=10)
        self.draw_days()

        action_frame = tk.Frame(container, bg=COLORS['background'])
        action_frame.pack(pady=10)
        tk.Button(action_frame, text="Clear", command=self.clear_date,
                  bg=COLORS['text_light'], fg='white', font=('Tahoma',10,'bold'),
                  relief=tk.FLAT, padx=20, pady=5, cursor='hand2').pack(side=tk.LEFT, padx=10)
        tk.Button(action_frame, text="Cancel", command=self.window.destroy,
                  bg=COLORS['accent'], fg='white', font=('Tahoma',10,'bold'),
                  relief=tk.FLAT, padx=20, pady=5, cursor='hand2').pack(side=tk.LEFT)

    def draw_days(self):
        for widget in self.cal_frame.winfo_children():
            widget.destroy()

        days = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
        for i, d in enumerate(days):
            tk.Label(self.cal_frame, text=d, font=('Tahoma',9,'bold'),
                     bg=COLORS['background'], fg=COLORS['text']).grid(row=0, column=i, padx=2, pady=2)

        cal = calendar.monthcalendar(self.year, self.month)
        for row_idx, week in enumerate(cal):
            for col_idx, day in enumerate(week):
                if day == 0:
                    continue
                btn = tk.Button(self.cal_frame, text=str(day), width=4,
                                bg=COLORS['card'], fg=COLORS['text'],
                                relief=tk.FLAT, cursor='hand2',
                                command=lambda d=day: self.select_date(d))
                btn.grid(row=row_idx+1, column=col_idx, padx=2, pady=2)
                # Highlight today
                if (day == datetime.now().day and self.month == datetime.now().month and
                    self.year == datetime.now().year):
                    btn.config(bg=COLORS['primary_light'], fg='white')
                # Highlight selected
                if self.selected_date:
                    try:
                        sel = datetime.strptime(self.selected_date, '%Y-%m-%d')
                        if sel.year == self.year and sel.month == self.month and sel.day == day:
                            btn.config(bg=COLORS['success'], fg='white')
                    except:
                        pass

    def change_month(self):
        month_name = self.month_var.get()
        if month_name:
            self.month = list(calendar.month_name).index(month_name)
            self.draw_days()

    def change_year(self):
        try:
            self.year = int(self.year_var.get())
            self.draw_days()
        except:
            pass

    def prev_month(self):
        if self.month == 1:
            self.month = 12
            self.year -= 1
        else:
            self.month -= 1
        self.update_controls()
        self.draw_days()

    def next_month(self):
        if self.month == 12:
            self.month = 1
            self.year += 1
        else:
            self.month += 1
        self.update_controls()
        self.draw_days()

    def go_today(self):
        today = datetime.now()
        self.year = today.year
        self.month = today.month
        self.update_controls()
        self.draw_days()

    def update_controls(self):
        self.month_var.set(calendar.month_name[self.month])
        self.year_var.set(str(self.year))

    def select_date(self, day):
        date_str = f"{self.year:04d}-{self.month:02d}-{day:02d}"
        self.selected_date = date_str
        self.date_label.config(text=f"Selected: {date_str}")
        self.draw_days()
        self.callback(date_str)
        self.window.destroy()

    def clear_date(self):
        self.selected_date = None
        self.date_label.config(text="Selected: None")
        self.callback(None)
        self.window.destroy()


# ---------- MODEL (Database) ----------
class Database:
    def __init__(self, db_name="healthlink.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.observers = []
        self.create_tables()
        self.insert_sample_data()

    def add_observer(self, callback):
        self.observers.append(callback)

    def notify_observers(self, data=None):
        for cb in self.observers:
            try:
                cb(data)
            except:
                pass

    def close(self):
        if self.conn:
            self.conn.close()

    def create_tables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT,
            role TEXT DEFAULT 'user'
        )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            gender TEXT NOT NULL,
            birth_date DATE,
            status TEXT NOT NULL,
            created_date DATE NOT NULL,
            contact TEXT,
            emergency_contact TEXT,
            blood_type TEXT,
            allergies TEXT,
            last_visit DATE
        )''')
        self.cursor.execute("PRAGMA table_info(patients)")
        columns = [col[1] for col in self.cursor.fetchall()]
        if 'birth_date' not in columns:
            self.cursor.execute("ALTER TABLE patients ADD COLUMN birth_date DATE")
        if 'emergency_contact' not in columns:
            self.cursor.execute("ALTER TABLE patients ADD COLUMN emergency_contact TEXT")
        if 'blood_type' not in columns:
            self.cursor.execute("ALTER TABLE patients ADD COLUMN blood_type TEXT")
        if 'allergies' not in columns:
            self.cursor.execute("ALTER TABLE patients ADD COLUMN allergies TEXT")
        if 'last_visit' not in columns:
            self.cursor.execute("ALTER TABLE patients ADD COLUMN last_visit DATE")

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            visit_date DATE NOT NULL,
            doctor TEXT,
            diagnosis TEXT,
            treatment TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        )''')
        self.conn.commit()

    def insert_sample_data(self):
        self.cursor.execute("SELECT COUNT(*) FROM patients")
        if self.cursor.fetchone()[0] >= 30:
            return

        self.cursor.execute("INSERT OR IGNORE INTO users (username,password,full_name,role) VALUES (?,?,?,?)",
                            ('admin','admin123','Administrator','admin'))
        self.cursor.execute("INSERT OR IGNORE INTO users (username,password,full_name,role) VALUES (?,?,?,?)",
                            ('doctor','doctor123','Dr. Mohamed Kamara','doctor'))
        self.cursor.execute("INSERT OR IGNORE INTO users (username,password,full_name,role) VALUES (?,?,?,?)",
                            ('nurse','nurse123','Nurse Fatmata Sesay','nurse'))

        first_names = ['Mohamed','Fatmata','Ibrahim','Aminata','Sulaiman','Mariama','Abdulai','Salamatu',
                       'Mustapha','Zainab','Alhaji','Hawa','Amadu','Kadiatu','Osman','Memuna','Sorie',
                       'Mabinty','Bakarr','Isatu','Santigie','Adama','Kanu','Foday','Mamu','Isatu','Mohamed',
                       'Mariama','Ibrahim','Fatmata']
        last_names = ['Koroma','Kamara','Jalloh','Sesay','Bangura','Conteh','Sankoh','Kargbo','Tarawally',
                      'Saffa','Bah','Fofanah','Kallay','Turay','Mansaray']*2
        statuses = ['Active','Inactive','Pending']
        genders = ['Male','Female','Other']
        blood_types = ['A+','A-','B+','B-','O+','O-','AB+','AB-']
        allergies_list = ['None','Penicillin','Sulfa','Latex','Peanuts']

        for i in range(30):
            first = first_names[i % len(first_names)]
            last = last_names[i % len(last_names)]
            full_name = f"{first} {last}"
            gender = random.choice(genders)
            birth_date = (datetime.now() - timedelta(days=random.randint(6570, 29200))).strftime('%Y-%m-%d')
            status = random.choice(statuses)
            contact = f"7{random.randint(1000000,9999999)}"
            emergency = f"7{random.randint(1000000,9999999)}"
            blood = random.choice(blood_types)
            allergy = random.choice(allergies_list)
            days_ago = random.randint(0,90)
            created = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            last_visit = (datetime.now() - timedelta(days=random.randint(0,30))).strftime('%Y-%m-%d')
            self.cursor.execute('''INSERT INTO patients
                (full_name,gender,birth_date,status,created_date,contact,emergency_contact,blood_type,allergies,last_visit)
                VALUES (?,?,?,?,?,?,?,?,?,?)''',
                (full_name,gender,birth_date,status,created,contact,emergency,blood,allergy,last_visit))
            pid = self.cursor.lastrowid
            for _ in range(random.randint(1,3)):
                visit_date = (datetime.now() - timedelta(days=random.randint(0,60))).strftime('%Y-%m-%d')
                doctor = random.choice(['Dr. Kamara', 'Dr. Sesay', 'Dr. Koroma', 'Dr. Bangura'])
                diagnosis = random.choice(['Malaria', 'Typhoid', 'Respiratory infection', 'Hypertension', 'Diabetes', 'Routine checkup'])
                treatment = random.choice(['Antibiotics', 'Painkillers', 'Lifestyle advice', 'Referral', 'Observation'])
                self.cursor.execute('''INSERT INTO visits (patient_id,visit_date,doctor,diagnosis,treatment)
                                       VALUES (?,?,?,?,?)''',
                                    (pid, visit_date, doctor, diagnosis, treatment))
        self.conn.commit()
        self.notify_observers({'action':'data_loaded'})

    # ---------- CRUD ----------
    def get_all_patients(self, limit=None, offset=0):
        if limit:
            self.cursor.execute("SELECT * FROM patients ORDER BY id LIMIT ? OFFSET ?", (limit, offset))
        else:
            self.cursor.execute("SELECT * FROM patients ORDER BY id")
        return self.cursor.fetchall()

    def get_patient(self, pid):
        self.cursor.execute("SELECT * FROM patients WHERE id=?", (pid,))
        return self.cursor.fetchone()

    def get_patient_count(self):
        self.cursor.execute("SELECT COUNT(*) FROM patients")
        return self.cursor.fetchone()[0]

    def add_patient(self, data):
        created = datetime.now().strftime('%Y-%m-%d')
        self.cursor.execute('''INSERT INTO patients
            (full_name,gender,birth_date,status,created_date,contact,emergency_contact,blood_type,allergies,last_visit)
            VALUES (?,?,?,?,?,?,?,?,?,?)''',
            (data['full_name'], data['gender'], data['birth_date'], data['status'], created,
             data.get('contact',''), data.get('emergency',''), data.get('blood',''),
             data.get('allergies',''), created))
        self.conn.commit()
        pid = self.cursor.lastrowid
        self.notify_observers({'action':'add', 'id':pid})
        return pid

    def update_patient(self, pid, data):
        self.cursor.execute('''UPDATE patients SET
            full_name=?, gender=?, birth_date=?, status=?, contact=?, emergency_contact=?,
            blood_type=?, allergies=?, last_visit=?
            WHERE id=?''',
            (data['full_name'], data['gender'], data['birth_date'], data['status'],
             data.get('contact',''), data.get('emergency',''),
             data.get('blood',''), data.get('allergies',''),
             datetime.now().strftime('%Y-%m-%d'), pid))
        self.conn.commit()
        self.notify_observers({'action':'update', 'id':pid})

    def delete_patient(self, pid):
        self.cursor.execute("DELETE FROM visits WHERE patient_id=?", (pid,))
        self.cursor.execute("DELETE FROM patients WHERE id=?", (pid,))
        self.conn.commit()
        self.notify_observers({'action':'delete', 'id':pid})

    # ---------- Search ----------
    def search_patients(self, term=None, search_by='all', blood=None, date_from=None, date_to=None):
        query = "SELECT * FROM patients WHERE 1=1"
        params = []
        if term and term.strip():
            term = f'%{term.strip()}%'
            if search_by == 'id':
                try:
                    query += " AND id=?"
                    params.append(int(term.strip('%')))
                except:
                    return []
            elif search_by == 'name':
                query += " AND full_name LIKE ?"
                params.append(term)
            elif search_by == 'status':
                query += " AND status LIKE ?"
                params.append(term)
            elif search_by == 'gender':
                query += " AND gender LIKE ?"
                params.append(term)
            elif search_by == 'blood':
                query += " AND blood_type LIKE ?"
                params.append(term)
            else:
                query += " AND (full_name LIKE ? OR status LIKE ? OR gender LIKE ? OR blood_type LIKE ? OR CAST(id AS TEXT) LIKE ?)"
                params.extend([term, term, term, term, term])
        if blood and blood != 'All':
            query += " AND blood_type=?"
            params.append(blood)
        if date_from:
            query += " AND created_date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND created_date <= ?"
            params.append(date_to)
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    # ---------- Visits ----------
    def get_visits(self, patient_id):
        self.cursor.execute("SELECT * FROM visits WHERE patient_id=? ORDER BY visit_date DESC", (patient_id,))
        return self.cursor.fetchall()

    def add_visit(self, patient_id, data):
        self.cursor.execute('''INSERT INTO visits (patient_id, visit_date, doctor, diagnosis, treatment)
                               VALUES (?,?,?,?,?)''',
                            (patient_id, data['visit_date'], data['doctor'], data['diagnosis'], data['treatment']))
        self.conn.commit()
        self.notify_observers({'action':'add_visit', 'patient_id':patient_id})

    # ---------- Stats ----------
    def get_stats(self):
        self.cursor.execute("SELECT COUNT(*) FROM patients")
        total = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT gender, COUNT(*) FROM patients GROUP BY gender")
        gender = self.cursor.fetchall()
        self.cursor.execute("SELECT status, COUNT(*) FROM patients GROUP BY status")
        status = self.cursor.fetchall()
        self.cursor.execute('''SELECT created_date, COUNT(*)
            FROM patients WHERE created_date >= date('now','-30 days')
            GROUP BY created_date ORDER BY created_date''')
        daily = self.cursor.fetchall()
        self.cursor.execute('''
            SELECT 
                CASE 
                    WHEN (strftime('%Y', 'now') - strftime('%Y', birth_date)) < 18 THEN '0-17'
                    WHEN (strftime('%Y', 'now') - strftime('%Y', birth_date)) BETWEEN 18 AND 30 THEN '18-30'
                    WHEN (strftime('%Y', 'now') - strftime('%Y', birth_date)) BETWEEN 31 AND 50 THEN '31-50'
                    WHEN (strftime('%Y', 'now') - strftime('%Y', birth_date)) BETWEEN 51 AND 65 THEN '51-65'
                    ELSE '65+'
                END as age_group,
                COUNT(*)
            FROM patients
            WHERE birth_date IS NOT NULL
            GROUP BY age_group
        ''')
        age_groups = self.cursor.fetchall()
        self.cursor.execute('''
            SELECT visit_date, COUNT(*) 
            FROM visits 
            WHERE visit_date >= date('now','-30 days')
            GROUP BY visit_date
            ORDER BY visit_date
        ''')
        visits_daily = self.cursor.fetchall()
        return {'total':total,'gender':gender,'status':status,'daily':daily,
                'age_groups':age_groups, 'visits_daily':visits_daily}

    def get_recent_patients(self, limit=5):
        self.cursor.execute('''SELECT full_name, created_date FROM patients
                               ORDER BY id DESC LIMIT ?''', (limit,))
        return self.cursor.fetchall()

    def get_reports_data(self, period, start_date=None, end_date=None):
        if period == 'custom' and start_date and end_date:
            start = start_date
            end = end_date
        else:
            today = datetime.now()
            if period == 'weekly':
                start = (today - timedelta(days=7)).strftime('%Y-%m-%d')
                end = today.strftime('%Y-%m-%d')
            elif period == 'monthly':
                start = (today - timedelta(days=30)).strftime('%Y-%m-%d')
                end = today.strftime('%Y-%m-%d')
            elif period == 'yearly':
                start = (today - timedelta(days=365)).strftime('%Y-%m-%d')
                end = today.strftime('%Y-%m-%d')
            else:
                start = (today - timedelta(days=7)).strftime('%Y-%m-%d')
                end = today.strftime('%Y-%m-%d')
        self.cursor.execute('''SELECT * FROM patients
            WHERE created_date BETWEEN ? AND ? ORDER BY created_date DESC''', (start,end))
        records = self.cursor.fetchall()
        gender_counts = {'Male':0,'Female':0,'Other':0}
        status_counts = {'Active':0,'Inactive':0,'Pending':0}
        for r in records:
            if r['gender'] in gender_counts: gender_counts[r['gender']] += 1
            if r['status'] in status_counts: status_counts[r['status']] += 1
        return {
            'records': records,
            'total': len(records),
            'gender_counts': gender_counts,
            'status_counts': status_counts,
            'start_date': start,
            'end_date': end
        }

    def authenticate(self, username, password):
        self.cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username,password))
        return self.cursor.fetchone()


# ============================================================
# CONTROLLER
# ============================================================
class Controller:
    def __init__(self):
        self.db = Database()
        self.current_user = None
        self._observers = []
        self.db.add_observer(self._notify_observers)

    def _notify_observers(self, data):
        for cb in self._observers:
            try:
                cb(data)
            except:
                pass

    def add_observer(self, cb):
        self._observers.append(cb)

    def login(self, username, password):
        user = self.db.authenticate(username, password)
        if user:
            self.current_user = user
            return True
        return False

    def logout(self):
        self.current_user = None

    def get_user(self):
        return self.current_user

    def get_user_role(self):
        if self.current_user:
            return self.current_user['role']
        return None

    def get_all_patients(self, limit=None, offset=0):
        return self.db.get_all_patients(limit, offset)

    def get_patient_count(self):
        return self.db.get_patient_count()

    def get_patient(self, pid):
        return self.db.get_patient(pid)

    def add_patient(self, data):
        return self.db.add_patient(data)

    def update_patient(self, pid, data):
        self.db.update_patient(pid, data)

    def delete_patient(self, pid):
        self.db.delete_patient(pid)

    def search_patients(self, term=None, search_by='all', blood=None, date_from=None, date_to=None):
        return self.db.search_patients(term, search_by, blood, date_from, date_to)

    def get_visits(self, patient_id):
        return self.db.get_visits(patient_id)

    def add_visit(self, patient_id, data):
        self.db.add_visit(patient_id, data)

    def get_stats(self):
        return self.db.get_stats()

    def get_recent_patients(self, limit=5):
        return self.db.get_recent_patients(limit)

    def get_reports_data(self, period, start_date=None, end_date=None):
        return self.db.get_reports_data(period, start_date, end_date)

    def export_csv(self, patients, filename):
        if not patients:
            return False
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID','Full Name','Gender','Birth Date','Status','Created','Contact','Blood Type','Allergies'])
            for p in patients:
                writer.writerow([p['id'], p['full_name'], p['gender'], p['birth_date'],
                                 p['status'], p['created_date'], p['contact'], p['blood_type'], p['allergies']])
        return True

    def generate_pdf_report(self, period, start_date=None, end_date=None):
        if not REPORTLAB:
            return None
        data = self.get_reports_data(period, start_date, end_date)
        if not data['records']:
            return None
        os.makedirs("reports", exist_ok=True)
        pname = "Custom Range" if period == 'custom' else period.capitalize()
        fname = f"reports/healthlink_{period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        doc = SimpleDocTemplate(fname, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24,
                                     textColor=colors.darkblue, alignment=1, spaceAfter=20)
        story.append(Paragraph("HealthLink Sierra Leone", title_style))
        sub = ParagraphStyle('Sub', parent=styles['Heading2'], fontSize=16,
                             textColor=colors.darkblue, alignment=1, spaceAfter=10)
        story.append(Paragraph(f"{pname} Patient Report", sub))
        date_style = ParagraphStyle('Date', parent=styles['Normal'], fontSize=10,
                                    alignment=1, textColor=colors.grey)
        story.append(Paragraph(f"Period: {data['start_date']} to {data['end_date']}", date_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", date_style))
        story.append(Spacer(1, 0.3*inch))

        story.append(Paragraph("Summary Statistics", styles['Heading3']))
        story.append(Spacer(1, 0.1*inch))
        sum_data = [
            ['Metric','Value'],
            ['Total Patients', str(data['total'])],
            ['Male', str(data['gender_counts']['Male'])],
            ['Female', str(data['gender_counts']['Female'])],
            ['Other', str(data['gender_counts']['Other'])],
            ['Active', str(data['status_counts']['Active'])],
            ['Inactive', str(data['status_counts']['Inactive'])],
            ['Pending', str(data['status_counts']['Pending'])]
        ]
        sum_table = Table(sum_data, colWidths=[2.5*inch, 1.5*inch])
        sum_table.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.darkblue),
            ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
            ('ALIGN',(0,0),(-1,-1),'CENTER'),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
            ('FONTSIZE',(0,0),(-1,0),11),
            ('BOTTOMPADDING',(0,0),(-1,0),10),
            ('BACKGROUND',(0,1),(-1,-1),colors.beige),
            ('GRID',(0,0),(-1,-1),1,colors.black),
        ]))
        story.append(sum_table)
        story.append(Spacer(1, 0.3*inch))

        if MATPLOTLIB:
            try:
                fig, ax = plt.subplots(figsize=(4,2.5))
                genders = ['Male','Female','Other']
                counts = [data['gender_counts'].get(g,0) for g in genders]
                ax.bar(genders, counts, color=['#2e86c1','#e74c3c','#95a5a6'])
                ax.set_title('Gender Distribution')
                ax.set_ylabel('Count')
                chart_file = f"reports/chart_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                plt.savefig(chart_file, dpi=100, bbox_inches='tight')
                plt.close()
                story.append(Paragraph("Gender Distribution Chart", styles['Heading3']))
                story.append(Spacer(1, 0.1*inch))
                story.append(Image(chart_file, width=4*inch, height=2.5*inch))
                story.append(Spacer(1, 0.3*inch))
            except:
                pass

        story.append(Paragraph("Patient Records", styles['Heading3']))
        story.append(Spacer(1, 0.1*inch))
        table_data = [['ID','Full Name','Gender','Status','Date','Contact']]
        for r in data['records']:
            table_data.append([
                str(r['id']), r['full_name'], r['gender'], r['status'],
                r['created_date'], r['contact'] or 'N/A'
            ])
        pat_table = Table(table_data, colWidths=[0.6*inch,2*inch,0.8*inch,0.8*inch,1*inch,1.2*inch])
        pat_table.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.darkblue),
            ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
            ('ALIGN',(0,0),(-1,-1),'CENTER'),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
            ('FONTSIZE',(0,0),(-1,0),9),
            ('BOTTOMPADDING',(0,0),(-1,0),8),
            ('BACKGROUND',(0,1),(-1,-1),colors.white),
            ('GRID',(0,0),(-1,-1),0.5,colors.grey),
            ('FONTSIZE',(0,1),(-1,-1),8),
        ]))
        story.append(pat_table)
        story.append(Spacer(1, 0.3*inch))

        footer = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9,
                                textColor=colors.grey, alignment=1)
        story.append(Paragraph("HealthLink Sierra Leone – Open Source | MIT License", footer))

        doc.build(story)
        return fname


# ============================================================
# VIEWS
# ============================================================

# ---------- Login ----------
class LoginView:
    def __init__(self, root, controller, on_success):
        self.root = root
        self.controller = controller
        self.on_success = on_success
        self.root.title("HealthLink Sierra Leone - Login")
        self.root.geometry("480x400")
        self.root.resizable(False, False)
        self.root.configure(bg=COLORS['background'])
        self.center()
        self.build()

    def center(self):
        w,h = 480,400
        x = (self.root.winfo_screenwidth()//2) - (w//2)
        y = (self.root.winfo_screenheight()//2) - (h//2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def build(self):
        main = tk.Frame(self.root, bg='white', relief=tk.RAISED, bd=2)
        main.place(relx=0.5, rely=0.5, anchor='center', width=400, height=350)
        header = tk.Frame(main, bg=COLORS['primary'], height=90)
        header.pack(fill=tk.X)
        tk.Label(header, text="HealthLink Sierra Leone", font=('Tahoma',20,'bold'),
                 bg=COLORS['primary'], fg='white').pack(pady=(15,0))
        tk.Label(header, text="Hospital Management System", font=('Tahoma',10),
                 bg=COLORS['primary'], fg='#aed6f1').pack()

        form = tk.Frame(main, bg='white', padx=30, pady=20)
        form.pack(fill=tk.BOTH, expand=True)
        tk.Label(form, text="Username", font=('Tahoma',10), bg='white').pack(anchor=tk.W, pady=(0,3))
        self.username = tk.Entry(form, font=('Tahoma',11), bg='#f8f9fa', relief=tk.FLAT,
                                 highlightthickness=1, highlightcolor=COLORS['primary_light'])
        self.username.pack(fill=tk.X, pady=(0,15), ipady=5)
        self.username.insert(0, 'admin')

        tk.Label(form, text="Password", font=('Tahoma',10), bg='white').pack(anchor=tk.W, pady=(0,3))
        self.password = tk.Entry(form, font=('Tahoma',11), bg='#f8f9fa', relief=tk.FLAT,
                                 highlightthickness=1, highlightcolor=COLORS['primary_light'], show='*')
        self.password.pack(fill=tk.X, pady=(0,20), ipady=5)
        self.password.insert(0, 'admin123')

        tk.Button(form, text="Login", command=self.do_login,
                  bg=COLORS['primary_light'], fg='white', font=('Tahoma',11,'bold'),
                  relief=tk.FLAT, padx=40, pady=8, cursor='hand2').pack(pady=5)
        self.status = tk.Label(form, text="", font=('Tahoma',9), bg='white', fg=COLORS['accent'])
        self.status.pack(pady=5)
        tk.Label(form, text="Default: admin / admin123", font=('Tahoma',8),
                 bg='white', fg=COLORS['text_light']).pack()
        self.root.bind('<Return>', lambda e: self.do_login())

    def do_login(self):
        u = self.username.get().strip()
        p = self.password.get().strip()
        if not u or not p:
            self.status.config(text="Please enter both")
            return
        if self.controller.login(u, p):
            self.status.config(text="Login successful!", fg=COLORS['success'])
            self.root.after(500, self.on_success)
        else:
            self.status.config(text="Invalid credentials")
            self.password.delete(0, tk.END)


# ---------- Main Dashboard ----------
class DashboardApp:
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        self.root.title("HealthLink Sierra Leone")
        self.root.geometry("1400x850")
        self.root.configure(bg=COLORS['background'])

        self.theme_var = tk.StringVar(value='light')
        self.current_page_name = 'home'
        self.pagination_offset = 0
        self.pagination_limit = 20
        self.total_patients = 0
        self.current_patients = []

        self.home_stat_labels = {}  # Store references to home stat labels
        self.home_recent_frame = None

        self.build_sidebar()
        self.build_main_area()

        self.controller.add_observer(self.on_db_change)

        self.show_home()
        self.center()

    def center(self):
        w,h = 1400,850
        x = (self.root.winfo_screenwidth()//2) - (w//2)
        y = (self.root.winfo_screenheight()//2) - (h//2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    # ---------- Sidebar ----------
    def build_sidebar(self):
        self.sidebar = tk.Frame(self.root, bg=COLORS['sidebar_bg'], width=240)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, expand=False)
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="HealthLink", font=('Tahoma',18,'bold'),
                 bg=COLORS['sidebar_bg'], fg='white').pack(pady=(20,5))
        tk.Label(self.sidebar, text="Sierra Leone", font=('Tahoma',11),
                 bg=COLORS['sidebar_bg'], fg='#aed6f1').pack(pady=(0,20))

        role = self.controller.get_user_role()
        items = []
        if role in ['admin', 'doctor', 'nurse']:
            items.append(('🏠 Home', self.show_home))
        if role in ['admin', 'doctor']:
            items.append(('👤 Patients', self.show_patients))
        if role in ['admin', 'doctor', 'nurse']:
            items.append(('📊 Charts', self.show_dashboard))
            items.append(('📄 Reports', self.show_reports))
        if role == 'admin':
            items.append(('⚙️ Settings', self.show_settings))
        items.append(('🚪 Logout', self.logout))

        for text, cmd in items:
            btn = tk.Button(self.sidebar, text=text, command=cmd,
                            bg=COLORS['sidebar_bg'], fg='white', font=('Tahoma',11),
                            relief=tk.FLAT, anchor='w', padx=20, pady=10,
                            activebackground=COLORS['sidebar_hover'], activeforeground='white',
                            bd=0, cursor='hand2')
            btn.pack(fill=tk.X, pady=2)

        user = self.controller.get_user()
        tk.Label(self.sidebar, text=f"User: {user['full_name'] if user else 'Unknown'}",
                 font=('Tahoma',10), bg=COLORS['sidebar_bg'], fg='#aed6f1').pack(side=tk.BOTTOM, pady=10)

    # ---------- Main Content Area ----------
    def build_main_area(self):
        self.main_frame = tk.Frame(self.root, bg=COLORS['background'])
        self.main_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.content_container = tk.Frame(self.main_frame, bg=COLORS['background'])
        self.content_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.pages = {}
        self.current_page = None

    def show_page(self, name, frame):
        if self.current_page:
            self.current_page.pack_forget()
        frame.pack(fill=tk.BOTH, expand=True)
        self.current_page = frame
        self.pages[name] = frame
        self.current_page_name = name

    # ---------- Home Page ----------
    def show_home(self):
        try:
            if 'home' not in self.pages:
                page = tk.Frame(self.content_container, bg=COLORS['background'])
                header_frame = tk.Frame(page, bg=COLORS['primary'], height=130)
                header_frame.pack(fill=tk.X, pady=(0,15))
                header_stripe = tk.Frame(header_frame, bg=COLORS['primary_light'], height=5)
                header_stripe.pack(side=tk.BOTTOM, fill=tk.X)

                user = self.controller.get_user()
                user_name = user['full_name'] if user else 'User'
                tk.Label(header_frame, text=f"Welcome back, {user_name} 👋",
                         font=('Tahoma',22,'bold'), bg=COLORS['primary'], fg='white').pack(pady=(25,0))
                tk.Label(header_frame, text="Here's your hospital management dashboard",
                         font=('Tahoma',13), bg=COLORS['primary'], fg='#aed6f1').pack()

                stats = self.controller.get_stats()
                card_frame = tk.Frame(page, bg=COLORS['background'])
                card_frame.pack(fill=tk.X, pady=10, padx=10)

                cards_data = [
                    ('total', f"👥 {stats['total']}", "Total Patients", COLORS['primary_light']),
                    ('active', f"✅ {self._get_status_count('Active', stats)}", "Active", COLORS['success']),
                    ('pending', f"⏳ {self._get_status_count('Pending', stats)}", "Pending", COLORS['warning']),
                    ('days', f"📅 {len(stats['daily'])}", "Days Active (30d)", COLORS['secondary'])
                ]
                for i, (key, value, label, color) in enumerate(cards_data):
                    card = tk.Frame(card_frame, bg=COLORS['card'], relief='ridge', bd=3, width=220, height=130)
                    card.grid(row=0, column=i, padx=15, pady=10, sticky='nsew')
                    card.grid_propagate(False)
                    lbl = tk.Label(card, text=value, font=('Tahoma',22,'bold'),
                                   bg=COLORS['card'], fg=color)
                    lbl.pack(pady=(20,0))
                    tk.Label(card, text=label, font=('Tahoma',12),
                             bg=COLORS['card'], fg=COLORS['text_light']).pack(pady=(5,0))
                    self.home_stat_labels[key] = lbl
                for i in range(4):
                    card_frame.grid_columnconfigure(i, weight=1)

                tk.Label(page, text="Quick Actions", font=('Tahoma',18,'bold'),
                         bg=COLORS['background'], fg=COLORS['primary']).pack(pady=(20,10))
                action_frame = tk.Frame(page, bg=COLORS['background'])
                action_frame.pack(pady=10)
                for text, cmd, color in [
                    ('➕ Add Patient', self.show_patients, COLORS['success']),
                    ('📊 Charts', self.show_dashboard, COLORS['primary_light']),
                    ('📄 Report', self.show_reports, COLORS['secondary'])
                ]:
                    tk.Button(action_frame, text=text, command=cmd,
                              bg=color, fg='white', font=('Tahoma',11,'bold'),
                              relief=tk.FLAT, padx=25, pady=10, cursor='hand2',
                              borderwidth=0, highlightthickness=0).pack(side=tk.LEFT, padx=15)

                # Recent patients
                recent = self.controller.get_recent_patients(5)
                recent_frame = tk.Frame(page, bg=COLORS['background'])
                recent_frame.pack(fill=tk.X, padx=20, pady=(10,0))
                self.home_recent_frame = recent_frame
                self._update_recent_patients(recent)

                tk.Label(page, text="HealthLink v5.0 | Sierra Leone | Open Source",
                         font=('Tahoma',9), bg=COLORS['background'], fg=COLORS['text_light']).pack(side=tk.BOTTOM, pady=10)

                self.pages['home'] = page
            else:
                # If home page exists, just refresh its stats
                self.update_home_stats()
                self.update_home_recent()
            self.show_page('home', self.pages['home'])
        except Exception as e:
            fallback = tk.Frame(self.content_container, bg=COLORS['background'])
            tk.Label(fallback, text="Home Page - Error loading content", font=('Tahoma',16),
                     bg=COLORS['background'], fg=COLORS['accent']).pack(expand=True)
            tk.Label(fallback, text=str(e), font=('Tahoma',12), bg=COLORS['background']).pack()
            self.pages['home'] = fallback
            self.show_page('home', fallback)

    def _get_status_count(self, status, stats):
        for s,c in stats['status']:
            if s == status:
                return c
        return 0

    def update_home_stats(self):
        """Update the home page stat cards with fresh data."""
        if not self.home_stat_labels:
            return
        stats = self.controller.get_stats()
        mapping = {
            'total': f"👥 {stats['total']}",
            'active': f"✅ {self._get_status_count('Active', stats)}",
            'pending': f"⏳ {self._get_status_count('Pending', stats)}",
            'days': f"📅 {len(stats['daily'])}"
        }
        for key, label in self.home_stat_labels.items():
            if key in mapping:
                label.config(text=mapping[key])

    def update_home_recent(self):
        """Update the recent patients list on the home page."""
        if not self.home_recent_frame:
            return
        recent = self.controller.get_recent_patients(5)
        self._update_recent_patients(recent)

    def _update_recent_patients(self, recent):
        # Clear existing widgets
        for widget in self.home_recent_frame.winfo_children():
            widget.destroy()
        if recent:
            tk.Label(self.home_recent_frame, text="📋 Recently Registered", font=('Tahoma',14,'bold'),
                     bg=COLORS['background'], fg=COLORS['primary']).pack(anchor=tk.W, pady=(0,5))
            for name, date in recent:
                tk.Label(self.home_recent_frame, text=f"• {name}  ({date})",
                         font=('Tahoma',10), bg=COLORS['background'],
                         fg=COLORS['text_light']).pack(anchor=tk.W, pady=2)
        else:
            tk.Label(self.home_recent_frame, text="No recent patients.", font=('Tahoma',10),
                     bg=COLORS['background'], fg=COLORS['text_light']).pack(anchor=tk.W)

    # ---------- Patients Page ----------
    def show_patients(self):
        if 'patients' not in self.pages:
            page = tk.Frame(self.content_container, bg=COLORS['background'])
            self.build_patients_page(page)
            self.pages['patients'] = page
        self.show_page('patients', self.pages['patients'])
        self.pagination_offset = 0
        self.refresh_patients()

    def build_patients_page(self, parent):
        # Top: CRUD form
        top_frame = tk.Frame(parent, bg=COLORS['background'])
        top_frame.pack(fill=tk.X, pady=(0,5))

        form_frame = tk.Frame(top_frame, bg=COLORS['card'], relief=tk.RAISED, bd=1)
        form_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,10), ipadx=10, ipady=10)

        row1 = tk.Frame(form_frame, bg=COLORS['card'])
        row1.pack(fill=tk.X, pady=2)
        row2 = tk.Frame(form_frame, bg=COLORS['card'])
        row2.pack(fill=tk.X, pady=2)

        def make_label(text):
            return tk.Label(row1, text=text, font=('Tahoma',9,'bold'), bg=COLORS['card'], fg=COLORS['text'])
        def make_entry():
            return tk.Entry(row1, font=('Tahoma',10), width=15, relief=tk.FLAT,
                            bg=COLORS['background'], fg=COLORS['text'])

        make_label("Name").pack(side=tk.LEFT, padx=(0,5))
        self.entry_name = make_entry()
        self.entry_name.pack(side=tk.LEFT, padx=(0,10))

        make_label("Gender").pack(side=tk.LEFT, padx=(0,5))
        self.gender_var = tk.StringVar(value='Male')
        for g in ['Male','Female','Other']:
            tk.Radiobutton(row1, text=g, variable=self.gender_var, value=g,
                           bg=COLORS['card'], fg=COLORS['text'], selectcolor='#d4e6f1',
                           font=('Tahoma',9)).pack(side=tk.LEFT, padx=(0,5))

        make_label("Status").pack(side=tk.LEFT, padx=(0,5))
        self.status_var = tk.StringVar(value='Active')
        for s in ['Active','Inactive','Pending']:
            tk.Radiobutton(row1, text=s, variable=self.status_var, value=s,
                           bg=COLORS['card'], fg=COLORS['text'], selectcolor='#d4e6f1',
                           font=('Tahoma',9)).pack(side=tk.LEFT, padx=(0,5))

        make_label("Blood").pack(side=tk.LEFT, padx=(0,5))
        self.blood_var = tk.StringVar(value='O+')
        blood_combo = ttk.Combobox(row1, textvariable=self.blood_var,
                                   values=['A+','A-','B+','B-','O+','O-','AB+','AB-'],
                                   font=('Tahoma',9), width=5, state='readonly')
        blood_combo.pack(side=tk.LEFT, padx=(0,5))

        make_label("Birth").pack(side=tk.LEFT, padx=(0,5))
        self.birth_date_var = tk.StringVar()
        self.birth_btn = tk.Button(row1, text="Select Birth Date", command=self.pick_birth_date,
                                   bg=COLORS['primary_light'], fg='white', font=('Tahoma',9,'bold'),
                                   relief=tk.FLAT, padx=5, pady=2, cursor='hand2')
        self.birth_btn.pack(side=tk.LEFT, padx=(0,5))
        self.birth_label = tk.Label(row1, text="None", font=('Tahoma',9), bg=COLORS['card'], fg=COLORS['text_light'])
        self.birth_label.pack(side=tk.LEFT, padx=(0,5))

        make_label("Contact").pack(side=tk.LEFT, padx=(0,5))
        self.entry_contact = make_entry()
        self.entry_contact.pack(side=tk.LEFT, padx=(0,5))

        for text, cmd, color in [
            ('Add', self.do_add, COLORS['success']),
            ('Update', self.do_update, COLORS['primary_light']),
            ('Delete', self.do_delete, COLORS['accent']),
            ('Clear', self.clear_form, COLORS['text_light']),
            ('Export CSV', self.export_csv, COLORS['secondary'])
        ]:
            tk.Button(row2, text=text, command=cmd,
                      bg=color, fg='white', font=('Tahoma',9,'bold'),
                      relief=tk.FLAT, padx=10, pady=3, cursor='hand2').pack(side=tk.LEFT, padx=(0,5))

        # ---- Search bar (moved up, below CRUD) ----
        search_frame = tk.Frame(parent, bg=COLORS['background'])
        search_frame.pack(fill=tk.X, pady=5)

        row_s = tk.Frame(search_frame, bg=COLORS['card'], relief=tk.RAISED, bd=1)
        row_s.pack(fill=tk.X, padx=5, pady=5, ipadx=5, ipady=5)

        tk.Label(row_s, text="Search:", font=('Tahoma',9,'bold'), bg=COLORS['card'], fg=COLORS['text']).pack(side=tk.LEFT, padx=(5,5))
        self.entry_search = tk.Entry(row_s, font=('Tahoma',10), width=18, relief=tk.FLAT,
                                     bg=COLORS['background'], fg=COLORS['text'])
        self.entry_search.pack(side=tk.LEFT, padx=(0,8))

        tk.Label(row_s, text="by:", font=('Tahoma',9), bg=COLORS['card'], fg=COLORS['text']).pack(side=tk.LEFT, padx=(5,5))
        self.search_by_var = tk.StringVar(value='all')
        search_by_menu = ttk.Combobox(row_s, textvariable=self.search_by_var,
                                       values=['all','name','id','status','gender','blood'],
                                       font=('Tahoma',9), width=8, state='readonly')
        search_by_menu.pack(side=tk.LEFT, padx=(0,8))

        tk.Label(row_s, text="Blood:", font=('Tahoma',9), bg=COLORS['card'], fg=COLORS['text']).pack(side=tk.LEFT, padx=(10,5))
        self.search_blood = tk.StringVar(value='All')
        blood_menu = ttk.Combobox(row_s, textvariable=self.search_blood,
                                   values=['All','A+','A-','B+','B-','O+','O-','AB+','AB-'],
                                   font=('Tahoma',9), width=6, state='readonly')
        blood_menu.pack(side=tk.LEFT, padx=(0,8))

        tk.Label(row_s, text="Date from:", font=('Tahoma',9), bg=COLORS['card'], fg=COLORS['text']).pack(side=tk.LEFT, padx=(10,5))
        self.entry_date_from = tk.Entry(row_s, font=('Tahoma',10), width=10, relief=tk.FLAT,
                                        bg=COLORS['background'], fg=COLORS['text'])
        self.entry_date_from.pack(side=tk.LEFT, padx=(0,5))
        tk.Label(row_s, text="to:", font=('Tahoma',9), bg=COLORS['card'], fg=COLORS['text']).pack(side=tk.LEFT, padx=(5,5))
        self.entry_date_to = tk.Entry(row_s, font=('Tahoma',10), width=10, relief=tk.FLAT,
                                      bg=COLORS['background'], fg=COLORS['text'])
        self.entry_date_to.pack(side=tk.LEFT, padx=(0,8))

        tk.Button(row_s, text="🔍 Search", command=self.do_search,
                  bg=COLORS['primary_light'], fg='white', font=('Tahoma',9,'bold'),
                  relief=tk.FLAT, padx=12, pady=4, cursor='hand2').pack(side=tk.LEFT, padx=(0,5))
        tk.Button(row_s, text="✖ Clear", command=self.clear_search,
                  bg=COLORS['text_light'], fg='white', font=('Tahoma',9,'bold'),
                  relief=tk.FLAT, padx=12, pady=4, cursor='hand2').pack(side=tk.LEFT)

        # ---- Table (takes remaining space) ----
        table_container = tk.Frame(parent, bg=COLORS['background'])
        table_container.pack(fill=tk.BOTH, expand=True, pady=5)

        table_frame = tk.Frame(table_container, bg=COLORS['card'], relief=tk.RAISED, bd=1)
        table_frame.pack(fill=tk.BOTH, expand=True, ipadx=5, ipady=5)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview",
                        background=COLORS['tree_bg'],
                        foreground=COLORS['tree_fg'],
                        rowheight=28,
                        font=('Tahoma',9))
        style.configure("Treeview.Heading",
                        background=COLORS['primary'],
                        foreground='white',
                        font=('Tahoma',10,'bold'))
        style.map('Treeview',
                  background=[('selected', COLORS['tree_selected'])],
                  foreground=[('selected', 'white')])

        cols = ('ID','Full Name','Gender','Birth','Status','Blood','Contact','Created')
        self.tree = ttk.Treeview(table_frame, columns=cols, show='headings', height=18, style="Treeview")
        widths = {'ID':50,'Full Name':180,'Gender':80,'Birth':90,'Status':90,'Blood':70,'Contact':100,'Created':110}
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=widths.get(c,100), anchor='w')

        vsb = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        self.tree.bind('<Double-Button-1>', self.on_double_click)

        self.selected_id = None

        # Pagination (kept below table)
        pag_frame = tk.Frame(table_container, bg=COLORS['background'])
        pag_frame.pack(fill=tk.X, pady=5)
        self.pag_label = tk.Label(pag_frame, text="", font=('Tahoma',9), bg=COLORS['background'], fg=COLORS['text_light'])
        self.pag_label.pack(side=tk.LEFT, padx=5)
        tk.Button(pag_frame, text="◀ Prev", command=self.prev_page,
                  bg=COLORS['primary_light'], fg='white', font=('Tahoma',9,'bold'),
                  relief=tk.FLAT, padx=10, pady=2, cursor='hand2').pack(side=tk.LEFT, padx=2)
        tk.Button(pag_frame, text="Next ▶", command=self.next_page,
                  bg=COLORS['primary_light'], fg='white', font=('Tahoma',9,'bold'),
                  relief=tk.FLAT, padx=10, pady=2, cursor='hand2').pack(side=tk.LEFT, padx=2)

    def pick_birth_date(self):
        CalendarPicker(self.root, self.set_birth_date, initial_date=self.birth_date_var.get())

    def set_birth_date(self, date_str):
        self.birth_date_var.set(date_str if date_str else '')
        self.birth_label.config(text=date_str if date_str else 'None')

    def refresh_patients(self, patients=None, reset_offset=True):
        if reset_offset:
            self.pagination_offset = 0
        if patients is None:
            total = self.controller.get_patient_count()
            self.total_patients = total
            patients = self.controller.get_all_patients(self.pagination_limit, self.pagination_offset)
        else:
            self.total_patients = len(patients)
        self.current_patients = patients
        for item in self.tree.get_children():
            self.tree.delete(item)
        for p in patients:
            age = self.calculate_age(p['birth_date']) if p['birth_date'] else 'N/A'
            self.tree.insert('', 'end', values=(
                p['id'], p['full_name'], p['gender'], age,
                p['status'], p['blood_type'] or 'Unknown', p['contact'] or 'N/A',
                p['created_date']
            ))
        start = self.pagination_offset + 1
        end = min(self.pagination_offset + self.pagination_limit, self.total_patients)
        if self.total_patients > 0:
            self.pag_label.config(text=f"Showing {start}-{end} of {self.total_patients}")
        else:
            self.pag_label.config(text="No patients")

    def calculate_age(self, birth_date):
        if not birth_date:
            return 'N/A'
        try:
            birth = datetime.strptime(birth_date, '%Y-%m-%d')
            today = datetime.now()
            age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
            return str(age)
        except:
            return 'N/A'

    def next_page(self):
        if self.pagination_offset + self.pagination_limit < self.total_patients:
            self.pagination_offset += self.pagination_limit
            self.refresh_patients(reset_offset=False)

    def prev_page(self):
        if self.pagination_offset >= self.pagination_limit:
            self.pagination_offset -= self.pagination_limit
            self.refresh_patients(reset_offset=False)

    # ---- CRUD ----
    def get_form_data(self):
        return {
            'full_name': self.entry_name.get().strip(),
            'gender': self.gender_var.get(),
            'birth_date': self.birth_date_var.get() or None,
            'status': self.status_var.get(),
            'blood': self.blood_var.get(),
            'contact': self.entry_contact.get().strip(),
        }

    def clear_form(self):
        self.entry_name.delete(0, tk.END)
        self.entry_contact.delete(0, tk.END)
        self.birth_date_var.set('')
        self.birth_label.config(text='None')
        self.gender_var.set('Male')
        self.status_var.set('Active')
        self.blood_var.set('O+')
        self.selected_id = None

    def validate_contact(self, contact):
        if not contact:
            return True
        pattern = r'^[738]\d{7}$'
        return re.match(pattern, contact) is not None

    def do_add(self):
        data = self.get_form_data()
        if not data['full_name']:
            messagebox.showwarning("Input Error", "Full Name is required.")
            return
        if data['contact'] and not self.validate_contact(data['contact']):
            messagebox.showwarning("Input Error", "Contact must be a valid Sierra Leone number (e.g., 7XXXXXXX).")
            return
        try:
            self.controller.add_patient(data)
            messagebox.showinfo("Success", f"Patient '{data['full_name']}' added.")
            self.clear_form()
            self.refresh_patients()
            # Update home stats if home page is currently shown
            if self.current_page_name == 'home':
                self.update_home_stats()
                self.update_home_recent()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def do_update(self):
        if self.selected_id is None:
            messagebox.showwarning("Select", "Please select a patient from the list.")
            return
        data = self.get_form_data()
        if not data['full_name']:
            messagebox.showwarning("Input Error", "Full Name is required.")
            return
        if data['contact'] and not self.validate_contact(data['contact']):
            messagebox.showwarning("Input Error", "Contact must be a valid Sierra Leone number.")
            return
        try:
            self.controller.update_patient(self.selected_id, data)
            messagebox.showinfo("Success", "Patient updated.")
            self.clear_form()
            self.refresh_patients()
            if self.current_page_name == 'home':
                self.update_home_stats()
                self.update_home_recent()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def do_delete(self):
        if self.selected_id is None:
            messagebox.showwarning("Select", "Please select a patient to delete.")
            return
        if messagebox.askyesno("Confirm Delete", "Delete this patient permanently?"):
            try:
                self.controller.delete_patient(self.selected_id)
                self.clear_form()
                self.refresh_patients()
                if self.current_page_name == 'home':
                    self.update_home_stats()
                    self.update_home_recent()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def on_select(self, event):
        sel = self.tree.selection()
        if sel:
            item = self.tree.item(sel[0])
            vals = item['values']
            self.selected_id = vals[0]
            p = self.controller.get_patient(self.selected_id)
            if p:
                self.entry_name.delete(0, tk.END)
                self.entry_name.insert(0, p['full_name'])
                self.gender_var.set(p['gender'])
                self.birth_date_var.set(p['birth_date'] or '')
                self.birth_label.config(text=p['birth_date'] or 'None')
                self.status_var.set(p['status'])
                self.blood_var.set(p['blood_type'] or 'O+')
                self.entry_contact.delete(0, tk.END)
                self.entry_contact.insert(0, p['contact'] or '')

    def on_double_click(self, event):
        if self.selected_id:
            self.show_patient_details()

    def show_patient_details(self):
        if self.selected_id is None:
            return
        p = self.controller.get_patient(self.selected_id)
        if not p:
            return
        detail_window = tk.Toplevel(self.root)
        detail_window.title("Patient Details")
        detail_window.geometry("600x500")
        detail_window.configure(bg='white')
        detail_window.update_idletasks()
        x = (detail_window.winfo_screenwidth() // 2) - 300
        y = (detail_window.winfo_screenheight() // 2) - 250
        detail_window.geometry(f"600x500+{x}+{y}")

        header = tk.Frame(detail_window, bg=COLORS['primary'], height=50)
        header.pack(fill=tk.X)
        tk.Label(header, text="Patient Details", font=('Tahoma',14,'bold'),
                 bg=COLORS['primary'], fg='white').pack(pady=10)

        info_frame = tk.Frame(detail_window, bg='white', padx=20, pady=10)
        info_frame.pack(fill=tk.X)
        info = [
            ("Name", p['full_name']),
            ("Gender", p['gender']),
            ("Birth Date", p['birth_date'] or 'N/A'),
            ("Age", self.calculate_age(p['birth_date'])),
            ("Status", p['status']),
            ("Blood Type", p['blood_type'] or 'Unknown'),
            ("Contact", p['contact'] or 'N/A'),
            ("Emergency", p['emergency_contact'] or 'N/A'),
            ("Allergies", p['allergies'] or 'None'),
            ("Created", p['created_date']),
            ("Last Visit", p['last_visit'] or 'Never'),
        ]
        for label, value in info:
            frame = tk.Frame(info_frame, bg='white')
            frame.pack(fill=tk.X, pady=2)
            tk.Label(frame, text=f"{label}:", font=('Tahoma',10,'bold'),
                     bg='white', width=14, anchor='w').pack(side=tk.LEFT)
            tk.Label(frame, text=value, font=('Tahoma',10), bg='white', anchor='w').pack(side=tk.LEFT)

        visits = self.controller.get_visits(p['id'])
        tk.Label(detail_window, text="Visit History", font=('Tahoma',12,'bold'),
                 bg='white', fg=COLORS['primary']).pack(pady=(10,0))
        if visits:
            visit_frame = tk.Frame(detail_window, bg='white')
            visit_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            cols = ('Date','Doctor','Diagnosis','Treatment')
            tree = ttk.Treeview(visit_frame, columns=cols, show='headings', height=5)
            for c in cols:
                tree.heading(c, text=c)
                tree.column(c, width=120, anchor='w')
            for v in visits:
                tree.insert('', 'end', values=(v['visit_date'], v['doctor'], v['diagnosis'], v['treatment']))
            tree.pack(fill=tk.BOTH, expand=True)
        else:
            tk.Label(detail_window, text="No visits recorded.", font=('Tahoma',10),
                     bg='white', fg=COLORS['text_light']).pack()

        tk.Button(detail_window, text="Close", command=detail_window.destroy,
                  bg=COLORS['accent'], fg='white', font=('Tahoma',10,'bold'),
                  relief=tk.FLAT, padx=20, pady=5, cursor='hand2').pack(pady=10)

    # ---- Search ----
    def do_search(self):
        term = self.entry_search.get().strip()
        search_by = self.search_by_var.get()
        blood = self.search_blood.get() if self.search_blood.get() != 'All' else None
        date_from = self.entry_date_from.get().strip()
        date_to = self.entry_date_to.get().strip()
        results = self.controller.search_patients(term, search_by, blood, date_from, date_to)
        self.refresh_patients(results, reset_offset=True)

    def clear_search(self):
        self.entry_search.delete(0, tk.END)
        self.search_blood.set('All')
        self.entry_date_from.delete(0, tk.END)
        self.entry_date_to.delete(0, tk.END)
        self.refresh_patients()

    # ---- Export ----
    def export_csv(self):
        if not self.current_patients:
            messagebox.showwarning("No Data", "No patients to export.")
            return
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if filename:
            if self.controller.export_csv(self.current_patients, filename):
                messagebox.showinfo("Export", f"Data exported to {filename}")
            else:
                messagebox.showerror("Export", "Export failed.")

    # ---------- Charts Page ----------
    def show_dashboard(self):
        if 'charts' not in self.pages:
            page = tk.Frame(self.content_container, bg=COLORS['background'])
            page.pack_propagate(False)
            page.config(height=700)
            self.build_charts_page(page)
            self.pages['charts'] = page
        else:
            if MATPLOTLIB:
                for widget in self.pages['charts'].winfo_children():
                    widget.destroy()
                self.build_charts_content(self.pages['charts'])
        self.show_page('charts', self.pages['charts'])

    def build_charts_page(self, parent):
        if not MATPLOTLIB:
            tk.Label(parent, text="Matplotlib not installed. Please install: pip install matplotlib numpy",
                     font=('Tahoma',14), bg=COLORS['background'], fg=COLORS['accent']).pack(expand=True)
            return
        self.build_charts_content(parent)

    def build_charts_content(self, parent):
        try:
            stats = self.controller.get_stats()
            fig_bg = COLORS['background']
            text_color = COLORS['text']
            fig = plt.Figure(figsize=(15, 8), dpi=90, facecolor=fig_bg)
            plt.rcParams['text.color'] = text_color
            plt.rcParams['axes.labelcolor'] = text_color
            plt.rcParams['xtick.color'] = text_color
            plt.rcParams['ytick.color'] = text_color

            # Gender bar
            ax1 = fig.add_subplot(241)
            gd = dict(stats['gender'])
            vals = [gd.get('Male',0), gd.get('Female',0), gd.get('Other',0)]
            bars = ax1.bar(['Male','Female','Other'], vals, color=['#2e86c1','#e74c3c','#95a5a6'])
            ax1.set_title('Gender', color=text_color)
            ax1.set_ylabel('Count', color=text_color)
            ax1.set_facecolor(fig_bg)
            ax1.tick_params(colors=text_color)
            for bar,v in zip(bars,vals):
                ax1.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5, str(v), ha='center', va='bottom', color=text_color)

            # Status bar
            ax2 = fig.add_subplot(242)
            sd = dict(stats['status'])
            vals = [sd.get('Active',0), sd.get('Inactive',0), sd.get('Pending',0)]
            bars = ax2.bar(['Active','Inactive','Pending'], vals, color=['#27ae60','#e74c3c','#f39c12'])
            ax2.set_title('Status', color=text_color)
            ax2.set_ylabel('Count', color=text_color)
            ax2.set_facecolor(fig_bg)
            ax2.tick_params(colors=text_color)
            for bar,v in zip(bars,vals):
                ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5, str(v), ha='center', va='bottom', color=text_color)

            # Age distribution
            ax3 = fig.add_subplot(243)
            age_groups = dict(stats['age_groups'])
            all_groups = ['0-17','18-30','31-50','51-65','65+']
            counts = [age_groups.get(g,0) for g in all_groups]
            bars = ax3.bar(all_groups, counts, color=['#3498db','#2ecc71','#f1c40f','#e67e22','#e74c3c'])
            ax3.set_title('Age Distribution', color=text_color)
            ax3.set_ylabel('Count', color=text_color)
            ax3.set_facecolor(fig_bg)
            ax3.tick_params(colors=text_color, rotation=45)
            for bar,v in zip(bars,counts):
                ax3.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5, str(v), ha='center', va='bottom', color=text_color)

            # Gender pie
            ax4 = fig.add_subplot(244)
            if sum(vals)>0:
                ax4.pie([gd.get('Male',0), gd.get('Female',0), gd.get('Other',0)],
                        labels=['Male','Female','Other'], colors=['#2e86c1','#e74c3c','#95a5a6'],
                        autopct='%1.1f%%', startangle=90, textprops={'color':text_color})
            ax4.set_title('Gender %', color=text_color)

            # Status pie
            ax5 = fig.add_subplot(245)
            if sum(vals)>0:
                ax5.pie([sd.get('Active',0), sd.get('Inactive',0), sd.get('Pending',0)],
                        labels=['Active','Inactive','Pending'], colors=['#27ae60','#e74c3c','#f39c12'],
                        autopct='%1.1f%%', startangle=90, textprops={'color':text_color})
            ax5.set_title('Status %', color=text_color)

            # Daily registrations
            ax6 = fig.add_subplot(246)
            daily = stats['daily']
            if daily:
                dates = [d[0] for d in daily]
                counts = [d[1] for d in daily]
                if len(dates)>30:
                    dates=dates[-30:]; counts=counts[-30:]
                ax6.plot(dates, counts, marker='o', color=COLORS['primary'], linewidth=2)
                ax6.fill_between(dates, counts, alpha=0.25, color=COLORS['primary_light'])
                ax6.set_title('Daily Registrations (30d)', color=text_color)
                ax6.set_xlabel('Date', color=text_color)
                ax6.set_ylabel('Count', color=text_color)
                ax6.set_facecolor(fig_bg)
                ax6.tick_params(colors=text_color)
                plt.setp(ax6.xaxis.get_majorticklabels(), rotation=45, fontsize=8)
                if len(counts)>1:
                    z = np.polyfit(range(len(counts)), counts, 1)
                    trend = np.poly1d(z)
                    ax6.plot(dates, trend(range(len(counts))), '--', color=COLORS['accent'], label='Trend')
                    ax6.legend(facecolor=fig_bg, edgecolor=COLORS['border'], labelcolor=text_color)

            # Visits per day – TRANSPARENT BACKGROUND
            ax7 = fig.add_subplot(247)
            visits = stats['visits_daily']
            if visits:
                dates = [v[0] for v in visits]
                counts = [v[1] for v in visits]
                bar_color = COLORS['secondary']
                ax7.bar(dates, counts, color=bar_color, edgecolor='none')
                ax7.set_title('Visits per Day (30d)', color=text_color)
                ax7.set_xlabel('Date', color=text_color)
                ax7.set_ylabel('Visits', color=text_color)
                ax7.set_facecolor('none')          # transparent
                ax7.tick_params(colors=text_color)
                plt.setp(ax7.xaxis.get_majorticklabels(), rotation=45, fontsize=8)
            else:
                ax7.text(0.5,0.5,'No visit data', ha='center', va='center', color=text_color, transform=ax7.transAxes)
                ax7.set_title('Visits per Day', color=text_color)
                ax7.set_facecolor('none')

            # Summary
            ax8 = fig.add_subplot(248)
            ax8.axis('off')
            summary = f"""
    Summary
    Total Patients: {stats['total']}
    Gender: M {gd.get('Male',0)}  F {gd.get('Female',0)}  O {gd.get('Other',0)}
    Status: A {sd.get('Active',0)}  I {sd.get('Inactive',0)}  P {sd.get('Pending',0)}
    Age groups: 0-17 {age_groups.get('0-17',0)}  18-30 {age_groups.get('18-30',0)}  31-50 {age_groups.get('31-50',0)}  51-65 {age_groups.get('51-65',0)}  65+ {age_groups.get('65+',0)}
    Days recorded: {len(daily)}
    Visits (30d): {sum(c for _,c in stats['visits_daily'])}
            """
            ax8.text(0.1,0.9, summary, transform=ax8.transAxes, fontsize=9,
                     verticalalignment='top', fontfamily='monospace',
                     bbox=dict(boxstyle='round', facecolor=COLORS['card'], alpha=0.9, edgecolor=COLORS['border']),
                     color=text_color)

            fig.tight_layout(pad=3.0)

            container = tk.Frame(parent, bg=COLORS['background'])
            container.pack(fill=tk.BOTH, expand=True)

            canvas = FigureCanvasTkAgg(fig, master=container)
            toolbar = NavigationToolbar2Tk(canvas, container)
            toolbar.update()
            toolbar.pack(side=tk.TOP, fill=tk.X)

            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            stats_frame = tk.Frame(parent, bg=COLORS['background'])
            stats_frame.pack(fill=tk.X, pady=10)
            for label, value, color in [
                ("Total", stats['total'], COLORS['primary_light']),
                ("Active", sd.get('Active',0), COLORS['success']),
                ("Pending", sd.get('Pending',0), COLORS['warning']),
                ("Days", len(daily), COLORS['secondary'])
            ]:
                frame = tk.Frame(stats_frame, bg=COLORS['card'], relief='ridge', bd=2, width=150, height=50)
                frame.pack(side=tk.LEFT, padx=10, pady=5, expand=True, fill=tk.X)
                tk.Label(frame, text=label, font=('Tahoma',10,'bold'), bg=COLORS['card'], fg=COLORS['text_light']).pack(side=tk.LEFT, padx=10)
                tk.Label(frame, text=str(value), font=('Tahoma',14,'bold'), bg=COLORS['card'], fg=color).pack(side=tk.RIGHT, padx=10)

        except Exception as e:
            tk.Label(parent, text=f"Error loading charts: {str(e)}",
                     font=('Tahoma',12), bg=COLORS['background'], fg=COLORS['accent']).pack(expand=True)

    # ---------- Reports Page ----------
    def show_reports(self):
        if 'reports' not in self.pages:
            page = tk.Frame(self.content_container, bg=COLORS['background'])
            tk.Label(page, text="Generate PDF Reports", font=('Tahoma',20,'bold'),
                     bg=COLORS['background'], fg=COLORS['primary']).pack(pady=(40,20))

            btn_frame = tk.Frame(page, bg=COLORS['background'])
            btn_frame.pack(pady=20)

            for period, label in [('weekly','Weekly Report'), ('monthly','Monthly Report'), ('yearly','Yearly Report')]:
                tk.Button(btn_frame, text=label, command=lambda p=period: self.gen_report(p),
                          bg=COLORS['primary_light'], fg='white', font=('Tahoma',11,'bold'),
                          relief=tk.FLAT, padx=30, pady=15, cursor='hand2').pack(side=tk.LEFT, padx=10)

            custom_frame = tk.Frame(page, bg=COLORS['background'])
            custom_frame.pack(pady=20)
            tk.Label(custom_frame, text="Custom Range:", font=('Tahoma',12,'bold'),
                     bg=COLORS['background'], fg=COLORS['primary']).pack(side=tk.LEFT, padx=(0,10))

            self.start_date_var = tk.StringVar()
            self.end_date_var = tk.StringVar()

            tk.Button(custom_frame, text="Start Date", command=lambda: CalendarPicker(self.root, self.set_start_date),
                      bg=COLORS['secondary'], fg='white', font=('Tahoma',9,'bold'),
                      relief=tk.FLAT, padx=10, pady=5, cursor='hand2').pack(side=tk.LEFT, padx=5)
            self.start_label = tk.Label(custom_frame, text="None", font=('Tahoma',9),
                                        bg=COLORS['background'], fg=COLORS['text_light'])
            self.start_label.pack(side=tk.LEFT, padx=5)

            tk.Button(custom_frame, text="End Date", command=lambda: CalendarPicker(self.root, self.set_end_date),
                      bg=COLORS['secondary'], fg='white', font=('Tahoma',9,'bold'),
                      relief=tk.FLAT, padx=10, pady=5, cursor='hand2').pack(side=tk.LEFT, padx=10)
            self.end_label = tk.Label(custom_frame, text="None", font=('Tahoma',9),
                                      bg=COLORS['background'], fg=COLORS['text_light'])
            self.end_label.pack(side=tk.LEFT, padx=5)

            tk.Button(custom_frame, text="Generate Report", command=self.generate_custom_report,
                      bg=COLORS['success'], fg='white', font=('Tahoma',11,'bold'),
                      relief=tk.FLAT, padx=20, pady=8, cursor='hand2').pack(side=tk.LEFT, padx=20)

            tk.Label(page, text="Reports include summary statistics, patient list, and a chart.",
                     font=('Tahoma',11), bg=COLORS['background'], fg=COLORS['text_light']).pack(pady=20)

            self.pages['reports'] = page
        self.show_page('reports', self.pages['reports'])

    def set_start_date(self, date_str):
        self.start_date_var.set(date_str if date_str else '')
        self.start_label.config(text=date_str if date_str else 'None')

    def set_end_date(self, date_str):
        self.end_date_var.set(date_str if date_str else '')
        self.end_label.config(text=date_str if date_str else 'None')

    def generate_custom_report(self):
        start = self.start_date_var.get()
        end = self.end_date_var.get()
        if not start or not end:
            messagebox.showwarning("Missing Dates", "Please select both start and end dates.")
            return
        if start > end:
            messagebox.showwarning("Invalid Range", "Start date must be before end date.")
            return
        fname = self.controller.generate_pdf_report('custom', start, end)
        if fname:
            messagebox.showinfo("Report", f"Report saved:\n{fname}")
        else:
            messagebox.showinfo("Report", "No data for this range.")

    def gen_report(self, period):
        if not REPORTLAB:
            messagebox.showwarning("ReportLab missing", "Please install reportlab.")
            return
        fname = self.controller.generate_pdf_report(period)
        if fname:
            messagebox.showinfo("Report", f"Report saved:\n{fname}")
        else:
            messagebox.showinfo("Report", "No data for this period.")

    # ---------- Settings ----------
    def show_settings(self):
        if 'settings' not in self.pages:
            page = tk.Frame(self.content_container, bg=COLORS['background'])
            tk.Label(page, text="Settings", font=('Tahoma',20,'bold'),
                     bg=COLORS['background'], fg=COLORS['primary']).pack(pady=(30,20))

            theme_frame = tk.Frame(page, bg=COLORS['background'])
            theme_frame.pack(fill=tk.X, pady=10, padx=40)
            tk.Label(theme_frame, text="Theme:", font=('Tahoma',11,'bold'),
                     bg=COLORS['background'], fg=COLORS['text']).pack(side=tk.LEFT, padx=(0,20))
            theme_combo = ttk.Combobox(theme_frame, textvariable=self.theme_var,
                                       values=['light','dark'], font=('Tahoma',10), width=10, state='readonly')
            theme_combo.pack(side=tk.LEFT)
            theme_combo.bind('<<ComboboxSelected>>', self.change_theme)

            reset_frame = tk.Frame(page, bg=COLORS['background'])
            reset_frame.pack(fill=tk.X, pady=20, padx=40)
            tk.Button(reset_frame, text="Reset Database (keep sample data)",
                      command=self.reset_db,
                      bg=COLORS['warning'], fg='white', font=('Tahoma',10,'bold'),
                      relief=tk.FLAT, padx=20, pady=8, cursor='hand2').pack(side=tk.LEFT)

            tk.Label(page, text="System Information", font=('Tahoma',12,'bold'),
                     bg=COLORS['background'], fg=COLORS['primary']).pack(pady=(30,10))
            info_text = f"Database: {self.controller.db.db_name}\nRecords: {len(self.controller.get_all_patients())}\nPython version: {sys.version.split()[0]}\nTkinter version: {tk.TkVersion}"
            tk.Label(page, text=info_text, font=('Tahoma',10), bg=COLORS['background'],
                     fg=COLORS['text_light'], justify=tk.LEFT).pack(pady=10, padx=40, anchor=tk.W)

            self.pages['settings'] = page
        self.show_page('settings', self.pages['settings'])

    # ---------- Theme Change ----------
    def change_theme(self, event=None):
        theme = self.theme_var.get()
        apply_theme(theme)
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview",
                        background=COLORS['tree_bg'],
                        foreground=COLORS['tree_fg'],
                        rowheight=28,
                        font=('Tahoma',9))
        style.map('Treeview',
                  background=[('selected', COLORS['tree_selected'])],
                  foreground=[('selected', 'white')])
        self.root.configure(bg=COLORS['background'])
        self.main_frame.configure(bg=COLORS['background'])
        self.content_container.configure(bg=COLORS['background'])

        for name, frame in list(self.pages.items()):
            frame.destroy()
        self.pages.clear()
        self.show_home()
        self.show_patients()
        self.show_dashboard()
        self.show_reports()
        self.show_settings()
        if self.current_page_name in self.pages:
            self.show_page(self.current_page_name, self.pages[self.current_page_name])
        else:
            self.show_home()

    # ---------- Reset Database ----------
    def reset_db(self):
        if messagebox.askyesno("Reset Database", "This will delete all patient records and reload sample data. Continue?"):
            self.controller.db.close()
            db_path = self.controller.db.db_name
            if os.path.exists(db_path):
                os.remove(db_path)
            self.controller.db = Database(db_path)
            self.controller.db.add_observer(self.controller._notify_observers)
            self.controller.db.notify_observers({'action':'data_loaded'})
            if 'patients' in self.pages:
                self.refresh_patients()
            # Also refresh home if visible
            if self.current_page_name == 'home':
                self.update_home_stats()
                self.update_home_recent()
            messagebox.showinfo("Reset", "Database has been reset with sample data.")

    # ---------- Logout ----------
    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.controller.logout()
            self.root.destroy()
            start_app()

    # ---------- Database change observer ----------
    def on_db_change(self, data):
        # If we are on the patients page, refresh the table
        if self.current_page_name == 'patients':
            self.root.after(100, self.refresh_patients)
        # If we are on the home page, update stats and recent list
        elif self.current_page_name == 'home':
            self.root.after(100, self.update_home_stats)
            self.root.after(100, self.update_home_recent)


# ============================================================
# LAUNCHER
# ============================================================
def start_app():
    root = tk.Tk()
    ctrl = Controller()
    def on_login():
        root.destroy()
        main_root = tk.Tk()
        DashboardApp(main_root, ctrl)
        main_root.mainloop()
    LoginView(root, ctrl, on_login)
    root.mainloop()

if __name__ == "__main__":
    start_app()