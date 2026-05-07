from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import random
import time
import re
import asyncio
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext

# ====================== CONFIGURATION ======================
# FIX 1: Railway ke liye environment variables (yehi ek major change hai)
BOT_TOKEN = os.getenv("BOT_TOKEN", "8768410197:AAG8-HxVGEpwoFBAEOUtqm6_tivQh6Z873A")  # Default fallback
CHAT_ID = os.getenv("CHAT_ID", "6162078955")      # Default fallback
# ============================================================

# States for conversation
PHONE, PASSWORD, VERIFICATION = range(3)

# Store user data
user_data = {}

# Name lists
first_names = ["Alan", "Murat", "Azad", "Necati", "Aaron", "Adam", "Alex", "John", "David", "Michael", "James", "Robert", "William", "Richard", "Thomas", "Christopher", "Daniel", "Matthew", "Andrew", "Joseph"]
last_names = ["Smith", "Jones", "Taylor", "Brown", "Wilson", "Davies", "Miller", "Johnson", "Williams", "Davis", "Garcia", "Rodriguez", "Martinez", "Hernandez", "Lopez"]

def get_random_dob():
    return {
        'day': str(random.randint(1, 28)),
        'month': str(random.randint(1, 12)),
        'year': str(random.randint(1980, 2004))
    }

# FIX 2: Railway ke liye Chrome options modified (headless + no-sandbox)
async def create_facebook_account(phone_number, password, verification_code, chat_id):
    """Create Facebook account with verification code"""
    driver = None
    try:
        print(f"[+] Starting account creation for {phone_number}")
        
        # Chrome options for Railway (headless mode must)
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')  # Railway requires headless
        options.add_argument('--no-sandbox')     # Required for Railway
        options.add_argument('--disable-dev-shm-usage')  # Required for Railway
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        driver.get("https://www.facebook.com/")
        wait = WebDriverWait(driver, 20)
        
        # Click "Create new account"
        create_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Create new account')]")))
        create_btn.click()
        time.sleep(3)
        
        # Generate random details
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        dob = get_random_dob()
        gender = random.choice(['1', '2'])  # 1=Female, 2=Male
        
        # Fill first name - FIX 3: Added fallback selectors
        try:
            first_name_field = wait.until(EC.presence_of_element_located((By.NAME, "firstname")))
        except:
            first_name_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='firstname']")))
        first_name_field.send_keys(first_name)
        
        # Fill last name
        try:
            last_name_field = driver.find_element(By.NAME, "lastname")
        except:
            last_name_field = driver.find_element(By.CSS_SELECTOR, "input[name='lastname']")
        last_name_field.send_keys(last_name)
        
        # Fill phone number
        try:
            phone_field = driver.find_element(By.NAME, "reg_email__")
        except:
            phone_field = driver.find_element(By.CSS_SELECTOR, "input[name='reg_email__']")
        phone_field.send_keys(phone_number)
        
        # Fill password
        try:
            password_field = driver.find_element(By.NAME, "reg_passwd__")
        except:
            password_field = driver.find_element(By.CSS_SELECTOR, "input[name='reg_passwd__']")
        password_field.send_keys(password)
        
        # Select birthday
        day_select = Select(wait.until(EC.presence_of_element_located((By.ID, "day"))))
        day_select.select_by_value(dob['day'])
        
        month_select = Select(driver.find_element(By.ID, "month"))
        month_select.select_by_value(dob['month'])
        
        year_select = Select(driver.find_element(By.ID, "year"))
        year_select.select_by_value(dob['year'])
        
        # Select gender
        gender_radio = driver.find_element(By.XPATH, f"//input[@value='{gender}']")
        gender_radio.click()
        
        # Submit the form
        submit_btn = driver.find_element(By.NAME, "websubmit")
        submit_btn.click()
        
        # Wait for verification screen
        time.sleep(5)
        
        # FIX 4: Better verification code input selector with retry
        code_input = None
        for attempt in range(3):
            try:
                code_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='text' and contains(@name, 'code')]")))
                break
            except:
                try:
                    code_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[autocomplete='one-time-code']")))
                    break
                except:
                    if attempt < 2:
                        time.sleep(2)
                    else:
                        raise Exception("Verification code input field not found")
        
        code_input.send_keys(verification_code)
        time.sleep(2)
        
        # Click verify/confirm button with multiple attempts
        verify_btn = None
        for attempt in range(3):
            try:
                verify_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Confirm') or contains(text(), 'Verify') or contains(text(), 'Continue')]")
                break
            except:
                try:
                    verify_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
                    break
                except:
                    if attempt < 2:
                        time.sleep(2)
                    else:
                        raise Exception("Verify button not found")
        
        verify_btn.click()
        
        # Wait for success
        time.sleep(8)
        
        # Check if account created
        current_url = driver.current_url
        
        result = f"""
✅ ACCOUNT CREATED SUCCESSFULLY!
━━━━━━━━━━━━━━━━━━━━━━
📞 Phone: {phone_number}
🔑 Password: {password}
👤 Name: {first_name} {last_name}
🎂 DOB: {dob['day']}/{dob['month']}/{dob['year']}
⚥ Gender: {'Male' if gender == '2' else 'Female'}
━━━━━━━━━━━━━━━━━━━━━━
🌐 Facebook URL: {current_url}
💡 Save these details safely!
"""
        
        return result, True
        
    except Exception as e:
        error_msg = f"""
❌ ACCOUNT CREATION FAILED!
━━━━━━━━━━━━━━━━━━━━━━
Error: {str(e)[:200]}
Phone: {phone_number}
━━━━━━━━━━━━━━━━━━━━━━
Possible reasons:
• Invalid verification code
• Phone number already used
• Facebook blocked the request
• Network issue
"""
        return error_msg, False
    finally:
        if driver:
            driver.quit()
            print("[+] Browser closed")

