from abc import ABC, abstractmethod

# --- Abstract Visitor Interface ---

class DocumentVisitor(ABC):
    """The Visitor interface declaring visit operations for every concrete element type."""
    @abstractmethod
    def visit_heading(self, element: 'HeadingNode') -> None:
        pass

    @abstractmethod
    def visit_paragraph(self, element: 'ParagraphNode') -> None:
        pass

    @abstractmethod
    def visit_code_block(self, element: 'CodeBlockNode') -> None:
        pass


# --- Abstract Element Interface ---

class DocumentNode(ABC):
    """The Element interface establishing the Double Dispatch accept contract."""
    @abstractmethod
    def accept(self, visitor: DocumentVisitor) -> None:
        pass


# --- Concrete Document Elements ---

class HeadingNode(DocumentNode):
    def __init__(self, text: str, level: int = 1):
        self.text = text
        self.level = level

    def accept(self, visitor: DocumentVisitor) -> None:
        # Double Dispatch: Directs execution back to the visitor's specific visit method
        visitor.visit_heading(self)


class ParagraphNode(DocumentNode):
    def __init__(self, text: str):
        self.text = text

    def accept(self, visitor: DocumentVisitor) -> None:
        visitor.visit_paragraph(self)


class CodeBlockNode(DocumentNode):
    def __init__(self, code: str, language: str = "python"):
        self.code = code
        self.language = language

    def accept(self, visitor: DocumentVisitor) -> None:
        visitor.visit_code_block(self)


# --- Concrete Visitor Operations ---

class MarkdownExporterVisitor(DocumentVisitor):
    """Visitor 1: Converts document AST nodes into formatted Markdown syntax."""
    def __init__(self):
        self.output: list[str] = []

    def visit_heading(self, element: HeadingNode) -> None:
        self.output.append(f"{'#' * element.level} {element.text}")

    def visit_paragraph(self, element: ParagraphNode) -> None:
        self.output.append(f"{element.text}\n")

    def visit_code_block(self, element: CodeBlockNode) -> None:
        self.output.append(f"```{element.language}\n{element.code}\n```\n")

    def get_markdown(self) -> str:
        return "\n".join(self.output)


class WordCountVisitor(DocumentVisitor):
    """Visitor 2: Audits document nodes to compute overall word metrics."""
    def __init__(self):
        self.total_words = 0

    def visit_heading(self, element: HeadingNode) -> None:
        self.total_words += len(element.text.split())

    def visit_paragraph(self, element: ParagraphNode) -> None:
        self.total_words += len(element.text.split())

    def visit_code_block(self, element: CodeBlockNode) -> None:
        self.total_words += len(element.code.split())


if __name__ == "__main__":
    print("--- Initializing Document AST Processor ---\n")

    # 1. Construct the document tree hierarchy
    document_ast: list[DocumentNode] = [
        HeadingNode("Visitor Design Pattern", level=1),
        ParagraphNode("This pattern separates an algorithm from an object structure on which it operates."),
        HeadingNode("Code Example", level=2),
        CodeBlockNode("node.accept(visitor)", language="python")
    ]

    # 2. Run Execution Pass 1: Exporting to Markdown syntax
    markdown_exporter = MarkdownExporterVisitor()
    for node in document_ast:
        node.accept(markdown_exporter)

    print("[EXPORT RESULT] Generated Markdown Document:")
    print("-" * 50)
    print(markdown_exporter.get_markdown())
    print("-" * 50)

    # 3. Run Execution Pass 2: Running word-count analysis over the same tree
    analytics_auditor = WordCountVisitor()
    for node in document_ast:
        node.accept(analytics_auditor)

    print(f"[ANALYTICS] Total Word Count across document nodes: {analytics_auditor.total_words}")

# Output :
# --- Initializing Document AST Processor ---
# [EXPORT RESULT] Generated Markdown Document:
# --------------------------------------------------
# # Visitor Design Pattern
# This pattern separates an algorithm from an object structure on which it operates.
# ## Code Example
# ```python
# node.accept(visitor)
# ```

# --------------------------------------------------
# [ANALYTICS] Total Word Count across document nodes: 19
