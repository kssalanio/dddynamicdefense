from pprint import pprint
import time
import spacy
import argparse
import os
import ntpath


def test_redaction(nlp_model,
                   reference_entities,
                   email_file_path,
                   test_output_dir):
    ann_file_path=os.path.splitext(email_file_path)[0] + ".ann"
    print("Preprocessing annotations: "+ann_file_path)

    pre_process_multispace(ann_file_path)

    print("Reading file: " + email_file_path)
    with open(email_file_path, 'r') as email_fh:

        # zero-padded email name
        email_file_name_pfx = os.path.splitext(ntpath.basename(email_file_path))[0]

        # open a file to write pii detection results
        out_file_name = os.path.join(test_output_dir, email_file_name_pfx + '.pii')
        print("Writing to file: "+out_file_name)
        with open(out_file_name,
                  'w') as test_email_file_ann:

            pii_token_count = 1
            total_token_count = 0

#            for msg_line in email_fh:

            #print("Evaluating: [" + str(msg_line) + "] for tokens: ")
#            udoc_tokenized = nlp_model(unicode(msg_line))
#             text_body = email_fh.readlines().strip("\n")
#             text_body = u"\n".join(text_body).encode('unicode_escape').decode('utf-8')

            text_body = email_fh.readlines()
            text_body = str_list_to_unicode(text_body)

            print(">>>")
            print(text_body)
            udoc_tokenized = nlp_model(text_body)

            # NER Method ID and redaction:
            new_msg_line = ""
            cursor = 0
            total_token_count += len(udoc_tokenized)

            for ent in udoc_tokenized.ents:
                if (ent.label_ in reference_entities) and (not ent.text.isspace()) and (str(ent.text) != "\n"):
                    # TODO: evaluate tokens (e.g. regex phone # evaluation$
                    #print("T" + str(pii_token_count), ent.label_, ent.start_char, ent.end_char, ent.text)

                    # TODO: write this to (.ann) file, along with original smtp_doc (.txt)
                    # Annotation Format
                    # pii_ann_str = "%s|%s|%s|%s|%s\n" % ("T" + str(pii_token_count), ent.label_, ent.start_char,
                    #                                         ent.end_char, ent.text.strip())
                    pii_ann_str = "%s\t%s %s %s\t%s\n" % ("T" + str(pii_token_count), ent.label_, ent.start_char,
                                                        ent.end_char, ent.text.strip().replace('\n', ' ').replace('\r', ''))

                    if len(pii_ann_str) > 1:
                        print(pii_ann_str)
                        test_email_file_ann.write(pii_ann_str)

                    pii_token_count += 1

            print("Email token count: " + str(total_token_count))
            cnt_file_name=os.path.splitext(email_file_path)[0] + ".cnt"
            with open(cnt_file_name,
                      'w') as test_email_file_cnt:
                test_email_file_cnt.write(str(total_token_count)+"\n")

def str_list_to_unicode(str_list):
    new_list=[]
    for line in str_list:
        new_list.append(unicode(line))
    return u"\n".encode("utf").join(new_list)

def eval_emails(emails_dir):
    time_start = time.time()
    spacy_model_name = 'en_core_web_md'
    print "Loading Spacy Model: %s" % spacy_model_name
    nlp_model = spacy.load(spacy_model_name)
    time_end = time.time()
    print "NLP Loading Time: %s\n" % str(time_end - time_start)



    fcount = 0

    for filename in os.listdir(emails_dir):

        # if fcount > 10:
        #     return
        # else:
        #     fcount += 1

        #print(os.path.splitext(filename)[1]+"|"+filename)
        if os.path.splitext(filename)[1] == ".txt":
            filepath = os.path.join(emails_dir, filename)
            test_redaction(nlp_model,
                           ["PERSON", "MONEY", "CARDINAL", "GPE", "LOC"],
                           filepath,
                           emails_dir)


def pre_process_multispace(filepath, delimiter="|"):
    """
    Preprocess a csv file containing multiple spaces. Creates
    a new CSV file.

    :param filepath: filepath of the CSV file
    :param delimiter: delimiter for the output csv file
    """
    newpath = os.path.splitext(filepath)[0]+".csv"
    with open(filepath, "r") as src_csv_file:
        with open(newpath, "w") as dst_csv_file:
            for src_line in src_csv_file:
                dst_csv_file.write(delimiter.join(src_line.split())+"\n")


