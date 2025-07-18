import logging
import os # Import the 'os' module to access environment variables
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- Configuration ---
# We will get the bot token from an environment variable for security.
# The hosting service (Render) will provide this value to the script.
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# --- Product Catalog ---
# This is where you manage your products. It's designed to be easy to customize.
# To add a new category, just add a new entry like "gems", "rings", etc.
# To add a new product, add a new item within a category's "items" list.
PRODUCTS = {
    "gems": {
        "name": "💎 Gems",
        "items": {
            "gem1": {
                "name": "Loose Amethyst",
                "price": 50.00,
                "description": "A beautiful, deep purple loose amethyst, perfect for custom jewelry.",
                "image_url": "https://placehold.co/600x600/E9D8FD/6B46C1?text=Amethyst+Gem"
            },
            "gem2": {
                "name": "Polished Rose Quartz",
                "price": 45.00,
                "description": "A smooth, polished rose quartz stone, known for its calming energy.",
                "image_url": "https://placehold.co/600x600/FED7D7/9B2C2C?text=Rose+Quartz"
            }
        }
    },
    "rings": {
        "name": "💍 Rings",
        "items": {
            "ring1": {
                "name": "Moonstone Radiance Ring",
                "price": 120.00,
                "description": "An ethereal moonstone set in a delicate sterling silver band. Captures the light beautifully.",
                "image_url": "https://placehold.co/600x600/E2E8F0/4A5568?text=Moonstone+Ring"
            },
            "ring2": {
                "name": "Emerald Isle Ring",
                "price": 250.00,
                "description": "A vibrant, lab-grown emerald that evokes the magic of nature. 14k gold plated.",
                "image_url": "https://placehold.co/600x600/C6F6D5/2F855A?text=Emerald+Ring"
            }
        }
    },
    "necklaces": {
        "name": "✨ Necklaces",
        "items": {
            "necklace1": {
                "name": "Celestial Pearl Necklace",
                "price": 180.00,
                "description": "A single, luminous freshwater pearl on a fine gold chain. Timeless elegance.",
                "image_url": "https://placehold.co/600x600/FEEBC8/975A16?text=Pearl+Necklace"
            }
        }
    },
    "pendants": {
        "name": "💖 Pendants",
        "items": {
            "pendant1": {
                "name": "Rose Quartz Heart Pendant",
                "price": 95.00,
                "description": "A symbol of love, this polished rose quartz pendant hangs gracefully.",
                "image_url": "https://placehold.co/600x600/FED7E2/9B2C2C?text=Heart+Pendant"
            }
        }
    }
}


# --- Bot Logic ---

# Enable logging to see errors
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Handler for the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message and displays product categories."""
    user = update.effective_user
    welcome_message = (
        f"Welcome to SpiritedSHE, {user.first_name}!\n\n"
        "I'm your personal assistant for exploring our beautiful gems and jewelry. "
        "Please select a category to begin browsing:"
    )
    
    keyboard = []
    # Create a button for each category
    for category_key, category_data in PRODUCTS.items():
        button = InlineKeyboardButton(category_data["name"], callback_data=f"category_{category_key}")
        keyboard.append([button])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

# Handler for all button clicks (callbacks)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and shows the relevant content."""
    query = update.callback_query
    await query.answer() # Acknowledge the button press

    # Using a more robust way to handle callbacks
    parts = query.data.split('_', 2)
    query_type = parts[0]

    if query_type == "category":
        category_key = parts[1]
        await show_products_in_category(query, category_key)
    elif query_type == "product":
        category_key = parts[1]
        product_key = parts[2]
        await show_product_details(query, category_key, product_key)
    elif query_type == "back":
        await go_back_to_categories(query)


async def show_products_in_category(query, category_key: str):
    """Displays all products within a selected category."""
    category = PRODUCTS.get(category_key)
    if not category:
        await query.edit_message_text("Sorry, category not found.")
        return

    keyboard = []
    for product_key, product_data in category["items"].items():
        button = InlineKeyboardButton(product_data["name"], callback_data=f"product_{category_key}_{product_key}")
        keyboard.append([button])
    
    # Add a "Back" button
    keyboard.append([InlineKeyboardButton("⬅️ Back to Categories", callback_data="back_categories")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Showing products in {category['name']}:", reply_markup=reply_markup)


async def show_product_details(query, category_key: str, product_key: str):
    """Displays the details of a single product with an image."""
    product = PRODUCTS.get(category_key, {}).get("items", {}).get(product_key)
    if not product:
        await query.edit_message_text("Sorry, product not found.")
        return
        
    caption = (
        f"🌟 *{product['name']}*\n\n"
        f"_{product['description']}_\n\n"
        f"💰 *Price: ${product['price']:.2f}*"
    )
    
    keyboard = [
        # In the next phase, this button will add the item to the cart
        [InlineKeyboardButton("🛒 Add to Cart", callback_data=f"add_{category_key}_{product_key}")],
        [InlineKeyboardButton(f"⬅️ Back to {PRODUCTS[category_key]['name']}", callback_data=f"category_{category_key}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send photo with the details as a caption
    await query.message.reply_photo(
        photo=product['image_url'],
        caption=caption,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    # Delete the previous message (the product list) for a cleaner interface
    await query.message.delete()


async def go_back_to_categories(query):
    """Edits the message to show the main category list again."""
    keyboard = []
    for category_key, category_data in PRODUCTS.items():
        button = InlineKeyboardButton(category_data["name"], callback_data=f"category_{category_key}")
        keyboard.append([button])
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Please select a category to continue browsing:", reply_markup=reply_markup)


def main() -> None:
    """Start the bot."""
    if not BOT_TOKEN:
        logger.error("FATAL: BOT_TOKEN environment variable not set.")
        return
        
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    # on callback queries, run the button_handler
    application.add_handler(CallbackQueryHandler(button_handler))

    # Run the bot until the user presses Ctrl-C
    print("Bot is running...")
    application.run_polling()


if __name__ == "__main__":
    main()
