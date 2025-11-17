from __future__ import annotations

import re
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import List, Optional


SECTION_SUMMARY = "Summary"
SECTION_SKILLS = "Skills"
SECTION_WORK_EXPERIENCE = "Work Experience"


@dataclass
class WorkExperience:
    job_title: str
    company: str
    start_date: str
    end_date: str
    location: str
    experience_points: List[str] = field(default_factory=list)


class ResumeBuilder:
    def __init__(self, file_name: str) -> None:
        self.file_name = file_name
        self.name: Optional[str] = None
        self.address: Optional[str] = None
        self.phone_number: Optional[str] = None
        self.email: Optional[str] = None
        self.contacts: List[tuple[str, str, str]] = []

        self.summary: Optional[str] = None
        self.skills: OrderedDict[str, List[str]] = OrderedDict()
        self.work_experiences: List[WorkExperience] = []
        self._section_order: List[str] = []

    # ------------------------------------------------------------------ #
    # Personal details
    # ------------------------------------------------------------------ #
    def set_name(self, name: str) -> Optional[str]:
        """Store the applicant's display name that will be rendered in the header."""
        error = self._validate_string_param(name, 'name')
        if error:
            return error
        self.name = name.strip()
        return None

    def set_address(self, address: str) -> Optional[str]:
        """Store the mailing, city, or general location line for the header.
        
        Guardrails:
        - Use the format: <City>, <State/Province>, <Country>"""
        error = self._validate_string_param(address, 'address')
        if error:
            return error
        self.address = address.strip()
        return None

    def set_phone_number(self, number: str) -> Optional[str]:
        """Store a primary phone number to combine with the address and email.
        
        Guardrails:
        - use the format (###) ###-####"""
        error = self._validate_string_param(number, 'number')
        if error:
            return error
        self.phone_number = number.strip()
        return None

    def set_email(self, email: str) -> Optional[str]:
        """Store the email address that appears with other contact details."""
        error = self._validate_string_param(email, 'email')
        if error:
            return error
        self.email = email.strip()
        return None

    def add_contact(self, contact_type: str, display_name: str, link: str) -> Optional[str]:
        """Track an external contact method (e.g., GitHub, LinkedIn) with its URL.
        
        Guardrails:
        - For contact_type, place the platform name, for example: Github
        - For display_name, use the username of the URL, for example, if the link was github.com/r-butl, use r-butl
        - For link, place the full URL in the string
        """
        params = {
            'contact_type': contact_type,
            'display_name': display_name,
            'link': link,
        }
        
        for param_name, param_value in params.items():
            error = self._validate_string_param(param_value, param_name)
            if error:
                return error
        
        self.contacts.append((contact_type.strip(), display_name.strip(), link.strip()))
        return None

    # ------------------------------------------------------------------ #
    # Resume sections
    # ------------------------------------------------------------------ #
    def set_summary(self, summary: str) -> Optional[str]:
        """Populates the optional professional summary section.

        Guardrails:
        - Keep the summary concise and focus on alignment with the candidate's experience.
        """
        error = self._validate_string_param(summary, 'summary')
        if error:
            return error
        self.summary = summary.strip()
        self._ensure_section_order(SECTION_SUMMARY)
        return None

    def add_skills(self, section: str, skills: str) -> Optional[str]:
        """Add or append a labeled skills subsection with one or more skills.
        
        Guardrails:
        - Make sure the section is upper case
        - For the skills parameter expects a string of comma seperated values, with no qoutes around values
        """
        params = {
            'section': section,
            'skills': skills,
        }
        
        for param_name, param_value in params.items():
            error = self._validate_string_param(param_value, param_name)
            if error:
                return error
        
        cleaned_section = section.strip()
        if cleaned_section not in self.skills:
            self.skills[cleaned_section] = []
        cleaned_skills = [skill.strip() for skill in skills.split(',') if skill.strip()]
        if not cleaned_skills:
            return "Error: 'skills' must be a comma-separated list with at least one valid skill"
        self.skills[cleaned_section].extend(cleaned_skills)
        if self.skills[cleaned_section]:
            self._ensure_section_order(SECTION_SKILLS)
        return None

    def add_work_experience(
        self,
        job_title: str,
        company: str,
        start_date: str,
        end_date: str,
        location: str,
        experience_points: str,
    ) -> Optional[str]:
        """Append a job entry with bullet-point accomplishments.
        
        Guardrails:
        - For job title, write what position the candidate was, for example: Software Engineer
        - For dates, use the format <month> <last two digits of year> as such: May '25
        - For experience_points do the following:
            - seperate the statements using the symbol sequence '<<'
            - write using the STAR method, aka, Situation, Task, Action, Result. Focus on impact.
            - do not use leading dash or bullet point characters, bullet points will be applied automatically
            - Limit the experience_points to 3 sentences at most. That means use up to two '<<' seperation characters, then stop.
            - Use the most relevan information provided to answer this section.
        """
        params = {
            'job_title': job_title,
            'company': company,
            'start_date': start_date,
            'end_date': end_date,
            'location': location,
            'experience_points': experience_points,
        }
        
        for param_name, param_value in params.items():
            error = self._validate_string_param(param_value, param_name)
            if error:
                return error
        
        points = [points.strip() for points in experience_points.split("<<")]

        if len(points) == 1 and points[0] == '':
            return "Error: 'experience_points' field was left empty."

        if len(points) > 3:
            return "Error: 'experience_points' field contains more than 3 sentences seperated by the symbol '<<'"

        self.work_experiences.append(
            WorkExperience(
                job_title=job_title.strip(),
                company=company.strip(),
                start_date=start_date.strip(),
                end_date=end_date.strip(),
                location=location.strip(),
                experience_points=points,
            )
        )
        self._ensure_section_order(SECTION_WORK_EXPERIENCE)
        return None

    def view_current_resume_contents(self) -> str:
        contents = self.render()
        return contents

    # ------------------------------------------------------------------ #
    # Output helpers
    # ------------------------------------------------------------------ #
    def render(self) -> str:
        lines: List[str] = [
            "% Resume Template",
            r"\documentclass[]{mcdowellcv}",
            "",
            r"\usepackage{amsmath}",
            r"\usepackage{hyperref}",
            r"\usepackage{multicol}",
            "",
            r"\setlength{\parskip}{1.3em}",
            "",
            rf"\name{{{self.name or ''}}}",
            rf"\address{{{self._format_address()}}}",
            rf"\contacts{{{self._format_contacts()}}}",
            "",
            r"\begin{document}",
            "",
            r"\makeheader",
            "",
            r"\vspace{-2.0em}",
            "",
        ]

        for section in self._section_order:
            if section == SECTION_SUMMARY and self.summary:
                lines.extend(self._render_summary())
            elif section == SECTION_SKILLS and self.skills:
                lines.extend(self._render_skills())
            elif section == SECTION_WORK_EXPERIENCE and self.work_experiences:
                lines.extend(self._render_work_experience())

        lines.extend(
            [
                r"\end{document}",
                "",
            ]
        )

        return "\n".join(lines)

    def save(self) -> str:
        latex_content = self.render()
        with open(self.file_name, "w", encoding="utf-8") as file:
            file.write(latex_content)
        return self.file_name

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _ensure_section_order(self, section_name: str) -> None:
        if section_name not in self._section_order:
            self._section_order.append(section_name)

    def _format_address(self) -> str:
        parts = [part for part in [self.address, self.phone_number, self.email] if part]
        return r" \textbullet{} ".join(parts)

    def _format_contacts(self) -> str:
        formatted_contacts = []
        for contact_type, display_name, link in self.contacts:
            hyperlink = rf"\href{{{link}}}{{{display_name}}}"
            if contact_type:
                hyperlink += rf" \textbf{{({contact_type})}}"
            formatted_contacts.append(hyperlink)
        return r" \textbullet{} ".join(formatted_contacts)

    def _render_summary(self) -> List[str]:
        return [
            r"\begin{cvsection}{Summary}",
            f"  {self.summary}",
            r"\end{cvsection}",
            "",
            r"\vspace{-1.0em}",
            "",
        ]

    def _render_skills(self) -> List[str]:
        lines = [
            r"\begin{cvsection}{Skills}",
        ]
        for section, skills in self.skills.items():
            if not skills:
                continue
            skill_line = r", ".join(skills)
            lines.append(f"  \\textbf{{{section}}}: {skill_line} \\\\")
        lines.append(r"\end{cvsection}")
        lines.append("")
        lines.append(r"\vspace{-1.0em}")
        lines.append("")
        return lines

    def _render_work_experience(self) -> List[str]:
        lines = [
            r"\begin{cvsection}{Work Experience}",
        ]
        for index, experience in enumerate(self.work_experiences):
            lines.append(f"  \\textbf{{{experience.job_title}}}  \\\\")
            lines.append(
                f"  {experience.company}, {experience.location} \\textbullet{{}} "
                f"{experience.start_date}--{experience.end_date}"
            )
            if experience.experience_points:
                lines.append("  \\begin{itemize}")
                for point in experience.experience_points:
                    point = self._escape_latex_characters(point)    # escape certain characters
                    lines.append(f"    \\item {point}")
                lines.append("  \\end{itemize}")
            if index < len(self.work_experiences) - 1:
                lines.append("")
                lines.append("  \\vspace{0.2em}")
                lines.append("")
        lines.append(r"\end{cvsection}")
        lines.append("")
        return lines

    def _validate_string_param(self, value: str, param_name: str) -> Optional[str]:
        """Validate a string parameter for type and LaTeX content.
        
        Args:
            value: The value to validate
            param_name: The name of the parameter for error messages
            
        Returns:
            None if valid, error message string if invalid
        """
        if not isinstance(value, str):
            return f"Type error: '{param_name}' must be a string, got {type(value).__name__}"
        if self._has_latex(value):
            return f"Error: LaTeX syntax detected in '{param_name}'. Plain text only."
        return None

    def _has_latex(self, text: str) -> bool:
        """Detect if there is any LaTeX present within the text.
        
        Returns:
            True if LaTeX commands, environments, or math mode delimiters are found, False otherwise.
        """
        if not isinstance(text, str):
            return False
        
        # Check for LaTeX commands (backslash followed by letters)
        if re.search(r'\\[a-zA-Z]+\{?', text):
            return True
        
        # Check for LaTeX environments (\begin{...} or \end{...})
        if re.search(r'\\(begin|end)\{', text):
            return True
        
        # Check for math mode delimiters ($, $$, \(, \), \[, \])
        if re.search(r'\$\$?|\\[\(\)\[\]]', text):
            return True
        
        # Check for LaTeX special command characters (%, &, # when preceded by backslash)
        if re.search(r'\\[%&#]', text):
            return True
        
        return False

    def _escape_latex_characters(self, text) -> str:
        characters_to_escape = ['$', '%']

        for esc_char in characters_to_escape:
            text = text.replace(esc_char, f"\\{esc_char}")

        return text