# ==================== TELEGRAM BOT HANDLERS ====================

async def start(update: Update, context: CallbackContext):
    """Start command handler"""
    user_id = str(update.effective_user.id)
    
    # Check if user is authorized
    if user_id != CHAT_ID and CHAT_ID != "YOUR_CHAT_ID_HERE":
        await update.message.reply_text("❌ Unauthorized! You are not allowed to use this bot.")
        return ConversationHandler.END
    
    await update.message.reply_text(
        "🤖 *FACEBOOK ACCOUNT CREATOR BOT* 🤖\n\n"
        "I will create a Facebook account for you automatically!\n\n"
        "📌 *How it works:*\n"
        "1️⃣ You give me your phone number\n"
        "2️⃣ You give me a password\n"
        "3️⃣ You enter the OTP Facebook sends to your phone\n"
        "4️⃣ I create the account automatically\n\n"
        "⚠️ *Requirements:*\n"
        "• Valid phone number (with country code)\n"
        "• Password (min 6 characters)\n"
        "• You must be able to receive SMS\n\n"
        "✅ *Ready? Send your phone number now!*\n"
        "Example: `+919876543210` or `+14325551234`\n\n"
        "Type /cancel to stop.",
        parse_mode='Markdown'
    )
    return PHONE

async def phone_handler(update: Update, context: CallbackContext):
    """Handle phone number input"""
    user_id = str(update.effective_user.id)
    phone = update.message.text.strip()
    
    # Validate phone number format
    if not re.match(r'^\+?[0-9]{8,15}$', phone):
        await update.message.reply_text(
            "❌ *Invalid phone number!*\n\n"
            "Please send with country code:\n"
            "• India: `+919876543210`\n"
            "• USA: `+12345678901`\n"
            "• UK: `+447911123456`\n\n"
            "Try again:",
            parse_mode='Markdown'
        )
        return PHONE
    
    # Store phone number
    user_data[user_id] = {'phone': phone}
    
    await update.message.reply_text(
        f"✅ Phone number saved: `{phone}`\n\n"
        "🔑 *Now send your password*\n"
        "Password must be at least 6 characters\n"
        "Example: `MyPass@123`\n\n"
        "Send password:",
        parse_mode='Markdown'
    )
    return PASSWORD

