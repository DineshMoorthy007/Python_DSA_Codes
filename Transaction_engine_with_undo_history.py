class Command:
    """Abstract Interface for concrete command execution."""
    def execute(self): raise NotImplementedError
    def undo(self): raise NotImplementedError

class TextEditor:
    """The Receiver class containing the actual state logic."""
    def __init__(self):
        self.text = ""

class AppendCommand(Command):
    """A concrete command payload capturing text alterations."""
    def __init__(self, editor, text_to_append):
        self.editor = editor
        self.text_to_append = text_to_append

    def execute(self):
        self.editor.text += self.text_to_append

    def undo(self):
        # Slice off the exact segment appended by this specific command
        slice_len = len(self.text_to_append)
        self.editor.text = self.editor.text[:-slice_len]

class HistoryManager:
    """The Invoker class managing state transaction tracking."""
    def __init__(self):
        self._undo_stack = []
        self._redo_stack = []

    def execute_action(self, command):
        command.execute()
        self._undo_stack.append(command)
        self._redo_stack.clear() # Clear redo history on a fresh action

    def undo(self):
        if not self._undo_stack:
            print("[WARN] Nothing to undo.")
            return
        command = self._undo_stack.pop()
        command.undo()
        self._redo_stack.append(command)

    def redo(self):
        if not self._redo_stack:
            print("[WARN] Nothing to redo.")
            return
        command = self._redo_stack.pop()
        command.execute()
        self._undo_stack.append(command)
      
document = TextEditor()
manager = HistoryManager()

print("--- Typing Text ---")
manager.execute_action(AppendCommand(document, "Hello "))
manager.execute_action(AppendCommand(document, "World "))
manager.execute_action(AppendCommand(document, "2026!"))
print(f"Current State: '{document.text}'")

print("\n--- Triggering Undo x2 ---")
manager.undo()
manager.undo()
print(f"Current State: '{document.text}'")

print("\n--- Triggering Redo x1 ---")
manager.redo()
print(f"Current State: '{document.text}'")
