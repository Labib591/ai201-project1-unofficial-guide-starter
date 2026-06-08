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


def _format_retrieved(hits: list[dict]) -> str:
    """Render each retrieved chunk with its cosine distance + relevance marker
    so a viewer can see *why* the answer is (or isn't) grounded."""
    if not hits:
        return "_(no chunks retrieved)_"
    lines = ["**Lower distance = more relevant. ✅ = used as context (≤0.75), ⚠️ = too weak / dropped.**\n"]
    for i, h in enumerate(hits, 1):
        m = h["metadata"]
        mark = "✅" if h["distance"] <= 0.75 else "⚠️"
        text = h["text"].replace("\n", " ")
        snippet = text[:240] + ("…" if len(text) > 240 else "")
        lines.append(
            f"**{i}. {mark} distance {h['distance']:.3f} — {m['source_name']}** "
            f"(`{m['content_type']}`)\n> {snippet}\n"
        )
    return "\n".join(lines)


def handle_query(question: str):
    question = (question or "").strip()
    if not question:
        return "Please enter a question.", "", ""
    result = ask(question)
    sources = result["sources"]
    sources_md = "\n".join(f"- {s}" for s in sources) if sources else "_(no sources — question not covered by the documents)_"
    retrieved_md = _format_retrieved(result.get("retrieved", []))
    return result["answer"], sources_md, retrieved_md


with gr.Blocks(title="The Unofficial Guide — NJIT") as demo:
    gr.Markdown(
        "# The Unofficial Guide — NJIT\n"
        "Ask about housing, dining, professors, careers, and campus life. "
        "Answers come **only** from collected student reviews and official NJIT pages."
    )
    inp = gr.Textbox(label="Your question", placeholder="e.g. Is the meal plan required?", lines=2)
    btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=8)
    gr.Markdown("### Retrieved from")
    sources = gr.Markdown()
    with gr.Accordion("Retrieved chunks + relevance (distance) scores", open=True):
        retrieved = gr.Markdown()
    gr.Examples(examples=EXAMPLES, inputs=inp)

    btn.click(handle_query, inputs=inp, outputs=[answer, sources, retrieved])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources, retrieved])


if __name__ == "__main__":
    demo.launch()
