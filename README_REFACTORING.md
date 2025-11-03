# Refactored Discord Bot Project Structure

This project has been refactored from a monolithic `Main.py` file into a modular, maintainable structure.

## Project Structure

```
DiscordBotGrapher/
├── bot/
│   ├── __init__.py
│   └── client.py              # MyClient class with event handlers
├── commands/
│   ├── __init__.py
│   ├── trivia.py              # Trivia-related commands (placeholder)
│   ├── stats.py               # Stats commands (placeholder)
│   ├── gambling.py            # Gambling commands (placeholder)
│   ├── admin.py               # Admin commands (placeholder)
│   ├── graph.py               # Graph commands (placeholder)
│   └── settings.py            # Settings commands (placeholder)
├── handlers/
│   ├── __init__.py
│   ├── message_handler.py     # on_message logic
│   ├── reaction_handler.py    # on_reaction_add logic
│   └── guild_handler.py       # on_guild_join, on_thread_create
├── ui/
│   ├── __init__.py
│   ├── question_ui.py         # Question-related UI components (placeholder)
│   ├── gambling_ui.py         # Gambling UI components (placeholder)
│   ├── settings_ui.py         # Settings UI components (placeholder)
│   └── auction_ui.py          # Auction UI components (placeholder)
├── tasks/
│   ├── __init__.py
│   └── scheduled_tasks.py     # Scheduled tasks
├── utils/
│   ├── __init__.py
│   ├── helpers.py             # Helper functions (sigmoid, numToGrade)
│   ├── auth.py               # Authorization utilities
│   ├── database.py           # Database helper functions
│   ├── queries.py            # Query functions (emojiQuery, Graph, topChat)
│   └── llm.py                # LLM utilities
├── database/
│   └── __init__.py
├── config/
│   └── __init__.py
├── Main.py                    # Original monolithic file (kept for reference)
├── main.py                    # NEW entry point
└── REFACTORING_NOTES.md       # Detailed refactoring notes

```

## Key Changes

### ✅ Completed
- Created folder structure with `__init__.py` files
- Extracted database utilities (`utils/database.py`)
- Extracted helper functions (`utils/helpers.py`, `utils/auth.py`, `utils/queries.py`, `utils/llm.py`)
- Extracted event handlers (`handlers/message_handler.py`, `handlers/reaction_handler.py`, `handlers/guild_handler.py`)
- Extracted scheduled tasks (`tasks/scheduled_tasks.py`)
- Extracted bot client class (`bot/client.py`)
- Created new entry point (`main.py`)

### ⚠️ Placeholders (Need Implementation)
The following files contain placeholders and need to have the actual code extracted from `Main.py`:

- `commands/trivia.py` - Trivia commands (daily-trivia, etc.)
- `commands/stats.py` - Stats commands (stats, inventory, grade-report, leaderboard)
- `commands/gambling.py` - Gambling commands (auction-house, flip)
- `commands/admin.py` - Admin commands (add-authorized-user, etc.)
- `commands/graph.py` - Graph commands (server-graph, most-used-emojis)
- `commands/settings.py` - Settings commands (game-settings-set/get, goofs-settings-set/get)
- `ui/question_ui.py` - Question UI components (QuestionPickButton, QuestionModal, etc.)
- `ui/gambling_ui.py` - Gambling UI components (GamblingButton, GamblingIntroModal, etc.)
- `ui/settings_ui.py` - Settings UI components (ServerSettingsView, PatchNotesModal)
- `ui/auction_ui.py` - Auction UI components (BidModal, OpenBidButton, etc.)

## Next Steps

1. **Extract Commands**: Move each command from `Main.py` to its respective file in `commands/`
   - Each command should use `@client.tree.command()` decorator
   - Import the client from `bot.client` or pass it as a parameter

2. **Extract UI Components**: Move UI components (buttons, modals, views) to `ui/`
   - Ensure proper imports and client references

3. **Update Imports**: Replace all references to functions/classes with their new module paths
   - Update `bot/client.py` to import handlers and commands
   - Update `main.py` to properly initialize everything

4. **Test**: Run the bot and fix any import errors or circular dependencies

## Notes

- The original `Main.py` is kept for reference during migration
- Some functions may need the `client` parameter passed explicitly
- Watch for circular imports - use TYPE_CHECKING or late imports where needed
- The `tasks` module uses a global client reference set by `set_client()`

## Migration Guide

When extracting commands:
1. Find the command in `Main.py` (e.g., `@client.tree.command(name="ping")`)
2. Move it to the appropriate `commands/` file
3. Ensure all imports are correct
4. Register the command in `main.py` or via imports

When extracting UI components:
1. Find the class in `Main.py` (e.g., `class QuestionModal`)
2. Move it to the appropriate `ui/` file
3. Ensure all dependencies are imported
4. Update any references from commands/handlers

