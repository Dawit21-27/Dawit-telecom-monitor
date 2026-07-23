"""
Dawit Telecom - Enterprise Network Monitor & Self-Healing Bot
-------------------------------------------------------------
Automated network health monitoring system with Telegram Bot API,
SSH self-healing, File reporting, and SMS notification integration.
"""

import os
import subprocess
import time
import json
import requests
from dotenv import load_dotenv

# Base Directory & Configuration Binding
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
MY_PHONE_NUMBER = os.getenv("MY_PHONE_NUMBER", "+251900000000")

JSON_FILE = os.path.join(BASE_DIR, "network_report.json")
LOG_FILE = os.path.join(BASE_DIR, "network_events.log")

TARGET_HOSTS = ["8.8.8.8", "1.1.1.1", "10.99.99.99"]


def append_event_log(event_text):
    """
    Appends execution history and network events to a persistent .log file.
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {event_text}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as error:
        print(f"❌ Failed to write log: {error}")


def send_telegram_alert(message):
    """
    Dispatches automated text alerts to Telegram.
    """
    if not BOT_TOKEN or not CHAT_ID:
        return

    token = BOT_TOKEN.strip()
    if token.startswith("bot"):
        token = token[3:]

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": CHAT_ID.strip(), "text": message}
    
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as error:
        print(f"❌ Failed to reach Telegram API: {error}")


def send_telegram_file(file_path):
    """
    Sends history/log files directly as documents to Telegram chat.
    """
    if not BOT_TOKEN or not CHAT_ID or not os.path.exists(file_path):
        send_telegram_alert("⚠️ የመዝገብ ፋይሉ አልተገኘም።")
        return

    token = BOT_TOKEN.strip()
    if token.startswith("bot"):
        token = token[3:]

    url = f"https://api.telegram.org/bot{token}/sendDocument"
    
    try:
        with open(file_path, "rb") as file:
            requests.post(url, data={"chat_id": CHAT_ID.strip()}, files={"document": file}, timeout=10)
    except Exception as error:
        print(f"❌ Document Dispatch Error: {error}")


def send_sms_alert(message, phone_number):
    """
    Dispatches SMS alerts via Termux API (Local) or Twilio (PC/Cloud).
    """
    print(f"📱 [SMS Dispatch Attempt] Target: {phone_number}")
    append_event_log(f"SMS Alert triggered for {phone_number}: {message}")
    
    # ----------------------------------------------------
    # 📱 OPTION A: Termux Native SMS (ለስልክህ የሚሰራው)
    # ----------------------------------------------------
    try:
        result = subprocess.run(
            ["termux-sms-send", "-n", phone_number, message],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            print("✅ SMS በ Termux API ተልኳል!")
        else:
            print(f"⚠️ Termux SMS Error: {result.stderr}")
    except Exception as e:
        print(f"⚠️ Termux Dispatch Exception: {e}")

    # ----------------------------------------------------
    # 💻 OPTION B: Twilio Cloud SMS (ለወደፊት ወደ PC ስትቀይር የምትከፍተው)
    # ----------------------------------------------------
    """
    from twilio.rest import Client
    
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_number = os.getenv("TWILIO_PHONE_NUMBER")

    if account_sid and auth_token and twilio_number:
        try:
            client = Client(account_sid, auth_token)
            msg = client.messages.create(
                body=message,
                from_=twilio_number,
                to=phone_number
            )
            print(f"✅ Twilio SMS Sent! SID: {msg.sid}")
        except Exception as err:
            print(f"❌ Twilio Error: {err}")
    """

def ping_ip(ip):
    """
    Executes ICMP echo request.
    """
    try:
        result = subprocess.run(
            ["ping", "-c", "2", ip],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def try_self_healing_ssh(ip):
    """
    Attempts SSH remote recovery or falls back to simulation mode.
    """
    msg = f"🛠️ Initiating SSH connection to {ip}..."
    print(msg)
    append_event_log(msg)
    
    try:
        import paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        key_path = os.path.expanduser("~/.ssh/id_rsa")
        
        if os.path.exists(key_path):
            private_key = paramiko.RSAKey.from_private_key_file(key_path)
            ssh.connect(ip, username="admin", pkey=private_key, timeout=5)
            ssh.exec_command("sudo systemctl restart nginx")
            ssh.close()
            status = "⚡ Simulated SSH 'sudo systemctl restart nginx' ትእዛዝ በስኬት ተላከ! (Simulation Mode)"
        else:
            status = "⚡ Simulated SSH 'sudo systemctl restart nginx' ትእዛዝ በስኬት ተላከ! (Simulation Mode)"

    except ImportError:
        time.sleep(1)
        status = "⚡ Simulated SSH 'sudo systemctl restart nginx' ትእዛዝ በስኬት ተላከ! (Simulation Mode)"
        
    except Exception as error:
        status = f"⚠️ የ SSH ግንኙነት አልተሳካም፦ {error}"

    append_event_log(f"Self-Healing Result: {status}")
    return status


def save_report_to_json(status_data, timestamp):
    """
    Persists current operational state to JSON.
    """
    report = {
        "last_check": timestamp,
        "overall_status": "CRITICAL" if any(s == "OFFLINE" for s in status_data.values()) else "HEALTHY",
        "nodes": status_data
    }
    try:
        with open(JSON_FILE, "w") as file:
            json.dump(report, file, indent=4)
    except Exception as error:
        print(f"❌ JSON Error: {error}")


def get_current_report_summary():
    """
    Generates summary text from JSON.
    """
    if not os.path.exists(JSON_FILE):
        return "⚠️ ምንም የቅርብ ጊዜ የኔትወርክ ሪፖርት አልተገኘም።"
    
    try:
        with open(JSON_FILE, "r") as file:
            data = json.load(file)
            
        summary = f"📊 CURRENT NETWORK STATUS 📊\n"
        summary += f"Last Check: {data.get('last_check')}\n"
        summary += f"Overall: {data.get('overall_status')}\n\n"
        
        for node, state in data.get("nodes", {}).items():
            icon = "✅" if state == "ONLINE" else "❌"
            summary += f"{icon} {node} -> {state}\n"
            
        return summary
    except Exception as error:
        return f"⚠️ ሪፖርቱን ማንበብ አልተቻለም፦ {error}"


def check_telegram_updates(last_update_id):
    """
    Polls Telegram API for commands including /status, /log, /check, and /help.
    Supports lower & upper case inputs dynamically.
    """
    if not BOT_TOKEN:
        return last_update_id

    token = BOT_TOKEN.strip()
    if token.startswith("bot"):
        token = token[3:]

    url = f"https://api.telegram.org/bot{token}/getUpdates"
    params = {"offset": last_update_id + 1, "timeout": 2}

    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            updates = response.json().get("result", [])
            for update in updates:
                last_update_id = update["update_id"]
                message = update.get("message", {})
                raw_text = message.get("text", "").strip()
                
                # Case-insensitive reading (ትልቅና ትንሽ ፊደላትን አንድ ያደርጋል)
                cmd = raw_text.lower().split('@')[0]

                if cmd == "/status":
                    send_telegram_alert(get_current_report_summary())
                elif cmd == "/log":
                    send_telegram_alert("📄 የአጠቃላይ የታሪክ መዝገብ ፋይል (Event Log File) እየተላከ ነው...")
                    send_telegram_file(LOG_FILE)
                elif cmd.startswith("/check"):
                    parts = raw_text.split()
                    if len(parts) > 1:
                        target_ip = parts[1]
                        send_telegram_alert(f"🔍 Checking {target_ip} on demand...")
                        is_online = ping_ip(target_ip)
                        status = "ONLINE ✅" if is_online else "OFFLINE ❌"
                        send_telegram_alert(f"Result for {target_ip}: {status}")
                    else:
                        send_telegram_alert("⚠️ እባክዎን IP ይጻፉ። ለምሳሌ፦ /check 8.8.8.8")
                elif cmd == "/help" or cmd == "/start":
                    help_msg = (
                        "🤖 Dawit Telecom Monitor Help Menu\n\n"
                        "📌 /status - የአሁኑን አጠቃላይ የኔትወርክ ሁኔታ ያያሉ\n"
                        "📌 /log - የአጠቃላይ የታሪክ መዝገብ ፋይል (Log File) ያገኛሉ\n"
                        "📌 /check <IP> - የተወሰነ IP አሁኑኑ ፈትነው ያውቃሉ\n"
                        "📌 /help - ይህንን መመሪያ ያያሉ"
                    )
                    send_telegram_alert(help_msg)

    except Exception as error:
        print(f"❌ Telegram Polling Error: {error}")

    return last_update_id
    

def smart_network_check():
    """
    Core monitoring loop.
    """
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n--- 🌐 Enterprise Network Monitor [{current_time}] ---")
    
    current_status = {}
    critical_failure_detected = False
    ssh_logs = ""

    for ip in TARGET_HOSTS:
        print(f"Checking: {ip}...")
        
        if ping_ip(ip):
            current_status[ip] = "ONLINE"
        else:
            print(f"⚠️ {ip} አልመለሰም። ድጋሚ እየተሞከረ ነው (Retry)...")
            time.sleep(2)
            
            if ping_ip(ip):
                current_status[ip] = "ONLINE"
            else:
                current_status[ip] = "OFFLINE"
                critical_failure_detected = True
                
                # Dynamic Self-Healing
                ssh_result = try_self_healing_ssh(ip)
                ssh_logs += f"\n🔧 ማስታወሻ፦ {ssh_result}"

    # Log to persistent file
    append_event_log(f"Check Complete. Status: {current_status}")

    # Save to JSON
    save_report_to_json(current_status, current_time)

    # Dispatch Telegram Alert (ቀደም ሲል የነበረው አጭር አላርም መልእክት)
    if critical_failure_detected:
        alert_msg = (
            f"🚨 ENTERPRISE NETWORK ALERT! 🚨\n"
            f"Time: {current_time}\n\n"
            f"❌ Critical Site 10.99.99.99 is DOWN!"
            f"{ssh_logs}"
        )
        send_telegram_alert(alert_msg)
        
        # Dispatch SMS Alert
        send_sms_alert(f"CRITICAL: Site 10.99.99.99 is DOWN at {current_time}", MY_PHONE_NUMBER)


def main():
    print("🚀 Level 4 Enterprise Monitor & Logging Engine ስራ ጀምሯል!")
    append_event_log("--- Monitoring System Started ---")
    send_telegram_alert("🤖 Dawit Telecom Monitor Online!\nትእዛዝ ለመስጠት /help ወይም /log ብለው ይጻፉ።")

    last_update_id = 0

    while True:
        smart_network_check()

        for _ in range(15):
            last_update_id = check_telegram_updates(last_update_id)
            time.sleep(1)


if __name__ == "__main__":
    main()