if __name__ == "__main__":
    test = ResumeBuilder("test_document.tex")

    # 1. Valid input (should not return an error)
    print("Valid input:")
    error = test.add_work_experience(
        job_title="Research Assistant",
        company="Elephant Listening Project, Student Research Group, CSU, Chico",
        start_date="August '24",
        end_date="Expected Graduation December '25",
        location="Chico, CA",
        experience_points="Worked with RNNs and CNNs for elephant detection<<Analyzed infrasound data<<Achieved 95% accuracy using CNNs"
    )
    print("Error:", error)

    # 2. Non-string parameter (should trigger type error)
    print("\nNon-string parameter test (start_date as int):")
    error = test.add_work_experience(
        job_title="Research Assistant",
        company="Elephant Listening Project",
        start_date=2024,
        end_date="Dec '25",
        location="Chico, CA",
        experience_points="Did research on elephant data"
    )
    print("Error:", error)

    # 3. LaTeX detected in job_title (should trigger LaTeX error)
    print("\nLaTeX in job_title:")
    error = test.add_work_experience(
        job_title="Lead \\textbf{Engineer}",
        company="Tech Place",
        start_date="Jan '23",
        end_date="May '24",
        location="Remote",
        experience_points="Managed software projects"
    )
    print("Error:", error)

    # 4. Empty experience_points (should trigger missing skills error)
    print("\nEmpty experience_points:")
    error = test.add_work_experience(
        job_title="Developer",
        company="Web Company",
        start_date="Feb '22",
        end_date="Jan '23",
        location="USA",
        experience_points=""
    )
    print("Error:", error)

    # 5. More than three experience points (test only first three kept)
    print("\nMore than three experiences (should only be 3 used):")
    error = test.add_work_experience(
        job_title="Analyst",
        company="DataCorp",
        start_date="Jul '21",
        end_date="Jul '22",
        location="Boston, MA",
        experience_points="Identified trends<<Built dashboards<<Presented findings<<Extra point should be ignored"
    )
    print("Error:", error)

    # 6. Experience point with LaTeX math (should be error)
    print("\nLaTeX math in experience_points:")
    error = test.add_work_experience(
        job_title="Data Scientist",
        company="Analytics LLC",
        start_date="Feb '20",
        end_date="Mar '21",
        location="New York",
        experience_points="Achieved $99\\%$ accuracy using models"
    )
    print("Error:", error)


    test.save()