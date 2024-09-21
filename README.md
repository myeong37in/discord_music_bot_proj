Discord bot playing audio with given YouTube video link

### How to use it
 This bot is run in Amazon EC2.
 Invite it to your server [Invite Link](https://discord.com/oauth2/authorize?client_id=1286312263631769620&permissions=35184375252992&integration_type=0&scope=bot)
 Enter '!manual' to see user manual
 BUT you can also establish your own local environment to run it. The way you can do it is written below.
 
### How to set up your own Discord bot

 If you want to run it on your local environment, follow the steps below
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

How to download and run the program
1. Clone the repository
    ```bash
    git clone <repository_url>
2. Copy '.env.example' to '.env' and fill in the required values(discord bot token which you have copied earlier)
    ```bash
    cp .env.example .env
3. Run main.py in your IDE