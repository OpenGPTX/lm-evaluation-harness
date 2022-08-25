from . import gpt2
from . import gpt3
from . import gptx
from . import dummy

MODEL_REGISTRY = {
    "hf": gpt2.HFLM,
    "gpt2": gpt2.GPT2LM,
    "gpt3": gpt3.GPT3LM,
    "gptx": gptx.GPTXLM,
    "dummy": dummy.DummyLM
}


def get_model(model_name):
    return MODEL_REGISTRY[model_name]
