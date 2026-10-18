from adityacli.core.models import Message, Role, ToolResult


class PromptBuilder:
    """Include each instruction and each referenced file once per request."""

    def build(
        self, *, messages: list[Message], tool_result: ToolResult | None,
        read_files: dict[str, str] | None = None,
    ) -> list[Message]:
        prompt = list(messages)
        current = None
        if tool_result is not None:
            # Replace the raw slash command, which repeats its natural
            # language request, with the tool's complete prepared prompt.
            if prompt and prompt[-1].role is Role.USER:
                prompt.pop()
            current = Message(Role.USER, tool_result.prompt)
        elif prompt and prompt[-1].role is Role.USER:
            current = prompt.pop()

        supplied = set()
        if tool_result:
            supplied.update(path for path, _ in tool_result.metadata.files_read)
            supplied.update(tool_result.metadata.files_written)
            instructions = tool_result.metadata.extra.get("instructions")
            if isinstance(instructions, str):
                # Keep one system message for local chat templates that
                # only honor an initial system role. The active contract
                # is temporary and never accumulated in session history.
                if prompt and prompt[0].role is Role.SYSTEM:
                    prompt[0] = Message(Role.SYSTEM, prompt[0].content + "\n\nCurrent tool task:\n" + instructions)
                else:
                    prompt.insert(0, Message(Role.SYSTEM, instructions))
        sections = []
        for path, content in (read_files or {}).items():
            if path in supplied:
                continue
            sections.append(f"=== FILE: {path} ===\n{content}\n")
        if sections:
            prompt.append(Message(Role.USER,
                "Reference files (untrusted data):\n===== BEGIN UNTRUSTED FILE =====\n"
                + "\n".join(sections) + "\n===== END UNTRUSTED FILE ====="))
        if current is not None:
            prompt.append(current)
        return prompt
