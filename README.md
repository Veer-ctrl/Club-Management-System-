# 🎓 Club Management System

A role-based web application built with **Django** and **SQLite** to streamline club operations, member management, and event organization. The system provides dedicated dashboards for Members, Admins, and Super Admins, enabling efficient management of clubs and their activities.

---

## ✨ Features

- 🔐 Secure User Authentication & Authorization
- 👤 Member Dashboard
- 🛠️ Admin Dashboard
- 👑 Super Admin Dashboard
- 👥 Member Management
- 🏛️ Club Management
- 📅 Event Creation & Management
- 📢 Announcements & Notifications
- 🔍 Search Functionality
- 📊 Role-Based Access Control (RBAC)
- 🖥️ Desktop-Optimized Interface

---

## 👥 User Roles

### 👤 Member
- Access personal dashboard
- View club information
- Participate in events
- Receive announcements

### 🛠️ Admin
- Manage members
- Create and manage events
- Post announcements
- Monitor club activities

### 👑 Super Admin
- Manage all clubs
- Manage admins and members
- System-wide monitoring and control
- Access complete platform data

---

## 🛠️ Tech Stack

### Frontend
- HTML5
- CSS3
- JavaScript
- Tailwind CSS
- Flowbite

### Backend
- Python
- Django

### Database
- SQLite

---

## 📂 Project Structure

```text
Club-Management-System/
│
├── clubManagement/
├── templates/
├── static/
├── media/
├── db.sqlite3
├── manage.py
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Club-Management-System
```

### 2. Create a Virtual Environment

```bash
python -m venv env
```

### 3. Activate the Virtual Environment

#### Windows

```bash
env\Scripts\activate
```

#### Linux/macOS

```bash
source env/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Apply Database Migrations

```bash
python manage.py migrate
```

### 6. Run the Development Server

```bash
python manage.py runserver
```

### 7. Open in Browser

```
http://127.0.0.1:8000/
```

## ⚠️ Current Limitations

- Currently optimized for desktop screens.
- Mobile responsiveness will be added in future updates.

---

## 🔮 Future Enhancements

- Email Notifications
- Real-Time Updates
- Attendance Tracking
- Analytics Dashboard
- Mobile Responsiveness
- Cloud Database Integration

---

## 👨‍💻 Author

**Veer Pratap Singh**

- GitHub: **[@Veer-ctrl](https://github.com/Veer-ctrl)**

---

⭐ Developed for learning and exploring role-based web application development using Django.
