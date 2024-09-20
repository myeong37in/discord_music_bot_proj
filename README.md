Discord bot playing audio with given YouTube video link


### How to set up your own Discord bot

 You'll need to create your own bot to make it run as it's only functional at local environment for now. Follow the steps below
 1. Go to the [Discord Developer Portal](https://discord.com/developers/applications/)
 2. Click "New Application"
 3. In Settings, go to "Bot" and set your bot's icon and username(which will be the actual name of bot)
 4. Reset Token and copy it
 5. Scroll down, enable 'Server Members Intent' and 'Message Content Intent' in 'Privileged Gateway Intents'
 6. In Settings, go to OAuth2
 7. Under Scopes, check the box for 'bot'
 8. In Bot Permissions, select 'Administrator'. It gives the bot full permissions.
 9. Scroll down and click 'Copy' to copy bot invite link
 10. Paste it in your browser address bar, it will give you an option in which server you want to invite the bot(you need administrator rights on the server)
 12. Run the bot program


How to run the program
1. Clone the repository
    ```bash
    git clone <repository_url>
2. Copy '.env.example' to '.env' and fill in the required values(discord bot token which you have copied earlier)
    ```bash
    cp .env.example .env
3. Run main.py in your IDE