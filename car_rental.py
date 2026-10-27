"""Car rental system: fleet, customers, bookings, promos and receipts."""
import os
import re
import sqlite3
import hashlib
import hmac
import secrets
import tempfile
from datetime import datetime

EXTRA_KM_LIMIT = 300
EXTRA_KM_RATE = 5
DATE_FORMAT = "%Y-%m-%d"

# Global rental state
fleet = {}
bookings = []
conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE customers (name TEXT, licence TEXT, phone TEXT)")


def add_car(plate, model="Unknown", daily_rate=0, features=None):
    """Add a car to the fleet and return its record."""
    if not is_valid_plate(plate):
        raise ValueError(f"Invalid number plate: {plate!r}")
    if daily_rate <= 0:
        raise ValueError(f"Daily rate must be positive, got {daily_rate}")
    if features is None:
        features = []
    fleet[plate] = {"model": model, "rate": daily_rate,
                    "available": True, "features": features}
    return fleet[plate]


def register_customer(name, licence, phone):
    """Store a customer using a parameterised query."""
    conn.execute("INSERT INTO customers VALUES (?, ?, ?)",
                 (name, licence, phone))


def find_customer(name):
    """Return all customer rows matching the exact name."""
    return conn.execute("SELECT * FROM customers WHERE name = ?",
                        (name,)).fetchall()


def rent_car(plate, customer, start, end):
    """Book an available car for a registered customer and return the cost."""
    if not find_customer(customer):
        raise ValueError(f"Customer not registered: {customer}")
    if plate not in fleet:
        raise ValueError(f"Unknown car: {plate}")
    if not fleet[plate]["available"]:
        raise ValueError(f"Car {plate} is already rented")
    days = (datetime.strptime(end, DATE_FORMAT)
            - datetime.strptime(start, DATE_FORMAT)).days
    if days <= 0:
        raise ValueError("End date must be after start date")
    cost = days * fleet[plate]["rate"]
    fleet[plate]["available"] = False
    bookings.append({"code": booking_code(), "plate": plate,
                     "customer": customer, "days": days, "cost": cost})
    return cost


def return_car(plate, km_driven):
    """Mark a car as returned and return the extra-kilometre charge."""
    if plate not in fleet:
        raise ValueError(f"Unknown car: {plate}")
    fleet[plate]["available"] = True
    return max(0, km_driven - EXTRA_KM_LIMIT) * EXTRA_KM_RATE


def booking_code():
    """Generate an unpredictable booking reference."""
    return "BK-" + str(10000 + secrets.randbelow(90000))


def licence_hash(licence):
    """Return a SHA-256 hash of a driving licence number."""
    return hashlib.sha256(licence.encode()).hexdigest()


def apply_promo(discount_percent, amount):
    """Apply a percentage discount (0-100) entered by counter staff."""
    discount_percent = float(discount_percent)
    if not 0 <= discount_percent <= 100:
        raise ValueError("Discount must be between 0 and 100")
    return amount * (100 - discount_percent) / 100


def is_valid_plate(plate):
    """Check an Indian-style number plate such as KA01AB1234."""
    pattern = r"[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}"
    return bool(re.fullmatch(pattern, plate or ""))


def write_receipt(booking):
    """Write a private receipt file for a booking and return its path."""
    fd, path = tempfile.mkstemp(suffix=".txt")
    with os.fdopen(fd, "w", encoding="utf-8") as receipt:
        receipt.write(f"Booking {booking['code']}: {booking['plate']} for "
                      f"{booking['days']} days = Rs.{booking['cost']}\n")
    os.chmod(path, 0o600)
    return path


def admin_login(user, password):
    """Check admin credentials against the RENTAL_ADMIN_PASSWORD env var."""
    expected = os.environ.get("RENTAL_ADMIN_PASSWORD")
    if not expected or not password:
        return False
    return user == "admin" and hmac.compare_digest(password, expected)


def available_cars():
    """List the plates of all cars that are not currently rented."""
    return [plate for plate, car in fleet.items() if car["available"]]


def try_action(label, action, *args):
    """Run a demo action and print its result or the error it raised."""
    try:
        print(label, action(*args))
    except ValueError as error:
        print(label, "ERROR -", error)


def main():
    """Run the built-in demo."""
    add_car("KA01AB1234", "Swift", 1500)
    add_car("KA02CD5678", "Innova", 3000)
    try_action("Add Nexon (bad rate):", add_car, "KA03EF9999", "Nexon", -500)
    register_customer("Ravi", "DL-0420110012345", "9845012345")
    register_customer("Meera", "DL-0420110099999", "9845099999")
    try_action("Rent Swift:", rent_car,
               "KA01AB1234", "Ravi", "2026-11-01", "2026-11-04")
    try_action("Rent Swift again:", rent_car,
               "KA01AB1234", "Ravi", "2026-11-02", "2026-11-03")
    try_action("Rent Innova:", rent_car,
               "KA02CD5678", "Ravi", "2026-11-10", "2026-11-07")
    print("Lookup injection:", find_customer("x' OR '1'='1"))
    print("Available while Swift is out:", available_cars())
    try_action("Extra km charge:", return_car, "KA01AB1234", 420)
    try_action("Return unknown car:", return_car, "XX00XX0000", 50)
    print("Promo price:", apply_promo(10, 4500))
    print("Plate valid?", is_valid_plate("KA01AB1234"))
    print("Licence hash:", licence_hash("DL-0420110012345"))
    print("Admin:", admin_login("admin", "admin@rent"))
    print("Available:", available_cars())
    print("Receipt saved to:", write_receipt(bookings[0]))


if __name__ == "__main__":
    main()
