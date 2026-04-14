from __future__ import annotations

import streamlit as st

from orchestrator import ResumeBuilderOrchestrator


st.set_page_config(page_title="AI Resume Builder", page_icon="📄", layout="wide")

st.title("AI Resume Builder")
st.caption("Paste raw career details, notes, or an unstructured profile to generate a structured resume draft.")

raw_profile = st.text_area(
    "Career details",
    height=320,
    placeholder=(
        "Example:\n"
        "Name: Asha Mehta\n"
        "Email: asha@email.com\n"
        "3 years as Python developer at ABC Tech...\n"
        "Built internal dashboard...\n"
        "B.Tech in Computer Science..."
    ),
)

if st.button("Build Resume", type="primary", use_container_width=True):
    if not raw_profile.strip():
        st.error("Please paste some candidate details first.")
        st.stop()

    orchestrator = ResumeBuilderOrchestrator()

    with st.spinner("Generating resume..."):
        try:
            result, saved_path = orchestrator.run(raw_profile)
        except Exception as exc:
            st.error(f"Processing failed: {exc}")
            st.stop()

    st.subheader("Short Summary")
    st.write(result.summary.short_summary)

    st.subheader("Detailed Summary")
    st.write(result.summary.detailed_summary)

    st.subheader("Skills")
    if result.skills:
        for skill in result.skills:
            level = f" ({skill.level.value})" if skill.level else ""
            st.write(f"- {skill.name}{level}")
    else:
        st.write("No skills extracted.")

    st.subheader("Experience")
    if result.experience:
        for item in result.experience:
            st.markdown(f"**{item.role} - {item.company}**")
            meta = " | ".join(part for part in [item.duration, item.location] if part)
            if meta:
                st.caption(meta)
            for achievement in item.achievements:
                st.write(f"- {achievement}")
    else:
        st.write("No experience extracted.")

    st.subheader("Education")
    if result.education:
        for item in result.education:
            st.write(f"- {item.degree}, {item.institution}")
    else:
        st.write("No education extracted.")

    st.subheader("Projects")
    if result.projects:
        for project in result.projects:
            st.markdown(f"**{project.name}**")
            st.write(project.description)
    else:
        st.write("No projects extracted.")

    st.subheader("Saved Report Path")
    st.code(saved_path)

    with open(saved_path, "rb") as handle:
        st.download_button(
            label="Download Markdown Resume",
            data=handle.read(),
            file_name=saved_path.split("\\")[-1].split("/")[-1],
            mime="text/markdown",
            use_container_width=True,
        )
