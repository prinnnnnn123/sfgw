import streamlit as st
import time
import threading
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import database as db

st.set_page_config(
    page_title="FB E2EE by Prince Malhotra",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded"
)

custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    
    * {
        font-family: 'Poppins', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    .main-header h1 {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    .main-header p {
        color: rgba(255,255,255,0.9);
        font-size: 1.1rem;
        margin-top: 0.5rem;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }
    
    .login-box {
        background: white;
        padding: 3rem;
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.1);
        max-width: 500px;
        margin: 2rem auto;
    }
    
    .success-box {
        background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 1rem 0;
    }
    
    .error-box {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 1rem 0;
    }
    
    .footer {
        text-align: center;
        padding: 2rem;
        color: #667eea;
        font-weight: 600;
        margin-top: 3rem;
    }
    
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stNumberInput>div>div>input {
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        padding: 0.75rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
    }
    
    .info-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
    }
    
    .log-container {
        background: #1e1e1e;
        color: #00ff00;
        padding: 1rem;
        border-radius: 10px;
        font-family: 'Courier New', monospace;
        max-height: 400px;
        overflow-y: auto;
    }
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'automation_running' not in st.session_state:
    st.session_state.automation_running = False
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'message_count' not in st.session_state:
    st.session_state.message_count = 0

class AutomationState:
    def __init__(self):
        self.running = False
        self.message_count = 0
        self.logs = []
        self.message_rotation_index = 0

if 'automation_state' not in st.session_state:
    st.session_state.automation_state = AutomationState()

if 'auto_start_checked' not in st.session_state:
    st.session_state.auto_start_checked = False

def log_message(msg, automation_state=None):
    timestamp = time.strftime("%H:%M:%S")
    formatted_msg = f"[{timestamp}] {msg}"
    
    if automation_state:
        automation_state.logs.append(formatted_msg)
    else:
        if 'logs' in st.session_state:
            st.session_state.logs.append(formatted_msg)

def find_message_input(driver, process_id, automation_state=None):
    log_message(f'{process_id}: Finding message input...', automation_state)
    time.sleep(10)
    
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
    except Exception:
        pass
    
    try:
        page_title = driver.title
        page_url = driver.current_url
        log_message(f'{process_id}: Page Title: {page_title}', automation_state)
        log_message(f'{process_id}: Page URL: {page_url}', automation_state)
    except Exception as e:
        log_message(f'{process_id}: Could not get page info: {e}', automation_state)
    
    message_input_selectors = [
        'div[contenteditable="true"][role="textbox"]',
        'div[contenteditable="true"][data-lexical-editor="true"]',
        'div[aria-label*="message" i][contenteditable="true"]',
        'div[aria-label*="Message" i][contenteditable="true"]',
        'div[contenteditable="true"][spellcheck="true"]',
        '[role="textbox"][contenteditable="true"]',
        'textarea[placeholder*="message" i]',
        'div[aria-placeholder*="message" i]',
        'div[data-placeholder*="message" i]',
        '[contenteditable="true"]',
        'textarea',
        'input[type="text"]'
    ]
    
    log_message(f'{process_id}: Trying {len(message_input_selectors)} selectors...', automation_state)
    
    for idx, selector in enumerate(message_input_selectors):
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            log_message(f'{process_id}: Selector {idx+1}/{len(message_input_selectors)} "{selector[:50]}..." found {len(elements)} elements', automation_state)
            
            for element in elements:
                try:
                    if element.is_displayed() and element.size['width'] > 0 and element.size['height'] > 0:
                        element.click()
                        time.sleep(1)
                        
                        is_editable = driver.execute_script("""
                            return arguments[0].contentEditable === 'true' || 
                                   arguments[0].tagName === 'TEXTAREA' || 
                                   arguments[0].tagName === 'INPUT';
                        """, element)
                        
                        if is_editable:
                            element_text = driver.execute_script("return arguments[0].placeholder || arguments[0].getAttribute('aria-label') || arguments[0].getAttribute('aria-placeholder') || '';", element).lower()
                            
                            keywords = ['message', 'write', 'type', 'send', 'chat', 'msg', 'reply', 'text']
                            if any(keyword in element_text for keyword in keywords):
                                log_message(f'{process_id}: Found message input with text: {element_text[:50]}', automation_state)
                                return element
                            elif selector == '[contenteditable="true"]' or selector == 'textarea':
                                log_message(f'{process_id}: Using fallback editable element', automation_state)
                                return element
                except Exception as e:
                    continue
        except Exception as e:
            continue
    
    try:
        page_source = driver.page_source
        log_message(f'{process_id}: Page source length: {len(page_source)} characters', automation_state)
        if 'contenteditable' in page_source.lower():
            log_message(f'{process_id}: Page contains contenteditable elements', automation_state)
        else:
            log_message(f'{process_id}: No contenteditable elements found in page', automation_state)
    except Exception:
        pass
    
    return None

