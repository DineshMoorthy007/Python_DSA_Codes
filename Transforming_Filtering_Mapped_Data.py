# Raw dataset: list of tuples (Username, Account_Status)
raw_users = [
    ("alice_dev", "active"),
    ("bob_manager", "suspended"),
    ("charlie_tester", "active"),
    ("david_admin", "inactive")
]

# Dictionary Comprehension with filtering logic
# Syntax format -> { key: value for item in iterable if condition }
active_user_tokens = {
    user[0]: f"TOKEN_{user[0].upper()}_2026" 
    for user in raw_users 
    if user[1] == "active"
}

print("--- Parsing User Database ---")
print(active_user_tokens)

# Instant O(1) hash map lookup test
print(f"\n[LOOKUP] Verification: charlie_tester -> {active_user_tokens.get('charlie_tester')}")

# Output :
# --- Parsing User Database ---
# {'alice_dev': 'TOKEN_ALICE_DEV_2026', 'charlie_tester': 'TOKEN_CHARLIE_TESTER_2026'}

# [LOOKUP] Verification: charlie_tester -> TOKEN_CHARLIE_TESTER_2026
