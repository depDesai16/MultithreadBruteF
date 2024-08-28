import threading
import hashlib
import time

# Example target hash to crack (SHA-1 hash of the target password)
target_hash = '0c6f6845bb8c62b778e9147c272ac4b5bdb9ae71'  # Replace with your actual target hash

# Number of threads to use
num_threads = 8  # Set to the desired number of threads

# Shared variable to stop threads once the password is found
found = threading.Event()

# Shared variable to count failed attempts
failed_attempts = 0
failed_attempts_lock = threading.Lock()  # Lock for thread-safe updates

# Path to the RockYou wordlist
wordlist_path = 'rockyou.txt'  # Update with the correct path if different

# Lock for thread-safe printing
print_lock = threading.Lock()

def load_passwords(file_path):
    """Loads passwords from the specified wordlist file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            passwords = [line.strip() for line in file]
        return passwords
    except FileNotFoundError:
        print(f"Wordlist file '{file_path}' not found.")
        return []

def hash_password(password):
    """Hashes a password using SHA-1."""
    return hashlib.sha1(password.encode()).hexdigest()

def brute_force(thread_id, start, end, passwords):
    """Attempts to brute-force the password by checking hashes in the provided range."""
    global found, failed_attempts
    for i in range(start, end):
        if found.is_set():
            return
        password = passwords[i]
        hashed = hash_password(password)
        if hashed == target_hash:
            with print_lock:
                print(f"\nPassword found by Thread {thread_id}: {password}")
            found.set()
            return
        # Increment failed attempts counter in a thread-safe manner
        with failed_attempts_lock:
            failed_attempts += 1

def update_failed_attempts():
    """Periodically prints the number of failed attempts."""
    while not found.is_set():
        time.sleep(1)  # Update every second
        with failed_attempts_lock:
            with print_lock:
                print(f"Failed attempts: {failed_attempts}", end='\r')

def update_active_threads():
    """Periodically prints the number of active threads."""
    while not found.is_set() or threading.active_count() > 1:
        time.sleep(1)  # Update every second
        with print_lock:
            # Ensure we subtract 1 to exclude the main thread from count
            print(f"Active threads: {threading.active_count() - 1}", end='\r')

def main():
    # Load the passwords from the wordlist
    passwords = load_passwords(wordlist_path)
    
    if not passwords:
        return

    # Record the start time
    start_time = time.time()

    # Start threads for displaying failed attempt count and active thread count
    counter_thread = threading.Thread(target=update_failed_attempts)
    counter_thread.start()
    
    active_thread_thread = threading.Thread(target=update_active_threads)
    active_thread_thread.start()

    # Determine the range of passwords each thread will handle
    chunk_size = max(1, len(passwords) // num_threads)  # Ensure chunk size is at least 1
    threads = []

    for i in range(num_threads):
        start = i * chunk_size
        # Ensure the last thread gets any remaining passwords
        end = (i + 1) * chunk_size if i != num_threads - 1 else len(passwords)
        if start >= len(passwords):  # Avoid starting threads with no work
            break
        thread = threading.Thread(target=brute_force, args=(i, start, end, passwords))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Ensure the counter threads stop if the password is found or all threads are done
    found.set()
    counter_thread.join()
    active_thread_thread.join()

    # Record the end time
    end_time = time.time()
    elapsed_time = end_time - start_time

    if not found.is_set():
        with print_lock:
            print("\nPassword not found.")
    else:
        with print_lock:
            print(f"\nTotal failed attempts: {failed_attempts}")

    # Print elapsed time
    with print_lock:
        print(f"Elapsed time: {elapsed_time:.2f} seconds")

if __name__ == "__main__":
    main()
