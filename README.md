<div align="center">

# 🟢 SmartRx
### Smart Pharmacy Inventory Management System

![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-black?style=for-the-badge&logo=flask)
![SQLite](https://img.shields.io/badge/SQLite-Database-blue?style=for-the-badge&logo=sqlite)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6-yellow?style=for-the-badge&logo=javascript)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

> A full-stack pharmacy inventory system where every core feature is powered by a real Data Structure — Trie, B+ Tree, QuadTree, and Min-Heap.

</div>

---

## 📌 Table of Contents

- [About the Project](#-about-the-project)
- [Why SmartRx?](#-why-smartrx)
- [Features](#-features)
- [Data Structures Used](#-data-structures-used)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [API Endpoints](#-api-endpoints)
- [Database](#-database)
- [Deployment](#-deployment)
- [Author](#-author)

---

## 🏥 About the Project

**SmartRx** is a Smart Pharmacy Inventory Management System built as a Data Structures and Algorithms project at **VIT Pune**. The name comes from:
- **Smart** — intelligent, DSA-powered real-time operations
- **Rx** — the universal symbol for medical prescriptions (from Latin *"Recipe"*)

The system solves a real-world problem — people in cities like Pune and Bangalore visit multiple pharmacies searching for medicines that may be out of stock or expired. SmartRx allows users to instantly search which nearby pharmacy has a medicine in stock, at what price, and how much quantity is available.

---

## 💡 Why SmartRx?

| Problem | SmartRx Solution |
|---|---|
| Can't find medicine nearby | QuadTree spatial search across 25 pharmacies |
| Manual expiry tracking | Min-Heap auto-sorts by urgency |
| Slow medicine search | Trie gives O(m) autocomplete |
| No price transparency | PharmEasy API fetches live MRP |
| Fake data entry | Role-based Auth (Admin vs User) |
| No age verification | Age restriction on Rx medicines |

---

## ✨ Features

### 👤 For Users
- 🔍 **Real-time medicine search** with autocomplete (powered by Trie)
- 🗺️ **Interactive map** showing all nearby pharmacies (Leaflet.js + OpenStreetMap)
- ⚠️ **Expiry alerts** sorted by urgency (powered by Min-Heap)
- 🔞 **Age restriction** on prescription medicines
- 🌍 **4 languages** — English, Hindi, Marathi, Kannada
- 🌙 **Dark mode / Light mode**
- 📱 **Responsive design** — works on mobile and desktop

### 🔐 For Admins
- ➕ **Add/Edit/Delete** inventory and pharmacies
- 📊 **Analytics dashboard** with live charts (Chart.js)
- 🔮 **AI expiry prediction** with risk scores (0–100)
- 💰 **Auto price fetch** from PharmEasy API
- 🖨️ **PDF report generator** with DSA stats
- 👥 **User management** with role-based access

### 🏗️ System Features
- 26 REST API endpoints
- SHA-256 password hashing
- Session-based authentication
- SQLite database (zero config)
- Production-ready with PostgreSQL + Gunicorn support

---

## 🧠 Data Structures Used

### 1. 🌳 Trie — Medicine Search
```
User types "Para"
     root
      |
      p → a → r → a → [Paracetamol ✅]
                    → [Paracip ✅]
                    → [Paralen ✅]
```
- **Time Complexity:** O(m) where m = prefix length
- **vs Linear Search:** O(n×m) — Trie is exponentially faster
- **Used for:** Autocomplete suggestions as user types

---

### 2. 🌲 B+ Tree — Inventory Storage
```
         [50]
        /    \
    [20,35]  [65,80]
    /  |  \   /  |  \
  [..][..][..][..][..][..]  ← All data in leaf nodes
         ↕   ↕   ↕         ← Linked for range queries
```
- **Time Complexity:** O(log n) insert/search, O(log n + k) range
- **Used for:** Storing all inventory records, price range queries

---

### 3. 🗺️ QuadTree — Pharmacy Location Search
```
Pune/Bangalore map divided into 4 quadrants:
┌────────┬────────┐
│  NW    │  NE   │
│ [ph1]  │[ph3]  │
├────────┼────────┤
│  SW    │  SE   │
│ [ph2]  │[ph4]  │
└────────┴────────┘
Each quadrant splits again until 1 pharmacy per node
```
- **Time Complexity:** O(log n) for spatial queries
- **Used for:** Find pharmacies within 20km of user

---

### 4. ⏰ Min-Heap — Expiry Alerts
```
        [2 days] ← Most urgent always at root!
       /         \
  [5 days]     [7 days]
  /     \
[12]   [30]
```
- **Time Complexity:** O(1) peek, O(log n) insert
- **Used for:** Expiry alerts sorted by urgency automatically

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | HTML5, CSS3, JavaScript ES6 | Single page application |
| **Backend** | Python 3.11, Flask 3.0 | REST API server |
| **Database** | SQLite (local), PostgreSQL (production) | Data storage |
| **Maps** | Leaflet.js + OpenStreetMap | Pharmacy location map |
| **Charts** | Chart.js 4.4 | Analytics dashboard |
| **Server** | Gunicorn | Production WSGI server |
| **Security** | SHA-256 Hashing | Password protection |
| **Prices** | PharmEasy API | Live medicine MRP |
| **Fonts** | Google Fonts | Instrument Serif + Geist |

---

## 📁 Project Structure

```
smartrx/
│
├── app.py                  # Flask app factory + server entry point
├── database.py             # SQLite operations (CRUD)
├── ds_manager.py           # All 4 Data Structures (Trie, B+Tree, QuadTree, MinHeap)
├── medicines.py            # /api/v1/medicines Blueprint
├── pharmacies.py           # /api/v1/pharmacies Blueprint
├── inventory.py            # /api/v1/inventory Blueprint
├── alerts.py               # /api/v1/alerts Blueprint
├── auth.py                 # /api/v1/register + /api/v1/login Blueprint
├── predict_expiry.py       # AI expiry prediction Blueprint
├── settings.py             # Configuration (port, thresholds, paths)
├── db_config.py            # SQLite ↔ PostgreSQL adapter
│
├── index.html              # Main frontend (single page app)
├── expiry_dashboard.html   # AI expiry prediction dashboard
│
├── medicines.csv           # 132 medicines seed data
├── pharmacies.csv          # 25 pharmacies (Pune + Bangalore)
├── inventory.csv           # 300+ inventory records
│
├── pharmacy.db             # SQLite database (auto-created, gitignored)
│
├── requirements.txt        # Python dependencies
├── Procfile                # Render/Heroku deployment config
├── render.yaml             # Render deployment config
└── .gitignore              # Ignores db, env, cache files
```

---

## ⚙️ Installation

### Prerequisites
- Python 3.11 or higher → [python.org](https://python.org)
- Git → [git-scm.com](https://git-scm.com)

### Step 1 — Clone the Repository
```bash
git clone https://github.com/shreya-raut/smartrx.git
cd smartrx
```

### Step 2 — Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3 — Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Setup Database
```bash
python setup_users.py
```

### Step 5 — Run the Server
```bash
python app.py
```

### Step 6 — Open in Browser
```
http://127.0.0.1:5000
```

### Default Login Credentials

| Role | Username | Password |
|---|---|---|
| 👤 User | `user` | `user123` |
| 🔐 Admin | `admin` | `admin@smartrx` |

---

## 🔌 API Endpoints

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/register` | Register new user |
| POST | `/api/v1/login` | Login |
| POST | `/api/v1/age_check` | Medicine age restriction check |

### Medicines
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/medicines` | Get all medicines |
| GET | `/api/v1/medicines/search?q=para` | Trie autocomplete search |
| GET | `/api/v1/medicines/<id>` | Get single medicine |

### Pharmacies
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/pharmacies` | Get all pharmacies |
| GET | `/api/v1/pharmacies/nearby?lat=&lon=&radius=` | QuadTree spatial search |
| POST | `/api/v1/pharmacies` | Add pharmacy (Admin) |

### Inventory
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/inventory` | Get all inventory |
| POST | `/api/v1/inventory` | Add inventory (Admin) |
| PUT | `/api/v1/inventory/<id>` | Update record (Admin) |
| DELETE | `/api/v1/inventory/<id>` | Delete record (Admin) |

### Alerts & Analytics
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/alerts?days=7` | Min-Heap expiry alerts |
| GET | `/api/v1/dashboard` | System stats |
| GET | `/api/v1/predict_expiry` | AI risk scores |
| GET | `/api/v1/health` | Server health check |

---

## 🗄️ Database

SmartRx uses **SQLite** locally — a single file `pharmacy.db` containing:

| Table | Records | Description |
|---|---|---|
| `medicines` | 132 | Medicine catalog with categories |
| `pharmacies` | 25 | Pune (10) + Bangalore (15) |
| `inventory` | 300+ | Stock, price, expiry per pharmacy |
| `users` | — | Registered users with hashed passwords |

View using [DB Browser for SQLite](https://sqlitebrowser.org) → Open `pharmacy.db` → Browse Data

---

## 🚀 Deployment

Configured for **Render.com** (free):

1. Push to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your GitHub repo
4. Add environment variable: `SECRET_KEY=your-secret`
5. Add free PostgreSQL database
6. Deploy!

See `DEPLOYMENT_GUIDE.md` for detailed steps.

---

## 👩‍💻 Author

**Shweta Raut**
- 🎓 VIT Pune — Second Year
- 📧 shwetadraut01@gmail.com

---

## 📄 License

This project is licensed under the MIT License.

---

<div align="center">

Made with ❤️ for DSA Project — VIT Pune 2025-26

⭐ **Star this repo if you found it helpful!**

</div>
