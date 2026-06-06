"""Gradio interface for The Unofficial Guide (Milestone 5).

Run:
    python app.py
Then open http://localhost:7860
"""

import gradio as gr

from src.generate import ask

EXAMPLES = [
    "Is the meal plan required and how much does it cost?",
    "How much does a double room cost on campus?",
    "What do students say about internships and career outcomes?",
    "How do I look for a job on campus?",
    "What do students say about safety around campus?",
]


def handle_query(question: str):
    question = (question or "").strip()
    if not question:
        return "Please enter a question.", ""
    result = ask(question)
    sources = result["sources"]
    sources_md = "\n".join(f"- {s}" for s in sources) if sources else "_(no sources — question not covered by the documents)_"
    return result["answer"], sources_md


with gr.Blocks(title="The Unofficial Guide — NJIT") as demo:
    gr.Markdown(
        "# The Unofficial Guide — NJIT\n"
        "Ask about housing, dining, professors, careers, and campus life. "
        "Answers come **only** from collected student reviews and official NJIT pages."
    )
    inp = gr.Textbox(label="Your question", placeholder="e.g. Is the meal plan required?", lines=2)
    btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Markdown(label="Retrieved from")
    gr.Examples(examples=EXAMPLES, inputs=inp)

    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])


if __name__ == "__main__":
    demo.launch()
