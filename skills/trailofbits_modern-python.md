# Trailofbits: Modern Python Skill

## 🎯 Goal
Ensure all Python code written adheres to modern standards (Python 3.10+), emphasizing strong typing, memory safety, and structural predictability.

## 📋 Core Directives
- **Strong Typing:** All function parameters, return values, and class attributes MUST include type hints (`str`, `int`, `list[str]`, `dict[str, Any]`, `Callable`). Use `|` instead of `Union`. Avoid `Any` wherever possible.
- **Data Structures:** Prefer `@dataclass(slots=True)` or `pydantic.BaseModel` over dictionaries for passing configuration objects and state.
- **Pattern Matching:** Use `match/case` for complex control flows involving enums, command routing, or AST node inspection.
- **Exception Handling:** Never use bare `except:`. Always catch specific exceptions. Re-raise with `from e` to preserve stack traces.
- **Resource Management:** Ensure all file handles, network sockets, and subprocesses are wrapped in `with` blocks (Context Managers) to guarantee cleanup.
- **Decoupling:** Do not pollute the global namespace. Pass dependencies directly via constructors.
