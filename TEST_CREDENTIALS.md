# Test Credentials for Campus Sphere

## Overview
This document contains test credentials for all user types in the Campus Sphere application. The system now has **three separate login pages** for different user types.

## Login Pages
1. **Student Login**: `/login-student` - For students only
2. **Authority Login**: `/login-authority` - For Faculty, Alumni, Driver, Bus Manager, Club Leader (select role from dropdown)
3. **Admin Login**: `/login-admin` - For system administrators

---

## 👨‍🎓 Student Accounts (Use `/login-student`)

**Student 1 (Also Club Leader)**
- **Email:** john.doe@example.com
- **Password:** password123
- **Details:** John Doe, B.Tech Computer Science, Batch 2025, Year 3, Leads Tech Club

**Student 2**
- **Email:** jane.smith@example.com
- **Password:** password123
- **Details:** Jane Smith, B.Tech Electronics, Batch 2026, Year 2

**Student 3**
- **Email:** rahul.k@example.com
- **Password:** password123
- **Details:** Rahul Kapoor, B.Tech Mechanical, Batch 2026, Year 2

**Student 4**
- **Email:** anita.d@example.com
- **Password:** password123
- **Details:** Anita Desai, B.Tech Civil, Batch 2025, Year 3

---

## 👨‍🏫 Faculty Accounts (Use `/login-authority`, select "Faculty")

**Faculty 1**
- **Email:** prof.sharma@campus.edu
- **Password:** faculty123
- **Name:** Dr. Ravi Sharma
- **Department:** Computer Science

**Faculty 2**
- **Email:** prof.kumar@campus.edu
- **Password:** faculty123
- **Name:** Dr. Priya Kumar
- **Department:** Mathematics

---

## 🎓 Alumni Accounts (Use `/login-authority`, select "Alumni")

**Alumni 1**
- **Email:** rajiv.patel@alumni.edu
- **Password:** alumni123
- **Details:** Rajiv Patel, Batch 2020, Senior Developer at Google

**Alumni 2**
- **Email:** meera.shah@alumni.edu
- **Password:** alumni123
- **Details:** Meera Shah, Batch 2018, Product Manager at Microsoft

**Alumni 3**
- **Email:** vikram.m@alumni.edu
- **Password:** alumni123
- **Details:** Vikram Malhotra, Batch 2019, Data Scientist at Amazon

**Alumni 4**
- **Email:** sneha.r@alumni.edu
- **Password:** alumni123
- **Details:** Sneha Reddy, Batch 2021, UX Designer at Adobe

---

## 🚌 Driver Accounts (Use `/login-authority`, select "Driver")

**Driver 1**
- **Email:** amit.driver@campus.edu
- **Password:** driverpass
- **Details:** Amit Kumar, Drives Bus UP16A 1234 (Main City Route)

**Driver 2**
- **Email:** raj.driver@campus.edu
- **Password:** driverpass
- **Details:** Raj Singh, Drives Bus UP16A 5678 (North Campus Route)

**Driver 3**
- **Email:** priya.driver@campus.edu
- **Password:** driverpass
- **Details:** Priya Sharma, Drives Bus UP16A 9012 (South Campus Route)

---

## 🚍 Bus Manager Account (Use `/login-authority`, select "Bus Manager")

**Bus Manager**
- **Email:** rajesh.manager@campus.edu
- **Password:** managerpass
- **Details:** Rajesh Verma, Phone: +91-9876543210
- **Manages:** All campus buses, drivers, and routes

---

## 🎯 Club Leader Account (Use `/login-authority`, select "Club Leader")

**Club Leader**
- **Email:** john.doe@example.com
- **Password:** password123
- **Details:** John Doe, Leads Tech Club (same as Student 1)

---

## 🔐 Admin Account (Use `/login-admin`)

**System Administrator**
- **Username:** superadmin
- **Password:** adminpass
- **Role:** Super Admin with full system access

---

## Features to Test

### 🎓 Student Features
- ✅ AI Teacher chatbot (Normal, Practice, Counseling modes)
- ✅ Bus tracking and selection (3 buses available)
- ✅ Club membership (Tech Club available)
- ✅ Event enrollment (multiple events available)
- ✅ Academic resources access
- ✅ **NEW:** Alumni contact requests
- ✅ Community forum participation

### 👨‍🏫 Faculty Features
- ✅ Faculty dashboard
- ✅ Upload academic resources
- ✅ Update timetable
- ✅ View student profiles

### 🎓 Alumni Features
- ✅ Alumni dashboard
- ✅ **NEW:** View and respond to contact requests from students
- ✅ Alumni network
- ✅ Community participation

### 🚌 Driver Features
- ✅ Driver panel
- ✅ Toggle location sharing
- ✅ Update bus location in real-time

### 🚍 Bus Manager Features
- ✅ **NEW:** Bus manager dashboard
- ✅ View all buses (3 buses) and drivers (3 drivers)
- ✅ Manage bus routes
- ✅ Assign drivers to buses
- ✅ Monitor active routes and status

### 🎯 Club Leader Features
- ✅ **NEW:** Club leader dashboard
- ✅ View led clubs (Tech Club)
- ✅ Manage club events
- ✅ Review membership requests

### 🔐 Admin Features
- ✅ Admin dashboard with statistics
- ✅ Manage faculty members
- ✅ Manage alumni accounts
- ✅ Manage clubs
- ✅ System reports

---

## 🆕 Recent Updates

### Three Separate Login Pages
- Students use `/login-student`
- Authorities use `/login-authority` with role selection dropdown
- Admins use `/login-admin`

### New Dashboards Created
- **Bus Manager Dashboard**: Full management interface for buses, drivers, and routes
- **Club Leader Dashboard**: Interface for club leaders to manage their clubs and events

### Chatbot Improvements
- Input field now hides in Practice Mode
- Subjective answers have fallback text (no more blank/undefined)
- Left panel scroll fixed (overflow: hidden)

### Alumni Contact Request Feature
- Students can request to contact alumni from `/alumni` page
- Alumni see pending requests on their dashboard
- Alumni can accept or reject requests
- Secure implementation with data attributes (no XSS vulnerabilities)

### Enhanced Sample Data
- 3 buses with different routes
- 3 drivers assigned to buses
- 4 students with various branches and batches
- 4 alumni from different companies and years
- Multiple events scheduled
- Bus manager account added

---

## Security Features
- ✅ Separate login pages for user types
- ✅ Role-based authentication with decorators
- ✅ Session token management (30-day expiry)
- ✅ Password hashing (Werkzeug security)
- ✅ Force logout on multiple devices
- ✅ Email verification for new users
- ✅ CSRF protection enabled
- ✅ XSS prevention with data attributes

---

All login flows and features have been tested and are working correctly!
