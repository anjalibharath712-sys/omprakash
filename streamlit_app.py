import streamlit as st

from mcp import BenefitMCP

st.set_page_config(
    page_title="eBV Benefits Eligibility Demo",
    page_icon="💊",
    layout="wide",
)

mcp = BenefitMCP()

EXAMPLE_PROMPTS = {
    "Covered (no restrictions)": (
        "Check eligibility for NPI 1234567890, patient John Doe born 1980-01-01 male member ID MBR00001, drug NDC 12345-6789."
    ),
    "Prior authorization required": (
        "Check eligibility for NPI 1234567890, patient Sarah Smith DOB 1975-10-21 female member ID MBR00002, drug NDC PA-0000."
    ),
    "Step therapy required": (
        "Check eligibility for NPI 1234567890, patient Peter Lee DOB 1990-06-15 male member ID MBR00003, drug NDC STEP-1234."
    ),
}

REQUIRED_FIELDS = [
    "npi",
    "patient.first_name",
    "patient.last_name",
    "patient.dob",
    "patient.gender",
    "patient.member_id",
    "drug.ndc",
]


def init_state() -> None:
    if "current_payload" not in st.session_state:
        st.session_state.current_payload = {}
    if "result" not in st.session_state:
        st.session_state.result = None
    if "request_text" not in st.session_state:
        st.session_state.request_text = ""


def run_eligibility_check() -> None:
    user_text = st.session_state.request_text.strip()
    if not user_text:
        st.warning("Enter a natural language eligibility request to continue.")
        return

    result = mcp.handle_text_input(user_text, st.session_state.current_payload)
    st.session_state.result = result
    st.session_state.current_payload = result.get("payload", st.session_state.current_payload)


def reset_demo() -> None:
    st.session_state.current_payload = {}
    st.session_state.request_text = ""
    st.session_state.result = None


init_state()

st.title("eBV Benefits Eligibility Demo")
st.write(
    "Use the MCP layer to convert free-form benefit eligibility requests into structured payloads, "
    "validate mandatory fields, and then execute the eligibility check only when the payload is complete."
)

with st.expander("How this demo works", expanded=True):
    st.markdown(
        "- Enter a free-form request containing provider, patient, and drug information.\n"
        "- The MCP attempts to extract structured fields from the text.\n"
        "- If required fields are missing, the backend is not called.\n"
        "- Once the payload is complete, the app executes the mock or remote benefits API call."
    )

col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("Enter a free-form eligibility request")
    st.text_area(
        "Request text",
        key="request_text",
        height=180,
        placeholder=(
            "Example: Check eligibility for NPI 1234567890 for patient Jane Doe DOB 1984-07-10 female "
            "member ID MBR12345 and drug NDC 12345-6789."
        ),
    )

    button_cols = st.columns(len(EXAMPLE_PROMPTS))
    for index, (label, prompt) in enumerate(EXAMPLE_PROMPTS.items()):
        if button_cols[index].button(label):
            st.session_state.request_text = prompt
            run_eligibility_check()

    st.write("---")
    run_button, reset_button = st.columns([1, 1])
    if run_button.button("Run eligibility check"):
        run_eligibility_check()
    if reset_button.button("Reset demo"):
        reset_demo()

    if st.session_state.result is not None:
        status = st.session_state.result.get("status", "unknown")
        st.markdown(f"### Result status: **{status}**")
        st.write(st.session_state.result.get("message", ""))

        if st.session_state.result.get("missing_fields"):
            st.warning(
                "Missing required fields: "
                + ", ".join(st.session_state.result["missing_fields"])
            )

        with st.expander("MCP result payload", expanded=True):
            st.json(st.session_state.result.get("payload", {}))

        if st.session_state.result.get("api_result") is not None:
            with st.expander("Backend eligibility response", expanded=True):
                st.json(st.session_state.result["api_result"])

with col_right:
    st.subheader("MCP requirements & debug info")
    st.markdown("**Required fields enforced by the MCP:**")
    for field in REQUIRED_FIELDS:
        st.markdown(f"- `{field}`")

    st.write("---")
    st.markdown("**Current aggregated payload**")
    st.json(st.session_state.current_payload)

    st.write("---")
    st.markdown("**Quick tips**")
    st.markdown(
        "- Use natural language to describe the request.\n"
        "- Include NPI, patient first/last name, DOB, gender, member ID, and drug NDC.\n"
        "- If you omit values, the MCP will list required fields instead of calling the backend."
    )
