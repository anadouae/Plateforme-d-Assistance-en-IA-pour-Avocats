"""Optional LoRA fine-tune for Sanad-Legal (requires GPU + peft/transformers).

Usage:
  pip install transformers peft datasets accelerate bitsandbytes trl
  python scripts/finetune_sanad_lora.py

If no GPU is available, skip this script and use the Ollama Modelfile
(backend/models/Modelfile) which already includes few-shot specialization.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data" / "sanad_legal_qa.jsonl"
OUT_DIR = Path(__file__).resolve().parents[1] / "models" / "sanad-legal-lora"


def load_rows() -> list[dict]:
    rows = []
    with DATA.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def format_example(row: dict) -> str:
    return (
        f"### Instruction:\n{row['instruction']}\n\n"
        f"### Input:\n{row['input']}\n\n"
        f"### Response:\n{row['output']}"
    )


def main() -> None:
    rows = load_rows()
    print(f"Loaded {len(rows)} Q/A pairs from {DATA}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    export = [{"text": format_example(r)} for r in rows]
    ready_path = OUT_DIR / "train_ready.json"
    ready_path.write_text(json.dumps(export, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Exported training texts to {ready_path}")

    try:
        import torch
        from datasets import Dataset
        from peft import LoraConfig, get_peft_model
        from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
        from trl import SFTTrainer
    except ImportError as exc:
        print(
            "Optional deps missing. Install: transformers peft datasets accelerate bitsandbytes trl\n"
            f"Detail: {exc}\n"
            "Fallback: use `ollama create sanad-legal -f models/Modelfile` (no GPU needed)."
        )
        sys.exit(0)

    if not torch.cuda.is_available():
        print("No CUDA GPU detected. Use the Ollama Modelfile path instead of LoRA.")
        sys.exit(0)

    base_model = "meta-llama/Meta-Llama-3.1-8B-Instruct"
    print(f"Fine-tuning {base_model} with LoRA on {len(rows)} examples...")

    tokenizer = AutoTokenizer.from_pretrained(base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=torch.float16,
        device_map="auto",
    )
    lora = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    )
    model = get_peft_model(model, lora)

    dataset = Dataset.from_list([{"text": format_example(r)} for r in rows])
    args = TrainingArguments(
        output_dir=str(OUT_DIR),
        num_train_epochs=3,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=2e-4,
        logging_steps=5,
        save_strategy="epoch",
        fp16=True,
        report_to=[],
    )
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        args=args,
        tokenizer=tokenizer,
        dataset_text_field="text",
        max_seq_length=1024,
    )
    trainer.train()
    trainer.save_model(str(OUT_DIR))
    tokenizer.save_pretrained(str(OUT_DIR))
    print(f"LoRA adapters saved to {OUT_DIR}")
    print("Next: merge adapters and import into Ollama (see models/README.md).")


if __name__ == "__main__":
    main()
