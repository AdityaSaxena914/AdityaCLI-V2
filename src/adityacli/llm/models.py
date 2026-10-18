from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AvailableModel:
    """Read-only LM Studio catalog entry; never a load configuration."""

    id: str
    name: str
    loaded: bool | None = None
    context_window: int | None = None
    quantization: str | None = None

    @property
    def label(self) -> str:
        details = [self.quantization] if self.quantization else []
        details.append("available" if self.loaded is None else "loaded" if self.loaded else "downloaded")
        return f"{self.name} ({', '.join(details)})"
