"""Data.

Fuel provides two solutions for reading text, and both don't seem
suitable:

- TextFile only reads sequentially
- H5PyDataset is built with an assumption that there exists
  a non-overlapping set of examples.

That said, we need a different basic solution.

"""

from fuel.datasets import Dataset
from fuel.datasets.hdf5 import H5PYDataset
from fuel.utils import do_not_pickle_attributes
from fuel.transformers import Transformer


class TextDataset(Dataset):
    """Provides basic access to lines of a text file."""
    provides_sources = ('words',)
    example_iteration_scheme = None

    def __init__(self, path, **kwargs):
        self._path = path
        super(TextDataset, self).__init__(**kwargs)

    def open(self):
        return open(self._path, 'r')

    def get_data(self, state, request=None):
        return (next(state).strip().split(),)


class _PutTextTransfomer(Transformer):

    def __init__(self, data_stream, dataset, **kwargs):
        super(_PutTextTransfomer, self).__init__(data_stream, **kwargs)
        self._text = dataset.text
        self.produces_examples = data_stream.produces_examples

    def transform_example(self, example):
        c_pos = self.sources.index('contexts')
        q_pos = self.sources.index('questions')
        example = list(example)
        example[c_pos] = self._text[example[c_pos][0]:example[c_pos][1]]
        example[q_pos] = self._text[example[q_pos][0]:example[q_pos][1]]
        return tuple(example)


    def transform_batch(self, batch):
        return (self.transform_example(example) for example in batch)


@do_not_pickle_attributes('text')
class SQuADDataset(H5PYDataset):
    """Adds default transformers."""
    def __init__(self, *args, **kwargs):
        super(SQuADDataset, self).__init__(*args, **kwargs)
        self.default_transformers = [(_PutTextTransfomer, [self], {},)]

    def load(self):
        super(SQuADDataset, self).load()
        self._out_of_memory_open()
        self.text = self._file_handle['text'][:]
        self._out_of_memory_close()
