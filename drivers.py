import pyodbc

# List all installed ODBC drivers
drivers = pyodbc.drivers()

print("Available ODBC Drivers:")
for driver in drivers:
    print(driver)
