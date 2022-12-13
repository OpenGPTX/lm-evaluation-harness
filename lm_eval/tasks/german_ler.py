"""
German-LER: Fine-Grained Named Entity Recognition in Legal Documents
https://huggingface.co/datasets/elenanereiss/german-ler

The dataset consists of approx. 67,000 sentences and contains 54,000 anno- tated entities.
The 19 fine-grained classes were automatically generalised to seven more coarse-grained classes
(person, location, organization, legal norm, case-by-case regulation,
court decision, and legal literature).Thus, the dataset includes two annotation variants,
i.e., coarse- and fine-grained.

Git: https://github.com/elenanereiss/Legal-Entity-Recognition
Paper: https://link.springer.com/content/pdf/10.1007/978-3-030-33220-4_20.pdf
"""
import datasets
from lm_eval.base import Task, rf
from lm_eval.metrics import mean
from functools import partial
import numpy as np


_CITATION = """
@misc{https://doi.org/10.48550/arxiv.2003.13016,
  doi = {10.48550/ARXIV.2003.13016},
  url = {https://arxiv.org/abs/2003.13016},
  author = {Leitner, Elena and Rehm, Georg and Moreno-Schneider, Julián},
  keywords = {Computation and Language (cs.CL), Information Retrieval (cs.IR), FOS: Computer and information sciences, FOS: Computer and information sciences},
  title = {A Dataset of German Legal Documents for Named Entity Recognition},
  publisher = {arXiv},
  year = {2020},
  copyright = {arXiv.org perpetual, non-exclusive license}
}"""


# Helper functions for aggregation
def _gLER_agg_precision(key, items):
    references, predictions = zip(*items)
    precisions = []

    def precision(ref, pred):
        count = 0
        for true_token in ref:
            for pred_token in pred:
                if not true_token.lower() in pred_token:
                    count = count + 1
        return (len(pred) - count) / len(pred)

    for r, p in zip(references, predictions):
        precisions.append(precision(r, p))
    return np.mean(precisions)


# def _gLER_agg_recall(key, items):

# def _gLER_agg_f1(key, items):


class GermanLER(Task):
    VERSION = 0
    DATASET_PATH = "elenanereiss/german-ler"
    DATASET_NAME = None

    def has_training_docs(self):
        return True

    def has_validation_docs(self):
        return True

    def has_test_docs(self):
        return True

    def training_docs(self):
        if self.has_training_docs():
            return self.dataset["train"]

    def validation_docs(self):
        if self.has_validation_docs():
            return self.dataset["validation"]

    def test_docs(self):
        if self.has_test_docs():
            return self.dataset["test"]

    def list_to_string(self, tokens):
        list_string = ""
        for token in tokens:
            list_string = list_string + token + " "
        return list_string

    def doc_to_text(self, doc):
        return "Text: " + self.list_to_string(doc["tokens"]) + "\n\n" + "Person: "

    def get_target(self, doc, tag):
        coarse_tags = doc["ner_coarse_tags"]
        tokens = doc["tokens"]
        tag_indices = np.where(coarse_tags == tag)[0]
        if len(tag_indices) == 0:
            return ["None"]
        else:
            tag_tokens = [tokens[i] for i in tag_indices]
            return tag_tokens

    def doc_to_target(self, doc):
        # The prepended `" "` is required to space out the `doc_to_text` and
        # `doc_to_target` strings.

        targets = self.get_target(doc, 4)
        label = ""
        for token in targets:
            label = label + token

        return " " + label

    def construct_requests(self, doc, ctx):
        """Uses RequestFactory to construct Requests and returns an iterable of
        Requests which will be sent to the LM.

        :param doc:
            The document as returned from training_docs, validation_docs, or
            test_docs.
        :param ctx: str
            The context string, generated by fewshot_context. This includes the natural
            language description, as well as the few shot examples, and the question
            part of the document for `doc`.
        """

        return rf.greedy_until(ctx, ["\n"])

    def process_results(self, doc, results):
        """Take a single document and the LM results and evaluates, returning a
        dict where keys are the names of submetrics and values are the values of
        the metric for that one document

        :param doc:
            The document as returned from training_docs, validation_docs, or test_docs.
        :param results:
            The results of the requests created in construct_requests.
        """

        pred_tokens = [token for token in results[0].split(" ")]
        true_tokens = self.get_target(doc, 4)

        return {
            # "acc": pred == true_label,
            "precision": (true_tokens, pred_tokens),
            # "recall": (true_label, pred),
            # "f1": (true_label, pred),
        }

    def aggregation(self):
        """
        :returns: {str: [metric_score] -> float}
            A dictionary where keys are the names of submetrics and values are
            functions that aggregate a list of metric scores
        """
        return {
            # "acc": mean,
            "precision": partial(_gLER_agg_precision, "precision"),
            # "recall": partial(_xstance_agg_recall, "recall"),
            # "f1": partial(_xstance_agg_f1, "f1"),
        }

    def higher_is_better(self):
        return {"precision": True}
        # return {"acc": True, "precision": True, "recall": True, "f1": True}
