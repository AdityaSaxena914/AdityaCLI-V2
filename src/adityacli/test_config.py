from pathlib import Path

from adityacli.workspace import WorkspaceManager

workspace = WorkspaceManager()
workspace.load(Path.cwd())

repository = workspace.repository

print("resolve_symbol:")
print(repository.resolve_symbol("RuntimeManager.execute"))

print()

print("resolve_callers:")
print(repository.resolve_callers("RuntimeManager.execute"))

for cls in repository.classes():
    for method in cls.methods:
        for call in method.calls:
            if call.name == "execute":
                print(f"{cls.name}.{method.name} -> {call.name}")