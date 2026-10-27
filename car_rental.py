import os
import json
import re
import sqlite3
import hashlib
import hmac
import secrets
import tempfile
from datetime import datetime

# Global rental state
fleet = {}
bookings = []
conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE customers (name TEXT, licence TEXT, phone TEXT)")

def addCar(plate, model="Unknown", daily_rate=0, features=[]):
    if not plate:
        return
    fleet[plate] = {"model": model, "rate": daily_rate, "available": True, "features": features}
    return fleet[plate]

def registerCustomer(name, licence, phone):
    conn.execute("INSERT INTO customers VALUES (?, ?, ?)", (name, licence, phone))

def findCustomer(name):
    return conn.execute("SELECT * FROM customers WHERE name = ?", (name,)).fetchall()

def rentCar(plate, customer, start, end):
    if not findCustomer(customer):
        raise ValueError("Customer not registered")
    days = (datetime.strptime(end, "%Y-%m-%d") - datetime.strptime(start, "%Y-%m-%d")).days
    cost = days * fleet[plate]["rate"]
    bookings.append({"code": bookingCode(), "plate": plate, "customer": customer, "days": days, "cost": cost})
    return cost

def returnCar(plate, km_driven):
    try:
        fleet[plate]["available"] = True
        if km_driven > 300:
            return (km_driven - 300) * 5
    except KeyError:
        print("Unknown car:", plate)
        return None

def bookingCode():
    return "BK-" + str(10000 + secrets.randbelow(90000))

def licenceHash(licence):
    return hashlib.sha256(licence.encode()).hexdigest()

def applyPromo(discount_percent, amount):
    # counter staff now enter a number (e.g. 10 for 10% off), never code
    discount_percent = float(discount_percent)
    if not 0 <= discount_percent <= 100:
        raise ValueError("Discount must be between 0 and 100")
    return amount * (100 - discount_percent) / 100

def isValidPlate(plate):
    if re.match(r"^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}$", plate):
        return True
    else:
        return False

def writeReceipt(booking):
    fd, path = tempfile.mkstemp(suffix=".txt")
    f = os.fdopen(fd, "w")
    f.write("Booking %s: %s for %d days = Rs.%d\n" % (booking["code"], booking["plate"], booking["days"], booking["cost"]))
    f.close()
    os.chmod(path, 0o600)
    return path

def adminLogin(user, password):
    expected = os.environ.get("RENTAL_ADMIN_PASSWORD")
    if not expected or not password:
        return False
    return user == "admin" and hmac.compare_digest(password, expected)

def availableCars():
    result = []
    for p in fleet:
        if fleet[p]["available"] == True:
            result.append(p)
    return result

def main():
    addCar("KA01AB1234", "Swift", 1500)
    addCar("KA02CD5678", "Innova", 3000)
    addCar("KA03EF9999", "Nexon", -500)
    registerCustomer("Ravi", "DL-0420110012345", "9845012345")
    registerCustomer("Meera", "DL-0420110099999", "9845099999")
    print("Rent Swift:", rentCar("KA01AB1234", "Ravi", "2026-11-01", "2026-11-04"))
    print("Rent Swift again:", rentCar("KA01AB1234", "Ravi", "2026-11-02", "2026-11-03"))
    print("Rent Innova:", rentCar("KA02CD5678", "Ravi", "2026-11-10", "2026-11-07"))
    print("Lookup injection:", findCustomer("x' OR '1'='1"))
    print("Extra km charge:", returnCar("KA01AB1234", 420))
    print("Return unknown car:", returnCar("XX00XX0000", 50))
    print("Promo price:", applyPromo(10, 4500))
    print("Plate valid?", isValidPlate("KA01AB1234"))
    print("Licence hash:", licenceHash("DL-0420110012345"))
    print("Admin:", adminLogin("admin", "admin@rent"))
    print("Available:", availableCars())
    print("Receipt saved to:", writeReceipt(bookings[0]))

main()
