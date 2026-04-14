from __future__ import annotations

from pydantic import BaseModel, ValidationError

from flotorch_client import FloTorchClient
from models.schemas import FinalResumeOutput, ResumeSummary
from tools.export_resume import export_markdown_resume
from tools.parse_profile import parse_profile_input

_JSON_SYSTEM = (
    "You extract structured career information. "
    "Return valid JSON only. No markdown fences. No extra commentary."
)

_TEXT_SYSTEM = (
    "You are a resume writing assistant. "
    "Write clearly, professionally, and keep outputs concise."
)


def _strip_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


class ResumeBuilderOrchestrator:
    def __init__(self, client: FloTorchClient | None = None) -> None:
        self.client = client or FloTorchClient()

    def _validated(self, model_class: type[BaseModel], prompt: str, raw_output: str) -> BaseModel:
        cleaned_output = _strip_fences(raw_output)
        try:
            return model_class.model_validate_json(cleaned_output)
        except ValidationError as original_error:
            repair_prompt = (
                "Repair the following output so it becomes valid JSON for this schema only.\n\n"
                f"Schema:\n{model_class.model_json_schema()}\n\n"
                f"Original prompt:\n{prompt}\n\n"
                f"Broken output:\n{cleaned_output}"
            )
            repaired = self.client.generate(system_prompt=_JSON_SYSTEM, user_prompt=repair_prompt)
            repaired_output = _strip_fences(repaired)
            try:
                return model_class.model_validate_json(repaired_output)
            except ValidationError as repair_error:
                raise ValueError(
                    f"JSON repair failed for {model_class.__name__}. "
                    f"Original error: {original_error} Repair error: {repair_error} "
                    f"Last raw output:\n{cleaned_output}"
                ) from repair_error

    def summarize(self, profile_text: str) -> ResumeSummary:
        prompt = (
            "Create a concise professional summary from the candidate information below.\n\n"
            f"Return JSON matching this schema:\n{ResumeSummary.model_json_schema()}\n\n"
            f"Candidate input:\n{profile_text}"
        )
        raw_output = self.client.generate(system_prompt=_JSON_SYSTEM, user_prompt=prompt)
        return self._validated(ResumeSummary, prompt, raw_output)

    def extract_resume_data(self, profile_text: str, summary: ResumeSummary) -> FinalResumeOutput:
        prompt = (
            "Build a complete resume data object from the candidate input.\n"
            "Infer missing structure conservatively. Do not invent hard facts.\n\n"
            f"Return JSON matching this schema:\n{FinalResumeOutput.model_json_schema()}\n\n"
            f"Candidate input:\n{profile_text}\n\n"
            f"Approved summary:\nShort: {summary.short_summary}\nDetailed: {summary.detailed_summary}"
        )
        raw_output = self.client.generate(system_prompt=_JSON_SYSTEM, user_prompt=prompt)
        return self._validated(FinalResumeOutput, prompt, raw_output)

    def build_report_markdown(self, output: FinalResumeOutput) -> str:
        lines: list[str] = []
        details = output.personal_details

        lines.append(f"# {details.full_name}")
        if details.title:
            lines.append(f"**{details.title}**")

        contact_parts = [
            part for part in [details.email, details.phone, details.location, details.linkedin, details.portfolio] if part
        ]
        if contact_parts:
            lines.append(" | ".join(contact_parts))

        lines.append("")
        lines.append("## Professional Summary")
        lines.append(output.summary.short_summary)
        lines.append("")
        lines.append(output.summary.detailed_summary)

        if output.skills:
            lines.append("")
            lines.append("## Skills")
            for skill in output.skills:
                level = f" ({skill.level.value})" if skill.level else ""
                lines.append(f"- {skill.name}{level}")

        if output.experience:
            lines.append("")
            lines.append("## Experience")
            for item in output.experience:
                header_parts = [item.role, item.company]
                header = " - ".join(part for part in header_parts if part)
                meta_parts = [item.duration, item.location]
                meta = " | ".join(part for part in meta_parts if part)
                lines.append(f"### {header}")
                if meta:
                    lines.append(meta)
                for achievement in item.achievements:
                    lines.append(f"- {achievement}")

        if output.education:
            lines.append("")
            lines.append("## Education")
            for item in output.education:
                lines.append(f"- **{item.degree}**, {item.institution}")
                meta = " | ".join(part for part in [item.duration, item.score] if part)
                if meta:
                    lines.append(f"  {meta}")

        if output.projects:
            lines.append("")
            lines.append("## Projects")
            for project in output.projects:
                lines.append(f"### {project.name}")
                lines.append(project.description)
                if project.technologies:
                    lines.append(f"- Technologies: {', '.join(project.technologies)}")
                if project.impact:
                    lines.append(f"- Impact: {project.impact}")

        if output.certifications:
            lines.append("")
            lines.append("## Certifications")
            for certification in output.certifications:
                lines.append(f"- {certification}")

        return "\n".join(lines).strip()

    def run(self, raw_text: str) -> tuple[FinalResumeOutput, str]:
        cleaned_text = parse_profile_input(raw_text)
        summary = self.summarize(cleaned_text)
        resume_output = self.extract_resume_data(cleaned_text, summary)
        resume_output.summary = summary
        markdown = self.build_report_markdown(resume_output)
        file_path = export_markdown_resume(markdown)
        return resume_output, file_path
