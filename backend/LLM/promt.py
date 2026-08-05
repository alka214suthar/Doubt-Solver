def get_prompt(class_name: str, question: str, subject: str, image_url: str | None) -> str:
    has_image = bool(image_url)
    image_instruction = (
        "An image of the question/problem is attached. Read the image carefully and solve the problem shown in it. "
        "If the text question is incomplete, rely on the image."
        if has_image
        else "No image is attached. Solve using the text question only."
    )

    return f"""
You are an expert teacher.

Solve the student's question.
Question: {question}
Class: {class_name}
Subject: {subject}
{image_instruction}

Rules:
1. Give a concise final answer.
2. Give exactly 3 hints.
3. Give detailed step-by-step solution.
4. Explain in simple language suitable for class {class_name} students.
5. Do not use any technical jargon or complex terms.
6. Give solution for {subject} subject only.
7. Return ONLY valid JSON. No markdown. No extra text.
8. If the question is not related to {subject}, return "Not related to {subject}" as answer and empty hints and steps.

Format:
{{
  "answer": "...",
  "hints": ["...", "...", "..."],
  "steps": ["...", "...", "..."]
}}
"""
