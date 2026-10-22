# Custom-IT-Help-Desk-Ticketing-Bot
This bot automates and tracks IT support requests directly within Discord, reducing response times and eliminating lost emails. It features automated ticket creation, status tracking, and a web-based admin dashboard for management.
it-help-desk-bot/
│
├── bot/                 # Main bot code
│   ├── __init__.py
│   ├── bot.py           # Bot setup and event handlers
│   ├── commands.py      # All the bot commands (create_ticket, check_status, etc.)
│   └── database.py      # Functions to interact with the database
│
├── web/                 # Admin web interface
│   ├── templates/       # HTML files for the web pages
│   │   └── dashboard.html
│   ├── static/          # CSS, JavaScript, images
│   └── app.py           # Flask web application code
│
├── database/            # Database scripts
│   └── schema.sql       # SQL commands to create the ticket tables
│
├── .gitignore
├── README.md            # **CRUCIAL: This is your project's documentation!**
└── requirements.txt     # List of Python libraries needed (e.g., discord.py, flask)
