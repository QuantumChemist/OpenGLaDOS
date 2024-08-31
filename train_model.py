from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
from datasets import load_dataset
import json

# Read the text file
with open('corpus.txt', 'r', encoding='utf-8') as file:
    lines = file.readlines()

# Remove any unnecessary whitespace characters
lines = [line.strip() for line in lines if line.strip()]

# Convert to JSON format (list of lines)
json_data = {"lines": lines}

# Write the JSON to a file
with open('corpus.json', 'w', encoding='utf-8') as json_file:
    json.dump(json_data, json_file, ensure_ascii=False, indent=4)

print("Conversion to JSON is complete.")

# Example loading a local JSON dataset
dataset = load_dataset('json', data_files={'train': 'corpus.json'})

model_name = "mistralai/Mistral-7B-Instruct-v0.2"
model = AutoModelForCausalLM.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

def tokenize_function(examples):
    return tokenizer(examples["input_text"], padding="max_length", truncation=True, max_length=128)

tokenized_datasets = dataset.map(tokenize_function, batched=True)

training_args = TrainingArguments(
    output_dir="./results",
    per_device_train_batch_size=2,  # Adjust based on your GPU memory
    per_device_eval_batch_size=2,
    num_train_epochs=3,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    logging_dir="./logs",
    logging_steps=10,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["validation"],
)

trainer.train()

model.save_pretrained("./OpenGLaDOS_model")
tokenizer.save_pretrained("./OpenGLaDOS_model")