def setup_browser(automation_state=None):
    log_message('Setting up Chrome browser...', automation_state)
    
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
    
    chromium_paths = [
        '/usr/bin/chromium',
        '/usr/bin/chromium-browser',
        '/usr/bin/google-chrome',
        '/usr/bin/chrome'
    ]
    
    for chromium_path in chromium_paths:
        if Path(chromium_path).exists():
            chrome_options.binary_location = chromium_path
            log_message(f'Found Chromium at: {chromium_path}', automation_state)
            break
    
    chromedriver_paths = [
        '/usr/bin/chromedriver',
        '/usr/local/bin/chromedriver'
    ]
    
    driver_path = None
    for driver_candidate in chromedriver_paths:
        if Path(driver_candidate).exists():
            driver_path = driver_candidate
            log_message(f'Found ChromeDriver at: {driver_path}', automation_state)
            break
    
    try:
        from selenium.webdriver.chrome.service import Service
        
        if driver_path:
            service = Service(executable_path=driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            log_message('Chrome started with detected ChromeDriver!', automation_state)
        else:
            driver = webdriver.Chrome(options=chrome_options)
            log_message('Chrome started with default driver!', automation_state)
        
        driver.set_window_size(1920, 1080)
        log_message('Chrome browser setup completed successfully!', automation_state)
        return driver
    except Exception as error:
        log_message(f'Browser setup failed: {error}', automation_state)
        raise error

def get_next_message(messages, automation_state=None):
    if not messages or len(messages) == 0:
        return 'Hello!'
    
    if automation_state:
        message = messages[automation_state.message_rotation_index % len(messages)]
        automation_state.message_rotation_index += 1
    else:
        message = messages[0]
    
    return message

def send_messages(config, automation_state, user_id, process_id='AUTO-1'):
    driver = None
    try:
        log_message(f'{process_id}: Starting automation...', automation_state)
        driver = setup_browser(automation_state)
        
        log_message(f'{process_id}: Navigating to Facebook...', automation_state)
        driver.get('https://www.facebook.com/')
        time.sleep(8)
        
        if config['cookies'] and config['cookies'].strip():
            log_message(f'{process_id}: Adding cookies...', automation_state)
            cookie_array = config['cookies'].split(';')
            for cookie in cookie_array:
                cookie_trimmed = cookie.strip()
                if cookie_trimmed:
                    first_equal_index = cookie_trimmed.find('=')
                    if first_equal_index > 0:
                        name = cookie_trimmed[:first_equal_index].strip()
                        value = cookie_trimmed[first_equal_index + 1:].strip()
                        try:
                            driver.add_cookie({
                                'name': name,
                                'value': value,
                                'domain': '.facebook.com',
                                'path': '/'
                            })
                        except Exception:
                            pass
        
        if config['chat_id']:
            chat_id = config['chat_id'].strip()
            log_message(f'{process_id}: Opening conversation {chat_id}...', automation_state)
            driver.get(f'https://www.facebook.com/messages/t/{chat_id}')
        else:
            log_message(f'{process_id}: Opening messages...', automation_state)
            driver.get('https://www.facebook.com/messages')
        
        time.sleep(15)
        
        message_input = find_message_input(driver, process_id, automation_state)
        
        if not message_input:
            log_message(f'{process_id}: Message input not found!', automation_state)
            automation_state.running = False
            db.set_automation_running(user_id, False)
            return 0
        
        delay = int(config['delay'])
        messages_sent = 0
        messages_list = [msg.strip() for msg in config['messages'].split('\n') if msg.strip()]
        
        if not messages_list:
            messages_list = ['Hello!']
        
        while automation_state.running:
            base_message = get_next_message(messages_list, automation_state)
            
            if config['name_prefix']:
                message_to_send = f"{config['name_prefix']} {base_message}"
            else:
                message_to_send = base_message
            
            try:
                message_input.click()
                time.sleep(0.5)
                
                driver.execute_script("""
                    const element = arguments[0];
                    const message = arguments[1];
                    
                    element.focus();
                    element.click();
                    
                    if (element.tagName === 'DIV') {
                        element.textContent = message;
                        element.innerHTML = message;
                    } else {
                        element.value = message;
                    }
                    
                    element.dispatchEvent(new Event('input', { bubbles: true }));
                    element.dispatchEvent(new Event('change', { bubbles: true }));
                    element.dispatchEvent(new InputEvent('input', { bubbles: true, data: message }));
                """, message_input, message_to_send)
                
                time.sleep(1)
                
                sent = driver.execute_script("""
                    const sendButtons = document.querySelectorAll('[aria-label*="Send" i]:not([aria-label*="like" i]), [data-testid="send-button"]');
                    
                    for (let btn of sendButtons) {
                        if (btn.offsetParent !== null) {
                            btn.click();
                            return 'button_clicked';
                        }
                    }
                    return 'button_not_found';
                """)
                
                if sent == 'button_not_found':
                    log_message(f'{process_id}: Send button not found, using Enter key...', automation_state)
                    driver.execute_script("""
                        const element = arguments[0];
                        element.focus();
                        
                        const events = [
                            new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }),
                            new KeyboardEvent('keypress', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }),
                            new KeyboardEvent('keyup', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true })
                        ];
                        
                        events.forEach(event => element.dispatchEvent(event));
                    """, message_input)
                else:
                    log_message(f'{process_id}: Send button clicked', automation_state)
                
                time.sleep(1)
                
                messages_sent += 1
                automation_state.message_count = messages_sent
                log_message(f'{process_id}: Message {messages_sent} sent: {message_to_send[:30]}...', automation_state)
                
                time.sleep(delay)
                
            except Exception as e:
                log_message(f'{process_id}: Error sending message: {str(e)}', automation_state)
                break
        
        log_message(f'{process_id}: Automation stopped! Total messages sent: {messages_sent}', automation_state)
        automation_state.running = False
        db.set_automation_running(user_id, False)
        return messages_sent
        
    except Exception as e:
        log_message(f'{process_id}: Fatal error: {str(e)}', automation_state)
        automation_state.running = False
        db.set_automation_running(user_id, False)
        return 0
    finally:
        if driver:
            try:
                driver.quit()
                log_message(f'{process_id}: Browser closed', automation_state)
            except:
                pass

def start_automation(user_config, user_id):
    automation_state = st.session_state.automation_state
    
    if automation_state.running:
        return
    
    automation_state.running = True
    automation_state.message_count = 0
    automation_state.logs = []
    
    db.set_automation_running(user_id, True)
    
    thread = threading.Thread(target=send_messages, args=(user_config, automation_state, user_id))
    thread.daemon = True
    thread.start()

def stop_automation(user_id):
    st.session_state.automation_state.running = False
    db.set_automation_running(user_id, False)

def monitor_and_lock_group(lock_config, lock_state, user_id):
    """Monitor group name and nicknames, auto-revert any changes"""
    driver = None
    try:
        log_message('LOCK: Starting Group Name & Nickname Lock System...', lock_state)
        driver = setup_browser(lock_state)
        
        log_message('LOCK: Navigating to Facebook...', lock_state)
        driver.get('https://www.facebook.com/')
        time.sleep(8)
        
        if lock_config['cookies'] and lock_config['cookies'].strip():
            log_message('LOCK: Adding cookies...', lock_state)
            cookie_array = lock_config['cookies'].split(';')
            for cookie in cookie_array:
                cookie_trimmed = cookie.strip()
                if cookie_trimmed:
                    first_equal_index = cookie_trimmed.find('=')
                    if first_equal_index > 0:
                        name = cookie_trimmed[:first_equal_index].strip()
                        value = cookie_trimmed[first_equal_index + 1:].strip()
                        try:
                            driver.add_cookie({
                                'name': name,
                                'value': value,
                                'domain': '.facebook.com',
                                'path': '/'
                            })
                        except Exception:
                            pass
        
        if not lock_config['chat_id']:
            log_message('LOCK: Group ID required!', lock_state)
            lock_state.running = False
            db.set_lock_enabled(user_id, False)
            return
        
        chat_id = lock_config['chat_id'].strip()
        log_message(f'LOCK: Opening group {chat_id}...', lock_state)
        driver.get(f'https://www.facebook.com/messages/t/{chat_id}')
        time.sleep(10)
        
        check_count = 0
        while lock_state.running:
            check_count += 1
            log_message(f'LOCK: Check #{check_count} - Monitoring group...', lock_state)
            
            updated_lock_config = db.get_lock_config(user_id)
            if updated_lock_config:
                lock_config = updated_lock_config
            
            try:
                current_group_name = driver.execute_script("""
                    const titleElements = document.querySelectorAll('h1, [role="heading"]');
                    for (let elem of titleElements) {
                        if (elem.textContent && elem.textContent.trim() && elem.offsetParent !== null) {
                            return elem.textContent.trim();
                        }
                    }
                    return null;
                """)
                
                if current_group_name and lock_config.get('locked_group_name'):
                    if current_group_name != lock_config['locked_group_name']:
                        log_message(f'LOCK: ⚠️ Group name changed! Current: "{current_group_name}" → Reverting to: "{lock_config["locked_group_name"]}"', lock_state)
                        revert_group_name(driver, lock_config['locked_group_name'], lock_state)
                    else:
                        log_message(f'LOCK: ✅ Group name locked: "{current_group_name}"', lock_state)
                
                if lock_config.get('locked_nicknames') and check_count % 3 == 0:
                    log_message(f'LOCK: Checking {len(lock_config["locked_nicknames"])} locked nickname(s)...', lock_state)
                    for member_id, nickname in lock_config['locked_nicknames'].items():
                        try:
                            apply_member_nickname(driver, member_id, nickname, lock_state)
                            time.sleep(1)
                        except Exception as e:
                            log_message(f'LOCK: Error checking nickname for {member_id}: {str(e)}', lock_state)
                
            except Exception as e:
                log_message(f'LOCK: Error monitoring group: {str(e)}', lock_state)
            
            time.sleep(5)
        
        log_message('LOCK: Lock system stopped!', lock_state)
        lock_state.running = False
        db.set_lock_enabled(user_id, False)
        
    except Exception as e:
        log_message(f'LOCK: Fatal error: {str(e)}', lock_state)
        lock_state.running = False
        db.set_lock_enabled(user_id, False)
    finally:
        if driver:
            try:
                driver.quit()
                log_message('LOCK: Browser closed', lock_state)
            except:
                pass

def revert_group_name(driver, locked_name, lock_state):
    """Revert group name to locked value"""
    try:
        log_message(f'LOCK: Reverting group name to "{locked_name}"...', lock_state)
        
        info_clicked = driver.execute_script("""
            // Only use aria-label method - no positional fallback
            const buttons = document.querySelectorAll('[role="button"], button, a[role="button"]');
            for (let btn of buttons) {
                const ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();
                const rect = btn.getBoundingClientRect();
                
                // Must be in header area (top 120px) and visible
                if (rect.top < 120 && btn.offsetParent !== null) {
                    // Comprehensive multilingual info button patterns
                    if (ariaLabel.includes('conversation information') || 
                        ariaLabel.includes('group information') ||
                        ariaLabel.includes('chat information') ||
                        ariaLabel.includes('thread information') ||
                        ariaLabel.includes('conversation details') ||
                        ariaLabel.includes('group details') ||
                        ariaLabel.includes('chat details') ||
                        // Hindi
                        ariaLabel.includes('बातचीत की जानकारी') || 
                        ariaLabel.includes('समूह की जानकारी') ||
                        ariaLabel.includes('चैट की जानकारी') ||
                        // Common short forms
                        (ariaLabel.includes('info') && !ariaLabel.includes('notifications'))) {
                        btn.click();
                        return ariaLabel;
                    }
                }
            }
            
            return false;
        """)
        
        time.sleep(3)
        
        if info_clicked:
            log_message(f'LOCK: Info button clicked using {info_clicked}, verifying panel...', lock_state)
            
            panel_verified = driver.execute_script("""
                // Verify specifically the info panel/sidebar opened (not just any dialog)
                // Look for elements that indicate the info/details panel
                
                // Check for common info panel indicators
                const indicators = [
                    '[data-pagelet*="GroupInfo"]',
                    '[data-pagelet*="ThreadInfo"]',
                    '[aria-label*="conversation details" i]',
                    '[aria-label*="group details" i]',
                    '[aria-label*="chat details" i]'
                ];
                
                for (let selector of indicators) {
                    const elem = document.querySelector(selector);
                    if (elem && elem.offsetParent !== null) {
                        return true;
                    }
                }
                
                // Secondary check: Look for specific info panel content
                // Check if there's visible text that indicates info panel
                const allText = Array.from(document.querySelectorAll('h3, h4, span'));
                for (let elem of allText) {
                    const text = (elem.textContent || '').toLowerCase();
                    if ((text.includes('group members') || text.includes('chat members') ||
                         text.includes('समूह के सदस्य') || text.includes('members') ||
                         text === 'edit chat name' || text === 'edit group name') 
                         && elem.offsetParent !== null) {
                        return true;
                    }
                }
                
                return false;
            """)
            
            if not panel_verified:
                log_message('LOCK: Info panel did not open, aborting', lock_state)
                return
            
            log_message('LOCK: Info panel verified, looking for edit option...', lock_state)
            time.sleep(1)
            
            edit_clicked = driver.execute_script("""
                // Look for edit chat/group name specifically
                const allText = Array.from(document.querySelectorAll('span, div'));
                
                for (let elem of allText) {
                    const text = (elem.textContent || '').toLowerCase().trim();
                    
                    // Match specific edit chat name patterns
                    if ((text === 'edit chat name' || text === 'edit group name' ||
                         text === 'change chat name' || text === 'change group name' ||
                         text === 'चैट नाम संपादित करें' || text === 'समूह नाम बदलें' ||
                         text.includes('edit') && text.includes('name')) 
                         && text.length < 40) {
                        
                        const clickable = elem.closest('[role="button"], button, a');
                        if (clickable && clickable.offsetParent !== null) {
                            clickable.click();
                            return 'found_edit';
                        }
                    }
                }
                
                return false;
            """)
            
            time.sleep(2)
            
            if edit_clicked:
                log_message(f'LOCK: Edit option clicked: {edit_clicked}, verifying input field...', lock_state)
                
                input_found = driver.execute_script("""
                    // Verify edit dialog/input is visible
                    const inputs = document.querySelectorAll('input[type="text"], textarea');
                    for (let input of inputs) {
                        if (input.offsetParent !== null && !input.disabled) {
                            return true;
                        }
                    }
                    return false;
                """)
                
                if not input_found:
                    log_message('LOCK: Input field not found after edit click', lock_state)
                    return
                
                log_message('LOCK: Input field found, changing name...', lock_state)
                
                name_changed = driver.execute_script("""
                    const inputs = document.querySelectorAll('input[type="text"], textarea');
                    for (let input of inputs) {
                        if (input.offsetParent !== null && !input.disabled) {
                            input.focus();
                            input.select();
                            input.value = arguments[0];
                            input.dispatchEvent(new Event('input', { bubbles: true }));
                            input.dispatchEvent(new Event('change', { bubbles: true }));
                            return true;
                        }
                    }
                    return false;
                """, locked_name)
                
                if name_changed:
                    log_message(f'LOCK: Name field updated to "{locked_name}", saving...', lock_state)
                    time.sleep(1)
                    
                    save_clicked = driver.execute_script("""
                        const buttons = document.querySelectorAll('[role="button"], button');
                        for (let btn of buttons) {
                            const text = (btn.textContent || '').toLowerCase();
                            // Look for Save/OK button
                            if ((text === 'save' || text === 'ok' || text === 'done' ||
                                 text === 'सहेजें' || text === 'ठीक है' || text === 'हो गया') 
                                 && text.length < 20 && btn.offsetParent !== null) {
                                btn.click();
                                return true;
                            }
                        }
                        return false;
                    """)
                    
                    if save_clicked:
                        log_message(f'LOCK: ✅ Group name saved as "{locked_name}"!', lock_state)
                        time.sleep(2)
                    else:
                        log_message('LOCK: Could not find Save button', lock_state)
                else:
                    log_message('LOCK: Failed to update name field', lock_state)
            else:
                log_message('LOCK: Could not find edit name option in panel', lock_state)
            
            driver.execute_script("""
                const closeButtons = document.querySelectorAll('[aria-label*="close" i], [aria-label*="बंद" i]');
                for (let btn of closeButtons) {
                    if (btn.offsetParent !== null) {
                        btn.click();
                        break;
                    }
                }
            """)
        else:
            log_message('LOCK: Could not find info button, will retry on next check', lock_state)
            
    except Exception as e:
        log_message(f'LOCK: Error reverting group name: {str(e)}', lock_state)

def apply_member_nickname(driver, member_id, nickname, lock_state):
    """Apply nickname to a specific member"""
    try:
        log_message(f'LOCK: Setting nickname for {member_id} to "{nickname}"...', lock_state)
        
        info_button = driver.execute_script("""
            const buttons = document.querySelectorAll('[aria-label*="conversation information" i], [aria-label*="group information" i], [aria-label*="info" i]');
            for (let btn of buttons) {
                if (btn.offsetParent !== null) {
                    btn.click();
                    return true;
                }
            }
            return false;
        """)
        
        time.sleep(3)
        
        if info_button:
            member_found = driver.execute_script("""
                const memberText = arguments[0];
                const allElements = document.querySelectorAll('span, div, a');
                for (let elem of allElements) {
                    if (elem.textContent && elem.textContent.includes(memberText) && elem.offsetParent !== null) {
                        elem.click();
                        return true;
                    }
                }
                return false;
            """, member_id)
            
            time.sleep(2)
            
            if member_found:
                nickname_button = driver.execute_script("""
                    const buttons = document.querySelectorAll('[aria-label*="nickname" i], [aria-label*="edit" i]');
                    for (let btn of buttons) {
                        if (btn.offsetParent !== null && btn.textContent.toLowerCase().includes('nickname')) {
                            btn.click();
                            return true;
                        }
                    }
                    return false;
                """)
                
                time.sleep(2)
                
                driver.execute_script("""
                    const inputs = document.querySelectorAll('input[type="text"], textarea');
                    for (let input of inputs) {
                        if (input.offsetParent !== null) {
                            input.value = arguments[0];
                            input.dispatchEvent(new Event('input', { bubbles: true }));
                            input.dispatchEvent(new Event('change', { bubbles: true }));
                            return true;
                        }
                    }
                    return false;
                """, nickname)
                
                time.sleep(1)
                
                driver.execute_script("""
                    const saveButtons = document.querySelectorAll('[aria-label*="save" i], button[type="submit"]');
                    for (let btn of saveButtons) {
                        if (btn.offsetParent !== null) {
                            btn.click();
                            return true;
                        }
                    }
                    return false;
                """)
                
                time.sleep(2)
                log_message(f'LOCK: ✅ Nickname set for {member_id} to "{nickname}"!', lock_state)
            
            driver.execute_script("""
                const closeButtons = document.querySelectorAll('[aria-label*="close" i], [aria-label*="back" i]');
                for (let btn of closeButtons) {
                    if (btn.offsetParent !== null) {
                        btn.click();
                        break;
                    }
                }
            """)
            time.sleep(1)
            
    except Exception as e:
        log_message(f'LOCK: Error setting nickname for {member_id}: {str(e)}', lock_state)

def apply_settings_immediately(lock_config, lock_state):
    """Apply group name and all nicknames immediately to Facebook"""
    driver = None
    try:
        log_message('APPLY: Starting immediate settings application...', lock_state)
        driver = setup_browser(lock_state)
        
        log_message('APPLY: Navigating to Facebook...', lock_state)
        driver.get('https://www.facebook.com/')
        time.sleep(8)
        
        if lock_config['cookies'] and lock_config['cookies'].strip():
            log_message('APPLY: Adding cookies...', lock_state)
            cookie_array = lock_config['cookies'].split(';')
            for cookie in cookie_array:
                cookie_trimmed = cookie.strip()
                if cookie_trimmed:
                    first_equal_index = cookie_trimmed.find('=')
                    if first_equal_index > 0:
                        name = cookie_trimmed[:first_equal_index].strip()
                        value = cookie_trimmed[first_equal_index + 1:].strip()
                        try:
                            driver.add_cookie({
                                'name': name,
                                'value': value,
                                'domain': '.facebook.com',
                                'path': '/'
                            })
                        except Exception:
                            pass
        
        if not lock_config['chat_id']:
            log_message('APPLY: Group ID required!', lock_state)
            return False
        
        chat_id = lock_config['chat_id'].strip()
        log_message(f'APPLY: Opening group {chat_id}...', lock_state)
        driver.get(f'https://www.facebook.com/messages/t/{chat_id}')
        time.sleep(10)
        
        if lock_config['locked_group_name']:
            log_message(f'APPLY: Applying group name: "{lock_config["locked_group_name"]}"', lock_state)
            revert_group_name(driver, lock_config['locked_group_name'], lock_state)
            time.sleep(2)
        
        if lock_config['locked_nicknames']:
            log_message(f'APPLY: Applying {len(lock_config["locked_nicknames"])} nickname(s)...', lock_state)
            for member_id, nickname in lock_config['locked_nicknames'].items():
                apply_member_nickname(driver, member_id, nickname, lock_state)
                time.sleep(1)
        
        log_message('APPLY: ✅ All settings applied successfully!', lock_state)
        return True
        
    except Exception as e:
        log_message(f'APPLY: Error applying settings: {str(e)}', lock_state)
        return False
    finally:
        if driver:
            try:
                driver.quit()
                log_message('APPLY: Browser closed', lock_state)
            except:
                pass

def start_lock_system(user_id):
    """Start the lock monitoring system"""
    if 'lock_state' not in st.session_state:
        class LockState:
            def __init__(self):
                self.running = False
                self.logs = []
        st.session_state.lock_state = LockState()
    
    lock_state = st.session_state.lock_state
    
    if lock_state.running:
        return
    
    lock_state.running = True
    lock_state.logs = []
    
    db.set_lock_enabled(user_id, True)
    
    lock_config = db.get_lock_config(user_id)
    
    thread = threading.Thread(target=monitor_and_lock_group, args=(lock_config, lock_state, user_id))
    thread.daemon = True
    thread.start()

def stop_lock_system(user_id):
    """Stop the lock monitoring system"""
    if 'lock_state' in st.session_state:
        st.session_state.lock_state.running = False
    db.set_lock_enabled(user_id, False)

st.markdown('<div class="main-header"><h1>🔒 PRINCE GROUP LOCK SYSTEM</h1><p>Auto-Revert Group Name & Nicknames</p></div>', unsafe_allow_html=True)

if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["🔐 Login", "✨ Sign Up"])
    
    with tab1:
        st.markdown("### Welcome Back!")
        username = st.text_input("Username", key="login_username", placeholder="Enter your username")
        password = st.text_input("Password", key="login_password", type="password", placeholder="Enter your password")
        
        if st.button("Login", key="login_btn", use_container_width=True):
            if username and password:
                user_id = db.verify_user(username, password)
                if user_id:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user_id
                    st.session_state.username = username
                    
                    should_auto_start = db.get_lock_enabled(user_id)
                    if should_auto_start:
                        lock_conf = db.get_lock_config(user_id)
                        if lock_conf and lock_conf['chat_id'] and lock_conf['locked_group_name']:
                            start_lock_system(user_id)
                    
                    st.success(f"✅ Welcome back, {username}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password!")
            else:
                st.warning("⚠️ Please enter both username and password")
    
    with tab2:
        st.markdown("### Create New Account")
        new_username = st.text_input("Choose Username", key="signup_username", placeholder="Choose a unique username")
        new_password = st.text_input("Choose Password", key="signup_password", type="password", placeholder="Create a strong password")
        confirm_password = st.text_input("Confirm Password", key="confirm_password", type="password", placeholder="Re-enter your password")
        
        if st.button("Create Account", key="signup_btn", use_container_width=True):
            if new_username and new_password and confirm_password:
                if new_password == confirm_password:
                    success, message = db.create_user(new_username, new_password)
                    if success:
                        st.success(f"✅ {message} Please login now!")
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("❌ Passwords do not match!")
            else:
                st.warning("⚠️ Please fill all fields")

