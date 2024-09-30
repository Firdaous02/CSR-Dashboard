**KPI Data Centralization Web Application**

This project is a web application developed during my internship at TE Connectivity.

To Configure the Database Connection:
1. Go to the db.py file in the project directory.
2. Replace the connection string with your own SQL Server credentials.

The connection string looks like this:
```python
     engine = create_engine('mssql+pyodbc://@localhost/CSIData?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes')
```
   - Replace the connection string with your own SQL Server credentials. Update the following:
     - `localhost`: The address of your SQL Server instance
     - `CSIData`: Your database name
     - `ODBC+Driver+17+for+SQL+Server`: If necessary, replace this with the driver version that matches your environment.
     - `trusted_connection=yes`: If using SQL Server authentication instead of Windows Authentication, remove this and add `username:password@` before the server address, like this:
       ```python
       engine = create_engine('mssql+pyodbc://username:password@server_address/database_name?driver=ODBC+Driver+17+for+SQL+Server')
       ```

