def is_balanced(expression):
    # A simple Python list acts as our lightweight Stack structure
    stack = []
    
    # Map closing brackets to their matching opening partners
    mapping = {")": "(", "}": "{", "]": "["}
    
    for char in expression:
        # If it's an opening bracket, push it onto the stack
        if char in mapping.values():
            stack.append(char)
            
        # If it's a closing bracket...
        elif char in mapping:
            # Pop the top element from the stack if it's not empty, else use dummy value
            top_element = stack.pop() if stack else '#'
            
            # If the mapping doesn't match the popped element, it's unbalanced
            if mapping[char] != top_element:
                return False
                
    # If the stack is empty, all brackets were successfully matched
    return len(stack) == 0
  
test_strings = [
    "{[()]}",      # Valid and nested balanced
    "[(])",        # Invalid (Incorrect nesting order)
    "((())"        # Invalid (Unclosed opening parenthesis)
]

print("--- Running Syntax Validation Engine ---")
for string in test_strings:
    status = "VALID" if is_balanced(string) else "INVALID"
    print(f"Expression: {string:10} -> Result: {status}")

# Output :
# --- Running Syntax Validation Engine ---
# Expression: {[()]}     -> Result: VALID
# Expression: [(])       -> Result: INVALID
# Expression: ((())      -> Result: INVALID
