from pprint import pprint
from decimal import Decimal
import time
import spacy
import ujson
import string
import heapq


class DocumentProcessor(object):
    """
        Object the preloads NLP model/s and lookup tables
    """
    def __init__(self, config):
        self.spacy_model_name           = config.get("models", "spacy_model")
        self.unicode_reference_words    = unicode(config.get("models", "reference_words")).split(",")
        self.reference_entities         = map(unicode, config.get("models", "reference_entities").split(","))

        self.heap_k                     = config.getint("models", "top_k")
        self.detection_threshold        = config.getfloat("models", "word_similarity_threshold")

        time_start = time.time()
        print "Loading Spacy Model: %s" % self.spacy_model_name
        self.nlp_model                  = spacy.load(self.spacy_model_name)
        time_end = time.time()
        print "NLP Loading Time: %s\n" % str(time_end - time_start)

    def similarity_top_k_spacy_model(self, json_doc, similarity_threshold=0.0, spacy_model = 'en_core_web_md'):

        print "Starting Top K using %s..." % self.spacy_model_name

        # Clean and feed JSON to model
        unicode_cleaned_json = unicode(' '.join(self.clean_json(json_doc).replace('\n', ' ').split()))
        pprint(unicode_cleaned_json)
        udoc_tokenized = self.nlp_model(unicode_cleaned_json)
        time_start = time.time()
        money_entities = self.extract_labeled_entities(udoc_tokenized, self.reference_entities)
        time_end = time.time()

        pprint(money_entities)
        print "Entity Extraction Time: %s\n" % str(time_end - time_start)

        time_start = time.time()
        result_dict = self.compute_similarity_json_keys_only(self.unicode_reference_words, json_doc)
        time_end = time.time()
        pprint(result_dict)
        print "JSON Key Similarity Top 5 Computation Time: %s\n" % str(time_end - time_start)

    def extract_labeled_entities(self, doc, entity_labels, extract_emails=True):
        # merge entities and noun chunks into one token
        spans = list(doc.ents) + list(doc.noun_chunks)
        for span in spans:
            span.merge()

        extracted_ents = []
        print "\nFiltering entities %s..." % str(entity_labels)
        for labelled_ent in filter(lambda w: (w.ent_type_ in entity_labels) or (w.like_email and extract_emails), doc):
            extracted_ents.append(labelled_ent)
        return extracted_ents

    def compute_similarity_top_k_json_keys_only(self, json_doc, heap_k=5):

        json_dict = ujson.loads(json_doc)
        unicode_json_keys = unicode(" ".join(json_dict.iterkeys()))

        udoc_tokenized = self.nlp_model(unicode_json_keys)
        reference_model_tokens = []
        for ref_word in self.unicode_reference_words:
            reference_model_tokens.append(self.nlp_model(ref_word))

        heap_dict = dict()

        for ref_tkn in self.unicode_reference_words:
            heap_dict[ref_tkn] = []

        for udoc_tkn in udoc_tokenized:
            if not udoc_tkn.is_punct:  # filter out punctuations
                for ref_mdl_tkn in reference_model_tokens:
                    ref_tkn = ref_mdl_tkn[0].text
                    try:
                        sim_val = udoc_tkn.similarity(ref_mdl_tkn[0])

                        tkn_tpl = (sim_val, udoc_tkn)

                        in_heap = False
                        for heap_tpl in heap_dict[ref_tkn]:
                            if heap_tpl[1].text == tkn_tpl[1].text:
                                in_heap = True
                                break

                        if not in_heap:
                            if len(heap_dict[ref_tkn]) < heap_k or sim_val > heap_dict[ref_tkn][0][0]:
                                # If the heap is full, remove the smallest element on the heap.
                                if len(heap_dict[ref_tkn]) == heap_k: heapq.heappop(heap_dict[ref_tkn])
                                # add the current element as the new smallest.
                                heapq.heappush(heap_dict[ref_tkn], tkn_tpl)
                    except KeyError:
                        continue
        return heap_dict

    def process_payload(self, payload_string):
        """
            PII detection of JSON document.

            :param document: HTTP payload containing a JSON document
            :return: True if PII is detected, False otherwise
        """
        json_doc = payload_string.split("\r\n\r\n")[1]
        json_dict = ujson.loads(json_doc)
        unicode_json_keys = unicode(" ".join(json_dict.iterkeys()))

        udoc_tokenized = self.nlp_model(unicode_json_keys)
        reference_model_tokens = []

        heap_dict = dict()
        for ref_word in self.unicode_reference_words:
            reference_model_tokens.append(self.nlp_model(ref_word))
            heap_dict[ref_word] = []

        for udoc_tkn in udoc_tokenized:
            if not udoc_tkn.is_punct:  # filter out punctuations
                for ref_mdl_tkn in reference_model_tokens:
                    ref_tkn = ref_mdl_tkn[0].text
                    try:
                        sim_val = udoc_tkn.similarity(ref_mdl_tkn[0])

                        if sim_val > self.detection_threshold:
                            return True
                    except KeyError:
                        continue

        return False

    def redact_smtp(self, smtp_doc):

        new_smtp_doc = []

        for msg_line in smtp_doc:
            print("Evaluating: [" + str(msg_line) +"] for tokens: ")
            udoc_tokenized = self.nlp_model(msg_line)

            # NER Method ID and redaction:
            new_msg_line = ""
            cursor = 0
            for ent in udoc_tokenized.ents:
                if ent.label_ in self.reference_entities:
                    print(ent.text, ent.start_char, ent.end_char, ent.label_)
                    new_msg_line += msg_line[cursor:ent.start_char] + "[REDACTED]"
                    cursor = ent.end_char

            new_msg_line += msg_line[cursor:-1]
            new_smtp_doc.append(new_msg_line)

        return new_smtp_doc


    def detect_smtp(self, smtp_doc):
        for msg_line in smtp_doc:
            print("Evaluating: [" + str(msg_line) +"] for tokens: ")
            udoc_tokenized = self.nlp_model(msg_line)

            # NER Method ID and redaction:
            new_msg_line = ""
            cursor = 0
            for ent in udoc_tokenized.ents:
                if ent.label_ in self.reference_entities:
                    # Handle detected entities
                    print(ent.text, ent.start_char, ent.end_char, ent.label_)

                    # TODO: Lookup table evaluation

                    # If PII:
                    return True

        # If no detected PII:
        return False


    def clean_json(self, json_doc):
        print "Cleaning JSON..."
        json_syms = '"\':;{}[]'
        time_start = time.time()
        # translator = string.maketrans(string.punctuation, ' '*len(string.punctuation)) #map punctuation to space
        translator = string.maketrans(json_syms, ' ' * len(json_syms))  # map punctuation to space
        result = json_doc.translate(translator)
        # print  result
        time_end = time.time()
        print "JSON Processing Time: %.4E" % (Decimal(time_end - time_start))
        return result