from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ProficiencyLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"
    expert = "expert"


class PersonalDetails(BaseModel):
    full_name: str = Field(..., description="Candidate full name.")
    title: str | None = Field(default=None, description="Preferred professional headline or role title.")
    email: str | None = Field(default=None, description="Primary email address.")
    phone: str | None = Field(default=None, description="Primary contact number.")
    location: str | None = Field(default=None, description="City, state, or country.")
    linkedin: str | None = Field(default=None, description="LinkedIn profile URL.")
    portfolio: str | None = Field(default=None, description="Portfolio, GitHub, or personal website URL.")


class ExperienceItem(BaseModel):
    company: str = Field(..., description="Company or organization name.")
    role: str = Field(..., description="Job title or responsibility label.")
    duration: str | None = Field(default=None, description="Employment period in plain text.")
    location: str | None = Field(default=None, description="Job location if available.")
    achievements: list[str] = Field(default_factory=list, description="Concise achievement bullets for the role.")


class EducationItem(BaseModel):
    institution: str = Field(..., description="School, college, or university name.")
    degree: str = Field(..., description="Degree, certification, or program name.")
    duration: str | None = Field(default=None, description="Study period in plain text.")
    score: str | None = Field(default=None, description="Grade, GPA, or marks if relevant.")


class ProjectItem(BaseModel):
    name: str = Field(..., description="Project or case study name.")
    description: str = Field(..., description="Short project summary.")
    technologies: list[str] = Field(default_factory=list, description="Tools or technologies used.")
    impact: str | None = Field(default=None, description="Outcome, metric, or business value.")


class SkillItem(BaseModel):
    name: str = Field(..., description="Skill name.")
    level: ProficiencyLevel | None = Field(default=None, description="Estimated proficiency level if inferable.")


class ResumeSummary(BaseModel):
    short_summary: str = Field(..., description="2-3 line professional summary.")
    detailed_summary: str = Field(..., description="Expanded summary for profile/about usage.")


class FinalResumeOutput(BaseModel):
    personal_details: PersonalDetails = Field(..., description="Core candidate contact and identity details.")
    summary: ResumeSummary = Field(..., description="Candidate professional summary.")
    skills: list[SkillItem] = Field(default_factory=list, description="Skills relevant to the resume.")
    experience: list[ExperienceItem] = Field(default_factory=list, description="Work experience entries.")
    education: list[EducationItem] = Field(default_factory=list, description="Education entries.")
    projects: list[ProjectItem] = Field(default_factory=list, description="Project highlights.")
    certifications: list[str] = Field(default_factory=list, description="Certifications or trainings.")
