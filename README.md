# Watch your portfolio tank from the comfort of your desktop environment

🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀

# Setup

## 0. Install PostgreSQL (and pgAdmin)

## 1. Clone the repo

## 2. Create a file named `.env` in the project root

File template:
```
# Database user
DB_USER=""

# Database password
DB_PASS=""

# Database hostname
DB_HOST=""

# Database port
DB_PORT=""

# Database name
DB_NAME="simple_crypto"

# Coinmarketcap API key
COINMARKETCAP_API_KEY=""

# Alphavantage API key
ALPHAVANTAGE_API_KEY=""
```

Enter the values that you set for your DB and API keys.

## 3. Install dependencies (suggested: conda base environment)

Note that if you plan to run the Windows service that fetches the data, you may also need to create all of the necessary `%path%` environmental variables (that point to additional libraries) and get the right binaries of the `psycopg2` and `pywin32` libraries.

### Fix 'Error pywin32 missing .dll'

> pip install pywin32

> python Scripts/pywin32_postinstall.py -install

> pip install psycopg2-binary

## 4. Working with services

Start PowerShell with admin privileges and navigate to project root
> cd src

> python ServiceSimpleCryptoWatch.py --startup auto install 

You can also change the startup type in `Windows Services`. Example: Find the service by the name of `SimpleCryptoWatch` and change the `Startup Type` to `Automatic`.

Useful commands:
```
# Installing the service
python ServiceSimpleCryptoWatch.py install

# Let the service start automatically 
python ServiceSimpleCryptoWatch.py --startup auto install 
 
# Starting the service
python ServiceSimpleCryptoWatch.py start

# Restarting the service
python ServiceSimpleCryptoWatch.py restart
 
# Stopping the service
python ServiceSimpleCryptoWatch.py stop
 
# Removing the service
python ServiceSimpleCryptoWatch.py remove
 ```

## 5. Start the GUI by calling MainForm.py

# Usage

The program supports multiple users. Passwords are hashed and salted. Each user can have multiple collections which represent different portfolios (for instance: DeFi, memecoins, ...). Coins can be added and removed from each collection. You can change the amount of each crpyto you have in a specific collection. You can also view price changes for each crypto by inspecting the crypto price graph. Click on random stuff and find out more.

# Disclaimer

This was a fun side project. In order to meet my own deadlines I had to cut some corners with code design so it may not always follow best practices (especially in `MainForm.py`). If I ever revisit it, I'll probably implement the frontend in PyQt5.