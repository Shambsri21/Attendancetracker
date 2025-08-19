# Employee Attendance and Management System

A robust web application built with Flask for managing employee attendance, user roles (Admin, HR, Employee), and essential employee information. This system provides functionalities for clocking in/out, tracking attendance, and generating basic reports.

![Build Status](https://img.shields.io/badge/build-passing-brightgreen) ![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Coverage](https://img.shields.io/badge/coverage-N%2FA-lightgrey)

## Table of Contents

- [Key Features](#key-features)

- [Architecture Overview](#architecture-overview)

- [Tech Stack](#tech-stack)

- [Getting Started](#getting-started)

  - [Prerequisites](#prerequisites)

  - [Installation](#installation)

- [Configuration](#configuration)

- [Usage](#usage)

- [Project Structure](#project-structure)

- [Scripts](#scripts)

- [Roadmap](#roadmap)

- [Contributing](#contributing)

- [Testing](#testing)

- [License](#license)

- [Acknowledgements](#acknowledgements)

## Key Features

-   **User Authentication & Authorization**: Secure login system with distinct roles for Admin, HR, and Employees.

-   **Employee Management**: Comprehensive CRUD (Create, Read, Update, Delete) operations for employee records.

-   **Attendance Tracking**: Employees can clock in and clock out, with records stored in the database.

-   **Attendance Reporting**: View monthly present days and average working hours for employees.

-   **Database Management**: Utilizes SQLAlchemy for efficient and object-relational mapping with a MySQL database.

-   **Secure Password Hashing**: Passwords are securely stored using `werkzeug.security` for enhanced security.

## Architecture Overview

This application follows a traditional Model-View-Controller (MVC) pattern, implemented using the Flask web framework. The backend logic is handled by Flask, which interacts with a MySQL database via Flask-SQLAlchemy, an Object Relational Mapper (ORM). User authentication and session management are managed by Flask-Login.

The system defines several key models: `User` (for authentication and roles), `Employee` (for employee details), `Attendance` (for clock-in/clock-out records), and `Activity` (for logging system events). Role-based access control ensures that different user types (Admin, HR, Employee) have appropriate permissions to access and modify data. Frontend interactions are rendered using Jinja2 templates, served by Flask.

## Tech Stack

| Area | Tool | Version |
|---|---|---|
|---|---|---|
| Backend | Python | 3.x |
| Web Framework | Flask | 3.0.2 |
|---|---|---|
| ORM | Flask-SQLAlchemy | 3.1.1 |
| Authentication | Flask-Login | 0.6.3 |
|---|---|---|
| Password Hashing | Werkzeug | 3.0.1 |
| Environment Variables | python-dotenv | 1.0.1 |
|---|---|---|
| Database | MySQL | 8.x |
| MySQL Connector | mysqlclient | 2.2.4 |
|---|---|---|
| MySQL Connector | mysql-connector-python | 8.3.0 |
| Reporting (Potential) | matplotlib | 3.8.3 |
|---|---|---|
| Reporting (Potential) | reportlab | 4.1.0 |



## Getting Started

Follow these steps to get your development environment set up and running.

### Prerequisites

Before you begin, ensure you have the following installed:

-   Python 3.8+

-   MySQL Server (e.g., MySQL Community Server, XAMPP, Dockerized MySQL)

### Installation

1.  **Clone the repository**:

```bash
git clone https://github.com/Shambsri21/Attendancetracker.git

cd Attendancetracker

```
2.  **Create a virtual environment**:

```bash
python -m venv venv

```
3.  **Activate the virtual environment**:

    -   On Linux/macOS:

```bash
source venv/bin/activate

```
-   On Windows:

```bash
venv\Scripts\activate

```
4.  **Install the required dependencies**:

```bash
pip install -r requirements.txt

```
5.  **Configure Environment Variables**:
    Create a `.env` file in the root directory of the project and add the following variables:

```env
SECRET_KEY='your_super_secret_key_here'

DATABASE_URL='mysql://username:password@host/database_name'

```
Replace `your_super_secret_key_here` with a strong, random string.

Replace `username`, `password`, `host`, and `database_name` with your MySQL database credentials. For example: `mysql://root:root@localhost/employee_management`.

6.  **Initialize the Database**:
    Run the `reset_db.py` script to create the database tables and populate them with default admin and HR users.

```bash
python reset_db.py

```
This will output the default credentials:

    -   Admin: Username `admin`, Password `admin123`

    -   HR: Username `hr`, Password `hr123`
