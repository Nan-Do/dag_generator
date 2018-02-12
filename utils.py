from random import choice
from string import ascii_letters, digits

DEBUG = False


def random_id_generator(size=6, chars=ascii_letters+digits):
    """
    Generate a random id.

    size -> The size of the generated id.
    chars -> The pool of characters to choose to generate the id.

    Returns a string.
    """
    return ''.join(choice(chars) for _ in range(size))


def get_chunks(seq, size, step=1):
    """
    Split a sequence into chunks of different sizes specified by
    size.

    seq -> The sequence to split.
    size -> Size of the chunks
    step -> How much to move on the original list before generating
    the next chunk.

    Similar to partition in clojure, it returns a generator for the
    chunks.
    """
    for x in xrange(0, len(seq) - size + step, step):
        yield seq[x:x+size]