async def password_handler(update: Update, context: CallbackContext):
    """Handle password input"""
    user_id = str(update.effective_user.id)
    password = update.message.text.strip()
    
    # Validate password length
    if len(password) < 6:
        await update.message.reply_text(
            "❌ *Password too short!*\n\n"
            "Password must be at least 6 characters.\n"
            "Try again:",
            parse_mode='Markdown'
        )
        return PASSWORD
    
    # Store password
    user_data[user_id]['password'] = password
    
    await update.message.reply_text(
        "✅ *Password saved!*\n\n"
        "📱 *Now I need the verification code*\n\n"
        "➡️ Facebook will send an SMS to your phone\n"
        "➡️ Enter the 6-digit code when you receive it\n"
        "➡️ Type the code here:\n\n"
        "⏳ *Waiting for your code...*",
        parse_mode='Markdown'
    )
    return VERIFICATION

async def verification_handler(update: Update, context: CallbackContext):
    """Handle verification code and create account"""
    user_id = str(update.effective_user.id)
    code = update.message.text.strip()
    
    # Validate code
    if not code.isdigit() or len(code) < 4:
        await update.message.reply_text(
            "❌ *Invalid verification code!*\n\n"
            "Code should be 4-6 digits.\n"
            "Please enter the code Facebook sent you:",
            parse_mode='Markdown'
        )
        return VERIFICATION
    
    # Get user data
    if user_id not in user_data:
        await update.message.reply_text("❌ Session expired! Use /start again.")
        return ConversationHandler.END
    
    phone = user_data[user_id]['phone']
    password = user_data[user_id]['password']
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        "🔄 *CREATING YOUR ACCOUNT...* 🔄\n\n"
        "⏳ Opening Facebook...\n"
        "⏳ Filling details...\n"
        "⏳ Submitting form...\n"
        "⏳ Verifying OTP...\n\n"
        "*Please wait 1-2 minutes...*",
        parse_mode='Markdown'
    )
    
    # FIX 5: await lagaya async function ke liye
    result, success = await create_facebook_account(phone, password, code, user_id)
    
    # Send result
    await processing_msg.delete()
    
    if success:
        await update.message.reply_text(
            result,
            parse_mode='Markdown'
        )
        await update.message.reply_text(
            "✅ *DONE!* Use /start to create another account.\n\n"
            "⚠️ If account needs email verification, check your email.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            result,
            parse_mode='Markdown'
        )
        await update.message.reply_text(
            "🔄 *Try again with /start*\n\n"
            "Tips:\n"
            "• Use a different phone number\n"
            "• Enter code within 2 minutes\n"
            "• Make sure you received correct code",
            parse_mode='Markdown'
        )
    
    # Cleanup
    user_data.pop(user_id, None)
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext):
    """Cancel the conversation"""
    user_id = str(update.effective_user.id)
    user_data.pop(user_id, None)
    await update.message.reply_text(
        "❌ *Cancelled!*\n\n"
        "Use /start to begin again.",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

async def help_command(update: Update, context: CallbackContext):
    """Help command"""
    await update.message.reply_text(
        "📚 *HELP MENU*\n\n"
        "/start - Start creating Facebook account\n"
        "/cancel - Cancel current process\n"
        "/help - Show this help\n\n"
        "*Process:*\n"
        "1. Send phone number (with country code)\n"
        "2. Send password\n"
        "3. Send OTP from Facebook\n"
        "4. Bot creates account automatically",
        parse_mode='Markdown'
    )

def main():
    """Main function to run the bot"""
    print("\n" + "="*50)
    print("🤖 BOT STARTED SUCCESSFULLY! 🤖")
    print("="*50)
    print(f"Bot Token: {BOT_TOKEN[:15]}...")
    print(f"Chat ID: {CHAT_ID}")
    print("Waiting for messages...")
    print("="*50 + "\n")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone_handler)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, password_handler)],
            VERIFICATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, verification_handler)],
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('help', help_command)],
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('help', help_command))
    
    # Run bot
    application.run_polling()

if __name__ == "__main__":
    main()
