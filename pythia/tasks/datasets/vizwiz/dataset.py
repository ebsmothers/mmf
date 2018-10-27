import numpy as np

from pythia.tasks.datasets.vqa2.dataset import VQA2Dataset


class VizWizDataset(VQA2Dataset):
    def __init__(self, imdb_file, image_feat_directories, verbose=False,
                 **data_params):
        super(VizWizDataset, self).__init__(imdb_file, image_feat_directories,
                                            verbose, **data_params)
        self.data_params = data_params
        self.name = 'vizwiz'

        if self.data_params['use_ocr']:
            self.context_max_len = self.config['context_max_len']

        if self.data_params['copy_included']:
            self.max_valid_answer_length = 11

    def __getitem__(self, idx):
        sample = super(VizWizDataset, self).__getitem__(idx)
        idx = self.first_element_idx + idx
        image = self.imdb[idx]
        features = self.features_db[idx]
        sample['image_id'] = image['image_name']

        if self.data_params['use_ocr']:
            context_seq = np.zeros((self.context_max_len), np.int32)
            info = features['image_info_0']

            is_ocr = info['is_ocr']
            tokens = info['image_text']

            final_tokens = []

            for token, ocr in zip(tokens, is_ocr):
                if ocr.item() > 0:
                    final_tokens.append(token)
            token_idxs = [self.context_vocab.stoi[w] for w in final_tokens]
            context_len = min(len(token_idxs), self.context_max_len)
            context_seq[:context_len] = token_idxs[:context_len]

            sample['contexts'] = context_seq
            # Context dim is actually 'length' of the final context
            sample['context_dim'] = context_len
        return sample

    def format_for_evalai(self, batch, answers):
        answers = answers.argmax(dim=1)

        predictions = []

        for idx, image_id in enumerate(batch['image_id']):
            answer = self.answer_dict.idx2word(answers[idx])
            # 'COCO_vizwiz_test_000000020255' -> 'VizWiz_test_000000020255.jpg'
            predictions.append({
                'image': "_".join(["VizWiz"] + image_id.split("_")[2:])
                         + ".jpg",
                'answer': answer
            })

        return predictions
