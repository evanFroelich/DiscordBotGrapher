"""
REFACTORING SUMMARY

This document outlines the new modular structure for the Discord bot.

FOLDER STRUCTURE:
├── bot/
│   ├── __init__.py
│   └── client.py              # MyClient class with event handlers
├── commands/
│   ├── __init__.py
│   ├── trivia.py              # Trivia-related commands
│   ├── stats.py               # Stats commands
│   ├── gambling.py            # Gambling commands
│   ├── admin.py               # Admin commands
│   ├── graph.py               # Graph commands
│   └── settings.py            # Settings commands
├── handlers/
│   ├── __init__.py
│   ├── message_handler.py     # on_message logic
│   ├── reaction_handler.py     # on_reaction_add logic
│   └── guild_handler.py       # on_guild_join, on_thread_create
├── ui/
│   ├── __init__.py
│   ├── question_ui.py         # Question-related UI components
│   ├── gambling_ui.py          # Gambling UI components
│   └── settings_ui.py         # Settings UI components
├── tasks/
│   ├── __init__.py
│   └── scheduled_tasks.py     # Scheduled tasks
├── utils/
│   ├── __init__.py
│   ├── helpers.py             # Helper functions (sigmoid, numToGrade)
│   ├── auth.py                # Authorization utilities
│   ├── database.py            # Database helper functions
│   ├── queries.py             # Query functions (emojiQuery, Graph, topChat)
│   └── llm.py                 # LLM utilities
├── database/
│   └── __init__.py
├── config/
│   └── __init__.py
└── main.py                    # Entry point

NOTE: Due to the large size of Main.py (~3000 lines), this refactoring extracts the 
core utilities and handlers. The remaining components (commands, UI components) should 
be extracted following the same pattern:

1. Commands should be in commands/ folder, each command file should register 
   commands using @client.tree.command decorator
2. UI components (buttons, modals, views) should be in ui/ folder
3. The bot client in bot/client.py should import and register commands/handlers
4. main.py should initialize the bot and run it

This structure provides:
- Better organization and maintainability
- Easier testing of individual components
- Reduced circular dependencies
- Clear separation of concerns
"""