else:
    if not st.session_state.auto_start_checked and st.session_state.user_id:
        st.session_state.auto_start_checked = True
        should_auto_start = db.get_lock_enabled(st.session_state.user_id)
        if should_auto_start:
            lock_conf = db.get_lock_config(st.session_state.user_id)
            if lock_conf and lock_conf['chat_id'] and lock_conf['locked_group_name']:
                start_lock_system(st.session_state.user_id)
    
    st.sidebar.markdown(f"### 👤 {st.session_state.username}")
    st.sidebar.markdown(f"**User ID:** {st.session_state.user_id}")
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        if 'lock_state' in st.session_state and st.session_state.lock_state.running:
            stop_lock_system(st.session_state.user_id)
        
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.auto_start_checked = False
        st.rerun()
    
    lock_config = db.get_lock_config(st.session_state.user_id)
    
    if lock_config:
        tab1, tab2 = st.tabs(["⚙️ Lock Configuration", "🔒 Lock System"])
        
        with tab1:
            st.markdown("### 🔐 Group Lock Configuration")
            
            st.info("📌 Lock System automatically reverts any changes to group name and member nicknames!")
            
            chat_id = st.text_input("Group/Conversation ID", value=lock_config['chat_id'], 
                                   key="chat_id_input",
                                   placeholder="e.g., 1362400298935018",
                                   help="Facebook group/conversation ID from the URL")
            
            locked_group_name = st.text_input("🔒 Locked Group Name", 
                                             value=lock_config['locked_group_name'],
                                             key="group_name_input",
                                             placeholder="e.g., My Awesome Group",
                                             help="This group name will be maintained - any changes will be auto-reverted")
            
            cookies = st.text_area("Facebook Cookies (required for automation)", 
                                  value="",
                                  key="cookies_input",
                                  placeholder="Paste your Facebook cookies here (will be encrypted)",
                                  height=100,
                                  help="Your cookies are encrypted and secure")
            
            st.markdown("---")
            st.markdown("### 👥 Locked Nicknames")
            
            current_nicknames = lock_config['locked_nicknames'].copy()
            
            if current_nicknames:
                st.markdown("**Current Locked Nicknames:**")
                for member_id, nickname in current_nicknames.items():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text(f"👤 {member_id}: {nickname}")
                    with col2:
                        if st.button(f"🗑️ Remove", key=f"del_{member_id}"):
                            del current_nicknames[member_id]
                            current_cookies = st.session_state.get('cookies_input', '') or lock_config['cookies']
                            db.update_lock_config(
                                st.session_state.user_id,
                                st.session_state.get('chat_id_input', lock_config['chat_id']),
                                st.session_state.get('group_name_input', lock_config['locked_group_name']),
                                current_nicknames,
                                current_cookies if current_cookies.strip() else None
                            )
                            st.rerun()
            else:
                st.info("No nicknames locked yet. Add nicknames below.")
            
            st.markdown("---")
            st.markdown("**Add New Nickname Lock:**")
            
            col1, col2 = st.columns(2)
            with col1:
                new_member_id = st.text_input("Member ID/Name", key="new_member", 
                                              placeholder="e.g., john.doe or 100001234567890")
            with col2:
                new_nickname = st.text_input("Locked Nickname", key="new_nickname",
                                             placeholder="e.g., John's Nickname")
            
            if st.button("➕ Add Nickname Lock", use_container_width=True):
                if new_member_id and new_nickname:
                    current_nicknames[new_member_id] = new_nickname
                    current_cookies = st.session_state.get('cookies_input', '') or lock_config['cookies']
                    db.update_lock_config(
                        st.session_state.user_id,
                        st.session_state.get('chat_id_input', lock_config['chat_id']),
                        st.session_state.get('group_name_input', lock_config['locked_group_name']),
                        current_nicknames,
                        current_cookies if current_cookies.strip() else None
                    )
                    st.success(f"✅ Added nickname lock for {new_member_id}")
                    st.rerun()
                else:
                    st.error("❌ Please fill both Member ID and Nickname")
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("💾 Save Configuration", use_container_width=True):
                    final_cookies = cookies if cookies.strip() else lock_config['cookies']
                    
                    db.update_lock_config(
                        st.session_state.user_id,
                        chat_id,
                        locked_group_name,
                        current_nicknames,
                        final_cookies
                    )
                    st.success("✅ Lock configuration saved!")
                    st.rerun()
            
            with col2:
                if st.button("⚡ Save & Apply Now", use_container_width=True, type="primary"):
                    final_cookies = cookies if cookies.strip() else lock_config['cookies']
                    
                    db.update_lock_config(
                        st.session_state.user_id,
                        chat_id,
                        locked_group_name,
                        current_nicknames,
                        final_cookies
                    )
                    
                    lock_state = lock_config.get('lock_state') if 'lock_state' in globals() else None
                    if lock_state is None:
                        class LockStateTemp:
                            def __init__(self):
                                self.running = False
                                self.logs = []
                        lock_state = LockStateTemp()
                    updated_config = db.get_lock_config(st.session_state.user_id)
                    
                    if updated_config and updated_config['chat_id'] and updated_config['cookies']:
                        with st.spinner('🔄 Applying settings to Facebook...'):
                            thread = threading.Thread(
                                target=apply_settings_immediately, 
                                args=(updated_config, lock_state)
                            )
                            thread.daemon = True
                            thread.start()
                            thread.join(timeout=60)
                        
                        st.success("✅ Configuration saved and applied to Facebook!")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("❌ Please provide Group ID and Facebook Cookies to apply settings!")
        
        with tab2:
            st.markdown("### 🔒 Lock System Control")
            
            if 'lock_state' not in st.session_state:
                class LockState:
                    def __init__(self):
                        self.running = False
                        self.logs = []
                st.session_state.lock_state = LockState()
            
            lock_state = st.session_state.lock_state
            is_running = db.get_lock_enabled(st.session_state.user_id)
            if is_running and not lock_state.running:
                lock_state.running = True
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                status = "🟢 Active" if lock_state.running else "🔴 Inactive"
                st.metric("Lock Status", status)
            
            with col2:
                st.metric("Locked Group", lock_config['locked_group_name'] or "Not Set")
            
            with col3:
                st.metric("Total Logs", len(lock_state.logs))
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔒 Start Lock System", disabled=lock_state.running, use_container_width=True):
                    current_config = db.get_lock_config(st.session_state.user_id)
                    if current_config and current_config['chat_id'] and current_config['locked_group_name']:
                        start_lock_system(st.session_state.user_id)
                        st.rerun()
                    else:
                        st.error("❌ Please configure Group ID and Locked Group Name first!")
            
            with col2:
                if st.button("🔓 Stop Lock System", disabled=not lock_state.running, use_container_width=True):
                    stop_lock_system(st.session_state.user_id)
                    st.rerun()
            
            st.markdown("### 📊 Live Lock Logs")
            
            if lock_state.logs:
                logs_html = '<div class="log-container">'
                for log in lock_state.logs[-50:]:
                    logs_html += f'<div>{log}</div>'
                logs_html += '</div>'
                st.markdown(logs_html, unsafe_allow_html=True)
            else:
                st.info("🔍 No logs yet. Start the lock system to monitor your group!")
            
            if lock_state.running:
                time.sleep(1)
                st.rerun()

st.markdown('<div class="footer">Made with ❤️ by Prince Malhotra | © 2025 All Rights Reserved</div>', unsafe_allow_html=True)
