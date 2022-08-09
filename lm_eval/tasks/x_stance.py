"""
X-Stance: A Multilingual Multi-Target Dataset for Stance Detection
http://ceur-ws.org/Vol-2624/paper9.pdf

The x-stance dataset consists of more than 150 political questions and 67,000 comments by candidates.
It can be used to train and evaluate stance detection systems.
Comments are in German, French and Italian (for this task only the German subset has been selected). Questions are given in all three languages and English.
The data have been extracted from the Swiss voting advice platform Smartvote.

https://github.com/ZurichNLP/xstance
"""
import datasets
from lm_eval.base import Task, rf
from lm_eval.metrics import mean
from functools import partial
import numpy as np

_CITATION = """
@inproceedings{vamvas2020xstance,
    author    = "Vamvas, Jannis and Sennrich, Rico",
    title     = "{X-Stance}: A Multilingual Multi-Target Dataset for Stance Detection",
    booktitle = "Proceedings of the 5th Swiss Text Analytics Conference (SwissText)  16th Conference on Natural Language Processing (KONVENS)",
    address   = "Zurich, Switzerland",
    year      = "2020",
    month     = "jun",
    url       = "http://ceur-ws.org/Vol-2624/paper9.pdf"
}
"""

# Helper functions for aggregation (separate function for each metric)
def _xstance_agg_precision(key, items):
    references, predictions = zip(*items)
    precision_metric = datasets.load_metric("precision")
    return precision_metric.compute(references=references, predictions=predictions, average='macro', labels= np.unique(predictions))[key]

def _xstance_agg_recall(key, items):
    references, predictions = zip(*items)
    recall_metric = datasets.load_metric("recall")
    return recall_metric.compute(references=references, predictions=predictions, average='macro', labels= np.unique(predictions))[key]

def _xstance_agg_f1(key, items):
    references, predictions = zip(*items)
    f1_metric = datasets.load_metric("f1")
    return f1_metric.compute(references=references, predictions=predictions, average='macro', labels= np.unique(predictions))[key]

class XStance(Task):
    VERSION = 0
    DATASET_PATH = "strombergnlp/x-stance"
    # Select only German part of the dataset
    DATASET_NAME = None
    TOPIC = "Thema: "
    OPINION = "Meine Meinung (pro oder contra): "
    STANCE = "Meine Meinung ist (pro oder contra): "
    FAVOR = "pro"
    AGAINST = "contra"
    
    
    def has_training_docs(self):
        return True

    def has_validation_docs(self):
        return True

    def has_test_docs(self):
        return True

    def training_docs(self):
        if self.has_training_docs():
            if self._training_docs is None:
                self._training_docs = list(self.dataset["train"])

            return self._training_docs

    def validation_docs(self):
        if self.has_validation_docs():
            return self.dataset["validation"]

    def test_docs(self):
        if self.has_test_docs():
            return self.dataset["test"]
        
    def doc_to_text(self, doc):
        return self.TOPIC + doc["question"]+ "\n\n"+ self.OPINION + doc["comment"]+ "\n\n" + self.STANCE # Formatting the prompts capitalized in German gives the highest scores

    def doc_to_target(self, doc):
        target = doc["label"]
        return " " + target

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
        # rf.loglikelihood as the task is a classification problem. For each document the model predicts loglikelihood for the correct label
        # ctx is the fully formatted fewshot example, i.e. K examples + comment to rate
        
        ll_favor = rf.loglikelihood(ctx, " " + self.FAVOR)
        ll_against = rf.loglikelihood(ctx, " " + self.AGAINST)

        return ll_favor, ll_against

    def process_results(self, doc, results):
        """Take a single document and the LM results and evaluates, returning a
        dict where keys are the names of submetrics and values are the values of
        the metric for that one document

        :param doc:
            The document as returned from training_docs, validation_docs, or test_docs.
        :param results:
            The results of the requests created in construct_requests.
        """

        pred = 0
        favor, against = results
        
        # Evaluation metrics will only work with numerical labels
        if favor[0] > against[0]:
            pred = 1
        else:
            pred = 0     
        true_label = doc["label"]
        print(self.FAVOR)
        return {"acc": pred==true_label, "precision":(true_label, pred), "recall":(true_label, pred), "f1":(true_label, pred)}
    
    def aggregation(self):
        """
        :returns: {str: [metric_score] -> float}
            A dictionary where keys are the names of submetrics and values are
            functions that aggregate a list of metric scores
        """

        return {"acc":mean, "precision": partial(_xstance_agg_precision, "precision"), 
                "recall" : partial(_xstance_agg_recall, "recall"), 
                "f1" : partial(_xstance_agg_f1, "f1")}

    def higher_is_better(self):
        return {"acc":True, "precision":True, "recall":True, "f1":True}
# German part of the dataset  
class XStanceDE(XStance):
    VERSION = 0
    DATASET_PATH = "strombergnlp/x-stance"
    DATASET_NAME = "de"
    TOPIC = "Thema: "
    OPINION = "Meine Meinung (pro oder contra): "
    STANCE = "Meine Meinung ist (pro oder contra): "
    FAVOR = "pro"
    AGAINST = "contra"
    
# French part of the dataset
class XStanceFR(XStance):
    VERSION = 0
    DATASET_PATH = "strombergnlp/x-stance" 
    DATASET_NAME = "fr"
    TOPIC = "Thème: "
    OPINION = "Mon opinion (pour ou contre): "
    STANCE = "Mon opinion est (pour ou contre): "
    FAVOR = "pour"
    AGAINST = "contre"
