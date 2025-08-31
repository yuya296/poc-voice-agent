from transformers import AutoModelForCausalLM, AutoTokenizer

# model_id = "meta-llama/Llama-2-7b-chat-hf"  # 3B版が無ければ7Bでも可
model_id = "openlm-research/open_llama_3b_v2"

tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=False)

# 量子化 (4bit)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    load_in_4bit=True,
)

prompt = "こんにちは！あなたは誰？"
inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

outputs = model.generate(**inputs, max_new_tokens=200)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
