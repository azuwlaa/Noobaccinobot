# Noobaccinobot
# Telegram Member Info Bot (Minimal Version)

A simple Telegram bot for storing and managing user information with admin access.

## Features

- Users can view their own info using `/myinfo`
- Users can update allowed fields via `/updateinfo`
- Admins can view full user info using `/thisuser <id>`
- Stores data in `data/users.json`
- Secure token handling using `.env`

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
