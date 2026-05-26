# BitePlate Restaurant OS

BitePlate is a Django-based restaurant operating system for table service, POS, kitchen display, inventory, staff, reporting and settings.

## Stack

- Python 3.12 and Django 5
- SQLite for local development
- Django templates for the server-rendered UI
- ReportLab/OpenPyXL for operational reports and exports

This stack was chosen because the assignment needs a working object-oriented application with a fast local setup, clear model classes, and easy demonstration of design patterns in Python.

## Run Locally

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## Main Modules

- Tables and waiter flow: `/waiter/`
- POS register: `/pos/`
- Kitchen display: `/kitchen/`
- Billing and payments: `/cashier/`
- Admin Studio and settings: `/settings/`
- Inventory and purchases: `/inventory/`
- Staff management: `/staff/`
- Accounting dashboard: `/settings/accounting/`
- Telegram report send: `/reports/telegram/send/`

## Assignment Pattern Map

- Command Pattern: `commandengine/commands.py`, `commandengine/services.py`
- Singleton Order History Log: `historylog/services.py`, `historylog/models.py`
- Strategy Pricing: `pricing/services.py`
- Composite Combo Meals: `menu/models.py`
- Observer notifications: `observerengine/`

## Verification

```bash
python manage.py check
python manage.py test commandengine pricing historylog
```