def process_results(emails_dir):
    filepath_sum = os.path.join(emails_dir, "summary.csv")
    print("Writing summary to: " + filepath_sum)
    with open(filepath_sum, 'w') as summary_fh:

        for filename_cnt in os.listdir(emails_dir):
            filename_tpl = os.path.splitext(filename_cnt)
            if filename_tpl[1] == ".cnt":
                filepath_cnt = os.path.join(emails_dir, filename_cnt)
                filepath_ann = os.path.join(emails_dir, (filename_tpl[0] + ".ann"))
                filepath_pii = os.path.join(emails_dir, (filename_tpl[0] + ".pii"))

                print("Reading files: ")
                print(filepath_cnt)
                print(filepath_ann)
                print(filepath_pii)
                compare_dict = dict()

                with open(filepath_ann, 'r') as ann_fh:
                    with open(filepath_pii, 'r') as pii_fh:

                        ann_lst = []
                        for ann_line in ann_fh:
                            if ann_line == "\n": continue

                            ann_id, ann_label, ann_pos, ann_text = split_ann_line(ann_line)
                            #ann_tpl = (ann_id, ann_label, ann_text)
                            ann_tpl = ("", ann_label, ann_text)

                            ann_lst.append(ann_tpl)
                            if ann_tpl not in compare_dict.keys():
                                compare_dict[ann_tpl] = []

                        pii_lst = []
                        for pii_line in pii_fh:
                            if pii_line == "\n": continue

                            pii_id, pii_label, pii_pos, pii_text = split_ann_line(pii_line)

                            pii_tpl = (pii_id, pii_label, pii_text)
                            pii_lst.append(pii_tpl)

                        for pii_tpl in pii_lst:
                            for ann_tpl in ann_lst:
                                if (pii_tpl[2] in ann_tpl[2]) or (ann_tpl[2] in pii_tpl[2]):
                                    compare_dict[ann_tpl].append(pii_tpl)

                        pprint(compare_dict)

                        for ann_tpl, pii_tpl_lst in compare_dict.iteritems():
                            # Evaluate False Negatives
                            if not pii_tpl_lst:
                                out_str = "%s|%s|%s|||FN\n" % (filename_tpl[0],
                                                                     ann_tpl[1],
                                                                     ann_tpl[2].strip().replace('\n', ' ').replace('\r', ''))
                                print ">>> "+out_str
                                summary_fh.write(out_str)

                            # Evaluate True Positives
                            else:
                                for pii_tpl in pii_tpl_lst:
                                    out_str = "%s|%s|%s|%s|%s|TP\n" % (filename_tpl[0],
                                                                             ann_tpl[1],
                                                                             ann_tpl[2].strip().replace('\n', ' ').replace('\r', ''),
                                                                             pii_tpl[1],
                                                                             pii_tpl[2].strip().replace('\n', ' ').replace('\r', ''))
                                    print ">>> " + out_str
                                    summary_fh.write(out_str)

                        # Evaluate False Positives
                        for pii_tpl in pii_lst:
                            # if pii_tpl not in compare_dict.values():
                            #     out_str = "%s|||%s|%s|FP\n" % (filename_tpl[0],
                            #                                          pii_tpl[1],
                            #                                          pii_tpl[2].strip().replace('\n', ' ').replace('\r', ''))
                            #     print ">>> " + out_str
                            #     summary_fh.write(out_str)

                            fp_status = True
                            for pii_list in compare_dict.values():
                                if pii_lst:
                                   for tmp_tpl in pii_lst:
                                       if pii_tpl == tmp_tpl:
                                           fp_status = False

                            if fp_status:
                                out_str = "%s|||%s|%s|FP\n" % (filename_tpl[0],
                                                                         pii_tpl[1],
                                                                         pii_tpl[2].strip().replace('\n', ' ').replace('\r', ''))
                                print ">>> " + out_str
                                summary_fh.write(out_str)

def split_ann_line(ann_line):
    #print(ann_line)
    #print(ann_line.split("\t"))
    ann_id, ann_label_pos, ann_text = ann_line.split("\t")
    ann_label, ann_pos = ann_label_pos.split(" ", 1)
    return ann_id, ann_label, ann_pos, ann_text

def count_true_negatives(email_dir):
    """
    # TODO: missing token count mapped to annotated & false negatives
    retokenize and eval which tokens are substring of the annotated false negatives
    - token count of actual false negatives

    :param email_dir:
    :return:
    """
    for filename_cnt in os.listdir(emails_dir):
        filename_tpl = os.path.splitext(filename_cnt)
        if filename_tpl[1] == ".cnt":
            filepath_cnt = os.path.join(emails_dir, filename_cnt)
            filepath_ann = os.path.join(emails_dir, (filename_tpl[0] + ".ann"))
            filepath_pii = os.path.join(emails_dir, (filename_tpl[0] + ".pii"))

            print("Reading files: ")
            print(filepath_cnt)
            print(filepath_ann)
            print(filepath_pii)
            compare_dict = dict()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='filter or summary')
    parser.add_argument('operation', help='filter or summary')
    args= parser.parse_args()

    emails_dir = "/home/ken/Dev/workspaces/PycharmProjects/sample_data/randys_email_test_data/enron/"

    if args.operation == "filter":
        eval_emails(emails_dir)
    elif args.operation == "summary":
        process_results(emails_dir)
    else:
        raise Exception("Invalid arg: " + args.operation)
